# Risk register: procurement audit planning (revision 3)

Built 2026-10-09 by `.claude/skills/risk-assessment/build_register.py` from `outputs/risk-ratings.json`. Every figure is filled from `outputs/analytics.json`; every citation resolves to rules.json, analytics.json or history.json. These are risk indicators to investigate, not findings of wrongdoing.

## Revision 3

- Responds to the decisions in `outputs/auditor-comments.md`.
- GENERAL approved.
- R-01 approved.
- R-02 approved.
- R-03 approved.
- R-05 approved.
- R-06 approved.
- R-07 approved.
- R-08 approved.
- R-04: description changed, likelihood changed, impact changed, proposed_focus changed, as asked ("[2026-10-09, Neil Doungsaeng] Keep all suppliers with no live notice in R-04 except care and education placements, which R-08 already covers. Grants, premises and agency staff stay in R-04 so they are still tested."). Narrowed to no-live-notice suppliers outside the care_education_placement tag (R-08 covers placements); grants, premises and agency staff stay in and are cited by tag. Scores unchanged: L3 and C3 rows do not move.
- R-09: likelihood 3 → 2, as asked ("[2026-10-09, Neil Doungsaeng] Likelihood 2, keep in scope. The spend data cannot show a waiver, so there is no evidence it is likely; high stakes affect impact, not likelihood."). Likelihood 3 to 2 as the auditor asked; justification cites the L2 row (council records only, last audit Reasonable).

## Scoring method

The council's own method, from `data/committee/risk-management-strategy-2024-27.pdf` (history.json `scoring_method`). Likelihood: 1 Rare, 2 Unlikely, 3 Likely, 4 Almost Certain, 5 Certain. Impact: 1 Negligible, 2 Minor, 3 Medium, 4 Major, 5 Critical. Score = likelihood × impact.

| Band | RAG | Scores | Escalation | Response |
|---|---|---|---|---|
| Extreme | Red | 15 -25 | Add to Corporate Risk Register and mitigation action. | Allocate to Executive Director to oversee and Service Director implement agreed actions. |
| Medium - High | Amber | 8-12 | Seek assurance that identified controls are effective | Allocate to Service Director to put in place Controls Assurance. |
| Moderate | not printed | 4-6 | None | Monitor risk |
| Low | Green | Up to 3 | None | Consider at next annual review |

Likelihood is rated with the rubric in the risk-assessment skill: 3 needs a test signal, 4 needs signals from two tests, and 5 only comes from a repeat finding (an adverse audit opinion on the same theme raises likelihood by one point, stated on the risk).

### Conflicts in the method

Where the council's papers disagree with themselves, the register uses one side and marks the other.

- Likelihood and impact labels and scores come from the scale tables (p14, p15); a label printed elsewhere with a different score is not used.
- The band comes from the score ranges in the band table (p19), which also carry escalation and response. The matrix (p18) cell label is shown in brackets where it differs.
- Matrix cells scoring 8, 9, 10, 12 are labelled 'High', where the band table names that range 'Medium - High'. The register uses 'Medium - High' and marks the matrix label.
- Financial impact maps a £ exposure onto the £ amounts in the 'Financial loss to Council' column; an amount on a boundary takes the higher score. The column's % ranges are not used.
- D-01: uses Table 1: Medium impact scores 3; marks Paragraph 4.3: 'Medium (2)'. Labels and scores come from the scale table the impact is read against; paragraph 4.3 repeats the score of Minor and leaves no score of 3.
- D-02: uses The £ amounts in the Financial loss column of Table 1; marks The overlapping % of annual budget ranges. The £ amounts rise without overlap, so an exposure maps onto one score; the % ranges overlap between Medium and Major.
- D-03: uses Table 4 band names and score ranges: scores 8-12 are 'Medium - High' (Amber); marks Figure 1 matrix cell label 'High' for those cells, shown in brackets. Table 4 carries the escalation and response for each band, so the band is read from it.
- D-05: uses The current level: likelihood and impact with existing controls, as Table 4 'Current Score' and Appendix 2 'Current risk rating'; marks Section 4.1 calls the same level 'Actual'; gross and expected levels are not rated. The evidence (spend data and past audit opinions) shows the position with controls already in place, which is what both names describe.
- D-09: uses Table 4: only Extreme (15-25) is added to the Corporate Risk Register; marks Figure 4: score 9 or above goes to the Corporate Risk Register. Table 4 is the band table the score is read against and carries the escalation for each band. Risks scoring 9-14 are marked: “would go to the Corporate Risk Register under Figure 4 (score 9 or above)”.
- D-06: no effect on any rating. A version label of the external appetite guidance; no likelihood, impact or band in this register uses it.

