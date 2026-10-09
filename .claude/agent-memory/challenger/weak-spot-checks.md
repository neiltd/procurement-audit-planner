---
name: weak-spot-checks
description: Where the strongest challenges came from when reviewing the planning pack; check these first
metadata:
  type: feedback
---

Read `pack-figures.json` `samples.T-xx.unit_list` before the prose. Most of the accepted challenges came out of it.

- Sorting by group_total fills split-purchase samples with recurring term-contract groups. Ask for a sort with few payments and the largest single payment first.
- Check unit concentration: one supplier holding many units of a test.
- A filter of tier >= X double-counts groups across tiers. A unit with 0 transactions gives it away.
- Tag filters can drop a small but high-value tag (e.g. agency_staff) from the off-contract test.
- Look in `not_tested` for "Threshold not published" reasons. The council holds the Threshold, so the pack can request it as a PBC item.
- Check that cleaning exclusions (e.g. redacted rows) are stated in the memo's Limitations.

**Why:** the planner accepted all of these in one rebuild. Rating and scope points go to the auditor however strong they are.
**How to apply:** prepare the candidates from the register, then confirm them against the unit_list once PACK READY arrives. Cite string-valued paths (e.g. `$.cleaning.exclusions_full_list`) when a list index might not resolve.
