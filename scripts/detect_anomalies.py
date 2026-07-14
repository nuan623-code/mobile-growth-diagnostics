#!/usr/bin/env python3
"""Run the anomaly playbooks over the unified data structure.

Methods: period-over-period shift, rolling mean ± k·σ outliers, structural gaps,
consistency checks (*_diff metrics), and ratio anomalies. Stdlib only.

Thresholds are read from references/anomaly_playbooks.md (the YAML block at the
top), so clients edit them in one place. Falls back to built-in defaults if the
file or PyYAML is unavailable (a tiny inline parser handles the simple block).

Usage:
  python detect_anomalies.py --data unified.json --out anomalies.json \
      [--playbooks ../references/anomaly_playbooks.md] [--scenarios data_quality,ua_performance]

Output: list of anomaly dicts with the uniform structure
  {severity, scenario, metric, slice, change, baseline, cause, action, query}
(cause/action are left as short hints; Claude rewrites them via report_copy.md.)
"""
import argparse
import json
import os
import statistics as stats
from collections import defaultdict

DEFAULT_THRESHOLDS = {
    "install_drop_pct": -0.30, "install_drop_percentile": 0.05,
    "cpi_rise_pct": 0.25, "roas_floor_d7": 0.15, "roas_floor_d30": 0.30,
    "retention_drop_pct": -0.20, "reconciliation_diff_pct": 0.10,
    "ctr_sigma": 3.0, "outlier_k": 3.0, "skan_null_rate_max": 0.20,
    "invalid_payload_rate_max": 0.05, "min_installs_for_signal": 50,
    "retention_benchmark_tol": 0.30, "ecpi_benchmark_tol": 0.50,
}
SEVERITY_BANDS = {"high": 2.0, "medium": 1.0, "low": 0.5}

# Adjust dimension values -> benchmark table geo names (see playbooks §8.5).
GEO_ALIASES = {
    "Viet Nam": "Vietnam", "Korea": "South Korea",
    "Republic Of Korea": "South Korea", "Korea, Republic Of": "South Korea",
    "Russian Federation": "Russia", "Türkiye": "Turkey",
    "United States Of America": "United States", "USA": "United States",
    "UAE": "United Arab Emirates", "UK": "United Kingdom",
}
BMK_RET_METRICS = {
    "retention_rate_1d": "ret_d1", "retention_rate_7d": "ret_d7",
    "retention_rate_14d": "ret_d14", "retention_rate_30d": "ret_d30",
}


