# Metrics Glossary (Adjust Datascape)

Source: https://help.adjust.com/en/article/datascape-metrics-glossary

This is the dictionary the skill uses to **select metrics, compute anomalies, and
label charts**. Each metric lists: display name / definition / formula (when
non-trivial) / **API Metric ID** (what you pass to the MCP).

Placeholders:
- `{cohort_period}` → an actual period, e.g. `roas_7d`, `retention_rate_30d`.
  Supported: Days 0–120 (`0d`–`120d`), Weeks 0–52 (`0w`–`52w`), Months 0–36
  (`0m`–`36m`). Datascape exposes only a subset in its UI; the API can take any
  `0–120d`.
- `{event_slug}` → an actual event name, e.g. `purchase_events`, `registration_events`.

**Units quirk:** ROAS / ROI return from the API as **decimals** (`0.4`). Display as
percent (`40%`) and note the conversion in tooltips.

## Table of contents
- [6.1 Conversion / activity](#61-conversion--activity)
- [6.2 Cohort (retention / LTV / ROAS by N days)](#62-cohort-retention--ltv--roas-by-n-days)
- [6.3 Ad spend](#63-ad-spend)
- [6.4 Revenue](#64-revenue)
- [6.5 SKAdNetwork (iOS)](#65-skadnetwork-ios)
- [6.6 Analyst default metric set (pull first)](#66-analyst-default-metric-set-pull-first)

---

## 6.1 Conversion / activity

| API Metric ID | Display | Notes |
|---|---|---|
| `installs` | Installs | Attributed installs. |
| `network_installs` | Network Installs | Installs as reported by the network. |
| `network_installs_diff` | Network Installs Diff | `network_installs − installs` (abs gap). |
| `network_installs_diff_signed` | Network Installs Diff (signed) | Signed gap; key attribution-loss / over-reporting signal. |
| `organic_installs` | Organic Installs | |
| `non_organic_installs` | Non-organic Installs | Paid + tracked. |
| `reattributions` | Reattributions | |
| `deattributions` | Deattributions | |
| `sessions` | Sessions | |
| `base_sessions` | Base Sessions | |
| `clicks` | Clicks | Adjust-measured. |
| `attribution_clicks` | Attribution Clicks | Clicks used for attribution. |
| `network_clicks` | Network Clicks | Network-reported clicks. |
| `impressions` | Impressions | |
| `attribution_impressions` | Attribution Impressions | |
| `network_impressions` | Network Impressions | |
| `ctr` | CTR | `clicks / impressions`. Fraud signal when abnormally high. |
| `click_conversion_rate` | CCR (Click→Install) | `installs / clicks`. |
| `impression_conversion_rate` | Impression Conversion Rate | `installs / impressions`. |
| `installs_per_mile` | Installs per Mille | Installs per 1k impressions. |
| `daus` | DAU | |
| `waus` | WAU | |
| `maus` | MAU | |
| `limit_ad_tracking_installs` | LAT Installs | |
| `limit_ad_tracking_install_rate` | LAT Install Rate | Fraud / privacy signal when abnormal. |
| `att_consent_rate` | ATT Consent Rate | iOS. |
| `att_status_authorized` | ATT Authorized | iOS. |
| `reinstalls` | Reinstalls | |
| `uninstalls` | Uninstalls | |
| `events` | Events | All tracked events. |
| `{event_slug}_events` | <Event> Events | Per-event counts. |

## 6.2 Cohort (retention / LTV / ROAS by N days)

Replace `{cohort_period}` with e.g. `1d`, `7d`, `30d`.

**Retention**
- `retention_rate_{cohort_period}` — Retention Rate. Retained / cohort size.
- `retained_users_{cohort_period}` — Retained Users.
- `cohort_size_{cohort_period}` — Cohort Size.
- `paying_users_retention_rate_{cohort_period}` — Paying-User Retention Rate.

**LTV**
- `lifetime_value_{cohort_period}` — LTV (All revenue).
- `lifetime_value_iap_{cohort_period}` — LTV (IAP).
- `lifetime_value_ad_{cohort_period}` — LTV (Ad).
- `paying_user_lifetime_value_{cohort_period}` — Paying-User LTV.

**ROAS (cohort)** — *decimal in API, show as %*
- `roas_{cohort_period}` — ROAS (All).
- `roas_iap_{cohort_period}` — ROAS (IAP).
- `roas_ad_{cohort_period}` — ROAS (Ad).

**Revenue per user**
- `revenue_per_user_{cohort_period}`, `all_revenue_per_user_{cohort_period}`,
  `revenue_total_per_user_{cohort_period}`.

**Paying**
- `paying_users_{cohort_period}`, `paying_user_rate_{cohort_period}`,
  `first_paying_users_total_{cohort_period}`, `paying_user_conversion_rate_{cohort_period}`.

**Behavior**
- `sessions_per_user_{cohort_period}`, `time_spent_per_user_{cohort_period}`,
  `revenue_events_per_user_{cohort_period}`.

## 6.3 Ad spend

| API Metric ID | Display | Notes |
|---|---|---|
| `cost` | Ad Spend | Primary spend metric. |
| `adjust_cost` | Cost (Attribution) | |
| `network_cost` | Cost (Network) | Network-reported spend. |
| `network_cost_diff` | Cost Diff | Attribution vs network spend gap (reconciliation). |
| `ecpi` | eCPI | `cost / installs`. |
| `ecpi_all` | eCPI (All installs) | |
| `network_ecpi` | eCPI (Network) | |
| `ecpm` | eCPM | |
| `network_ecpm` | eCPM (Network) | |
| `ecpc` | eCPC | |
| `click_cost` | Click Cost | |
| `impression_cost` | Impression Cost | |
| `install_cost` | Install Cost | |
| `event_cost` | Event Cost | |
| `paid_installs` | Paid Installs | |
| `paid_clicks` | Paid Clicks | |
| `paid_impressions` | Paid Impressions | |

## 6.4 Revenue

*ROAS/ROI/RCR/ROI are ratios — decimal in API.*

| API Metric ID | Display | Notes |
|---|---|---|
| `revenue` | Revenue | |
| `cohort_revenue` | Cohort Revenue | |
| `ad_revenue` | Ad Revenue | |
| `cohort_ad_revenue` | Cohort Ad Revenue | |
| `all_revenue` | All Revenue | IAP + Ad. |
| `cohort_all_revenue` | Cohort All Revenue | |
| `arpdau` | ARPDAU | |
| `arpdau_iap` | ARPDAU (IAP) | |
| `arpdau_ad` | ARPDAU (Ad) | |
| `ad_rpm` | Ad RPM | |
| `gross_profit` | Gross Profit | |
| `cohort_gross_profit` | Cohort Gross Profit | |
| `return_on_investment` | ROI | decimal → %. |
| `revenue_to_cost` | RCR (Revenue-to-Cost) | decimal. |
| `roas` | ROAS | decimal → %. |
| `roas_iap` | ROAS (IAP) | |
| `roas_ad` | ROAS (Ad) | |
| `revenue_events` | Revenue Events | |

## 6.5 SKAdNetwork (iOS)

| API Metric ID | Display | Notes |
|---|---|---|
| `skad_installs` | SKAN Installs | |
| `skad_reinstalls` | SKAN Reinstalls | |
| `skad_total_installs` | SKAN Total Installs | |
| `valid_conversions` | Valid Conversions | |
| `invalid_payloads` | Invalid Payloads | Data-quality signal when rising. |
| `skad_qualifiers` | SKAN Qualifiers | |
| `conversion_value_0` | CV = 0 | |
| `skad_conversion_value_gt_0` | CV > 0 | |
| `skad_conversion_value_null` | CV null | |
| `skad_conversion_value_null_rate` | CV Null Rate | Data-quality signal. |
| `conversion_value_total` | CV Total | |
| `skad_ecpi` | SKAN eCPI | |
| `network_ad_spend_skan` | SKAN Ad Spend (Network) | |
| `skad_revenue_min_roas` / `skad_revenue_est_roas` / `skad_revenue_max_roas` | SKAN ROAS (Min/Avg/Max) | decimal. |
| `skad_revenue_min_roi` / `..._est_roi` / `..._max_roi` | SKAN ROI (Min/Avg/Max) | decimal. |
| `skan_total_revenue_min` / `..._est` / `..._max` | SKAN Revenue (Min/Avg/Max) | |
| `skad_coarse_conversion_values_low/medium/high` | Coarse CV distribution | |

> Some SKAN metrics require Adjust TAM enablement. If a query returns nothing for
> them, **drop them, continue, and note the degradation** in the dashboard
> Appendix and Data-Validation module.

## 6.6 Analyst default metric set (pull first)

To control cost, pull this core set by default; add the rest per scenario / user
selection:

```
installs, non_organic_installs, cost, ecpi, revenue, all_revenue, arpdau,
roas_7d, roas_30d, retention_rate_1d, retention_rate_7d, retention_rate_30d,
lifetime_value_7d, lifetime_value_30d, sessions, ctr, click_conversion_rate,
network_installs_diff_signed, network_cost_diff
```

For **iOS apps, auto-append:** `skad_installs, invalid_payloads,
skad_conversion_value_null_rate`.
