# Mobile Growth Diagnostics

An analyst-grade mobile app growth data diagnostics skill for Claude. Powered by the Adjust MCP, it detects anomalies, reconciles multi-source data, and generates interactive HTML dashboards for UA teams.

Pulling data is the easy part — this skill's value is the **judgment layer**: an
industry benchmark dataset (retention/eCPI by sub-vertical × geo × OS) plus a
decision framework that turns metric readings into concrete UA actions
(scale / hold / cut, geo-network portfolio moves, creative-vs-bid diagnosis,
UA-vs-product routing).

## Features

✅ **Anomaly Detection** — Data quality, UA performance, cross-source reconciliation, ad-fraud signals  
✅ **Industry Benchmarks** — 2,412-entry baseline (Adjust 2025 H2): retention & eCPI vs your exact sub-vertical × geo × OS cell  
✅ **Decision Framework** — Metric→action playbooks with stable rule IDs; every recommendation is traceable to a rule  
✅ **Interactive Dashboard** — Light-themed, single-file HTML with drill-downs, benchmark curves, and colored vs-benchmark cells  
✅ **Multi-app Analysis** — Analyze multiple Adjust apps in one run  
✅ **Bilingual Output** — Dashboard and summaries in 中文 or English  
✅ **External Reconciliation** — Compare Adjust vs Meta/Google exports (mode B)  
✅ **Read-only Safe** — No write operations; aggregate data only  

## Quick Start

### 1. Prerequisites

- Claude 3.5+ (CLI, desktop, or web)
- Adjust account with data
- 5 minutes to configure

### 2. Generate Adjust MCP Token

Visit: https://automate.adjust.com/ai-assistant-service/mcp_token

Generate a token and copy it.

### 3. Add to Claude MCP Config

Edit `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "adjust-copilot": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://automate.adjust.com/ai-assistant-service/mcp/",
        "--header",
        "Authorization: Bearer <YOUR_TOKEN>"
      ]
    }
  }
}
```

### 4. Restart Claude

Fully quit and reopen Claude Code.

### 5. Run the Skill

```
/mobile-growth-diagnostics
```

The skill will guide you through:
1. **Configuration** — app tokens, date range, scenarios
2. **Pre-flight check** — sample validation
3. **Analysis** — anomaly detection
4. **Dashboard** — interactive HTML with insights

## Use Cases

### Installs dropped 30% last week
> *You:* "My installs dropped in Brazil last week. Can you investigate?"

The skill pulls data, checks for network issues, attribution loss, SKAN problems, and flags suspicious patterns.

### ROAS below floor
> *You:* "D7 ROAS is below 15% on Facebook. Is this fraud or just market saturation?"

The skill analyzes CTR, retention, and revenue per cohort to isolate the cause.

### Meta vs Adjust discrepancy
> *You:* "I have a Meta export. Can you compare it to Adjust?"

Upload the export; the skill reconciles on date × campaign and flags differences.

### Quarterly growth audit
> *You:* "Give me a full diagnostic: all countries, all networks, last 90 days."

The skill pulls cross-dimensional anomalies and produces a comprehensive dashboard for stakeholder meetings.

### Is my retention actually bad?
> *You:* "D1 is 9%. Is that bad?"

Depends entirely on the cell: 9% is near-median for Casino·Vietnam·Android
(12%) but a disaster for Puzzle·Japan·iOS (32%). The skill compares against the
exact **sub-vertical × geo × OS** benchmark and grades the gap — and if the
decay *shape* (D7/D1) is off-band, it routes the finding to product instead of
UA (rule 3D-2).

## The Judgment Layer

What separates this from "ask Claude to query Adjust":

- **`references/benchmarks_2025h2.json`** — 2,412 baseline entries extracted
  from Adjust's 2025 H2 App Trends: eCPI/eCPM + retention D1/D7(/D14)/D30 for
  Gaming (17 sub-verticals), Social, Utilities, E-commerce, Finance × ~40 geos
  × iOS/Android, mean+median (**median is the anchor**).
- **Benchmark-relative detection** (playbooks §8.5) — `retention_below_benchmark`
  and `ecpi_above_benchmark` compare each slice against its exact benchmark
  cell. Missing cells are skipped, never invented; unmapped apps degrade
  gracefully.