## Summary

| Risk | Title | L | I | Score | Band | Status |
|---|---|---|---|---|---|---|
| R-01 | Spend structured to stay just below the quote threshold | 4 | 3 | 12 | Medium - High (Amber) [matrix: High] | approved |
| R-02 | Spend kept at or just below the one-quote level | 4 | 2 | 8 | Medium - High (Amber) [matrix: High] | approved |
| R-03 | Payment groups crossing the Key Decision and Executive approval levels | 3 | 4 | 12 | Medium - High (Amber) [matrix: High] | approved |
| R-04 | Suppliers above the publication threshold with no live Contracts Finder notice | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | changed as asked (rev 3) |
| R-05 | Payments to suppliers whose every matched notice ended before the spend window | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | approved |
| R-06 | Annualised spend above the awarded contract value without a recorded variation | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | approved |
| R-07 | Repeat payments of the same amount to the same supplier within a week | 3 | 5 | 15 | Extreme (Red) | approved |
| R-08 | High-value care and education placements with no published contract notice | 3 | 3 | 9 | Medium - High (Amber) [matrix: High] | approved |
| R-09 | Waivers and exceptions to the Rules not approved or recorded in advance | 2 | 3 | 6 | Moderate | changed as asked (rev 3) |

## Risks

### R-01 Spend structured to stay just below the quote threshold

45 payments worth £1,075,396 sit in the band just below the £25,000 quote threshold, and 254 groups of two or more payments to one supplier within 30 days each stay under that threshold while their total reaches it. Both patterns are indicators that a requirement may have been divided or valued to avoid three quotes via the Portal [CPR-65] and the rule against splitting [CPR-13]. Many groups are recurring care and education placement payments, which the auditor should expect to explain a share of the flags.

**Likelihood 4 Almost Certain.** L4: two different tests flag the same risk, payments clustered just below the quote threshold [`$.tests.threshold_clustering.by_tier.25000.rows`] and payment groups crossing it [`$.tests.split_purchases.by_tier.25000.groups`]; only part of the split groups share one payment run [`$.tests.split_purchases.by_tier.25000.same_timestamp_groups`], so analytics.json does not explain the rest away. The Reasonable Assurance opinion on Contract Letting argues the other way [A-01] but does not move the rubric row.

**Impact 3 Medium, on Compliance (litigation, regulatory, contract) (council scale: “Reasonable possibility of successful legal challenge. Reasonable possibility of regulatory interest.”).** C3: the flagged items sit in the tier from the quote threshold up to the intranet Threshold, where three quotes via the Procurement Portal are required [CPR-65] [CPR-67]; row C4 does not apply because the Threshold-tied tiers were not tested.

**Score 12, Medium - High (Amber) [matrix: High].** Escalation: Seek assurance that identified controls are effective. Response: Allocate to Service Director to put in place Controls Assurance.

† D-09: would go to the Corporate Risk Register under Figure 4 (score 9 or above)

**Evidence**

