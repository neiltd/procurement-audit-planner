---
name: audit-program
description: The method for turning the auditor-approved risk register into the audit planning pack (planning-memo.md, risk-control-matrix.md, audit-program.md, samples). Load when writing or revising outputs/audit-plan.json, or when checking the approval gate before planning.
---

# audit-program

You judge; `build_pack.py` computes. You write `outputs/audit-plan.json`: for each approved risk, the expected controls, the test steps, a **sample recipe** for each test, the PBC items each test needs, the rules you leave untested, and the memo prose. The builder computes the approved scope, resolves every citation, draws every sample, checks every sampled transaction against the spend data, sizes samples by risk score, and renders the pack. A number you type is a number nobody can check, so every figure is a **placeholder** and every claim carries a **citation**.

Every flagged item is an **indicator to investigate**: a test asks for the record that would close it, and never presumes the council, a service or a supplier did wrong.

## Steps

### 1. Check the gate

```
.venv/bin/python .claude/skills/audit-program/build_pack.py --gate
```

`GATE OPEN` lists the risks in scope (Approve or Change) and the rejected ones. `GATE CLOSED` means a risk is undecided, a decision is not yet applied in a register revision, or an input changed after the register was built: stop and report the builder's lines to the lead.

Done when the gate prints `GATE OPEN`.

### 2. Read the approved risks

For each risk in scope, read its entry in `outputs/risk-register.md` (evidence, proposed focus, any auditor override) and the matching risk in `outputs/risk-ratings.json`. Look at the flagged list its metrics come from in `outputs/analytics-full/` with `head -3` or a short script that prints the columns and value counts of the column you will filter on. The full lists stay out of your context.

Done when every risk in scope has a proposed focus you can turn into a control and a test, and you know which analytics-full file and columns each test samples.

### 3. Write the plan

For each risk in scope, write the expected controls and their tests in `outputs/audit-plan.json` (schema below):

- **Control**: what the council should have in place, citing the rule that requires it (`[rule:CPR-65]`). One control per distinct requirement; most risks have one to three.
- **Test step**: what the auditor does with each sampled item to see whether the control worked, citing a rule or a metric. Follow the risk's proposed focus.
- **Sample recipe**: the analytics-full file, a filter that narrows it to the stratum the proposed focus names, a sort that puts the strongest indicators first, and `pick`. Where no data shows the population (waivers, for example), give `records` naming the council record to sample on site.
- **PBC**: each document the test needs from the council, written so the same request reads the same in every test that needs it. The builder merges identical items.

