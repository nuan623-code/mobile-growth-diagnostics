# Mobile Growth Diagnostics — Setup Guide

A comprehensive guide to setting up and using the mobile growth diagnostics skill with Claude.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Step 1: Generate Adjust MCP Token](#step-1-generate-adjust-mcp-token)
4. [Step 2: Configure Claude Code MCP](#step-2-configure-claude-code-mcp)
5. [Step 3: Restart Claude & Verify Connection](#step-3-restart-claude--verify-connection)
6. [Step 4: Enable the Skill](#step-4-enable-the-skill)
7. [First Run: Analysis Configuration](#first-run-analysis-configuration)
8. [Advanced Configuration](#advanced-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Architecture Overview](#architecture-overview)

---

## Quick Start

**For users with existing Adjust MCP setup:** This skill should work immediately. Just invoke it:

```
/mobile-growth-diagnostics
```

**For first-time users:** Follow steps 1–5 below (5 min total).

---

## Prerequisites

- **Claude 3.5 Sonnet or later** (via Claude Code CLI, desktop, or web)
- **Adjust account** with data you want to analyze
- **Adjust automation token** (one-time generation; see Step 1)
- **Read permission on Adjust data** (your API token scope)
- **No write permissions required** — this skill only reads aggregated data

---

## Step 1: Generate Adjust MCP Token

The Adjust MCP token is a secure credential that grants read-only access to your aggregated Adjust data. **You generate it once in Adjust's automation UI.**

### Where to get it

1. Log into [Adjust Dashboard](https://dashboard.adjust.com)
2. Go to: **Automation** → **[AI Assistant Service / MCP Token](https://automate.adjust.com/ai-assistant-service/mcp_token)**
3. Click **"Generate new token"**
4. A long token string appears (looks like: `adjust_mcp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
5. **Copy and save it somewhere safe** (1Password, .env, or clipboard for next step)

> ⚠️ **Security:** This token grants read-only access to your Adjust data. Treat it like a password. Do not commit it to git or share it publicly. The skill never persists or logs it.

### Multi-account users

If you have multiple Adjust accounts:
- Each account needs its own token (generate one per account).
- You will configure the skill to use the right token in Step 2 (via the `X-Account-ID` header).

---

## Step 2: Configure Claude Code MCP

The token belongs in your Claude **MCP client configuration**, not in the skill itself. Claude reads this config once at startup.

### Via Claude Code CLI

**File:** `~/.claude/settings.json` or `.claude/settings.json` (local)

Add this to the `mcpServers` section:

```json
{
  "mcpServers": {
    "adjust-copilot": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://automate.adjust.com/ai-assistant-service/mcp/",
        "--header",
        "Authorization: Bearer <PASTE_YOUR_TOKEN_HERE>"
      ]
    }
  }
}
```

**Replace** `<PASTE_YOUR_TOKEN_HERE>` with the token from Step 1.

### For multi-account setup

Add a second `--header` argument with your Account ID:

```json
{
  "mcpServers": {
    "adjust-copilot-account-1": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://automate.adjust.com/ai-assistant-service/mcp/",
        "--header",
        "Authorization: Bearer <TOKEN_ACCOUNT_1>",
        "--header",
        "X-Account-ID: <ACCOUNT_ID_1>"
      ]
    },
    "adjust-copilot-account-2": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://automate.adjust.com/ai-assistant-service/mcp/",
        "--header",
        "Authorization: Bearer <TOKEN_ACCOUNT_2>",
        "--header",
        "X-Account-ID: <ACCOUNT_ID_2>"
      ]
    }
  }
}
```

### Via Claude Desktop App

1. Open **Settings** → **MCP**
2. Add a new MCP server named `adjust-copilot`
3. Command: `npx`
4. Arguments:
   ```
   mcp-remote
   https://automate.adjust.com/ai-assistant-service/mcp/
   --header
   Authorization: Bearer <YOUR_TOKEN>
   ```
5. Save

---

## Step 3: Restart Claude & Verify Connection

After adding the MCP config:

1. **Restart** Claude Code CLI or desktop app (fully quit + reopen)
2. **Test connection:**
   ```
   /mobile-growth-diagnostics
   ```
3. The skill will automatically check if the Adjust MCP is reachable

**Expected output:**
- ✅ "Adjust MCP is connected" → proceed to Step 4
- ❌ "Adjust MCP not found" → debug (see [Troubleshooting](#troubleshooting))

---

## Step 4: Enable the Skill

The skill is built into Claude Code. To use it:

```
/mobile-growth-diagnostics
```

Or, from any chat:
- Mention "Adjust dashboard" or "analyze my growth data"
- Ask about anomalies, ROAS, installs, retention, etc.
- The skill will auto-trigger

---

## First Run: Analysis Configuration

When you invoke the skill, you'll see a **configuration form** or inline prompts with these fields:

### Core fields

| Field | Example | Default | Notes |
|-------|---------|---------|-------|
| **App Token(s)** | `000lkzbd`  | — | Required. Find in Adjust → Settings → Apps. Can analyze multiple apps at once. |
| **Date range** | Last 14 days | ✓ | How far back to pull data. Adjust MCP supports up to ~24 months. |
| **Comparison period** | Previous 14 days | ✓ | For period-over-period anomaly detection. |
| **Scenarios** | Data quality, UA perf, Fraud signals | ✓ | Which anomaly playbooks to run (see [Anomaly Playbooks](references/anomaly_playbooks.md)). |
| **Dimensions** | Country, Network, Platform | ✓ | Group data by these. Supports two-level drills (country × network). |
| **Cohort periods** | D0, D1, D7, D30 | ✓ | For retention/ROAS/LTV curves (e.g., `retention_rate_7d`). |
| **Thresholds** | See [Anomaly Playbooks](references/anomaly_playbooks.md) | ✓ | Severity flags for install drops, eCPI rises, ROAS floors, etc. |

### Optional fields

- **External files** — Meta/Google/BI exports for cross-source reconciliation (mode B)
- **Output language** — 中文 or English (defaults to your chat language)
- **Alert thresholds** — Editable in `references/anomaly_playbooks.md` if defaults don't fit your app's economics

### Example: Simple analysis

> *You:* "Analyze my Brazil data for the last 14 days. App token is 000lkzbd."

The skill will:
1. **Scope:** confirm Brazil, app 000lkzbd, Jun 4–18
2. **Pre-flight:** pull a 1-day sample, show you the row count and totals
3. **Ask:** "Does this reconcile with Datascape? Continue?"
4. **Pull:** aggregate data for data quality, UA performance, and fraud scenarios
5. **Detect:** run anomaly playbooks, find drops, ROAS breaks, retention cliffs
6. **Build:** generate an interactive HTML dashboard
7. **Deliver:** show you 3–5 bullets in chat + the dashboard file

---

## Advanced Configuration

### Edit anomaly thresholds

Thresholds live in [`references/anomaly_playbooks.md`](references/anomaly_playbooks.md), top of file:

```yaml
thresholds:
  install_drop_pct: -0.30        # flag installs dropping ≥ 30%
  cpi_rise_pct: 0.25             # flag eCPI rising ≥ 25%
  roas_floor_d7: 0.15            # flag D7 ROAS below 15%
  retention_drop_pct: -0.20      # flag D1/D7 retention drop ≥ 20%
  ctr_sigma: 3.0                 # flag CTR > mean + 3σ (fraud signal)
```

**After editing**, close and re-run the skill — it reads the thresholds on startup.

### Adjust core metric set

By default, the skill pulls the "analyst core set" (e.g., installs, spend, ROAS, retention, events). This controls cost. The full list is in [`references/metrics_glossary.md`](references/metrics_glossary.md#66-analyst-default-metric-set-pull-first).

To add a metric (e.g., `att_consent_rate` for iOS), tell the skill during Step 1:

> *You:* "I also want to see ATT consent rates and LAT install rate."

The skill will add them to the query.

### External reconciliation (mode B)

To reconcile Adjust vs Meta/Google:

1. Export reports from **Meta Ads Manager** and **Google Ads** (date, campaign, installs, spend)
2. Place them in your working directory as `.csv` or `.xlsx`
3. Tell the skill: "I have Meta and Google exports to reconcile"
4. The skill detects the files, maps columns to the unified schema, and flags differences > 10%

File naming hints: `meta_export_*.csv`, `google_ads_*.csv`, etc.

---

## Troubleshooting

### "Adjust MCP not found" or "Cannot call Adjust tools"

**Cause:** The Adjust MCP server is not registered in your Claude client config.

**Fix:**
1. Check `~/.claude/settings.json` (or `.claude/settings.json` local)
2. Verify `mcpServers.adjust-copilot` is present
3. Verify the token is correct (no typos, full string)
4. **Fully restart** Claude (Cmd+Q, then reopen)
5. Re-run the skill

### "401 Unauthorized" or "Invalid token"

**Cause:** Token is expired, revoked, or malformed.

**Fix:**
1. Go back to Step 1: regenerate a fresh token
2. Update `~/.claude/settings.json` with the new token
3. Restart Claude

### "App token not found" or "No data for this date range"

**Cause:** 
- App token is wrong (typo, old app ID, or not in your Adjust account)
- Date range has no data (e.g., a new app with < 24 hours history)

**Fix:**
- Verify app token in Adjust → Settings → Apps
- Try a wider date range (e.g., last 30 days instead of 7)

### "SKAN metrics not available"

**Cause:** Your Adjust account doesn't have SKAdNetwork TAM enabled.

**Fix:** The skill gracefully skips SKAN metrics and notes it in the dashboard. No action needed.

### Dashboard won't open or is empty

**Cause:** The HTML file wasn't generated (check the chat for errors) or your browser can't open local files.

**Fix:**
1. Drag the `.html` file into a browser tab (or use File → Open)
2. For CORS issues: use a simple local server:
   ```bash
   cd ~/Downloads  # or wherever the dashboard is
   python3 -m http.server 8000
   ```
   Then visit `http://localhost:8000/dashboard.html`

---

## Architecture Overview

### Data flow

```
┌─────────────────────────────────────────────────────────────┐
│  You (chat)                                                 │
│  • Tell the skill what to analyze                           │
│  • Review pre-flight sample                                 │
│  • Confirm analysis                                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ↓
        ┌─────────────────────┐
        │   Skill (you)       │
        │ • Query builder     │
        │ • MCP caller        │
        │ • Analyst reasoning │
        └─────────┬───────────┘
                  │
                  ↓
        ┌─────────────────────────────────────────┐
        │   Adjust MCP                            │
        │  (aggregated data, read-only)           │
        │  https://automate.adjust.com/ai-as.../ │
        │  └─ Adjust KPI Service                  │
        │  └─ SKAdNetwork                         │
        │  └─ Ad Spend                            │
        └─────────────────────┬───────────────────┘
                  │
                  ↓
        ┌──────────────────────────────────────────┐
        │   Python scripts (bundled)               │
        │  • transform.py         (rows→tidy)     │
        │  • detect_anomalies.py  (flagging)      │
        │  • validate_sample.py   (pre-flight)    │
        │  • build_dashboard.py   (HTML + data)   │
        └──────────────────────────────────────────┘
                  │
                  ↓
        ┌──────────────────────────────────────────┐
        │   output: single-file HTML dashboard     │
        │   • light theme, offline, interactive    │
        │   • charts, anomalies, drill-down        │
        │   • export-ready                         │
        └──────────────────────────────────────────┘
```

### Security & Privacy

- **Token:** never logged, never persisted, never sent to an LLM API
- **Data:** stays in your Claude session; no data is sent to external services (except to Adjust MCP for reading)
- **Write protection:** the skill reads aggregates only; it cannot modify campaigns, budgets, or network settings
- **Dashboard:** single HTML file, all charts are embedded, safe to email or share

---

## FAQ

**Q: Can I analyze multiple apps at once?**  
A: Yes. Pass multiple app tokens: `000lkzbd, 001abc98`. The skill pulls data for each and shows cross-app anomalies.

**Q: Can I use this without the Adjust MCP?**  
A: No. The skill requires the Adjust MCP for data. If you have CSV/JSON exports instead, use the external file mode (mode B) to at least reconcile against them.

**Q: How much will this cost in terms of tokens / API calls?**  
A: Adjust MCP calls consume tokens, not money. A typical analysis (2-week window, 3 dimensions, 4 scenarios) takes ~10–15 MCP queries. Cost is proportional to date range × dimensions × scenarios.

**Q: Can I customize the dashboard theme?**  
A: Yes. Edit `assets/theme.css` and re-run the skill. The dashboard uses standard CSS, so you can brand it.

**Q: How do I interpret the anomalies?**  
A: Each anomaly in the dashboard includes a **plain-language read** ("what this means") and a **traceable query** (the exact metrics × dimensions × date range) so you can verify it in Datascape or drill down.

**Q: What if I have questions about Adjust metrics themselves?**  
A: See [`references/metrics_glossary.md`](references/metrics_glossary.md) for definitions, or the [Adjust Datascape Glossary](https://help.adjust.com/en/article/datascape-metrics-glossary).

---

## Next Steps

1. **[Generate your token](#step-1-generate-adjust-mcp-token)** (5 min)
2. **[Add to your MCP config](#step-2-configure-claude-code-mcp)** (2 min)
3. **[Restart Claude](#step-3-restart-claude--verify-connection)** (1 min)
4. **Invoke the skill:**
   ```
   /mobile-growth-diagnostics
   ```

---

## References

- [Adjust MCP Setup](references/mcp_setup.md) — token, server URL, client config
- [Anomaly Playbooks](references/anomaly_playbooks.md) — detection logic & thresholds
- [Metrics Glossary](references/metrics_glossary.md) — API metric IDs & definitions
- [Dimensions](references/dimensions.md) — group-by & drill-down rules
- [Report Copy](references/report_copy.md) — bilingual summary templates
- [Adjust Datascape Help](https://help.adjust.com/en/article/datascape-metrics-glossary)

---

**Last updated:** 2026-06-18  
**Version:** 1.0  
**Status:** Production

