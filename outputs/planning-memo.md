# Planning memo: procurement audit, West Berkshire Council

Built 2026-10-08 by `.claude/skills/audit-program/build_pack.py` from `outputs/audit-plan.json`, on risk register revision 2. Every figure is filled from `outputs/analytics.json` or computed by the builder and listed in `outputs/pack-figures.json`. The analytics are risk indicators to investigate, not findings of wrongdoing by the council, a service or a supplier.

## Scope

The auditor's decisions in `outputs/auditor-comments.md` (register revision 2) put 9 risk(s) in scope and 0 out.

| Risk | Title | L | I | Score | Band | Decision | Controls | Tests | Sample size per test |
|---|---|---|---|---|---|---|---|---|---|
| R-01 | Spend structured to stay just below the quote threshold | 4 | 3 | 12 | Medium - High (Amber) [matrix: High] | Approve | 2 | 3 | 15 |
| R-02 | Spend kept at or just below the one-quote level | 4 | 2 | 8 | Medium - High (Amber) [matrix: High] | Approve | 2 | 2 | 15 |
| R-03 | Payment groups crossing the Key Decision and Executive approval levels | 3 | 4 | 12 | Medium - High (Amber) [matrix: High] | Approve | 1 | 2 | 15 |
| R-04 | Suppliers above the publication threshold with no live Contracts Finder notice | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | Approve | 1 | 2 | 15 |
| R-05 | Payments to suppliers whose every matched notice ended before the spend window | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | Approve | 1 | 1 | 15 |
| R-06 | Annualised spend above the awarded contract value without a recorded variation | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | Approve | 1 | 1 | 15 |
| R-07 | Repeat payments of the same amount to the same supplier within a week | 3 | 5 | 15 | Extreme (Red) | Approve | 1 | 4 | 25 |
| R-08 | High-value care and education placements with no published contract notice | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | Approve | 1 | 1 | 15 |
| R-09 | Waivers and exceptions to the Rules not approved or recorded in advance | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | Change | 1 | 2 | 15 |

General scope comment from the auditor: “[2026-10-08] R-10 (not in the register) rejected: grants will be covered by a separate review.”

## Objective

Seek assurance that the council's purchasing follows the Contract Procedure Rules where the spend data shows risk indicators: quotes and notices from the quote threshold up [CPR-64] [CPR-65] [CPR-66], no splitting of requirements [CPR-13], Key Decision and Executive approval at the higher tiers [CPR-04] [CPR-62], approved extensions and variations [CPR-76] [CPR-77], a recorded provider choice for placements [CPR-79], waivers approved in advance [CPR-23] [CPR-24], and written evidence for every purchase [CPR-35].

## Scope

The nine risks the auditor approved in register revision two, R-01 to R-09, at the scores the register gives them. R-10 (grants) is outside this audit: the auditor rejected it because grants will be covered by a separate review, so grant-tagged items are left out of every sample. The spend window runs from 2026-05-01 to 2026-07-31.

## Approach

The plan has 18 tests. All but one draw from the flagged lists the spend analysis wrote, pulling 3,659 transactions worth £61,889,211; the other samples the waiver and exception register on site. Where a sampled unit is a supplier or a payment group, every payment in it is pulled, so the transaction count is far larger than the number of units. Each sample takes the stratum the risk's proposed focus names and puts the strongest indicators first: the largest payments, groups, repeat values or spend-to-award ratios. Sample size per test follows the risk score on the council's bands. For each item the auditor requests the record that would close the indicator: the quote record, the award notice, the approval, the invoice or the case note.

## Sources of the indicators

Threshold clustering flagged 368 payments; split-purchase analysis flagged 508 same-supplier groups across its tiers, each within 30 days; 637 suppliers above the publication threshold had no live notice matched by name; 256 supplier and amount pairs recurred on different dates within 7 days; 7 suppliers were paid after every matched notice ended; and 7 suppliers showed an annualised estimate above the award's annual value.

## Limitations

The spend data covers one quarter, and every annualised figure is an estimate. Notices are matched to suppliers by normalised name, so 'no notice found' is a prompt to request contract evidence, not evidence that none exists; suppliers below the publication threshold are never questioned on notices. The intranet Threshold is not published in the data, so rules tied to it are not tested, except where T-06 and T-16 request the council's current Threshold figures to read the tender rules that apply above the Key Decision level. Care and education placements produce many recurring payments of the same amount, which explains a share of the split-purchase and repeat-payment flags. Payments published with the supplier name redacted (2,015 rows worth £2,746,747) were excluded from every analytics test, so they are outside every drawn sample; T-18 requests the unredacted listing to sample them on site. Repeat payments within one payment run were not sampled, as the register reads them as payment runs. All flagged items are risk indicators to investigate, not findings about the council, a service or a supplier.

## Samples

Sample size per test follows the risk score: score 15+ → 25, score 8+ → 15, score 4+ → 8, score 1+ → 3. Samples are drawn by a fixed filter and sort, so a rebuild draws the same items.

| Test | Risk | Drawn from | Population | Sampled | Transactions | Net £ |
|---|---|---|---|---|---|---|
| T-01 | R-01 | `analytics-full/threshold_clustering.csv` | 9 | 9 | 9 | £214,195 |
| T-02 | R-01 | `analytics-full/threshold_clustering.csv` | 31 | 15 | 15 | £365,591 |
| T-03 | R-01 | `analytics-full/split_purchases.csv` | 65 | 15 | 42 | £625,034 |
| T-04 | R-02 | `analytics-full/threshold_clustering.csv` | 91 | 15 | 15 | £14,380 |
| T-05 | R-02 | `analytics-full/split_purchases.csv` | 111 | 15 | 30 | £24,634 |
| T-06 | R-03 | `analytics-full/split_purchases.csv` | 3 | 3 | 113 | £10,261,095 |
| T-16 | R-03 | `analytics-full/split_purchases.csv` | 8 | 8 | 642 | £5,902,976 |
| T-07 | R-04 | `analytics-full/off_contract.csv` | 197 | 15 | 303 | £20,564,580 |
| T-08 | R-04 | `analytics-full/off_contract.csv` | 16 | 15 | 281 | £884,360 |
| T-09 | R-05 | `analytics-full/expired_notice_spend.csv` | 7 | 7 | 58 | £190,367 |
| T-10 | R-06 | `analytics-full/spend_vs_award.csv` | 7 | 7 | 30 | £633,768 |
| T-11 | R-07 | `analytics-full/duplicates.csv` | 23 | 23 | 55 | £540,202 |
| T-17 | R-07 | `analytics-full/duplicates.csv` | 28 | 25 | 94 | £117,456 |
| T-12 | R-07 | `analytics-full/duplicates.csv` | 204 | 25 | 137 | £2,544,445 |
| T-18 | R-07 | the council's unredacted listing of payments published as 'Redacted' in the spend window (on site) | n/a | 25 | n/a | n/a |
| T-13 | R-08 | `analytics-full/off_contract.csv` | 316 | 15 | 1,635 | £11,216,255 |
| T-14 | R-09 | the council's waiver and exception register covering the spend window (on site) | n/a | 15 | n/a | n/a |
| T-15 | R-09 | `analytics-full/off_contract.csv` | 197 | 15 | 200 | £7,789,872 |