- CPR-65 (App B row B1, p12): “Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including at least one SME* or VCSE* organisation and one local supplier”
- CPR-13 (6.16, p5): “There shall be no artificial splitting or disaggregation of a contract to avoid the application of the provisions of the Procurement Legislation and/or these Rules.”
- CPR-14 (6.17, p5): “Officers responsible for such procurement should therefore seek advice on the application of the Procurement Legislation where they envisage that they may be required to make such …”
- `$.tests.threshold_clustering.by_tier.25000.rows` = 45
- `$.tests.split_purchases.by_tier.25000.groups` = 254
- `$.tests.split_purchases.by_tier.25000.same_timestamp_groups` = 20
- A-01: Contract Letting (Finance, Property and Procurement), Reasonable Assurance, End of March 2025; data/committee/audit-completed-work-2024-25-annual.pdf p1
- CPR-67 (App B row B2, p12): “Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including at least one SME* or VCSE* organisation and one local supplier”

**Proposed focus.** Pull the clustered payments and the split groups in the general procurement and premises tags first; for each, request the quote record via the Portal [CPR-65] and ask whether the payments form one requirement under the anti-splitting rule [CPR-13] [CPR-14]. Treat recurring placement invoices as a lower-priority stratum.

### R-02 Spend kept at or just below the one-quote level

323 payments worth £307,192 sit just at or below £1,000, and 241 same-supplier payment groups each stay under that level while their total exceeds it. Above that level at least one quote is required [CPR-64]; the patterns are indicators to test against the anti-splitting rule [CPR-13].

**Likelihood 4 Almost Certain.** L4: two different tests flag the same risk, clustering just below the one-quote level [`$.tests.threshold_clustering.by_tier.1000.rows`] and same-supplier groups crossing it [`$.tests.split_purchases.by_tier.1000.groups`]; some groups share one payment run [`$.tests.split_purchases.by_tier.1000.same_timestamp_groups`], which leaves most unexplained. Contract Letting was rated Reasonable Assurance [A-01].

**Impact 2 Minor, on Compliance (litigation, regulatory, contract) (council scale: “Low possibility of legal challenge. Low possibility regulatory interest”).** C2: the flagged items sit below the quote threshold, in the band where one quote is sought [CPR-64].

**Score 8, Medium - High (Amber) [matrix: High].** Escalation: Seek assurance that identified controls are effective. Response: Allocate to Service Director to put in place Controls Assurance.

**Evidence**

- CPR-64 (App B row A, p12): “At least one quote must be sought from an appropriate source.”
- CPR-13 (6.16, p5): “There shall be no artificial splitting or disaggregation of a contract to avoid the application of the provisions of the Procurement Legislation and/or these Rules.”
- CPR-35 (10.1, p8): “There should be written evidence of all purchases (which shall include electronic evidence).”
- `$.tests.threshold_clustering.by_tier.1000.rows` = 323
- `$.tests.split_purchases.by_tier.1000.groups` = 241
- `$.tests.split_purchases.by_tier.1000.same_timestamp_groups` = 29
- A-01: Contract Letting (Finance, Property and Procurement), Reasonable Assurance, End of March 2025; data/committee/audit-completed-work-2024-25-annual.pdf p1

**Proposed focus.** Sample clustered payments and split groups outside the placement tags and request the single quote or written purchase evidence for each [CPR-64] [CPR-35].

### R-03 Payment groups crossing the Key Decision and Executive approval levels

10 same-supplier payment groups within 30 days total at least £500,000 while each payment stays below it, and 3 do the same at £2,500,000. Awards over the first level are Key Decisions [CPR-04] [CPR-60] and the second needs Executive approval [CPR-62]. These tiers are noisy: instalments under existing term contracts and recurring placement fees can produce the pattern, and the tier £ figures double-count groups that appear at more than one tier.

