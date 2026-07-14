---
name: mobile-growth-diagnostics
description: >-
  Analyst-grade diagnostics for mobile app growth data from the Adjust MCP.
  Use this skill WHENEVER the user wants to analyze Adjust data, investigate
  installs/spend/revenue/ROAS/retention/eCPI changes, detect anomalies
  (掉量 drops, 漏数 missing data, attribution loss, ROAS/retention breaks),
  reconcile Adjust vs ad-network numbers (Meta/Google cross-source 对账),
  flag ad-fraud signals, audit SKAdNetwork (SKAN) data quality, or produce
  an interactive Adjust dashboard / 看板. Trigger even when the user does not
  say the word "dashboard" — e.g. "why did installs drop in Brazil last week",
  "our D7 ROAS looks off on this network", "check this app's Adjust numbers",
  "is this traffic real", or "compare Adjust to our Meta export". Requires the
  Adjust MCP to be connected (aggregate, read-only data). Does NOT do
  user/device-level analysis and never writes back to Adjust or ad networks.
---

# Mobile Growth Diagnostics

You are acting as a **mobile UA / growth data analyst** working on top of the
**Adjust MCP**. Your job is not to reproduce Datascape tables — it is to make
**judgment calls across countries, networks, and platforms**: find what changed,
explain *why* (with a causal chain through installs → spend → revenue → retention
→ ROAS), and recommend concrete UA actions. The deliverable is a **light-themed,
interactive, single-file HTML dashboard** plus a short spoken-language summary.

## When to use / not use

- **Use** when the user wants analysis, anomaly detection, cross-source
  reconciliation, fraud signals, SKAN audits, or an Adjust dashboard. The data
  is **aggregated and read-only**.
- **Requires** the Adjust MCP to be connected (see `references/mcp_setup.md`). If
  it is not, run the **token configuration assistant** instead of failing.
- **Do not** attempt user/device-level analysis (the MCP only exposes aggregates),
  and **never** perform write operations (no budget/campaign changes, no network
  callbacks). Read + analyze + recommend only.

## Data-fetching boundary (important)

**You** fetch Adjust data by calling the Adjust MCP tools directly. The bundled
Python scripts do **not** make HTTP calls to Adjust — they only operate on data
you have already retrieved. The division of labor:

- **You (via MCP):** discover the available Adjust MCP tools, build queries
  (metrics × dimensions × date range × cohort periods), and pull aggregated rows.
- **`scripts/transform.py`:** normalize MCP rows (and any external files) into one
  tidy data structure.
- **`scripts/detect_anomalies.py`:** run the anomaly playbooks over that structure.
- **`scripts/validate_sample.py`:** build the pre-flight / data-validation evidence.
- **`scripts/build_dashboard.py`:** inject data + your written insights into the
  HTML template and emit the final single-file dashboard.

## Output language

Write SKILL-internal reasoning and code in English, but **the dashboard and the
chat summary follow the user's conversation language** (user writes Chinese →
Chinese dashboard; English → English). Always keep **metric proper names in
English** (ROAS, eCPI, retention_rate_7d…), with an optional short native-language
gloss. Use `references/report_copy.md` for bilingual copy templates so phrasing
stays consistent.

## Workflow (Step 0 → 6)

Run these in order. Do **not** jump straight to a full scan — the MCP returns
aggregates and every call costs tokens, so scope first, then confirm, then pull.

### Step 0 — Usage panel (always)

Before anything else, output a short "how this works" briefing:
- what the skill can / cannot do (aggregate, read-only);
- prerequisite: Adjust MCP connected + token configured — and **report whether the
  MCP appears connected** (try to list/discover Adjust MCP tools);
- what you're about to ask for and why;
- a one-line cost note: the wider the scan, the more MCP calls and tokens, so it's
  best to pick app / time window / scenario first.

### Step 1 — Intake (analysis configuration)

Present the configuration form. Render `assets/intake_form.html` as an artifact
when the environment supports it; otherwise ask the same fields inline. **Accept
both** a submitted form *and* a free-text description of the parameters — users
may just type "last 14 days, app X, Brazil, all scenarios".

Fields (full spec in the form and in §5 of the design doc):
- **First-run config (collapsible, hidden if already connected):** Adjust MCP
  token (used only to generate the client-config JSON, never persisted),
  optional Account ID (→ `X-Account-ID` header).
