# Mobile Growth Diagnostics — Quick Reference

## 📊 What This Does

Analyze your Adjust mobile app growth data with AI-powered anomaly detection. Get interactive dashboards showing:
- Install/revenue drops (detect 掉量)
- ROAS/retention breaks
- Cross-source reconciliation (Adjust vs Meta/Google)
- Ad-fraud signals
- Actionable UA recommendations

**Output:** Single-file HTML dashboard + chat summary. Works offline. Shareable.

---

## 🚀 30-Second Setup

### 1️⃣ Get Token
Go to: https://automate.adjust.com/ai-assistant-service/mcp_token → Generate

### 2️⃣ Add to Claude Config
Edit `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "adjust-copilot": {
      "command": "npx",
      "args": ["mcp-remote", "https://automate.adjust.com/ai-assistant-service/mcp/", "--header", "Authorization: Bearer <YOUR_TOKEN>"]
    }
  }
}
```

### 3️⃣ Restart Claude
Fully quit + reopen.

### 4️⃣ Use It
```
/mobile-growth-diagnostics
```

---

## 📋 Common Prompts

| Goal | Try This |
|------|----------|
| **Investigate install drop** | "My installs dropped 30% in Brazil last week. What happened?" |
| **Check ROAS floor** | "D7 ROAS is 12% on Facebook. Is this a problem?" |
| **Multi-country audit** | "Give me anomalies across all countries for the last 30 days." |
| **Reconcile Meta/Adjust** | "I have a Meta export. Can you compare it to Adjust?" |
| **iOS SKAN audit** | "Analyze my SKAdNetwork data for anomalies." |

---

## 🎯 Workflow (6 steps)

```
1. Configuration    → Pick app token, date range, scenarios
2. Pre-flight       → Verify data with a sample
3. Data Pull        → Fetch from Adjust MCP
4. Anomaly Detect   → Run playbooks (data quality, UA perf, fraud)
5. Build Dashboard  → Inject insights into HTML
6. Deliver          → Download .html + read chat summary
```

Each step is a confirmation point — you control the flow.

---

## 🔧 What You Can Tweak

| File | What to Change | When |
|------|---|---|
| `references/anomaly_playbooks.md` | Threshold values | You want stricter/looser flags |
| `assets/theme.css` | Colors, fonts, spacing | You want a custom dashboard theme |
| `references/report_copy.md` | Bilingual copy | You want different phrasing |

After editing, just re-run the skill — it picks up the changes.

---

## ⚠️ Common Issues

| Problem | Fix |
|---------|-----|
| "Adjust MCP not found" | Restart Claude (fully quit), check token in `settings.json` |
| "401 Unauthorized" | Token expired? Regenerate at https://automate.adjust.com/ai-assistant-service/mcp_token |
| "App token not found" | Verify in Adjust Dashboard → Settings → Apps |
| No data for date range | Try 30 days instead of 7 (new apps may lack history) |

**Full troubleshooting:** See [SETUP.md](SETUP.md#troubleshooting)

---

## 📚 Learning Resources

- **First time?** → Read [SETUP.md](SETUP.md) (10 min)
- **How it works?** → Read [SKILL.md](SKILL.md) (workflow, boundaries)
- **Metrics?** → See [references/metrics_glossary.md](references/metrics_glossary.md)
- **Thresholds?** → See [references/anomaly_playbooks.md](references/anomaly_playbooks.md)
- **Adjust help?** → https://help.adjust.com/en/article/adjust-mcp

---

## 💡 Pro Tips

1. **Start small:** Analyze one app, one country, 7 days. Then expand.
2. **Save dashboards:** The .html files are standalone — email them, Slack them, archive them.
3. **Customize thresholds:** Edit `anomaly_playbooks.md` to match your app's economics (e.g., your ROAS floor might be 20%, not 15%).
4. **Use external mode:** If you have Meta/Google exports, upload them for reconciliation (mode B).
5. **Re-run weekly:** Schedule time to run diagnostics on a cadence (e.g., Monday mornings).

---

## 🔐 Security

✅ **Token stays in your MCP config** — never logged or persisted  
✅ **Data stays in your Claude session** — not sent to external APIs  
✅ **Read-only** — no campaign/budget changes  
✅ **Aggregates only** — no user/device-level analysis  

---

## 📞 Need Help?

- **Setup issues?** [SETUP.md](SETUP.md#troubleshooting)
- **Metrics definitions?** [Adjust Datascape Glossary](https://help.adjust.com/en/article/datascape-metrics-glossary)
- **MCP not working?** [Adjust MCP Docs](https://help.adjust.com/en/article/adjust-mcp)
- **Claude Code questions?** `/help` in Claude or visit https://github.com/anthropics/claude-code

---

**Version:** 1.0 | **Last Updated:** 2026-06-18 | **License:** MIT