**Likelihood 3 Likely.** L3: one test flags groups at the higher tiers [`$.tests.split_purchases.by_tier.500000.groups`] [`$.tests.split_purchases.by_tier.2500000.groups`] and none of them share one payment run [`$.tests.split_purchases.by_tier.500000.same_timestamp_groups`], so analytics.json does not explain them away. Clustering below these levels flagged nothing [`$.tests.threshold_clustering.by_tier.500000.rows`], so row L4 does not apply. Contract Letting was rated Reasonable Assurance [A-01].

**Impact 4 Major, on Compliance (litigation, regulatory, contract) (council scale: “High possibility of legal challenge. High possibility of regulatory intervention.”).** C4: the flagged groups are at the Key Decision level and above, where the award must be a Key Decision [CPR-04] or go to the Executive [CPR-62].

**Score 12, Medium - High (Amber) [matrix: High].** Escalation: Seek assurance that identified controls are effective. Response: Allocate to Service Director to put in place Controls Assurance.

† D-09: would go to the Corporate Risk Register under Figure 4 (score 9 or above)

**Evidence**

- CPR-04 (4.3, p3): “Any contract award with a value over £500,000 is a Key Decision of the Council.”
- CPR-60 (App A row 3, p11): “The award of these contracts shall be a Key Decision delegated to the relevant Service Director in consultation with the relevant Portfolio Holder”
- CPR-62 (App A row 4, p11): “Contracts with a value in excess of £2.5million shall require Executive approval”
- `$.tests.split_purchases.by_tier.500000.groups` = 10
- `$.tests.split_purchases.by_tier.2500000.groups` = 3
- `$.tests.split_purchases.by_tier.500000.same_timestamp_groups` = 0
- `$.tests.threshold_clustering.by_tier.500000.rows` = 0
- A-01: Contract Letting (Finance, Property and Procurement), Reasonable Assurance, End of March 2025; data/committee/audit-completed-work-2024-25-annual.pdf p1

**Proposed focus.** For each higher-tier group, identify the contract the payments are made under and request the Key Decision or Executive approval record for the award [CPR-04] [CPR-60] [CPR-62]; close groups that trace to an approved term contract.

### R-04 Suppliers above the publication threshold with no live Contracts Finder notice

Outside care and education placements, which R-08 covers, suppliers whose annualised estimate reaches £25,000 and have no live notice matched by exact normalised name are: 169 in general procurement (£22,832,317 in the window), 124 grant recipients (£5,876,514), 27 premises suppliers (£957,959) and 1 agency staff supplier (£1,275,552); 16 suppliers across the full list have a near-miss candidate name listed separately. Grants stay in this risk: the auditor's scope decision keeps them here to be tested. Contracts at this level need a published notice [CPR-66] and quotes via the Portal [CPR-65]. The notice export starts in 2021 and matching is by name only, so 'no notice found' is a prompt to request contract evidence, not evidence that none exists.

**Likelihood 3 Likely.** L3: one test flags suppliers above the publication threshold with no live notice outside the placement tag, in general procurement [`$.tests.off_contract.counts.by_tag.general_procurement`], grants [`$.tests.off_contract.counts.by_tag.grant`], premises [`$.tests.off_contract.counts.by_tag.premises`] and agency staff [`$.tests.off_contract.counts.by_tag.agency_staff`]; analytics.json does not explain them away. Narrowing the population to these tags leaves the same single test, so the rubric row does not move. The Reasonable Assurance opinion on Contract Letting argues the other way [A-01].

**Impact 3 Medium, on Compliance (litigation, regulatory, contract) (council scale: “Reasonable possibility of successful legal challenge. Reasonable possibility of regulatory interest.”).** C3: the narrowed population still sits from the publication threshold up, the tier where a notice on the CDP and three Portal quotes are required [CPR-66] [CPR-65], across general procurement, grant, premises and agency staff suppliers [`$.tests.off_contract.gbp.by_tag.general_procurement`] [`$.tests.off_contract.gbp.by_tag.grant`]; row C4 would need the Threshold-tied rules, which were not tested, so the narrowing does not move the rubric row.

