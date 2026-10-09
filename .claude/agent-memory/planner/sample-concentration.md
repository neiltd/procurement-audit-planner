---
name: sample-concentration
description: build_pack has no per-supplier cap on sample units; how to spread a stratum dominated by one supplier
metadata:
  type: feedback
---

The sample recipe has no "max units per supplier" option. When a challenger flags one supplier filling a stratum, check `outputs/samples/T-*.csv` (`unit_supplier`): `pick: interval` spreads units in proportion to each supplier's share of the stratum. If a single supplier at one repeated rate holds most rows, filter it out with `supplier_norm ne` and request its contract once in the step text.

**Why:** a challenge in the rev-3 run: interval alone left one supplier with half of T-02.

**How to apply:** check unit_supplier counts after any placement-stratum recipe change. See [[prose-figure-traps]].