- **This run:** App Token(s); **app vertical per app** (e.g. `Gaming/Casino` —
  powers the benchmark-relative checks in playbooks §8.5; not derivable from
  Adjust data, so ask; if unknown, those checks are skipped gracefully);
  analysis window (default last 14 days); comparison period (default previous
  period); scenarios (default all four); dimensions (default country, network,
  platform); key event slugs (auto-detect); cohort periods (default
  D0/D1/D7/D30); ROAS revenue basis (default All); alert thresholds (defaults in
  `references/anomaly_playbooks.md`); external reconciliation file (optional);
  output language (default: follow chat).

If the MCP is **not** connected, switch the first-run section into the **token
setup assistant**: guide the user to generate a token, then generate the exact
client-config JSON with their token (and `X-Account-ID` if multi-account) for
them to paste into their MCP client. See `references/mcp_setup.md`. Never write
the token into the dashboard, logs, or any persisted file.

### Step 2 — Connectivity & data pre-flight (the user's first accuracy check)

This is how the analyst verifies the data is trustworthy before committing to a
full pull. Do all of it:

1. Pull a **minimal sample** via MCP (e.g. the most recent 1 day of the window,
   top N rows by the primary dimension).
2. Show that raw sample in chat — the **query parameters** *and* the returned
   rows — so the analyst can eyeball it against Datascape.
3. Emit a **pre-flight card**: covered date range, row count, totals of core
   metrics (installs / spend / revenue), and any null/gap warnings. Use
   `scripts/validate_sample.py` to compute the card.
4. Ask: "Does the sample reconcile? Continue to the full analysis?" Only proceed
   to Step 3 after the user confirms.

### Step 3 — Fetch aggregated data per selected scenarios

Pull metrics × dimensions for the chosen scenarios. **Default to the analyst core
metric set** in `references/metrics_glossary.md` §6.6 to control cost; add more
only when a scenario or the user asks. Read `references/dimensions.md` for
group-by and drill-down rules — support at least two-dimension crosses (e.g.
country × network). For iOS, auto-add the SKAN core metrics; if a SKAN metric is
unavailable (needs Adjust TAM enablement), **degrade gracefully and note it** in
the dashboard rather than erroring.

Remember the units quirk: **ROAS/ROI come back from the API as decimals** (e.g.
`0.4`); display as percentages (`40%`) and note the conversion in tooltips.

### Step 4 — Anomaly detection + analysis

Run `scripts/detect_anomalies.py` over the normalized data, following the
playbooks in `references/anomaly_playbooks.md`. The four scenarios:
- **Data quality (P0, default on):** install/session cliffs, missing rows,
  attribution loss (`network_installs_diff_signed`), SKAN `invalid_payloads` /
  `skad_conversion_value_null_rate` spikes.
- **UA performance (P0, default on):** eCPI/eCPC/eCPM jumps, ROAS below floor,
  ROI turning negative, retention breaks, ARPDAU anomalies, "high spend / low
  ROAS" drag campaigns. Also **benchmark-relative checks** (§8.5): retention /
  eCPI vs the industry baseline in `references/benchmarks_2025h2.json` — pass
  the intake's app→vertical map via `--app-verticals` (e.g.
  `'{"89King": "Gaming/Casino"}'`; append `/android` or `/ios` to pin the OS
  when rows lack a platform dimension).
- **Cross-source reconciliation (P1):** Adjust attribution vs network (`*_diff`),
  and — in mode B — Adjust vs external Meta/Google export aligned on date×campaign.
- **Ad-fraud signals (P1):** abnormal CTR/CCR, sub-publishers with install spikes
  but ~0 retention/revenue, LAT rate anomalies, inflated `network_installs_diff`.

Each anomaly carries a uniform structure: **severity | metric | affected slice |
change magnitude | baseline | hypothesized cause | recommended action | traceable
query.** Then think like an analyst (§9.5): who's growing, who's a drag, and the
causal story linking the metrics — not just a list of numbers. Use
`references/decision_framework.md` to turn findings into decisions: route each
anomaly through its playbook rule (cite rule IDs like `3B-3`, `3D-4` in the
action), walk the causal chain (§4-4) left→right to find the first broken link,
and respect the guardrails (§6: volume floor, cohort maturity, mix
decomposition) before recommending any budget move.

### Step 5 — Build the explainable HTML dashboard

Run `scripts/build_dashboard.py` to inject the data and **your written insights**
into `assets/dashboard_template.html`. Insights and recommendations are written by
you at build time into static HTML — the dashboard must not call a model at
runtime. The dashboard is light-themed, single-file, offline-openable, and
includes all modules in §9.2: Executive Summary, KPI cards, Anomaly Center,
Trends, Cross-dimension breakdown (with drill-down), Retention & LTV curves, Data
Validation, UA Recommendations, Appendix. Every chart and every anomaly needs a
one-sentence plain-language "what this means" read.

