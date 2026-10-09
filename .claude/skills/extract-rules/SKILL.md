---
name: extract-rules
description: Turn the council's Contract Procedure Rules (data/contract-rules.pdf) into outputs/rules.json, with testable rules, clause references and verbatim quotes. Use when the user runs /extract-rules or asks to build or rebuild rules.json.
---

# extract-rules

Read `data/contract-rules.pdf` and write `outputs/rules.json`. In that file every clause of the PDF is either a testable **rule** or an **exclusion** with a reason, and every quote is copied from the page it cites. Downstream agents compute against these rules, so every threshold must come from the page. You read and classify; `verify_quotes.py` checks.

## The document

- 15 pages. Page N is the Nth form-feed chunk of `pdftotext` output, and also the number in each page footer (`$3inav0bz.docx  N`).
- Sections 1–11 are numbered clauses `N.N`, `N.N.N` and `N.N.N.N`, followed by three appendix tables:
  - **App A** (p11): delegated authority to award, by contract value. It has four unlabelled bands; call them `App A row 1`–`App A row 4`, top to bottom.
  - **App B** (p12–13): award procedure and advertising by value. Rows are labelled `A`, `B1`, `B2`, `C`, `D`; footnotes `*` to `****` are on p13.
  - **App C** (p14–15): exclusions from competition. Rows are `A`–`F`, then an unnumbered closing paragraph; call it `App C note`.
- Clause IDs: `6.16`, `App B row B1`, `App A row 3`, `App C note`, `App B footnote ***`.
- **"The Threshold"** is never given a figure. 1.4 and the App B `***` footnote say the values are on the Procurement intranet, and the two lists of threshold types differ. The only printed amounts are £500 (spend publishing), £1,000, £5,000, £24,999.99, £25,000, £500,000 and £2.5million.
- Placeholders are printed as `[]` (for example "Part []", "Parts [] (Call-In)").
- Use `-layout` text to see the clause numbering and table rows. Copy quotes from **plain** text, which reads table cells in order; `-layout` interleaves neighbouring columns.

## Steps

1. **Preflight.** Check that `data/contract-rules.pdf` exists and that `pdftotext`/`pdfinfo` run. If either fails, stop and report it; never work from memory of the document.
2. **Extract.** `T=$(mktemp -d)`, then `pdftotext data/contract-rules.pdf $T/plain.txt` and `pdftotext -layout data/contract-rules.pdf $T/layout.txt`. Read both, every page.
3. **Inventory.** `.venv/bin/python .claude/skills/extract-rules/verify_quotes.py --inventory` lists every numbered clause and labelled appendix row with its page. Add the items it cannot detect: the four App A bands, `App C note`, and the App B footnotes. This list is your checklist.
4. **Classify** each checklist item, using the definitions under Reference below:
   - **Rule:** it sets a threshold, a required action, or an approver that an auditor could test against evidence. Give one rule per distinct obligation. An App B row normally yields two rules: the award procedure (`procedure`) and the advertising requirement (`publication`). App A row 2 yields an approver rule plus a written-report rule.
   - **Excluded:** definition, purpose, background, cross-reference, list lead-in, interpretation power, or a clause too vague to test. The reason is one line, under 200 characters. Excluding a parent clause (for example `6.1`) covers its children only when the same reason fits all of them.
   - **Note:** anything contradictory, gapped, garbled, mis-numbered or left as a placeholder. Record it as you read; see Notes below.
5. **Write** `outputs/rules.json` in the schema below. Order rules by document position and number them `CPR-01`, `CPR-02`, … with no gaps. Get `source.sha256` from `shasum -a 256 data/contract-rules.pdf`.
6. **Verify.** Run `.venv/bin/python .claude/skills/extract-rules/verify_quotes.py`. Fix every error it reports by going back to the page, then rerun. **Done when it prints `PASS`.** If an error seems to be the verifier's fault, report it and keep the rule as the page says; never edit the verifier to get a pass.
7. **Report** in at most 12 lines:
   - the counts of rules, exclusions and notes
   - the declared parameters, all null, which the auditor must source from the intranet
   - the notes of kind `contradiction` and `gap`, one line each
   - the verifier's PASS line

## Reference

### Schema of `outputs/rules.json`

