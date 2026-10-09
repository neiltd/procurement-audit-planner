# Planning memo: procurement audit, West Berkshire Council

Built 2026-10-09 by `.claude/skills/audit-program/build_pack.py` from `outputs/audit-plan.json`, on risk register revision 3. Every figure is filled from `outputs/analytics.json` or computed by the builder and listed in `outputs/pack-figures.json`. The analytics are risk indicators to investigate, not findings of wrongdoing by the council, a service or a supplier.

## Scope

The auditor's decisions in `outputs/auditor-comments.md` (register revision 3) put 9 risk(s) in scope and 0 out.

| Risk | Title | L | I | Score | Band | Decision | Controls | Tests | Sample size per test |
|---|---|---|---|---|---|---|---|---|---|
| R-01 | Spend structured to stay just below the quote threshold | 4 | 3 | 12 | Medium - High (Amber) [matrix: High] | Approve | 2 | 3 | 15 |
| R-02 | Spend kept at or just below the one-quote level | 4 | 2 | 8 | Medium - High (Amber) [matrix: High] | Approve | 2 | 2 | 15 |
| R-03 | Payment groups crossing the Key Decision and Executive approval levels | 3 | 4 | 12 | Medium - High (Amber) [matrix: High] | Approve | 1 | 2 | 15 |
| R-04 | Suppliers above the publication threshold with no live Contracts Finder notice | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | Change | 1 | 4 | 15 |
| R-05 | Payments to suppliers whose every matched notice ended before the spend window | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | Approve | 1 | 1 | 15 |
| R-06 | Annualised spend above the awarded contract value without a recorded variation | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | Approve | 1 | 1 | 15 |
| R-07 | Repeat payments of the same amount to the same supplier within a week | 3 | 5 | 15 | Extreme (Red) | Approve | 1 | 5 | 25 |
| R-08 | High-value care and education placements with no published contract notice | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | Approve | 1 | 1 | 15 |
| R-09 | Waivers and exceptions to the Rules not approved or recorded in advance | 2 | 3 | 6 | Moderate | Change | 1 | 2 | 8 |

