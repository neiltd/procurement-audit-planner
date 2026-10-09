---
name: risk-assessment
description: The method for rating procurement audit risks on the council's likelihood × impact scale and building outputs/risk-register.md and the auditor's decision template. Load when writing or revising outputs/risk-ratings.json, or when applying the auditor's decisions after the gate.
---

# risk-assessment

You judge; `build_register.py` computes. You write `outputs/risk-ratings.json`: which risks exist, a likelihood and impact score for each, and prose that cites its evidence. The builder resolves every citation, fills every figure from `analytics.json`, computes score, matrix label and band from the council's method in `history.json`, and renders `outputs/risk-register.md` and `outputs/auditor-comments.md`. A number you type is a number nobody can check, so every figure is a **placeholder** and every claim carries a **citation**.

Every risk is an **indicator to investigate**: "payments cluster just below the quote threshold", never a statement that the council, a service or a supplier did wrong.

## Steps

### 1. Read the evidence

- `outputs/rules.json`: rules by `type` and `evidence_source`, the `parameters` left null, and the `notes`.
- `outputs/analytics.json`: each test's `status`, `counts`, `gbp`, `by_tier`, notes and `rule_ids`. Print paths and values with a short script; the CSVs in `analytics-full/` are for the auditor, so read at most their `.head()`.
- `outputs/history.json`: `audits` (opinions), `risk_themes`, `scoring_method`, `discrepancies`, `gaps`.

If any of the three is missing or unreadable, stop and report it.

Done when you hold a list of candidate risks, each tied to at least one rule and at least one metric or history item, and every test whose status is `ran` (except the `high_value_suppliers` population) appears in at least one candidate.

### 2. Settle the method's conflicts

Run the builder once with your draft. It fails with `E-CONFLICT` for every discrepancy whose evidence sits on a page holding the council's scales, matrix or bands. Name each one in `method.choices` (which side the register uses, which it marks, and why) or in `method.not_affected` (why no rating depends on it). See **Method conflicts** below.

Done when the builder reports no `E-CONFLICT`.

### 3. Rate each risk

Score likelihood with the **likelihood rubric** and impact with the **impact rubric**, both below. Write the justification as you rate: name the rubric row, cite the evidence that puts the risk on that row, and put every figure in a placeholder. Apply the repeat-finding uplift where it qualifies.

Done when every candidate risk has both scores and both justifications carry at least one citation.

### 4. Build

```
.venv/bin/python .claude/skills/risk-assessment/build_register.py
```

Fix every error and rerun. Then work through what remains:
- `DROPPED`: a risk whose likelihood or impact justification has no citation that resolves. Fix the citation, or leave the risk dropped only when no evidence exists for it.
- `W-FIGURE`: a typed figure. Replace it with a placeholder. A clause number or year is fine.
- `W-LANGUAGE`: an accusing word. Rewrite it as an indicator.

**Done when the builder prints `BUILT`, with no `W-FIGURE` or `W-LANGUAGE` warning left.**

### 5. Revise after the gate

The auditor fills in `outputs/auditor-comments.md`. When you are asked to revise, read each row and apply it:

| Decision | What you do |
|---|---|
| Approve | Nothing. |
| Reject | Nothing. The risk stays in the file and the register shows it out of scope. |
| Change | Make exactly the change the comment asks for. A rating change is applied as asked, even against your rubric; the builder marks it as an auditor override. Keep a citation in the justification. |
| GENERAL Change | Add the risk (fields `["new"]`) or make the scope edit asked for, citing decision `GENERAL`. |

Add a `revision` block: `number` is the register's revision plus one, and `changes` lists each edit with the decision that asked for it. Change nothing else; never delete a risk. If a comment is unclear, or can't be applied with a citation, stop and put the question to the lead rather than guessing.

Done when the builder prints `BUILT revision N`. Its Gate line says `ready`, or names the risks still without a decision.