- **`references/decision_framework.md`** — the metrics→decisions layer: a
  four-lens metric map (Volume/Quality/Economics/Trust), budget & portfolio
  playbooks (incl. **CPRU** — cost per retained user, the metric that unmasks
  "cheap" junk traffic), creative-vs-bid diagnosis, UA-vs-product routing,
  combined-read 2×2s, monetization-mode north stars, and guardrails
  (cohort maturity, Simpson's paradox, volume floors). Rules carry stable IDs
  (`3A-2`, `3D-4`…) that anomalies and recommendations cite.
- **Demo:** [`examples/benchmark_demo_dashboard.html`](examples/benchmark_demo_dashboard.html)
  is a real pipeline run showing all of the above on a test account.

LTV/ROAS deliberately have **no** industry benchmark (the source deck has
none): the framework derives ROAS floors from the account's own payback curves
instead of inventing numbers.

## Architecture

```
┌─────────────────────┐
│       Claude        │  ← You + skill logic
├─────────────────────┤
│     Adjust MCP      │  ← Read-only aggregates
├─────────────────────┤
│       Python        │  ← Transform, detect (vs benchmarks), build
├─────────────────────┤
│     HTML Output     │  ← Dashboard w/ benchmark context & rule-cited advice
└─────────────────────┘
```

**Data never leaves your Claude session.** The skill reads from Adjust, processes locally, and outputs an offline-safe HTML file.

## References

- **[SETUP.md](SETUP.md)** — Detailed setup guide (token, MCP config, troubleshooting)
- **[SKILL.md](SKILL.md)** — Skill design doc (workflow, boundaries, data flow)
- **references/** — Playbooks, benchmarks, decision framework, metrics glossary, dimensions, MCP docs
- **scripts/** — Python transforms, anomaly + benchmark detection, dashboard builder
- **assets/** — HTML templates, CSS theme
- **examples/** — Mock-data preview + real-run benchmark demo

## Key Files

| File | Purpose |
|------|---------|
| `SETUP.md` | End-user setup guide |
| `SKILL.md` | Skill system prompt & architecture |
| `references/mcp_setup.md` | Adjust MCP token & client config |
| `references/anomaly_playbooks.md` | Detection logic & thresholds (incl. §8.5 benchmark rules) |
| `references/benchmarks_2025h2.json` | Industry baselines: sub-vertical × geo × OS, median anchor |
| `references/decision_framework.md` | Judgment layer: metric→action playbooks, rule IDs, guardrails |
| `references/metrics_glossary.md` | API metric definitions |
| `references/dimensions.md` | Grouping & drill-down rules |
| `scripts/transform.py` | Normalize MCP rows → tidy schema |
| `scripts/detect_anomalies.py` | Anomaly playbooks + benchmark-relative checks (`--app-verticals`) |
| `scripts/build_dashboard.py` | Inject data into HTML template (benchmark curves & colored cells) |
| `assets/dashboard_template.html` | Interactive dashboard markup |
| `examples/sample_dashboard.html` | Mock-data preview (look & feel) |
| `examples/benchmark_demo_dashboard.html` | Real-run demo of the judgment layer |

## Configuration & Customization

### Edit anomaly thresholds

Thresholds live in `references/anomaly_playbooks.md` (top of file):

```yaml
thresholds:
  install_drop_pct: -0.30        # Flag drops ≥ 30%
  cpi_rise_pct: 0.25             # Flag eCPI rises ≥ 25%
  roas_floor_d7: 0.15            # Flag D7 ROAS < 15%
  retention_drop_pct: -0.20      # Flag retention drops ≥ 20%
  ctr_sigma: 3.0                 # Flag CTR > mean + 3σ
  retention_benchmark_tol: 0.30  # Flag retention < benchmark median × 70%
  ecpi_benchmark_tol: 0.50       # Flag eCPI > benchmark median × 150%
```

### Customize dashboard theme

Edit `assets/theme.css` for colors, fonts, spacing. Re-run the skill to rebuild with your theme.

### Add metrics to default set

Default metrics are defined in `references/metrics_glossary.md` (§6.6). Add custom metrics during analysis, or edit the playbooks.

## Troubleshooting

### Adjust MCP not found
- Check `~/.claude/settings.json` has the server config
- Verify token is correct (no typos, full string)
- Fully restart Claude (not just close the chat)

### 401 Unauthorized
- Token expired or invalid
- Generate a new one at https://automate.adjust.com/ai-assistant-service/mcp_token
- Update `settings.json` and restart

### App token not found
- Verify in Adjust Dashboard → Settings → Apps
- Check for typos
- Try a wider date range (new apps may have < 24h data)

**More:** See [SETUP.md — Troubleshooting](SETUP.md#troubleshooting)

## Security & Privacy

- **Token is never logged, persisted, or sent anywhere.** It stays in your MCP client config.
- **Data stays in your Claude session.** No data is uploaded to external APIs (except Adjust MCP for reading aggregates).
- **Read-only.** The skill cannot modify campaigns, budgets, or network settings.
- **Aggregate only.** No user/device-level analysis.

## Multi-Account Setup

Each Adjust account needs its own token + Account ID:

```json
{
  "mcpServers": {
    "adjust-account-1": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://automate.adjust.com/ai-assistant-service/mcp/",
        "--header", "Authorization: Bearer <TOKEN_1>",
        "--header", "X-Account-ID: <ACCOUNT_ID_1>"
      ]
    },
    "adjust-account-2": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://automate.adjust.com/ai-assistant-service/mcp/",
        "--header", "Authorization: Bearer <TOKEN_2>",
        "--header", "X-Account-ID: <ACCOUNT_ID_2>"
      ]
    }
  }
}
```

## Development

### Directory structure

```
mobile-growth-diagnostics/
├── SKILL.md                        # Skill system prompt
├── SETUP.md                        # End-user setup guide
├── README.md                       # This file
├── references/
│   ├── mcp_setup.md               # Token & client config
│   ├── anomaly_playbooks.md       # Detection playbooks
│   ├── metrics_glossary.md        # Adjust API metrics
│   ├── dimensions.md              # Grouping rules
│   └── report_copy.md             # Bilingual copy templates
├── scripts/
│   ├── transform.py               # MCP rows → tidy schema
│   ├── detect_anomalies.py        # Anomaly detection
│   ├── validate_sample.py         # Pre-flight validation
│   └── build_dashboard.py         # Build HTML output
├── assets/
│   ├── dashboard_template.html    # Interactive template
│   ├── intake_form.html           # Configuration form
│   └── theme.css                  # Light theme
└── examples/
    └── sample_dashboard.html      # Mock-data preview
```

### Python dependencies

Install in your Claude environment (if running scripts locally):

```bash
pip install pandas numpy scipy
```

Scripts are designed to run with minimal dependencies (pandas, numpy, scipy for stats).

### Contributing

- Edit `SKILL.md` for prompt/workflow changes
- Edit `references/anomaly_playbooks.md` to tune thresholds or add detection logic
- Edit `assets/theme.css` for UI changes
- Update `README.md` and `SETUP.md` when adding features

## FAQ

**Q: Does this work with the Adjust Report Service API?**  
A: Yes. The Adjust MCP wraps the Report Service API; this skill uses the MCP.

**Q: Can I use CSV/JSON exports instead of the Adjust MCP?**  
A: Not for live pulls, but you can use mode B (external reconciliation) to compare your exports against Adjust data.

**Q: Can I modify Adjust campaigns or budgets?**  
A: No. The skill is read-only by design. It can only read and analyze.

**Q: How long does an analysis take?**  
A: A typical 2-week, 3-dimension analysis takes 1–3 minutes (depends on MCP response time and anomaly complexity).

**Q: Can I export the dashboard?**  
A: Yes. The HTML file is standalone and offline-safe. Email it, share it via Slack, or embed it in reports.

**Q: What about iOS vs Android?**  
A: The skill supports both. It auto-detects SKAdNetwork metrics for iOS and flags degradation if TAM isn't enabled.

## License

MIT. See [LICENSE](LICENSE).

## Support

- **Setup issues:** See [SETUP.md — Troubleshooting](SETUP.md#troubleshooting)
- **Metrics questions:** See [Adjust Datascape Glossary](https://help.adjust.com/en/article/datascape-metrics-glossary)
- **Adjust MCP:** See [Adjust Help](https://help.adjust.com/en/article/adjust-mcp)
- **Claude Code:** `/help` or visit https://github.com/anthropics/claude-code

---

**Version:** 1.0  
**Status:** Production  
**Last Updated:** 2026-06-18

Made with ❤️ for mobile growth teams.