General scope comment from the auditor: “[2026-10-09, Neil Doungsaeng] R-10 (grants) rejected as a separate risk because grants stay inside R-04; the Rules treat a grant as a contract, so they must not be excluded. Schools out of scope (challenge #8): this audit covers council purchasing; the school spend in the data is mainly council-funded placements already covered by R-08, and schools' own purchasing stays with their separate school audits.”

## Objective

Seek assurance that the council's purchasing follows the Contract Procedure Rules where the spend data shows risk indicators: quotes and notices from the quote threshold up [CPR-64] [CPR-65] [CPR-66], no splitting of requirements [CPR-13], Key Decision and Executive approval at the higher tiers [CPR-04] [CPR-62], approved extensions and variations [CPR-76] [CPR-77], a recorded provider choice for placements [CPR-79], waivers approved in advance [CPR-23] [CPR-24], and written evidence for every purchase [CPR-35].

## Scope

The nine risks the auditor approved or changed in register revision three, R-01 to R-09, at the scores the register gives them. Grants stay in scope: the auditor rejected a separate grants risk (R-10) because the Rules treat a grant as a contract, so grant recipients with no live notice are tested under R-04 and grant-tagged payments sit in every sample stratum outside the placement tag. R-04 covers suppliers with no live notice outside the care and education placement tag; placement suppliers are tested once, under R-08. Schools' own purchasing is out of scope: this audit covers council purchasing, the school spend in the data is mainly council-funded placements already covered by R-08, and schools' own purchasing stays with their separate school audits. The spend window runs from 2026-05-01 to 2026-07-31.

## Approach

The plan has 21 tests. All but two draw from the flagged lists the spend analysis wrote, pulling 4,013 transactions worth £64,388,556; the other two sample council records on site: the waiver and exception register, and the unredacted listing of redacted-supplier payments. Where a sampled unit is a supplier or a payment group, every payment in it is pulled, so the transaction count is far larger than the number of units. Each sample takes the stratum the risk's proposed focus names and puts the strongest indicators first: the largest payments, groups, repeat values or spend-to-award ratios. Sample size per test follows the risk score on the council's bands. For each item the auditor requests the record that would close the indicator: the quote record, the award notice, the approval, the invoice or the case note.

## Sources of the indicators

Threshold clustering flagged 368 payments; split-purchase analysis flagged 508 same-supplier groups across its tiers, each within 30 days; 637 suppliers above the publication threshold had no live notice matched by name; 256 supplier and amount pairs recurred on different dates within 7 days; 7 suppliers were paid after every matched notice ended; and 7 suppliers showed an annualised estimate above the award's annual value.

## Limitations

The spend data covers one quarter, and every annualised figure is an estimate. Notices are matched to suppliers by normalised name, so 'no notice found' is a prompt to request contract evidence, not evidence that none exists; suppliers below the publication threshold are never questioned on notices. The intranet Threshold is not published in the data, so no sample is stratified by it; the tests that read a Threshold-tied tier (T-06, T-07, T-10, T-14, T-16, T-19, T-20) request the council's current Threshold figures and apply them on site. Care and education placements produce many recurring payments of the same amount, which explains a share of the split-purchase and repeat-payment flags. Payments published with the supplier name redacted (2,015 rows worth £2,746,747) were excluded from every analytics test, so they are outside every drawn sample; T-18 requests the unredacted listing to sample them on site. Two further exclusions sit outside every sample: pension and statutory payments (15 rows worth £9,245,179) and payments to public bodies, including joint arrangements and payments to other local authorities or the NHS (53 rows worth £2,312,688), some of which may be bought services. Of 10,607 rows read worth £80,427,254, 8,524 worth £66,122,640 were analysed. Placement repeats within one payment run were not sampled, as the register reads them as per-client payment runs; same-run repeats in general procurement and premises are tested in T-21. All flagged items are risk indicators to investigate, not findings about the council, a service or a supplier.

## Samples

Sample size per test follows the risk score: score 15+ → 25, score 8+ → 15, score 4+ → 8, score 1+ → 3. Samples are drawn by a fixed filter and sort, so a rebuild draws the same items.

| Test | Risk | Drawn from | Population | Sampled | Transactions | Net £ |
|---|---|---|---|---|---|---|
| T-01 | R-01 | `analytics-full/threshold_clustering.csv` | 14 | 14 | 14 | £332,670 |
| T-02 | R-01 | `analytics-full/threshold_clustering.csv` | 17 | 15 | 15 | £361,403 |
| T-03 | R-01 | `analytics-full/split_purchases.csv` | 71 | 15 | 37 | £538,180 |
| T-04 | R-02 | `analytics-full/threshold_clustering.csv` | 103 | 15 | 15 | £14,454 |
| T-05 | R-02 | `analytics-full/split_purchases.csv` | 113 | 15 | 30 | £24,882 |
| T-06 | R-03 | `analytics-full/split_purchases.csv` | 3 | 3 | 113 | £10,261,095 |
| T-16 | R-03 | `analytics-full/split_purchases.csv` | 8 | 8 | 642 | £5,902,976 |
| T-07 | R-04 | `analytics-full/off_contract.csv` | 169 | 15 | 289 | £19,355,510 |
| T-19 | R-04 | `analytics-full/off_contract.csv` | 124 | 15 | 29 | £3,248,935 |
| T-20 | R-04 | `analytics-full/off_contract.csv` | 28 | 15 | 328 | £2,098,759 |
| T-08 | R-04 | `analytics-full/off_contract.csv` | 14 | 14 | 278 | £810,843 |
| T-09 | R-05 | `analytics-full/expired_notice_spend.csv` | 7 | 7 | 58 | £190,367 |
| T-10 | R-06 | `analytics-full/spend_vs_award.csv` | 7 | 7 | 30 | £633,768 |
| T-11 | R-07 | `analytics-full/duplicates.csv` | 24 | 24 | 57 | £541,802 |
| T-17 | R-07 | `analytics-full/duplicates.csv` | 28 | 25 | 94 | £117,456 |
| T-12 | R-07 | `analytics-full/duplicates.csv` | 204 | 25 | 111 | £1,047,037 |
| T-18 | R-07 | the council's unredacted listing of payments published as 'Redacted' in the spend window (on site) | n/a | 25 | n/a | n/a |
| T-21 | R-07 | `analytics-full/duplicates.csv` | 41 | 25 | 58 | £115,647 |
| T-13 | R-08 | `analytics-full/off_contract.csv` | 316 | 15 | 1,635 | £11,216,255 |
| T-14 | R-09 | the council's waiver and exception register covering the spend window (on site) | n/a | 8 | n/a | n/a |
| T-15 | R-09 | `analytics-full/off_contract.csv` | 321 | 8 | 180 | £7,576,518 |