## Report back

In at most 12 lines:
- risks rated, by band, with the top three by score
- risks dropped and why
- each method choice, one line
- warnings left
- on a revision, what changed and any auditor overrides
- the builder's `BUILT` and Gate lines

## Reference

### `outputs/risk-ratings.json`

```json
{
  "method": {
    "choices": [{"discrepancy": "D-09", "used": "Table 4: only Extreme (15-25) goes to the Corporate Risk Register",
                 "marked": "Figure 4: score 9 or above", "reason": "Table 4 is the table the score is read against.",
                 "mark": {"min_score": 9, "max_score": 14, "text": "would go to the Corporate Risk Register under Figure 4"}}],
    "not_affected": [{"discrepancy": "D-06", "reason": "A version label of the appetite guidance; no rating uses it."}]
  },
  "risks": [{
    "id": "R-01",
    "title": "Payments clustering just below the quote threshold",
    "description": "{{$.tests.threshold_clustering.by_tier.25000.rows}} payments worth {{$.tests.threshold_clustering.by_tier.25000.gbp|gbp}} sit just below {{$.thresholds.quote_threshold.value|gbp}} [rule:CPR-65].",
    "likelihood": {"score": 3, "justification": "L3: one test flags payments in the band below the quote threshold [metric:$.tests.threshold_clustering.by_tier.25000.rows]."},
    "impact": {"score": 3, "criterion": "Compliance (litigation, regulatory, contract)",
               "justification": "C3: contracts from the quote threshold need three quotes via the Portal [rule:CPR-65]."},
    "repeat_uplift": null,
    "proposed_focus": "Pull the flagged payments and request the quote record for each [rule:CPR-65]."
  }],
  "revision": {"number": 1, "changes": [{"risk": "R-01", "fields": ["likelihood"], "decision": "R-01",
                                          "note": "Raised to 4 as the auditor asked."}]}
}
```

- `id` is `R-01` upward. `criterion` is a column heading of the council's impact scale, copied exactly.
- `impact.exposure` (financial criterion only) is a `$.path` to the £ at stake; see the impact rubric.
- `repeat_uplift` is `null` or `{"audit": "A-..", "justification": "... [history:A-..]"}`.
- `revision` is absent until the auditor has decided. `fields` are drawn from `title`, `description`, `likelihood`, `impact`, `repeat_uplift`, `proposed_focus`, or `new`.

### Citations and placeholders

| Tag | Resolves to |
|---|---|
| `[rule:CPR-65]` | a rule in rules.json |
| `[metric:$.tests.off_contract.counts.total]` | a single value in analytics.json |
| `[history:A-15]` | an audit, theme, action, discrepancy or gap ID in history.json |

`{{$.path}}` puts a value from analytics.json into the prose. Formats: `{{$.path|gbp}}` gives £1,234,568, `|gbp2` gives £1,234,567.89 and `|int` gives 1,235; plain integers get thousands separators. A path that doesn't resolve, or that resolves to an object or list, is an error. Keys with digits work as written: `$.tests.split_purchases.by_tier.25000.groups`.

The builder lists each risk's resolved citations under its Evidence heading, so a citation also serves as the evidence list.

### Likelihood rubric

The council's scale is the chance the risk occurs within 12 months. Read it off the evidence as follows. When a risk fits two rows, take the lower and name the row that nearly applied.