```json
{
  "source": {"file": "data/contract-rules.pdf", "sha256": "<hex>", "pages": 15},
  "parameters": {
    "THRESHOLD_GOODS_SERVICES": {"value": null, "clause": "1.4", "page": 1,
      "printed_as": "Threshold", "description": "Goods & Services threshold; figure on the Procurement intranet"},
    "THRESHOLD_RELEVANT": {"value": null, "clause": "1.4", "page": 1, "printed_as": "Threshold",
      "description": "'the relevant Threshold': depends on contract type",
      "resolves_by_scope": {"goods": "THRESHOLD_GOODS_SERVICES", "services": "THRESHOLD_GOODS_SERVICES", "works": "THRESHOLD_WORKS"}}
  },
  "rules": [{
    "rule_id": "CPR-01", "clause": "App B row B1", "page": 12,
    "type": "procedure", "scope": ["goods", "services"],
    "condition": "goods/services contract valued from £25,000 up to the Threshold",
    "threshold_text": "£25,000 or more and less than the Threshold",
    "threshold_low": 25000, "threshold_low_inclusive": true, "threshold_low_param": null,
    "threshold_high": null, "threshold_high_inclusive": false, "threshold_high_param": "THRESHOLD_GOODS_SERVICES",
    "required_action": "invite quotes via the Procurement Portal from at least three sources",
    "approver": null,
    "evidence_source": ["council_records"], "evidence_detail": "Procurement Portal RFQ record",
    "verbatim_quote": "Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources"
  }],
  "excluded": [{"clause": "1.2", "page": 1, "reason": "States what the Rules are; no action or threshold"}],
  "notes": [{"id": "N-01", "kind": "gap", "clause": "4.3 / App A rows 2-3", "page": 11,
    "text": "A contract of exactly £500,000 falls in neither band.", "rule_ids": ["CPR-.."], "quote": "optional"}]
}
```

- `type`: `procedure` (process required at a value band), `approval` (who must authorise), `anti-avoidance` (no splitting or disaggregation; 6.16 at least), `documentation` (a record or report must exist), `contract-content` (what the contract must contain), `publication` (advertise or publish).
- `scope`: `["all"]`, or any of `goods`, `services`, `works`, `concessions`, `light_touch`, as the clause states them.
- `evidence_source`: one or more of:
  - `spend_data`: testable against the over-£500 spend workbooks
  - `contracts_finder`: testable against `contracts.csv`
  - `council_records`: needs a document request

  `evidence_detail` names the record.
- `approver`: the role as printed (for example "S.151 Officer"), or null.
- `verbatim_quote`: at least 20 characters, copied character for character and lying wholly on `page`. When a clause runs over a page break, quote the part on the page you cite.

### Thresholds as printed

- **Amounts.** Write whole pounds: `£2.5million` → `2500000`. The verifier requires each value to be an amount printed in `threshold_text`, and `threshold_text` to appear on the page.
- **Words to bounds:**

  | Printed | Bound | `_inclusive` |
  |---|---|---|
  | "above", "over", "more than", "exceeds", "in excess of" | low | false |
  | "or more", "at least" | low | true |
  | "less than", "below" | high | false |
  | "up to" | high | true (also add an `interpretation` note) |

- **Pence.** "more than £24,999.99" is the same band as "£25,000 or more" at penny resolution. Write `25000`, inclusive, and add an `interpretation` note naming the rule. A note is the only way the verifier accepts a value that isn't printed.
- **Named thresholds.** When the band is "the Threshold" or "the relevant Threshold", put the parameter name in `_param`, leave the value null, and still set `_inclusive`. Declare every parameter you use under `parameters`, with `value: null`. Name one parameter per threshold type the PDF lists. For "relevant"/"appropriate" Threshold across types, use `THRESHOLD_RELEVANT` with `resolves_by_scope`.
- **Never fill in a figure.** Parameter values stay null even when you know the current UK procurement thresholds. The figures come from the intranet, which is not in `data/`. The auditor supplies them later with a source.
- A bound the clause doesn't set is null, with `_inclusive` null too.

### Notes

Each note has `id` (`N-01` upward), `kind`, `clause`, `page`, a one-paragraph `text`, `rule_ids` (the affected rules, possibly `[]`) and an optional `quote`, which is verified like a rule quote. Kinds:

- `contradiction`: two clauses disagree (for example who may grant a waiver: 7.2.2 against 7.3).
- `gap`: a value or case no rule covers (for example a boundary amount that falls in neither of two adjacent bands, or a footnote marker defined but never used in the table).
- `placeholder`: `[]` text, or a figure deferred to the intranet.
- `drafting-error`: garbled or mis-numbered text (for example a heading printed as clause 6.23).
- `interpretation`: a reading you had to make (pence conversions, "up to", ambiguous scope).

Read with these in mind; the examples above are a starting point, not the full list.

## Files

- `verify_quotes.py`: the checker; `--inventory` lists the PDF's clauses. Exits 0 on pass, 1 on errors, 2 when the PDF, the rules file or poppler is missing.
- `tests/test_verify_quotes.py`: checks the verifier against a synthetic PDF with deliberate errors. Run it after changing the verifier.