**Score 9, Medium - High (Amber) [matrix: High].** Escalation: Seek assurance that identified controls are effective. Response: Allocate to Service Director to put in place Controls Assurance.

† D-09: would go to the Corporate Risk Register under Figure 4 (score 9 or above)

**Evidence**

- CPR-66 (App B row B1, p12): “A contract notice must be published on the CDP”
- CPR-65 (App B row B1, p12): “Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including at least one SME* or VCSE* organisation and one local supplier”
- CPR-07 (5.2.1, p3): “A register of contracts, including those in progress and those awarded, with key information such as the contract value, duration and supplier.”
- `$.tests.off_contract.counts.by_tag.general_procurement` = 169
- `$.tests.off_contract.counts.by_tag.grant` = 124
- `$.tests.off_contract.counts.by_tag.premises` = 27
- `$.tests.off_contract.counts.by_tag.agency_staff` = 1
- A-01: Contract Letting (Finance, Property and Procurement), Reasonable Assurance, End of March 2025; data/committee/audit-completed-work-2024-25-annual.pdf p1
- `$.tests.off_contract.gbp.by_tag.general_procurement` = 22,832,316.83
- `$.tests.off_contract.gbp.by_tag.grant` = 5,876,513.55

**Proposed focus.** Test the no-live-notice suppliers outside the care and education placement tag: general procurement first, then grants, premises and agency staff, plus the near-miss candidates. For each, request the contract or grant agreement, its award notice [CPR-66] and its entry on the contracts register [CPR-07]. Leave placement suppliers to R-08. Do not question suppliers below the publication threshold.

### R-05 Payments to suppliers whose every matched notice ended before the spend window

7 suppliers, paid £190,367 in the window, match only notices that ended before the window started. An extension provided for in a contract needs S151 approval [CPR-76]; a newer contract with no notice may also explain the payments.

**Likelihood 3 Likely.** L3: one test flags suppliers paid after every matched notice ended [`$.tests.expired_notice_spend.counts.total`] [`$.tests.expired_notice_spend.gbp.total`], and analytics.json records no benign pattern for them. Contract Letting was rated Reasonable Assurance [A-01].

**Impact 3 Medium, on Compliance (litigation, regulatory, contract) (council scale: “Reasonable possibility of successful legal challenge. Reasonable possibility of regulatory interest.”).** C3: the matched notices are Contracts Finder awards, published from the quote threshold tier [CPR-66], and continuing to pay needs an approved extension [CPR-76]; no metric places the flagged items at the Key Decision level, so row C4 does not apply.

**Score 9, Medium - High (Amber) [matrix: High].** Escalation: Seek assurance that identified controls are effective. Response: Allocate to Service Director to put in place Controls Assurance.

† D-09: would go to the Corporate Risk Register under Figure 4 (score 9 or above)

**Evidence**

- CPR-76 (App C row D, p14): “The proposed contract is an extension to an existing contract where the existing contract provides for such extension.”
- CPR-38 (10.4, p8): “must formally notify the Service Lead for Commissioning and Procurement (or nominated officer) of the award of all contracts for the purpose of it being recorded on the Council Con…”
- `$.tests.expired_notice_spend.counts.total` = 7
- `$.tests.expired_notice_spend.gbp.total` = 190,366.92
- A-01: Contract Letting (Finance, Property and Procurement), Reasonable Assurance, End of March 2025; data/committee/audit-completed-work-2024-25-annual.pdf p1
- CPR-66 (App B row B1, p12): “A contract notice must be published on the CDP”

**Proposed focus.** For each flagged supplier, request the S151 extension approval [CPR-76] or the current contract and its award record [CPR-38].

### R-06 Annualised spend above the awarded contract value without a recorded variation

7 of 18 suppliers matched to one live single-supplier notice show an annualised estimate at least 1.25 times the award's annual value. A variation of scope or value needs prior approval [CPR-77] [CPR-78]. Award values may be estimates or maxima, and annualising a 3-month total can overstate a lumpy year.

