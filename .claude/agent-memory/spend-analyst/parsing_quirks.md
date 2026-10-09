---
name: parsing-quirks
description: How-to lessons for WBC spend workbooks, Contracts Finder export and rules.json tier building (no figures or supplier names)
metadata:
  type: project
---

- Spend `Date` cells carry payment-run times (not midnight), so "same timestamp" means one payment run. Measure the 30-day and 7-day gaps in calendar days (normalise first), not raw timedeltas.
- `pd.read_excel(header=None)` keeps leading blank rows, so sheet row = raw index + 1. The openpyxl self-check confirmed this.
- The pension fund administrator is a borough council. Apply the pension narrative rule BEFORE public_body so those rows get the right reason. "Prudential AVC Teachers" is pension (AVC) but doesn't contain the word "pension"; it needs `\bAVC\b`.
- RBWM appears as "Royal Borough of ..." with no "COUNCIL" in the name, so the public-body pattern needs `ROYAL BOROUGH OF`.
- rules.json tiers: a `threshold_high` bound also defines a tier. "less than X" makes X low-inclusive for the next tier, and "up to X" makes it low-exclusive. Rules disagree at 500,000, so record "mixed" and use a closed band.
- contracts.csv also has `Contract start/end date` columns that duplicate `Start/End Date`. The export only covers publications from 2021, so pre-2021 long contracts never match. Caveat off_contract with this.
- Edit-by-python string replace silently failed once on a multi-line match. Use the Edit tool for multi-line changes.

**Why:** each of these cost a rerun or would have mis-tagged rows.
**How to apply:** check them first when rebuilding clean/contracts/analyse on new months.
