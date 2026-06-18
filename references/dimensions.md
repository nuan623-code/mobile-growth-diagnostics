# Dimensions

Group-by and cross-analysis dimensions. Aim for **analyst-grade** breakdowns:
support at least two-dimension crosses, and enable drill-down in the dashboard.

## Dimension list

| Dimension | API key (typical) | Notes |
|---|---|---|
| Date | `date` (`day` / `week` / `month`) | Choose granularity by window length. |
| App | `app` | Multi-app comparison supported. |
| Platform | `platform` / `os_name` | `ios` / `android`. iOS triggers SKAN metrics. |
| Country / Region | `country` / `region` | ISO country codes. |
| Network | `network` | Acquisition channel. |
| Campaign | `campaign` | |
| Adgroup | `adgroup` | |
| Creative | `creative` | |
| Partner | `partner` | |
| Store type | `store_type` | |
| Device type | `device_type` | |

## Group-by & cross rules

- **Always include `date`** for any trend/anomaly work (period-over-period and
  rolling-window detection need a time axis).
- **Two-dimension crosses are the analyst default.** Prefer the highest-signal
  pairs for the chosen scenario:
  - Data quality → `date × network`, `date × country`.
  - UA performance → `network × country`, `campaign × creative`.
  - Reconciliation → `date × campaign` (aligns with external exports).
  - Fraud → `network × sub-publisher/adgroup`.
- **Cost discipline:** crossing many high-cardinality dimensions explodes row
  count and token cost. Cap to the top-N slices by spend or installs, and offer
  drill-down rather than fetching everything up front.

## Drill-down model (for the dashboard)

The cross-dimension module supports click-to-expand:
- Click a **country** → expand that country's **network** breakdown.
- Click a **network** → expand its **campaign** breakdown.

Pre-compute the parent level for all slices, and the child level only for the
top-N parents (by spend), so the single-file dashboard stays lightweight while
still allowing the most useful drill-downs. Note any slices whose children were
omitted for size in the Data-Validation module.