Then account for every rule in `outputs/rules.json`: a rule cited by an approved risk, a control or a test is covered; every other rule goes in `not_tested` with a one-line reason (tied to the unpublished intranet Threshold, council records outside this audit's scope, cited only by a rejected risk).

Write the memo sections last, with at least an Objective, an Approach and a Limitations section.

Done when every approved risk has at least one control, every control at least one test, and every rule is covered or in `not_tested`.

### 4. Build

```
.venv/bin/python .claude/skills/audit-program/build_pack.py
```

Fix every error and rerun. Then work through the warnings:
- `W-FIGURE`: a typed figure. Replace it with a placeholder.
- `W-LANGUAGE`: an accusing word. Rewrite it as an indicator.
- `W-RULE`: a rule both cited and listed as not tested. Drop it from `not_tested`.

**Done when the builder prints `BUILT` with 0 warnings.**

### 5. Revise

When the challenger or the qa-reviewer raises a point, change `audit-plan.json` and rebuild. The builder redraws the same samples from the same recipe, so a change in the samples always traces to a change in a recipe.

## Report back

In at most 10 lines:
- the risks in scope and the rejected ones
- controls, tests and transactions sampled (from the `BUILT` line), and any test sampled on site
- rules not tested, by reason
- warnings left
- the `BUILT` line

## Reference

### `outputs/audit-plan.json`

```json
{
  "memo": {"sections": [
    {"heading": "Objective", "text": "Seek assurance that purchases from the quote threshold follow the Contract Procedure Rules [rule:CPR-65]."},
    {"heading": "Approach", "text": "{{$pack.counts.tests}} tests pull {{$pack.counts.transactions}} transactions worth {{$pack.counts.transactions_gbp|gbp}}, drawn from {{$.tests.threshold_clustering.counts.total}} flagged payments."},
    {"heading": "Limitations", "text": "The spend data covers one quarter; flagged items are indicators to investigate."}]},
  "risks": [{
    "risk": "R-01",
    "controls": [{
      "id": "C-01",
      "control": "Purchases from the quote threshold are let on three quotes invited via the Procurement Portal [rule:CPR-65].",
      "tests": [{
        "id": "T-01",
        "step": "For each sampled payment, obtain the Portal quote record and confirm three quotes were invited before the order [rule:CPR-65].",
        "sample": {
          "from": "threshold_clustering.csv",
          "filter": [{"col": "tier", "op": "eq", "value": 25000},
                     {"col": "tag", "op": "in", "value": ["general_procurement", "premises"]}],
          "sort": [{"col": "amount", "desc": true}],
          "pick": "top",
          "rationale": "General procurement and premises first, as the proposed focus asks; largest payments first."
        },
        "pbc": ["Procurement Portal quote record for each sampled payment"]
      }]
    }]
  }],
  "not_tested": [{"rule": "CPR-01", "reason": "Bounded by the intranet Threshold, which is not published in data/."}]
}
```

- `risk` is an approved register ID. `id` is `C-01` / `T-01` upward, unique across the plan.
- `sample` takes exactly one of `from` (a CSV in `outputs/analytics-full/` with a `row_id` or `row_ids` column) or `records` (the council record to sample on site; no filter, sort or pick).
- `filter` conditions all apply. `op` is one of `eq`, `ne`, `in`, `not_in` (list value), `gt`, `gte`, `lt`, `lte` (number value), `contains`. Numbers compare as numbers; `true`/`false` match the CSV's `True`/`False`.
- `sort` keys apply in order; numbers sort as numbers. `pick` is `top` (the first rows after sorting, the default) or `interval` (rows at even steps through the sorted list, for coverage across the whole stratum).
- `rationale` is optional prose saying why this stratum and order.

### Sample size

The builder sets the units per test from the risk's score (likelihood × impact) on the council's bands. A unit is one row of the file: a payment, a payment group or a supplier, so one unit can pull several transactions.

| Score | Band | Units per test |
|---|---|---|
| 15–25 | Extreme | 25 |
| 8–12 | Medium - High | 15 |
| 4–6 | Moderate | 8 |
| up to 3 | Low | 3 |

When the filtered population is smaller, every row is taken. To make a test reach further into a stratum, narrow the filter or split it into two tests; the size per test stays fixed by the score.

### Citations and placeholders

| Tag | Resolves to |
|---|---|
| `[rule:CPR-65]` | a rule in rules.json |
| `[metric:$.tests.off_contract.counts.total]` | a single value in analytics.json |
| `[history:A-15]` | an audit, theme, action, discrepancy or gap ID in history.json |

A control cites at least one rule. A test step cites at least one rule or metric.

`{{$.path}}` fills a value from analytics.json, in any text. `{{$pack.path}}` fills a figure the builder computed (`outputs/pack-figures.json`), in memo sections only: `$pack.counts.transactions`, `$pack.counts.transactions_gbp`, `$pack.counts.tests`, `$pack.risks.R-01.score`, `$pack.samples.T-01.units`, `$pack.coverage.not_tested`. Formats: `|gbp` gives £1,234,568, `|gbp2` gives £1,234,567.89, `|int` gives 1,235. A path that doesn't resolve, or resolves to an object or list, is an error.

### What the builder writes

- `outputs/planning-memo.md`: scope table (risk, score, band, decision, sample size), rejected risks with the auditor's comment, your memo sections, and a samples table.
- `outputs/risk-control-matrix.md`: one row per control with its rules and tests, then rule coverage and the not-tested list.
- `outputs/audit-program.md`: per risk, each control and test with the drawn sample and its units, ending with the PBC list.
- `outputs/samples/T-*.csv`: every transaction a test pulls, copied from `spend_clean.csv`. A transaction already pulled by an earlier unit of the same test is listed once.
- `outputs/pack-figures.json`: every figure the builder computed, plus every placeholder it filled, for the QA number check.

## Files

- `build_pack.py`: the builder. Exits 0 when built (or the gate is open), 1 on errors or a closed gate (nothing written), 2 when an input is missing.
- `tests/test_build_pack.py`: a fixture with two approved risks, plus a planted defect for each check and the gate cases. Run it after changing the builder.