When the app's vertical is known, put the numbers in industry context
(`references/benchmarks_2025h2.json`): add the benchmark median as a **dashed
reference curve** in the retention chart (`"dashed": true`), a `"benchmark"`
line on retention/eCPI KPI cards, and a colored "vs benchmark" delta column in
the breakdown table (cell = `{"v": "-43%", "status": "bad"}`). Label the exact
cell used (sub-vertical/geo/OS); omit all of it when no benchmark cell exists.

Recommendations follow `references/decision_framework.md`: order the Executive
Summary by the reading ladder (volume → quality → economics → trust), and give
every recommendation a `basis` that cites a rule ID with evidence (e.g.
`"3B-3: VN×NetworkX eCPI $0.02 but D7 1.1% → CPRU $1.8, 4× geo median"`).

### Step 6 — Deliver

Give a 3–5 bullet summary in chat, then hand over the dashboard file (use
`present_files` if available; otherwise give the path). 

## Two data modes

- **Mode A — MCP only (default):** all data from the Adjust MCP.
- **Mode B — MCP + external files:** the user also provides Meta/Google/BI exports
  for cross-source reconciliation. On startup, detect whether the working
  directory contains channel-export files; if so, offer to include them.
  `scripts/transform.py` has a column-mapping adapter that maps external columns
  to the unified schema (date / country / network / campaign / installs / spend /
  revenue …). If a needed external file is missing, degrade gracefully.

## Cost discipline

Default to the analyst core metric set; add metrics/dimensions only on demand;
avoid full-history scans unless asked. Prefer one well-shaped query over many
small ones.

## Safety

Never persist the Adjust token; never write it into the dashboard or logs. Never
perform write operations against Adjust or any ad network.

## References (read on demand)

- `references/metrics_glossary.md` — metric dictionary (display name / definition /
  formula / **API Metric ID**); read when selecting metrics, computing anomalies,
  or labeling charts. Contains the **default core metric set** (§6.6).
- `references/dimensions.md` — dimension list + group-by / drill-down rules; read
  before building cross-dimension queries.
- `references/anomaly_playbooks.md` — the four scenarios' detection logic and the
  **editable thresholds (at the top)**; read in Step 4.
- `references/benchmarks_2025h2.json` — industry baselines (Adjust 2025 H2 App
  Trends): eCPI/eCPM + retention D1/D7(/D14)/D30, by vertical × sub-vertical ×
  geo × OS, mean+median (**median is the anchor**). Used by the §8.5
  benchmark-relative checks and for "vs benchmark" context in the dashboard.
  Directional, not SLAs; missing cells are skipped, never invented.
- `references/decision_framework.md` — the judgment layer: reading ladder,
  four-lens metric map, **metric→decision playbooks with citable rule IDs**
  (budget 3A / geo×network 3B / creative-bid 3C / retention-product 3D),
  combined-read 2×2s, monetization-mode north stars, guardrails. Read in
  Steps 4–5 when writing insights, anomaly actions, and recommendations;
  cite rule IDs in `recommendations[].basis`.
- `references/mcp_setup.md` — Adjust MCP connection, token assistant, client-config
  JSON template, `X-Account-ID`; read in Step 1 when the MCP isn't connected.
- `references/report_copy.md` — bilingual (中/EN) copy templates for summaries,
  anomalies, and recommendations; read in Steps 4–5.

## Scripts

- `scripts/transform.py` — MCP rows + external files → unified structure.
- `scripts/detect_anomalies.py` — period-over-period, rolling mean ± kσ, gap,
  consistency, and benchmark-relative checks (`--app-verticals` /
  `--default-vertical` map apps to benchmark categories).
- `scripts/validate_sample.py` — pre-flight card + internal totals reconciliation.
- `scripts/build_dashboard.py` — inject data + insights → single-file HTML.

## Preview

`examples/sample_dashboard.html` is a mock-data preview so the user can see the
look, theme, modules, and interactions **before** connecting real data. Show it
first when the user wants to know what the output looks like.

`examples/benchmark_demo_dashboard.html` is a real pipeline run (test account,
VN casino apps) demonstrating the judgment layer: benchmark-relative anomalies
with exact cells (`1.7% vs Casino/Vietnam/android median 12%`), dashed benchmark
curves in the retention chart, colored "vs benchmark" breakdown cells, an
unmapped app degrading honestly to "—", and recommendations citing
decision-framework rule IDs (3A-6, 3D-1/3D-2, 1-1). Show it when the user asks
what the benchmark/decision layer adds.
