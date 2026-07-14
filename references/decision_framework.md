# Decision Framework — from metrics to UA decisions

This is the skill's judgment layer. `metrics_glossary.md` defines *what a metric
is*; `anomaly_playbooks.md` defines *when to flag it*; this file defines **what
question each metric answers, what "good" looks like, and what decision follows**.
Read it in Steps 4–5 when writing insights, anomaly actions, and recommendations.

Rules carry stable IDs (`3A-2`, `4-1`…). Cite them in `recommendations[].basis`
and anomaly `action` fields so every advice line is traceable to a rule.

---

## Part 0 · The reading ladder (order of interrogation)

Read an account in this order — each step gates the next. Use it to order the
Executive Summary takeaways.

```
spend → eCPI → installs → D1/D7 retention → LTV / payback → ROAS/ROI → decision
 (did we buy)  (how much)   (are they real)   (worth what)    (keep/scale/cut)
```

- **Retention is the gate.** Cheap installs that don't retain are not cheap —
  they are worthless. Never evaluate cost before quality (see CPRU, Part 3B).
- ROAS is the *last* number to read, not the first: it is only meaningful once
  the cohort is mature (Part 6) and the retention gate has been passed.
- Beginners: if you only track five numbers, track `cost`, `ecpi`,
  `retention_rate_1d`, `retention_rate_7d`, and cohort ROAS at your payback
  window. Everything else is diagnosis.

## Part 1 · Four-lens metric map

Every metric answers one of four questions. When something looks wrong, identify
which lens it belongs to — that alone routes the investigation.

| Lens | Question | Core metrics | A bad value means |
|---|---|---|---|
| **Volume** (量) | Are we acquiring? From where? | installs, non_organic_installs, by network/country | delivery, tracking, or budget problem — check Data Quality (8.1) before UA |
| **Quality** (质) | Are the users real & engaged? | retention D1/D7/D30, sessions/user, DAU/MAU stickiness, ARPDAU | traffic quality or product problem — route with 3D-4 |
| **Economics** (钱) | Is it worth it? When do we get money back? | eCPI, LTV_7d/30d/90d, ROAS, ROI, payback window; paying rate & ARPPU (IAP); trial→paid (subs) | wrong price paid or monetization lag — route with 3A |
| **Trust** (真) | Are these numbers real? | network_installs_diff_signed, CTR/CCR, CTIT distribution, LAT rate, SKAN quality | measurement or fraud problem — fix trust BEFORE acting on any other lens |

**Rule 1-1:** a Trust-lens anomaly invalidates decisions from the other three
lenses on the affected slice. Reconcile first, decide after.

## Part 2 · Benchmark quick reference (real data, median anchor)

Source: `references/benchmarks_2025h2.json` — Adjust internal data, 2025 Q4,
mean+median per **sub-vertical × geo × OS**. Always compare against the exact
cell; the extracts below exist to calibrate intuition, not to replace lookup.

### 2.1 Structural laws the dataset shows

- **L1 — median ≪ mean for eCPI** (heavy right skew: a few expensive campaigns
  drag the mean). Judge "typical" price with the **median**; the mean is an
  early-warning ceiling. Example: Strategy·US·Android eCPI mean $10.05 vs
  median $6.59.
- **L2 — iOS retains ~5–9pp better than Android** in the same category × geo
  (Casual D1: iOS US 25% vs Android US 19%). Never pool OSes when judging
  retention.
- **L3 — eCPI spans ~100–250× across geos** in the same category (Casual
  Android median: US $0.52 vs India $0.01). Account-level eCPI is a mix
  artifact — only per-geo comparison is meaningful (ties to rule 6-4).
- **L4 — retention decays on a stable curve:** in gaming, D7 ≈ 0.30–0.45 × D1
  and D30 ≈ 0.10–0.15 × D1 (Card/Board at the high end, Racing/Action low).
  A D7/D1 ratio far below the band with normal D1 = habit-loop break (3D-2),
  not an acquisition problem.
- **L5 — verticals live on different retention planets.** D1 median, US
  Android: Gaming(Casual) 19% · Social 16% · E-commerce 12% · Utilities 13% ·
  Finance 10%. Never judge a finance app against a gaming instinct.

### 2.2 Calibration extracts (median)

**Gaming sub-verticals (geo=ALL):**