**Likelihood 3 Likely.** L3: one test flags spend beyond the award's annual value [`$.tests.spend_vs_award.counts.total`] [`$.tests.spend_vs_award.gbp.total`], with no benign pattern recorded in analytics.json. Contract Letting was rated Reasonable Assurance [A-01].

**Impact 3 Medium, on Compliance (litigation, regulatory, contract) (council scale: “Reasonable possibility of successful legal challenge. Reasonable possibility of regulatory interest.”).** C3: the flagged contracts are published awards from the quote threshold tier upward [CPR-66], and a variation needs Monitoring Officer and S151 approval [CPR-77]; row C4 nearly applied because a variation above the Threshold goes to the relevant board [CPR-78], but no metric tiers the flagged awards.

**Score 9, Medium - High (Amber) [matrix: High].** Escalation: Seek assurance that identified controls are effective. Response: Allocate to Service Director to put in place Controls Assurance.

† D-09: would go to the Corporate Risk Register under Figure 4 (score 9 or above)

**Evidence**

- CPR-77 (App C row E, p14): “For contract value below the Threshold prior written approval from the Monitoring Officer and S151 Officer is required.”
- CPR-78 (App C row E, p14): “For contract value greater than the Threshold, approval of the relevant board, following the submission of an extension report to the relevant board”
- CPR-76 (App C row D, p14): “The proposed contract is an extension to an existing contract where the existing contract provides for such extension.”
- `$.tests.spend_vs_award.counts.total` = 7
- `$.tests.spend_vs_award.gbp.total` = 633,768.19
- A-01: Contract Letting (Finance, Property and Procurement), Reasonable Assurance, End of March 2025; data/committee/audit-completed-work-2024-25-annual.pdf p1
- CPR-66 (App B row B1, p12): “A contract notice must be published on the CDP”

**Proposed focus.** For each flagged supplier, compare actual spend to date with the award and request any variation approval [CPR-77] [CPR-78] or extension record [CPR-76].

### R-07 Repeat payments of the same amount to the same supplier within a week

256 supplier and amount pairs recur on different payment dates within 7 days, with a repeat value of £3,254,021; a further 527 pairs recur within one payment run (repeat value £3,722,012), mostly per-client placement invoices at a standard rate. No Contract Procedure Rule sets this test; it is a payment-control indicator tied to the written evidence each purchase needs [CPR-35]. The repeat value is an upper bound on money at stake, not a loss.

**Likelihood 3 Likely.** L3: one test flags repeat amounts on different payment dates [`$.tests.duplicates.different_dates.items`], which the one-payment-run pattern does not explain. The same-run repeats [`$.tests.duplicates.same_timestamp.items`] read as payment runs and alone would sit at row L2. Accounts Payable was rated Reasonable Assurance [A-15].

**Impact 5 Critical, on Financial loss to Council (council scale: “> 1% annual WBC budget >£2m”).** Financial: the repeat value of different-date pairs [`$.tests.duplicates.different_dates.gbp_repeat_value`] is the amount that could have been paid twice; it is an upper bound, since most pairs are placement fees for different clients [`$.tests.duplicates.different_dates.items_by_tag.care_education_placement`].

*Exposure* `$.tests.duplicates.different_dates.gbp_repeat_value` = £3,254,021, which maps to impact 5 on the £ amounts; it is the value passing through the flagged population, an upper bound, not a loss.

**Score 15, Extreme (Red).** Escalation: Add to Corporate Risk Register and mitigation action. Response: Allocate to Executive Director to oversee and Service Director implement agreed actions.

**Evidence**