| Score | Row | The evidence |
|---|---|---|
| 1 Rare | L1 | No test can see the risk (the rule's `evidence_source` is `council_records` only), and no history item touches the theme. |
| 2 Unlikely | L2 | A test looked and flagged nothing (count 0); or every flagged item has a benign pattern recorded in analytics.json (e.g. same-timestamp payment runs, instalments); or the evidence is `council_records` only and the last audit on the theme was Reasonable or Substantial. |
| 3 Likely | L3 | One test flags items (a count or £ above zero) that analytics.json does not explain away. |
| 4 Almost Certain | L4 | Two or more different tests flag the same risk. |
| 5 Certain | (none) | Reached only from 4 through the repeat-finding uplift. |

A **signal** is a metric citation in the likelihood justification under `$.tests.<test>`, outside `parameters`, `rule_ids` and `status`, whose value is a number above zero. `high_value_suppliers` is a population, not a signal. The builder enforces: L3 needs one signal, L4 needs signals from two different tests, and base 5 is rejected. These checks are lifted only for a score the auditor overrode.

### Impact rubric

Choose the impact-scale column by what goes wrong if the control fails, then read the level off that column:

- **Compliance (litigation, regulatory, contract).** This is the default for procedure, publication, approval, anti-avoidance and contract-content rules. The level follows the value tier of the flagged items, cited by rule or `by_tier` metric:

  | Tier | Level |
  |---|---|
  | below the quote threshold | C2 (low possibility) |
  | from the quote threshold up to the intranet Threshold | C3 (reasonable) |
  | £500,000 and above, or a rule tied to the Threshold | C4 (high) |

  C5 (probable) needs a history item showing challenge or regulatory interest.
- **Financial loss to Council.** Use this for money paid that should not have been, such as duplicates or spend beyond an award. Set `impact.exposure` to the analytics £ figure closest to money that could be lost (e.g. `$.tests.duplicates.same_timestamp.gbp_repeat_value`), not the total spend through the suppliers. The builder maps it onto the £ amounts in the council's column (a boundary amount takes the higher score) and fails if your score differs. The register labels it an upper bound, not a loss.
- **The other columns** apply only when a cited history item points at that consequence.

### Repeat-finding uplift

When a past audit **on the same theme** carries an adverse opinion (Limited Assurance, Weak, No Assurance, Minimal or Unsatisfactory), likelihood rises by one point, to at most 5. Set `repeat_uplift` with the audit ID, and in the justification say why the audit covers the same process, citing it. The builder rejects an uplift on any other opinion, shows the base and uplifted scores on the risk, and allows only one uplift per risk. A Reasonable or Substantial opinion on the theme argues the other way: cite it in the likelihood justification.

### Method conflicts

The council's papers disagree with themselves in places (history.json `discrepancies`). The register uses one side, marks the other, and says so in its header, so nothing is resolved silently. Some choices are fixed in the builder, and the header states them:

- Labels and scores come from the scale tables, not from a label printed elsewhere.
- The band comes from the band table's score ranges, which carry escalation and response. A matrix cell label that differs is shown in brackets.
- Financial impact uses the £ amounts, not the % ranges.

Every discrepancy on a scoring-method page must still be named in `method.choices` with its ID. Where a fixed choice covers it, `used` says the same thing as that choice. Where none does (the Corporate Risk Register threshold, for example), choose the side the score is read against, and give `mark` a score range so every affected risk carries a † note naming the other side.

### Revisions and the gate

- `outputs/risk-register.state.json` is the **baseline**: what the auditor last reviewed. The builder diffs against it. Leave it alone.
- Before any decision exists, the register is a draft at revision 0 and you may change anything.
- Once decisions exist, every change must trace to a new Change decision. The build fails on:
  - a Change left unapplied
  - a field that changed without a decision asking for it
  - a field listed as changed that didn't change
  - a removed risk
- Decisions in `auditor-comments.md` survive every rebuild. A decision on a risk that is no longer rated moves to an "orphaned" table there.
- The gate opens when the register is at revision 1 or later and every rated risk has a decision. `build_pack.py --gate` reads `gate` from the state file.

## Files

- `build_register.py`: the builder. Exits 0 when built, 1 on errors (nothing written), 2 when an input is missing.
- `tests/test_build_register.py`: a fixture with one good risk and one broken risk, plus a planted defect for each check and the revision cycle. Run it after changing the builder.
