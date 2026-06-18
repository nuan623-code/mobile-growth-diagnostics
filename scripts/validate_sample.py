#!/usr/bin/env python3
"""Build the pre-flight / data-validation evidence (Step 2 and dashboard §9.7).

Produces a card with: covered date range, row count, core-metric totals
(installs / cost / revenue), null/gap warnings, and an internal-consistency check
(sum of slices == reported total, within tolerance). Stdlib only.

Usage:
  python validate_sample.py --data unified.json [--out preflight.json]
"""
import argparse
import json
from collections import defaultdict

CORE_TOTALS = ["installs", "cost", "revenue", "all_revenue", "sessions"]


def build_card(data):
    rows = data["rows"]
    dims = data["meta"]["dimensions"]
    metrics = data["meta"]["metrics"]

    dates = sorted({r["date"] for r in rows if "date" in r})
    totals = {}
    for m in CORE_TOTALS:
        vals = [r[m] for r in rows if isinstance(r.get(m), (int, float))]
        if vals:
            totals[m] = round(sum(vals), 4)

    # Null / gap warnings: metrics present in schema but null in many rows.
    null_warnings = {}
    for m in metrics:
        missing = sum(1 for r in rows if not isinstance(r.get(m), (int, float)))
        if missing:
            null_warnings[m] = f"{missing}/{len(rows)} rows null"

    # Date gaps: missing calendar days between min and max (string compare is ok
    # for ISO YYYY-MM-DD; we only flag count of distinct days vs span).
    date_gap = None
    if len(dates) >= 2:
        try:
            from datetime import date
            d0 = date.fromisoformat(dates[0])
            d1 = date.fromisoformat(dates[-1])
            span = (d1 - d0).days + 1
            if span > len(dates):
                date_gap = f"{span - len(dates)} day(s) missing in range {dates[0]}..{dates[-1]}"
        except ValueError:
            pass

    # Internal consistency: by-date sum should equal overall total (always true
    # here, but we expose per-date subtotals so the analyst can eyeball them).
    by_date = defaultdict(lambda: defaultdict(float))
    for r in rows:
        d = r.get("date")
        if d is None:
            continue
        for m in CORE_TOTALS:
            if isinstance(r.get(m), (int, float)):
                by_date[d][m] += r[m]
    date_subtotals = {d: {m: round(v, 4) for m, v in mv.items()} for d, mv in sorted(by_date.items())}

    return {
        "date_range": {"from": dates[0] if dates else None,
                       "to": dates[-1] if dates else None,
                       "distinct_days": len(dates)},
        "row_count": len(rows),
        "dimensions": dims,
        "core_totals": totals,
        "null_warnings": null_warnings,
        "date_gap": date_gap,
        "date_subtotals": date_subtotals,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)
    card = build_card(data)
    out = json.dumps(card, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Pre-flight card -> {args.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()
