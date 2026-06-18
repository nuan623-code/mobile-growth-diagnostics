#!/usr/bin/env python3
"""Normalize Adjust MCP rows (and optional external channel exports) into one
unified data structure for downstream detection and dashboard building.

This script does NOT call Adjust. The caller (Claude, via the MCP) fetches the
rows and passes them in. Stdlib only.

Unified structure (written to stdout or --out):
{
  "meta": {"dimensions": [...], "metrics": [...], "source": "...", "generated_at": "..."},
  "rows": [ {dim: value, ..., metric: number, ...}, ... ]
}

Usage:
  # From an MCP rows JSON file (list of dicts, or {"rows":[...]})
  python transform.py --mcp mcp_rows.json --out unified.json

  # Mode B: also fold in an external channel export (CSV/TSV) with a column map
  python transform.py --mcp mcp_rows.json --external meta_export.csv \
      --external-map column_map.json --out unified.json

A column map (column_map.json) maps the external file's columns to the unified
schema, e.g.:
{
  "Day": "date", "Country": "country", "Campaign name": "campaign",
  "Results": "installs", "Amount spent (USD)": "cost", "_source": "meta"
}
Unmapped columns are dropped. "_source" (optional) tags the external rows.
"""
import argparse
import csv
import json
import sys
from datetime import datetime, timezone

# Canonical dimension keys we recognize (everything else is treated as a metric).
DIMENSION_KEYS = {
    "date", "app", "platform", "os_name", "country", "region", "network",
    "campaign", "adgroup", "creative", "partner", "store_type", "device_type",
    "source",
}

# Ratio metrics the Adjust API returns as decimals (display as percent later).
DECIMAL_RATIO_PREFIXES = ("roas", "return_on_investment", "revenue_to_cost", "skad_revenue")
DECIMAL_RATIO_SUFFIXES = ("_roas", "_roi", "_rate", "ctr", "click_conversion_rate")


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _coerce_number(v):
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip().replace(",", "")
    if s.endswith("%"):
        try:
            return float(s[:-1]) / 100.0
        except ValueError:
            return v
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return v  # keep strings (e.g. dimension-ish values) as-is


def _split_keys(row):
    dims, mets = set(), set()
    for k in row:
        (dims if k in DIMENSION_KEYS else mets).add(k)
    return dims, mets


def normalize_mcp(rows):
    """Accepts a list of dicts or {'rows': [...]} and coerces metric values."""
    if isinstance(rows, dict):
        rows = rows.get("rows") or rows.get("data") or []
    out = []
    for r in rows:
        nr = {}
        for k, v in r.items():
            key = "platform" if k == "os_name" else k
            nr[key] = v if key in DIMENSION_KEYS else _coerce_number(v)
        out.append(nr)
    return out


def load_external(path, colmap):
    """Read a CSV/TSV channel export and remap columns to the unified schema."""
    delim = "\t" if path.lower().endswith((".tsv", ".txt")) else ","
    source_tag = colmap.get("_source")
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delim)
        for raw in reader:
            nr = {}
            for src_col, value in raw.items():
                target = colmap.get(src_col)
                if not target or target == "_source":
                    continue
                nr[target] = value if target in DIMENSION_KEYS else _coerce_number(value)
            if source_tag:
                nr["source"] = source_tag
            elif "source" not in nr:
                nr["source"] = "external"
            if nr:
                rows.append(nr)
    return rows


def build(mcp_rows, external_rows=None):
    rows = list(mcp_rows)
    if external_rows:
        rows.extend(external_rows)
    dims, mets = set(), set()
    for r in rows:
        d, m = _split_keys(r)
        dims |= d
        mets |= m
    # Stable, useful ordering.
    dim_order = [d for d in ["date", "app", "platform", "country", "region",
                             "network", "campaign", "adgroup", "creative",
                             "partner", "store_type", "device_type", "source"]
                 if d in dims]
    return {
        "meta": {
            "dimensions": dim_order,
            "metrics": sorted(mets),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "row_count": len(rows),
        },
        "rows": rows,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mcp", required=True, help="JSON file of MCP rows")
    ap.add_argument("--external", help="External channel export CSV/TSV (mode B)")
    ap.add_argument("--external-map", help="JSON column map for the external file")
    ap.add_argument("--out", help="Write unified JSON here (default stdout)")
    args = ap.parse_args(argv)

    mcp_rows = normalize_mcp(_load_json(args.mcp))
    ext_rows = None
    if args.external:
        if not args.external_map:
            ap.error("--external requires --external-map")
        ext_rows = load_external(args.external, _load_json(args.external_map))

    unified = build(mcp_rows, ext_rows)
    out = json.dumps(unified, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"Wrote {unified['meta']['row_count']} rows -> {args.out}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
