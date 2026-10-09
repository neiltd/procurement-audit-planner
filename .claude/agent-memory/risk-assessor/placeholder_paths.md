---
name: placeholder-paths
description: How to put threshold/tier amounts and ratios into risk prose without tripping W-FIGURE in build_register.py
metadata:
  type: feedback
---

Never type a threshold amount (e.g. a £ tier) or a ratio into risk prose or titles; put it in a placeholder pointing at analytics.json.

**Why:** the builder's typed-figure regex catches £ amounts, 3+ digit numbers, decimals and percentages; only years and numbers after "clause/row/table/appendix/page" are exempt. Titles are checked too.

**How to apply:** tier amounts resolve through list indexes, e.g. `{{$.thresholds.tiers[2].value|gbp}}`; quote/publication thresholds via `{{$.thresholds.quote_threshold.value|gbp}}`; ratio flags via `$.tests.<test>.parameters.<key>`. A path to a list or object is an error, so never point at `parameters.tiers` itself. Where no placeholder fits, name the level by citing the rule (e.g. "the Key Decision level [rule:...]"). Signals for L3/L4 must be numeric metrics under `$.tests.<test>` outside parameters/rule_ids/status; `high_value_suppliers` never counts.