| Sub-vertical | eCPI Android | eCPI iOS | D1/D7/D30 Android | D1/D7/D30 iOS |
|---|--:|--:|---|---|
| Casual | $0.13 | $2.06 | 21% / 7% / 2% | 28% / 10% / 3% |
| Puzzle | $0.37 | $1.71 | 22% / 8% / 3% | 28% / 12% / 4% |
| Casino | — | — | 20% / 7% / 2% | 24% / 10% / 3% |
| Slots | $10.51 | $16.15 | 19% / 8% / 3% | 22% / 10% / 5% |
| Strategy | $1.98 | $4.19 | 20% / 6% / 2% | 25% / 9% / 3% |
| Role Playing | $0.94 | $6.79 | 19% / 6% / 1% | 25% / 8% / 3% |
| Card | $1.61 | $3.45 | 23% / 11% / 5% | 26% / 13% / 6% |

**Geo price tiers (Casual · Android · eCPI median)** — the tier structure
generalizes across categories even where exact prices differ:

| Tier | Geos | eCPI range |
|---|---|--:|
| T1 | US $0.52 · JP $1.03 · KR $0.75 · CA $0.49 | $0.5–1.0 |
| T2 | UK $0.33 · DE $0.22 · FR $0.15 | $0.15–0.35 |
| T3 | BR $0.05 · MX $0.05 · TR $0.03 | $0.03–0.10 |
| T4 | IN $0.01 · ID $0.02 · VN $0.03 · EG $0.01 | $0.01–0.03 |

**Usage rules:**
- **2-1:** flag thresholds come from `median × (1 ± tol)` (tols in
  anomaly_playbooks YAML). Value between median and mean = "watch"; beyond
  mean = escalate severity.
- **2-2:** missing cell → skip the comparison and say so. Never interpolate a
  benchmark from a neighboring geo or category.
- **2-3:** benchmarks are a Q4'25 snapshot — directional context, not SLAs.
  Pair every benchmark finding with the slice's own trend before acting.

## Part 3 · Decision playbooks (metric → action)

### 3A · Budget: scale / hold / cut / pause

Preconditions: cohort mature for the window used (6-2), slice above the volume
floor (6-1), Trust lens clean (1-1). "Target ROAS" comes from the payback
method in Part 5 — not from an industry table.

| # | Condition | Decision |
|---|---|---|
| 3A-1 | ROAS(mature window) ≥ target **and** eCPI stable **and** volume headroom | **Scale in +20–30% steps**; re-read after each step (bid pressure raises eCPI non-linearly) |
| 3A-2 | ROAS < target **but** LTV curve still climbing & cohort young | **Hold.** Judging an immature cohort = cutting your best late-monetizing traffic |
| 3A-3 | ROAS < target **and** LTV curve flattened **and** cohort mature | **Cut 30–50%** and re-test; pause if second reading confirms |
| 3A-4 | ROAS ≥ target **but** eCPI rising fast (>+25% PoP) | **Don't scale yet** — diagnose with 3C first; scaling into fatigue compounds the price rise |
| 3A-5 | High spend share + ROAS in bottom quartile of account (the "drag") | Cut the drag before scaling winners — freed budget outperforms new budget |
| 3A-6 | No spend/revenue integration in Adjust | Economics lens is **not evaluable** — say so, run Volume/Quality/Trust lenses only (never fabricate ROAS) |

### 3B · Geo × network portfolio

The unit of decision is the **geo × network cell**, never the account average
(L3, 6-4). Judge each cell on two axes: retention vs the benchmark cell, and
cost vs the benchmark cell.

| | **eCPI ≤ benchmark** | **eCPI > benchmark ×(1+tol)** |
|---|---|---|
| **retention ≥ benchmark** | 3B-1 **Scale** — the compounding cell | 3B-2 **Keep, optimize price** (3C); tolerable if LTV supports it |
| **retention < benchmark ×(1−tol)** | 3B-3 **Trap cell** — looks cheap, is expensive per real user (see CPRU) | 3B-4 **Cut first** — paying above market for below-market users |

**CPRU (cost per retained user)** — the metric that unmasks trap cells:

```
CPRU_D7 = eCPI / retention_rate_7d
```

Worked example (real benchmark medians, Casual·Android): India eCPI $0.01,
D7 5% → CPRU $0.20; US eCPI $0.52, D7 7% → CPRU $7.43. India is genuinely
cheaper per retained user — **but** compare CPRU to per-geo LTV before
concluding: a US retained user may be worth 30× more. CPRU reframes "cheap
installs" into "price per real user"; LTV closes the loop.

- **3B-5:** one network >70% of paid installs = concentration risk — flag it
  even when performance is good (one policy change can halve the account).
