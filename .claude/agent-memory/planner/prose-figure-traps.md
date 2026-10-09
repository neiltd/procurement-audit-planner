---
name: prose-figure-traps
description: Text patterns in audit-plan.json prose (steps, pbc, rationale, not_tested) that trip build_pack W-FIGURE, and how sample units count transactions
metadata:
  type: feedback
---

Write "S151", never "S.151": the dot creates a word boundary and the three digits trip W-FIGURE (TYPED_FIGURE_RE matches any 3+ digit run). Window lengths, thresholds and ratios go in as `{{$.tests.<test>.parameters...}}` placeholders, not typed. Numeric values in sample `filter` are fine (they aren't prose).

**Why:** check_prose runs over steps, rationale, pbc and not_tested reasons, not just the memo.

**How to apply:** when a sampled unit is a supplier or payment group (off_contract, split_purchases, duplicates), the builder pulls every payment in it, so the transaction count far exceeds units; say so in the memo Approach so the count does not read as a typo. See [[audit-program-skill]].
