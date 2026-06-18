# Anomaly Playbooks

Detection logic for the four scenarios. Each anomaly is emitted with a uniform
structure so the dashboard can render it consistently:

> **severity | metric | affected slice | change magnitude | baseline |
> hypothesized cause | recommended action | traceable query**

---

## Editable thresholds (clients change these here)

These are the defaults `scripts/detect_anomalies.py` reads. They live at the top
of this file on purpose — edit them in one place.

```yaml
thresholds:
  install_drop_pct: -0.30        # period-over-period install/session drop flagged at ≤ -30%
  install_drop_percentile: 0.05  # ...or below historical p5
  cpi_rise_pct: 0.25             # eCPI/eCPC/eCPM rise flagged at ≥ +25%
  roas_floor_d7: 0.15            # roas_7d target floor = 15% (API decimal 0.15)
  roas_floor_d30: 0.30           # roas_30d target floor (tune per app economics)
  retention_drop_pct: -0.20      # D1/D7 retention period-over-period drop flagged at ≤ -20%
  reconciliation_diff_pct: 0.10  # Adjust vs network/external diff flagged at > 10%
  ctr_sigma: 3.0                 # CTR flagged above rolling mean + 3σ
  outlier_k: 3.0                 # generic rolling mean ± k·σ outlier band
  skan_null_rate_max: 0.20       # skad_conversion_value_null_rate flagged above 20%
  invalid_payload_rate_max: 0.05 # invalid_payloads / skad_total_installs above 5%
  min_installs_for_signal: 50    # ignore slices below this volume (noise floor)
severity_bands:                  # by |relative change| vs the flagging threshold
  high: 2.0                      # ≥ 2× over threshold
  medium: 1.0                    # over threshold
  low: 0.5                       # approaching threshold (early warning)
```

## Detection methods (combined)

- **Period-over-period / year-over-year shift:** current vs comparison period
  change rate beyond threshold.
- **Statistical outlier:** rolling mean ± k·σ on a time series (or MAD / IQR);
  z-score across dimension slices to find anomalous segments.
- **Structural gap:** a slice that should have data shows 0 or drops below a
  historical percentile (missing data / 掉量).
- **Consistency check:** Attribution vs Network (`*_diff` metrics) beyond threshold.
- **Ratio anomaly:** CTR / CCR / LAT / null-rate landing in an abnormal range.

Always respect `min_installs_for_signal` to avoid flagging tiny noisy slices.

---

## 8.1 Data quality (P0 — default on)

- `installs` / `sessions` by `date × network × country`: cliff detection
  (drop > `install_drop_pct` **or** below historical p`install_drop_percentile`).
- Attribution loss: `network_installs_diff_signed` absolute value / share rising
  abnormally.
- SKAN: `invalid_payloads` share up (> `invalid_payload_rate_max`);
  `skad_conversion_value_null_rate` > `skan_null_rate_max`.
- Missing data: a slice that normally has data shows a 0/absent row on a date.

## 8.2 UA performance (P0 — default on)

- `ecpi` / `ecpc` / `ecpm` period-over-period rise > `cpi_rise_pct`.
- `roas_7d` < `roas_floor_d7`, `roas_30d` < `roas_floor_d30`;
  `return_on_investment` turning negative.
- `retention_rate_1d/7d/30d` drop > `retention_drop_pct`; `arpdau` anomalies.
- By campaign/creative: find "high spend, low ROAS/retention" drags
  (rank by `cost` among slices below the ROAS floor).

## 8.3 Cross-source reconciliation (P1)

- Adjust built-in: `network_installs_diff` (a.k.a. installs_diff_network),
  `network_cost_diff`, attribution vs network.
- External (mode B): Adjust installs/spend vs Meta/Google export, aligned on
  `date × campaign`; compute diff rate, flag > `reconciliation_diff_pct`.
- Output "Top-N differences + likely causes" (measurement definition, time zone,
  attribution window, de-duplication).

## 8.4 Ad-fraud signals (P1)

- CTR abnormally high (> rolling mean + `ctr_sigma`·σ) / CCR abnormal
  (click-injection signs).
- A sub-publisher with an install spike but `retention_rate_1d` ≈ 0 and
  `revenue` ≈ 0 (invalid traffic).
- LAT share `limit_ad_tracking_install_rate` abnormal.
- `network_installs_diff` inflated abnormally (network over-reporting).

---

## Output copy

Use `report_copy.md` for the bilingual phrasing of severity labels, cause
hypotheses, and recommended actions so anomalies read consistently. Each anomaly
must include a **traceable query** string (the metrics, dimensions, date range,
and revenue basis used) so the analyst can reproduce it in Datascape.