- CPR-35 (10.1, p8): “There should be written evidence of all purchases (which shall include electronic evidence).”
- `$.tests.duplicates.different_dates.items` = 256
- `$.tests.duplicates.same_timestamp.items` = 527
- A-15: Accounts Payable (Finance, Property and Procurement), Reasonable Assurance, End of December 2025; data/committee/audit-completed-work-2025-26-q3.pdf p1
- `$.tests.duplicates.different_dates.gbp_repeat_value` = 3,254,020.77
- `$.tests.duplicates.different_dates.items_by_tag.care_education_placement` = 204

**Proposed focus.** Sample the different-date pairs, general procurement and premises first, and match each payment to a distinct invoice and purchase record [CPR-35]; for placement pairs, confirm each payment relates to a different client or period.

### R-08 High-value care and education placements with no published contract notice

316 care and education placement suppliers above the publication threshold have no live notice, worth £31,583,840 in the window. Individual placements can be excluded from competition, but the reasons for the choice of provider must be on the case notes [CPR-79] and Provider Selection Regime decisions recorded [CPR-74].

**Likelihood 3 Likely.** L3: one test flags placement suppliers above the publication threshold with no live notice [`$.tests.off_contract.counts.by_tag.care_education_placement`]; analytics.json does not explain them away. Purchase of Residential and Nursing Care Provision was rated Reasonable Assurance [A-18], which argues the other way.

**Impact 3 Medium, on Compliance (litigation, regulatory, contract) (council scale: “Reasonable possibility of successful legal challenge. Reasonable possibility of regulatory interest.”).** C3: the suppliers are at or above the publication threshold tier [CPR-66], and the exclusion depends on a recorded provider choice [CPR-79].

**Score 9, Medium - High (Amber) [matrix: High].** Escalation: Seek assurance that identified controls are effective. Response: Allocate to Service Director to put in place Controls Assurance.

† D-09: would go to the Corporate Risk Register under Figure 4 (score 9 or above)

**Evidence**

- CPR-79 (App C row F, p15): “Service Directors must ensure that a record of the reasons for the choice of provider is maintained on the individual's case notes.”
- CPR-74 (App C row B, p14): “Key decisions must be recorded and the relevant process under PSR followed”
- `$.tests.off_contract.counts.by_tag.care_education_placement` = 316
- A-18: Purchase of Residential and Nursing Care Provision (Adult Social Care), Reasonable Assurance, End of December 2025; data/committee/audit-completed-work-2025-26-q3.pdf p1
- CPR-66 (App B row B1, p12): “A contract notice must be published on the CDP”

**Proposed focus.** Sample placement suppliers from the list and request the case-note record of provider choice [CPR-79], or the PSR decision record [CPR-74], or the framework or block contract the placement sits under.

### R-09 Waivers and exceptions to the Rules not approved or recorded in advance

Competition can be waived above the quote threshold only on urgency or Executive Director discretion with written reasons [CPR-21] [CPR-22], approved by the Monitoring Officer or S151 Officer [CPR-23] and fully documented [CPR-28]. No spend test can see a waiver; the evidence sits in council records.

**Likelihood 2 Unlikely.** L2: the evidence is council records only, since no spend test can see a waiver [CPR-23] [CPR-28], and the last audit on the theme, Contract Letting, was Reasonable Assurance [A-01]. Set by the auditor (decision R-09): high stakes bear on impact, not likelihood.

**Impact 3 Medium, on Compliance (litigation, regulatory, contract) (council scale: “Reasonable possibility of successful legal challenge. Reasonable possibility of regulatory interest.”).** C3: the waiver rules apply from the quote threshold tier [CPR-22]; exceptions above the Key Decision level go to the Executive [CPR-27], which would be row C4, but no metric shows waivers at that level.

**Score 6, Moderate.** Escalation: None. Response: Monitor risk.

**Auditor override (revision 1):** likelihood 2 → 3. Auditor's comment: “[2026-10-08] likelihood 3: awards above £500,000 are rare but carry the highest stakes.”

**Auditor override (revision 3):** likelihood 3 → 2. Auditor's comment: “[2026-10-09, Neil Doungsaeng] Likelihood 2, keep in scope. The spend data cannot show a waiver, so there is no evidence it is likely; high stakes affect impact, not likelihood.”