- **3B-6:** organic share collapsing while paid grows = paid may be cannibalizing
  organic (brand terms, re-engagement overlap). Check before crediting paid.

### 3C · Creative / bid diagnosis (why did eCPI move?)

eCPI = eCPM / (CTR × CVR) × 1000. When eCPI rises, the cause is upstream in
exactly one of three places — read them together:

| # | Symptom pattern | Diagnosis | Action |
|---|---|---|---|
| 3C-1 | eCPI↑ · CTR↓ · eCPM flat | Creative fatigue | Refresh creatives; rotate the top-20% performers; expect 1–2 week decay cycles at high frequency |
| 3C-2 | eCPI↑ · eCPM↑ · CTR flat | Auction pressure (seasonality, competitor entry, Q4) | Bid down or accept; do NOT refresh creatives — they're not the problem |
| 3C-3 | eCPI↑ · CVR(click→install)↓ | Targeting drift or store-page mismatch | Check audience broadening, store listing, creative-to-store promise gap |
| 3C-4 | CTR↑↑ abnormal · CVR↓↓ | Click spam / injection | → fraud playbook (8.4); check CTIT distribution; block sub-publishers |

**3C-5:** always diagnose per geo × network. An account-level eCPI rise with
all cells flat = mix shift (more T1 traffic), which is a *strategy* change,
not a performance problem.

### 3D · Retention breaks → UA vs product routing

Which day breaks tells you which mechanism broke:

| # | Break point | Broken mechanism | Owner & action |
|---|---|---|---|
| 3D-1 | D1 low (vs benchmark cell) | First-session experience, onboarding, or traffic intent | If per-source: UA (cut 3B-3/3B-4 cells). If uniform: product onboarding |
| 3D-2 | D1 normal · D7 low (D7/D1 below the L4 band) | No habit loop; content wall in week 1 | Product/live-ops signal — UA can't fix it; hand to PM with the cohort data |
| 3D-3 | D7 normal · D30 low | Endgame content, economy balance, notification strategy | Product signal; low UA relevance |
| 3D-4 | **The router:** compare paid vs organic retention on the same geo | Paid ≪ organic → traffic quality (UA). Paid ≈ organic, both below benchmark → product | This one comparison decides who owns the fix — run it before assigning blame |

**3D-5:** retention below benchmark but stable is a *strategic* finding (worth
a recommendation); retention *falling* vs own history is an *operational* one
(worth an anomaly). Different urgency — don't conflate.

## Part 4 · Combined reads (the 2×2s)

Single metrics mislead; pairs diagnose.

### 4-1 · eCPI × retention (both vs benchmark cell)

| | retention OK | retention low |
|---|---|---|
| **eCPI OK** | Healthy — scale per 3A-1 | Cheap junk — trap cell 3B-3 |
| **eCPI high** | Buying premium users — acceptable if LTV covers (3B-2) | Worst cell — cut now (3B-4) |

### 4-2 · ROAS × cohort maturity

| | cohort young | cohort mature |
|---|---|---|
| **ROAS ≥ trajectory** | Ahead of curve — early scale candidate | Proven — scale 3A-1 |
| **ROAS < trajectory** | **Wait (3A-2)** — most common false alarm in UA | Cut 3A-3 |

"Trajectory" = the account's own historical ROAS-by-cohort-age curve for that
geo/network, not a fixed number.

### 4-3 · installs × attribution diff (Volume × Trust)

| | diff normal | diff inflated |
|---|---|---|
| **installs up** | Real growth | Network over-claiming — reconcile (8.3) before celebrating |
| **installs down** | Real drop — check spend, then 3C | Attribution/SDK breakage — data problem (8.1), not UA problem |

### 4-4 · The causal chain (where did it break?)

```
spend →(eCPM)→ impressions →(CTR)→ clicks →(CVR)→ installs
  →(D1)→ activated →(D7 habit)→ retained →(paying rate)→ payers
  →(ARPPU)→ revenue → LTV →(vs eCPI)→ ROAS → payback
```

