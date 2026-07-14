# Report Copy Templates (中文 / English)

Use these so summaries, anomalies, and recommendations read consistently in both
languages. **Keep metric names in English** (ROAS, eCPI, retention_rate_7d…); add
a short native gloss only when helpful. Pick the column matching the user's
conversation language.

## Severity labels

| key | 中文 | English |
|---|---|---|
| high | 高 | High |
| medium | 中 | Medium |
| low | 低 | Low |

## Anomaly sentence template

- **中文:** `【{severity}】{metric} 在 {slice} 出现异常:{change}(基线 {baseline})。可能原因:{cause}。建议:{action}。`
- **EN:** `[{severity}] {metric} anomaly in {slice}: {change} (baseline {baseline}). Likely cause: {cause}. Recommendation: {action}.`

## "What this means" one-liners (per chart)

- **中文:** `这说明:{plain_language_read}。`
- **EN:** `What this means: {plain_language_read}.`

## Verdict template (mandatory — decision_framework rule 6-9)

Never state a bare verdict ("差 / 好 / 正常 / poor / healthy"). Every judgment
is **value + comparison object + gap**, so the reader can re-derive it:

- **中文:** `{metric} = {value},对比 {comparison_object}({reference_value}),缺口 {gap}{,判定 {verdict}}。`
- **EN:** `{metric} = {value} vs {comparison_object} ({reference_value}), gap {gap}{, verdict: {verdict}}.`

`comparison_object` must be exact: a benchmark cell (`Casino/Vietnam/android
median`, Adjust'25Q4) or an own-history window (`前 4 周均值` / `trailing 4-week
mean`). Examples:

| ✗ 不合格 | ✓ 合格 |
|---|---|
| 89King 留存差 | 89King D1 1.7%,对 Casino/Vietnam/android 基准中位 12%,缺口 −86% |
| eCPI 偏高 | eCPI $0.30,对 Puzzle/Vietnam/android 基准中位 $0.08,+275% |
| Retention is fine | D1 9.1% vs Casino/Vietnam/android median 12%, −24% — within the 30% tolerance |

## Cause-hypothesis snippets

| situation | 中文 | English |
|---|---|---|
| install cliff | 某渠道/国家投放暂停、tracking 配置变更或归因丢失 | channel/country spend paused, tracking change, or attribution loss |
| eCPI spike | 竞价加剧、定向收窄或素材疲劳 | bid pressure, narrowed targeting, or creative fatigue |
| ROAS below floor | 流量质量下降或变现未跟上获客成本 | traffic quality drop or monetization lagging acquisition cost |
| retention break | 低质流量混入或版本/体验回归 | low-quality traffic mix-in or a product/experience regression |
| recon diff | 口径差异、时区、归因窗口或去重差异 | measurement definition, time zone, attribution window, or de-dup差异 |
| fraud signal | 点击注水/无效流量,需核查子渠道 | click injection / invalid traffic; investigate sub-publishers |
| SKAN null/invalid | conversion value 配置或 postback 解析问题 | conversion-value config or postback parsing issue |

## Recommendation templates

- **预算重分配 / Budget reallocation**
  - 中文:`把预算从 {from_slice}(ROAS {x}、eCPI {y})转向 {to_slice}(ROAS {z}),预计 {impact}。依据:{metric};置信度:{conf};优先级:{prio}。`
  - EN:`Shift budget from {from_slice} (ROAS {x}, eCPI {y}) to {to_slice} (ROAS {z}); est. {impact}. Basis: {metric}; confidence: {conf}; priority: {prio}.`
- **暂停/观察 / Pause or watch**
  - 中文:`建议暂停 {slice}:{reason}。`
  - EN:`Consider pausing {slice}: {reason}.`
- **调查 / Investigate**
  - 中文:`核查 {slice} 的疑似 {issue},方向:{direction}。`
  - EN:`Investigate suspected {issue} in {slice}; direction: {direction}.`
- **修复 / Fix**
  - 中文:`检查 {slice} 的归因/SDK/tracking 配置:{detail}。`
  - EN:`Check attribution/SDK/tracking config for {slice}: {detail}.`

Each recommendation should carry: **basis metric, expected impact, confidence,
priority.**

## Executive-summary scaffold

- **中文:** 本期关键结论(3–5 条)/ 整体健康度 / 最严重的 3 个异常 / 最值得做的 3 个动作。
- **EN:** Key takeaways (3–5) / overall health / top 3 anomalies / top 3 actions.