**Evidence**

- CPR-21 (7.2.1, p6): “the work, supply or service is required as a matter of urgency and a delay would be likely to lead to financial loss, personal injury or damage to property”
- CPR-22 (7.2.2, p6): “at the discretion of the relevant Executive Director and/or the Chief Executive, acting lawfully, who may proceed in a manner most expedient for the efficient management of the Cou…”
- CPR-23 (7.3, p6): “Only the Monitoring Officer and/or the S.151 Officer may grant a waiver or an exception to these Rules”
- CPR-28 (7.5.1, p6): “All exceptions or waivers to these Rules must: 7.5.1 be fully documented;”
- CPR-24 (7.3, p6): “An officer who seeks a waiver of these Rules shall do so only in advance and only in exceptional circumstances.”
- CPR-30 (7.5.3, p7): “be subject to approval by the S.151 Officer who shall record they have considered the reasons for the waiver and that they are satisfied that the circumstances justifying the waive…”
- CPR-66 (App B row B1, p12): “A contract notice must be published on the CDP”
- A-01: Contract Letting (Finance, Property and Procurement), Reasonable Assurance, End of March 2025; data/committee/audit-completed-work-2024-25-annual.pdf p1
- CPR-27 (7.4.3, p6): “for contracts over £500,000 the S.151 Officer and the Monitoring Officer will make a recommendation to the Executive provided an exception report has been prepared and approved by …”

**Proposed focus.** Request the waiver and exception register and test a sample for advance approval and written reasons [CPR-24] [CPR-30]; cross-check against suppliers flagged in the off-contract list [CPR-66].

## Auditor decisions

Decisions are recorded in `outputs/auditor-comments.md`: Approve, Reject or Change (with a comment saying what to change). The risk-assessor applies them in a new revision, and this builder fails if a decision is left unapplied or anything changes that the auditor did not ask for.

| Risk | Decision | Comment | Status |
|---|---|---|---|
| R-01 | Approve | [2026-10-09, Neil Doungsaeng] | approved |
| R-02 | Approve | [2026-10-09, Neil Doungsaeng] Two separate tests flag it; score 8 already makes it the lowest priority, so sample fewer cases rather than lower the likelihood. | approved |
| R-03 | Approve | [2026-10-09, Neil Doungsaeng] | approved |
| R-04 | Change | [2026-10-09, Neil Doungsaeng] Keep all suppliers with no live notice in R-04 except care and education placements, which R-08 already covers. Grants, premises and agency staff stay in R-04 so they are still tested. | changed as asked (rev 3) |
| R-05 | Approve | [2026-10-09, Neil Doungsaeng] | approved |
| R-06 | Approve | [2026-10-09, Neil Doungsaeng] | approved |
| R-07 | Approve | [2026-10-09, Neil Doungsaeng] | approved |
| R-08 | Approve | [2026-10-09, Neil Doungsaeng] Keep likelihood 3 (challenge #5). Only one test supports it, the Reasonable Assurance opinion argues the other way, and placements have legitimate exceptions, so a missing notice is not "almost certain". | approved |
| R-09 | Change | [2026-10-09, Neil Doungsaeng] Likelihood 2, keep in scope. The spend data cannot show a waiver, so there is no evidence it is likely; high stakes affect impact, not likelihood. | changed as asked (rev 3) |
| GENERAL | Approve | [2026-10-09, Neil Doungsaeng] R-10 (grants) rejected as a separate risk because grants stay inside R-04; the Rules treat a grant as a contract, so they must not be excluded. Schools out of scope (challenge #8): this audit covers council purchasing; the school spend in the data is mainly council-funded placements already covered by R-08, and schools' own purchasing stays with their separate school audits. | noted |

Gate: ready: every rated risk has a decision, applied in revision 3.