Every arrow has one diagnostic metric. Walk the chain left→right; the first
broken link owns the failure — everything downstream of it is a symptom, not a
cause. Write causal stories in this order (it is also the §9.5 "analyst
narrative" order).

## Part 5 · Monetization modes (north stars & cut criteria)

The same numbers mean different things under different revenue models. Ask the
model at intake; it selects the column.

| | **IAP games** | **Ad-monetized / hybrid** | **Subscription** |
|---|---|---|---|
| North star | Cohort ROAS at D30/D90 | ARPDAU × retention tail | Trial→paid %, first renewal |
| Payback window | 90–180d | 7–30d | 6–12mo |
| Key extra metrics | paying rate, ARPPU, whale concentration (top-1% payer share) | impressions/DAU, eCPM by geo, ad LTV | trial start rate, early churn, MRR |
| LTV shape | Long climb; late whales | ≈ Σ(retained-days × ARPDAU) — **retention IS the LTV** | Step function at renewals |
| Cut rule | Project mature-cohort LTV; cut only when projection < CAC (3A-3) | Retention below benchmark = direct revenue diagnosis → cut fast | Judge at trial→paid + first renewal; ignore pre-trial noise |
| Trap | Cutting young cohorts before whales emerge (3A-2) | Chasing cheap installs with no tail (3B-3) | Optimizing trial starts instead of conversions |

- **5-1 (ROAS floor, method not table):** floor ROAS at window W =
  `W-day share of expected payback-window revenue`. Example: if D7 typically
  captures ~20% of D90 revenue and you need D90 breakeven, the D7 floor is
  ~0.20 (20%). Derive from the account's own curves; the playbook YAML defaults
  (15%/30%) are only cold-start placeholders.
- **5-2:** ad-monetized apps: benchmark eCPM by geo (in the dataset) is a
  *revenue-side* input too — a geo with T4 eCPI and T4 eCPM may still be CPRU-
  positive; run the arithmetic, not the instinct.

## Part 6 · Guardrails (how not to fool yourself)

| # | Guardrail | Rule |
|---|---|---|
| 6-1 | **Volume floor** | No flag/decision below `min_installs_for_signal` (default 50); budget decisions want ≥100–200 installs per cell |
| 6-2 | **Cohort maturity** | Never read D-N metrics on a cohort younger than N days; a "low D30 ROAS" on a 12-day cohort is not data, it's impatience |
| 6-3 | **Rolling windows** | Judge on 3–7d rolling values; single-day reads are noise (weekday/weekend, store review lags) |
| 6-4 | **Mix decomposition (Simpson's)** | Any account-level metric move: decompose by geo × network before concluding. A "worsening" average with all cells stable = composition shift |
| 6-5 | **OS separation** | Never pool iOS + Android for retention or eCPI comparisons (L2) |
| 6-6 | **Benchmark humility** | Median anchor; between median and mean = watch; missing cell = skip (2-2); snapshot not SLA (2-3) |
| 6-7 | **Trust gate** | Reconciliation/fraud findings freeze downstream decisions on that slice (1-1) |
| 6-8 | **Units** | ROAS/ROI arrive as API decimals — display %, note the conversion |
| 6-9 | **Evidence-bound verdicts** | Never emit a bare verdict ("差" / "poor" / "healthy"). Every judgment carries three parts: **observed value + comparison object (exact benchmark cell or own-history window) + gap magnitude**. Wrong: "89King 留存差". Right: "89King D1 1.7%,对 Casino/Vietnam/android 基准中位 12%,缺口 −86%"。 A verdict the reader cannot re-derive from the stated numbers is an opinion, not analysis |

## Part 7 · Wiring into the skill's output

- **Every verdict, everywhere (6-9):** KPI notes, anomaly reads, takeaways,
  chat summaries — all follow *value + comparison object + gap*. If a sentence
  says good/bad/normal without numbers the reader can check, rewrite it.
- **Executive Summary:** order takeaways by the Part 0 ladder (volume → quality
  → economics → trust); health score reflects the worst *gated* lens, not an
  average.
- **Anomaly `action` fields:** cite rule IDs — e.g. a `retention_below_benchmark`
  flag routes to `3D-4` (run the paid-vs-organic router) and `3B-3/3B-4`
  (portfolio action). `ecpi_above_benchmark` routes to `3C` (diagnose which
  upstream link moved) before any budget move.
- **`recommendations[].basis`:** name the rule and the evidence, e.g.
  `"3B-3: VN×NetworkX eCPI $0.02 but D7 1.1% → CPRU $1.8, 4× geo median"`.
- **Dashboard benchmark context:** dashed benchmark curves in retention charts,
  `benchmark` lines on KPI cards, colored "vs benchmark" cells in the breakdown
  (see build_dashboard.py schema) — always labeled with the exact cell
  (sub-vertical/geo/OS).
- **Thresholds:** numeric tolerances live in `anomaly_playbooks.md` YAML;
  benchmark values live in `benchmarks_2025h2.json`; this file holds the
  *decisions*. Change numbers there, not here.