def load_benchmarks(path):
    """Index benchmarks_2025h2.json as {(vertical, sub, os, geo, metric): median}."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        entries = json.load(f).get("benchmarks", [])
    return {(b["vertical"], b["sub_vertical"], b["os"], b["geo"], b["metric"]):
            b["median"] for b in entries if b.get("median")}


def parse_vertical(spec):
    """'Gaming/Casino[/android]' -> (vertical, sub_vertical, pinned_os|None)."""
    if not spec:
        return None
    parts = [p.strip() for p in str(spec).split("/") if p.strip()]
    if not parts:
        return None
    vertical = parts[0]
    sub = parts[1] if len(parts) > 1 else vertical
    os_pin = parts[2].lower() if len(parts) > 2 else None
    return vertical, sub, os_pin


def _row_bmk_ctx(row, app_verticals, default_vertical):
    """Resolve (vertical, sub, os, geo) for a row, or None if unmappable."""
    spec = (app_verticals or {}).get(row.get("app")) or default_vertical
    parsed = parse_vertical(spec)
    if not parsed:
        return None
    vertical, sub, os_pin = parsed
    os_ = str(row.get("platform") or "").strip().lower() or os_pin
    if os_ not in ("android", "ios"):
        return None
    country = row.get("country")
    geo = GEO_ALIASES.get(country, country)
    return vertical, sub, os_, geo


def load_thresholds(playbooks_path):
    th = dict(DEFAULT_THRESHOLDS)
    bands = dict(SEVERITY_BANDS)
    if not playbooks_path or not os.path.exists(playbooks_path):
        return th, bands
    with open(playbooks_path, "r", encoding="utf-8") as f:
        text = f.read()
    # Extract the first ```yaml ... ``` fenced block.
    if "```yaml" in text:
        block = text.split("```yaml", 1)[1].split("```", 1)[0]
        section = None
        for line in block.splitlines():
            raw = line.rstrip()
            if not raw.strip() or raw.strip().startswith("#"):
                continue
            if not raw.startswith(" ") and raw.endswith(":"):
                section = raw.strip()[:-1]
                continue
            if ":" in raw:
                key, val = raw.strip().split(":", 1)
                val = val.split("#", 1)[0].strip()
                try:
                    num = float(val)
                except ValueError:
                    continue
                if section == "severity_bands":
                    bands[key] = num
                else:
                    th[key] = num
    return th, bands


def _sev(ratio, bands):
    """ratio = |observed change| / threshold magnitude. Map to a band."""
    if ratio >= bands["high"]:
        return "high"
    if ratio >= bands["medium"]:
        return "medium"
    return "low"


def _slice_key(row, dims):
    return " × ".join(f"{d}={row[d]}" for d in dims if d in row and d != "date")


def _by_slice_timeseries(rows, dims, metric):
    """Group rows into {slice_key: [(date, value), ...] sorted by date}."""
    series = defaultdict(list)
    for r in rows:
        if metric in r and isinstance(r.get(metric), (int, float)) and "date" in r:
            series[_slice_key(r, dims)].append((r["date"], r[metric]))
    for k in series:
        series[k].sort(key=lambda t: t[0])
    return series


def _pct_change(curr, prev):
    if prev in (None, 0):
        return None
    return (curr - prev) / abs(prev)


def detect(data, scenarios, th, bands, bmk=None, app_verticals=None,
           default_vertical=None):
    rows = data["rows"]
    dims = [d for d in data["meta"]["dimensions"]]
    anomalies = []
    bmk = bmk or {}

    def add(scenario, metric, sl, change, baseline, cause, action, query, sev):
        anomalies.append({
            "severity": sev, "scenario": scenario, "metric": metric,
            "slice": sl, "change": change, "baseline": baseline,
            "cause": cause, "action": action, "query": query,
        })

    # ---- Data quality: install/session cliffs + gaps ----
    if "data_quality" in scenarios:
        for metric in ("installs", "sessions"):
            for sl, ts in _by_slice_timeseries(rows, dims, metric).items():
                vals = [v for _, v in ts]
                if not vals or max(vals) < th["min_installs_for_signal"]:
                    continue
                # cliff: last point vs trailing mean
                if len(ts) >= 4:
                    hist = vals[:-1]
                    curr = vals[-1]
                    base = stats.mean(hist)
                    ch = _pct_change(curr, base)
                    if ch is not None and ch <= th["install_drop_pct"]:
                        ratio = abs(ch) / abs(th["install_drop_pct"])
                        add("data_quality", metric, sl,
                            f"{ch*100:.0f}% vs trailing mean",
                            f"{base:.0f}", "install_cliff",
                            "investigate spend pause / tracking / attribution loss",
                            f"metric={metric}; dims={dims}; cliff vs trailing mean",
                            _sev(ratio, bands))
                # structural gap: a zero among otherwise non-zero history
                if any(v == 0 for v in vals[:-0] or vals) and any(v > 0 for v in vals):
                    zeros = [d for d, v in ts if v == 0]
                    if zeros:
                        add("data_quality", metric, sl,
                            f"zero on {len(zeros)} date(s): {zeros[:3]}",
                            "non-zero history", "missing_data",
                            "check delivery / ingestion gap",
                            f"metric={metric}; dims={dims}; zero-row gap",
                            "high")
        # attribution loss
        for sl, ts in _by_slice_timeseries(rows, dims, "network_installs_diff_signed").items():
            vals = [abs(v) for _, v in ts]
            if vals and ts[-1][1] and abs(ts[-1][1]) > 0:
                base = stats.mean(vals[:-1]) if len(vals) > 1 else 0
                if base and abs(ts[-1][1]) > base * 2:
                    add("data_quality", "network_installs_diff_signed", sl,
                        f"{ts[-1][1]:.0f} (>2× baseline)", f"{base:.0f}",
                        "attribution_loss_or_overreporting",
                        "reconcile attribution vs network",
                        "metric=network_installs_diff_signed; abs > 2× trailing mean",
                        "medium")
        # SKAN ratios
        for r in rows:
            nr = r.get("skad_conversion_value_null_rate")
            if isinstance(nr, (int, float)) and nr > th["skan_null_rate_max"]:
                add("data_quality", "skad_conversion_value_null_rate",
                    _slice_key(r, dims), f"{nr*100:.0f}%",
                    f"max {th['skan_null_rate_max']*100:.0f}%", "skan_config",
                    "audit conversion-value config / postback parsing",
                    "metric=skad_conversion_value_null_rate; ratio threshold",
                    _sev(nr / th["skan_null_rate_max"], bands))

    # ---- UA performance ----
    if "ua_performance" in scenarios:
        for metric in ("ecpi", "ecpc", "ecpm"):
            for sl, ts in _by_slice_timeseries(rows, dims, metric).items():
                if len(ts) >= 2:
                    ch = _pct_change(ts[-1][1], stats.mean([v for _, v in ts[:-1]]))
                    if ch is not None and ch >= th["cpi_rise_pct"]:
                        add("ua_performance", metric, sl, f"+{ch*100:.0f}%",
                            f"{stats.mean([v for _, v in ts[:-1]]):.2f}",
                            "bid_pressure_or_creative_fatigue",
                            "review bids / targeting / creative refresh",
                            f"metric={metric}; PoP rise", _sev(ch / th["cpi_rise_pct"], bands))
        for metric, floor in (("roas_7d", th["roas_floor_d7"]), ("roas_30d", th["roas_floor_d30"])):
            for r in rows:
                v = r.get(metric)
                inst = r.get("installs", 0) or 0
                if isinstance(v, (int, float)) and v < floor and inst >= th["min_installs_for_signal"]:
                    add("ua_performance", metric, _slice_key(r, dims),
                        f"{v*100:.0f}% < floor {floor*100:.0f}%", f"floor {floor*100:.0f}%",
                        "low_traffic_quality_or_monetization_lag",
                        "reduce/pause or investigate monetization",
                        f"metric={metric}; below floor", _sev((floor - v) / floor + 1, bands))
        for metric in ("retention_rate_1d", "retention_rate_7d", "retention_rate_30d"):
            for sl, ts in _by_slice_timeseries(rows, dims, metric).items():
                if len(ts) >= 2:
                    ch = _pct_change(ts[-1][1], stats.mean([v for _, v in ts[:-1]]))
                    if ch is not None and ch <= th["retention_drop_pct"]:
                        add("ua_performance", metric, sl, f"{ch*100:.0f}%",
                            f"{stats.mean([v for _, v in ts[:-1]])*100:.1f}%",
                            "low_quality_mix_or_product_regression",
                            "segment by network/country; check product changes",
                            f"metric={metric}; PoP drop", _sev(abs(ch) / abs(th["retention_drop_pct"]), bands))
        # Benchmark-relative checks (playbooks §8.5). Skip silently whenever the
        # app→vertical mapping, the OS, or the benchmark cell is missing:
        # a missing benchmark is not an anomaly.
        for r in rows:
            ctx = _row_bmk_ctx(r, app_verticals, default_vertical)
            if not ctx:
                continue
            vertical, sub, os_, geo = ctx
            inst = r.get("installs")
            if isinstance(inst, (int, float)) and inst < th["min_installs_for_signal"]:
                continue
            tol = th["retention_benchmark_tol"]
            for metric, bmk_metric in BMK_RET_METRICS.items():
                v = r.get(metric)
                if not isinstance(v, (int, float)):
                    continue
                # retention only: fall back to the sub-vertical ALL-geo row
                used_geo, med = geo, bmk.get((vertical, sub, os_, geo, bmk_metric))
                if not med:
                    used_geo, med = "ALL", bmk.get((vertical, sub, os_, "ALL", bmk_metric))
                if not med or v >= med * (1 - tol):
                    continue
                gap = (med - v) / med
                add("ua_performance", metric, _slice_key(r, dims),
                    f"{v*100:.1f}% vs benchmark median {med*100:.0f}% (-{gap*100:.0f}%)",
                    f"Adjust'25Q4 {sub}/{used_geo}/{os_} median {med*100:.0f}%",
                    "structurally_below_category_baseline",
                    "check traffic quality & onboarding; benchmark is directional — pair with own trend",
                    f"metric={metric}; vs benchmarks_2025h2 [{vertical}/{sub}/{os_}/{used_geo}]",
                    _sev(gap / tol, bands))
            v = r.get("ecpi")
            tol = th["ecpi_benchmark_tol"]
            if isinstance(v, (int, float)) and v > 0 and geo:
                med = bmk.get((vertical, sub, os_, geo, "ecpi"))  # per-geo only, no fallback
                if med and v > med * (1 + tol):
                    over = (v - med) / med
                    add("ua_performance", "ecpi", _slice_key(r, dims),
                        f"${v:.2f} vs benchmark median ${med:.2f} (+{over*100:.0f}%)",
                        f"Adjust'25Q4 {sub}/{geo}/{os_} median ${med:.2f}",
                        "paying_above_market_for_this_geo",
                        "review bids/targeting for this geo; compare per-geo, not account mix",
                        f"metric=ecpi; vs benchmarks_2025h2 [{vertical}/{sub}/{os_}/{geo}]",
                        _sev(over / tol, bands))

    # ---- Cross-source reconciliation ----
    if "reconciliation" in scenarios:
        for metric in ("network_installs_diff", "network_cost_diff"):
            for r in rows:
                v = r.get(metric)
                base = r.get("installs") if "install" in metric else r.get("cost")
                if isinstance(v, (int, float)) and isinstance(base, (int, float)) and base:
                    rate = abs(v) / abs(base)
                    if rate > th["reconciliation_diff_pct"]:
                        add("reconciliation", metric, _slice_key(r, dims),
                            f"{rate*100:.0f}% diff", f"max {th['reconciliation_diff_pct']*100:.0f}%",
                            "definition/timezone/attribution-window/dedup",
                            "reconcile with network export on date×campaign",
                            f"metric={metric}; diff rate", _sev(rate / th["reconciliation_diff_pct"], bands))

    # ---- Ad-fraud signals ----
    if "fraud" in scenarios:
        for sl, ts in _by_slice_timeseries(rows, dims, "ctr").items():
            vals = [v for _, v in ts]
            if len(vals) >= 4:
                mu, sd = stats.mean(vals[:-1]), (stats.pstdev(vals[:-1]) or 0)
                if sd and ts[-1][1] > mu + th["ctr_sigma"] * sd:
                    add("fraud", "ctr", sl, f"{ts[-1][1]*100:.1f}% (>{th['ctr_sigma']}σ)",
                        f"{mu*100:.1f}%±{sd*100:.1f}", "click_injection",
                        "inspect click→install time distribution; check sub-publishers",
                        "metric=ctr; > mean+kσ", "high")
        for r in rows:
            inst = r.get("installs", 0) or 0
            ret = r.get("retention_rate_1d")
            rev = r.get("revenue", 0) or 0
            if inst >= th["min_installs_for_signal"] and isinstance(ret, (int, float)) \
                    and ret < 0.01 and rev < 1:
                add("fraud", "installs", _slice_key(r, dims),
                    f"{inst:.0f} installs, D1 ret≈0, rev≈0", "expected >0 retention/revenue",
                    "invalid_traffic", "block sub-publisher; request network review",
                    "installs spike with ~0 retention & revenue", "high")

    # Dedupe row-level findings: the same slice can trip a per-row check on
    # many dates. Collapse to one anomaly per (scenario, metric, slice, cause),
    # keeping the worst severity and noting how many dates were affected.
    # `cause` distinguishes different checks on the same metric×slice (e.g. a
    # PoP retention drop vs a below-benchmark finding are separate anomalies —
    # operational vs structural, see decision_framework 3D-5).
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    merged = {}
    for a in anomalies:
        key = (a["scenario"], a["metric"], a["slice"], a["cause"])
        if key not in merged:
            a["_count"] = 1
            merged[key] = a
        else:
            m = merged[key]
            m["_count"] += 1
            if severity_rank.get(a["severity"], 9) < severity_rank.get(m["severity"], 9):
                cnt = m["_count"]
                a["_count"] = cnt
                merged[key] = a
    out = []
    for a in merged.values():
        if a.pop("_count", 1) > 1:
            a["change"] = f"{a['change']} (recurring)"
        out.append(a)
    out.sort(key=lambda a: severity_rank.get(a["severity"], 9))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="unified.json from transform.py")
    ap.add_argument("--out", help="Write anomalies JSON here (default stdout)")
    ap.add_argument("--playbooks", help="Path to anomaly_playbooks.md for thresholds")
    ap.add_argument("--scenarios", default="data_quality,ua_performance,reconciliation,fraud",
                    help="Comma-separated scenarios to run")
    ap.add_argument("--benchmarks", help="benchmarks_2025h2.json (default: references/)")
    ap.add_argument("--app-verticals",
                    help="App→vertical map for benchmark checks (§8.5): a JSON file "
                         "or inline JSON like '{\"89King\": \"Gaming/Casino/android\"}'")
    ap.add_argument("--default-vertical",
                    help="Fallback 'Vertical/SubVertical[/os]' for unmapped apps")
    args = ap.parse_args(argv)

    if not args.playbooks:
        guess = os.path.join(os.path.dirname(__file__), "..", "references", "anomaly_playbooks.md")
        args.playbooks = guess if os.path.exists(guess) else None
    if not args.benchmarks:
        guess = os.path.join(os.path.dirname(__file__), "..", "references", "benchmarks_2025h2.json")
        args.benchmarks = guess if os.path.exists(guess) else None
    app_verticals = {}
    if args.app_verticals:
        if os.path.exists(args.app_verticals):
            with open(args.app_verticals, "r", encoding="utf-8") as f:
                app_verticals = json.load(f)
        else:
            app_verticals = json.loads(args.app_verticals)

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)
    th, bands = load_thresholds(args.playbooks)
    scenarios = {s.strip() for s in args.scenarios.split(",") if s.strip()}
    anomalies = detect(data, scenarios, th, bands,
                       bmk=load_benchmarks(args.benchmarks),
                       app_verticals=app_verticals,
                       default_vertical=args.default_vertical)

    out = json.dumps({"thresholds": th, "anomalies": anomalies},
                     ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Found {len(anomalies)} anomalies -> {args.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()
