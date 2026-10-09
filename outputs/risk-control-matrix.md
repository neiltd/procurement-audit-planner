# Risk and control matrix

Built 2026-10-09 by `.claude/skills/audit-program/build_pack.py` from `outputs/audit-plan.json`, on risk register revision 3. Every figure is filled from `outputs/analytics.json` or computed by the builder and listed in `outputs/pack-figures.json`. The analytics are risk indicators to investigate, not findings of wrongdoing by the council, a service or a supplier.

| Risk | Score | Expected control | Rules | Tests |
|---|---|---|---|---|
| R-01 Spend structured to stay just below the quote threshold | 12, Medium - High (Amber) [matrix: High] | C-01: Purchases from the quote threshold up are let on at least three quotes invited via the Procurement Portal, including an SME or VCSE and a local supplier, and the procedure is documented [CPR-65] [CPR-67] [CPR-34]. | CPR-34, CPR-65, CPR-67 | T-01, T-02 |
| R-01 Spend structured to stay just below the quote threshold | 12, Medium - High (Amber) [matrix: High] | C-02: A requirement is valued as a whole and not split or disaggregated to stay below a threshold, and officers seek advice on repeat or similar purchases [CPR-13] [CPR-14]. | CPR-13, CPR-14 | T-03 |
| R-02 Spend kept at or just below the one-quote level | 8, Medium - High (Amber) [matrix: High] | C-03: Purchases above the one-quote level have at least one quote from an appropriate source, and every purchase has written evidence [CPR-64] [CPR-35]. | CPR-35, CPR-64 | T-04 |
| R-02 Spend kept at or just below the one-quote level | 8, Medium - High (Amber) [matrix: High] | C-04: Low-value requirements are not split across payments to stay below the one-quote level [CPR-13] [CPR-64]. | CPR-13, CPR-64 | T-05 |
| R-03 Payment groups crossing the Key Decision and Executive approval levels | 12, Medium - High (Amber) [matrix: High] | C-05: Contract awards above the Key Decision level are taken as Key Decisions on a board-approved report, and awards from the Executive level go to the Executive [CPR-04] [CPR-60] [CPR-61] [CPR-62]. | CPR-04, CPR-60, CPR-61, CPR-62 | T-06, T-16 |
| R-04 Suppliers above the publication threshold with no live Contracts Finder notice | 9, Medium - High (Amber) [matrix: High] | C-06: Contracts from the publication threshold up are let on Portal quotes, have a contract notice published on the CDP, are in writing, and are notified for the contracts register [CPR-65] [CPR-66] [CPR-68] [CPR-36] [CPR-07] [CPR-38]. | CPR-07, CPR-36, CPR-38, CPR-65, CPR-66, CPR-68 | T-07, T-19, T-20, T-08 |
| R-05 Payments to suppliers whose every matched notice ended before the spend window | 9, Medium - High (Amber) [matrix: High] | C-07: Payments continue after a contract's end only under an extension the contract provides for, approved by the S151 Officer, or under a new award notified for the contracts register [CPR-76] [CPR-38]. | CPR-38, CPR-76 | T-09 |
| R-06 Annualised spend above the awarded contract value without a recorded variation | 9, Medium - High (Amber) [matrix: High] | C-08: A variation of a contract's scope or value has prior written approval from the Monitoring Officer and S151 Officer, or the relevant board above the Threshold [CPR-77] [CPR-78]. | CPR-77, CPR-78 | T-10 |
| R-07 Repeat payments of the same amount to the same supplier within a week | 15, Extreme (Red) | C-09: Every payment rests on written evidence of a distinct purchase: its own invoice and order, so the same charge is not paid twice [CPR-35]. | CPR-35 | T-11, T-17, T-12, T-18, T-21 |
| R-08 High-value care and education placements with no published contract notice | 9, Medium - High (Amber) [matrix: High] | C-10: Each individual placement excluded from competition has the reasons for the choice of provider recorded on the case notes, and Provider Selection Regime decisions are recorded [CPR-79] [CPR-74]. | CPR-74, CPR-79 | T-13 |
| R-09 Waivers and exceptions to the Rules not approved or recorded in advance | 6, Moderate | C-11: Waivers and exceptions are sought only in advance, granted by the Monitoring Officer or S151 Officer on recorded urgency or discretion grounds, fully documented, and reported to the relevant board or the Executive where required [CPR-21] [CPR-22] [CPR-23] [CPR-24] [CPR-27] [CPR-28] [CPR-29] [CPR-30]. | CPR-21, CPR-22, CPR-23, CPR-24, CPR-27, CPR-28, CPR-29, CPR-30 | T-14, T-15 |

## Rule coverage

80 rules in `outputs/rules.json`, 80 accounted for. Cited by an approved risk: 24; by a control: 29; by a test step: 42 (a rule can be cited in more than one place). Not tested, with a reason: 38.

### Rules not tested

| Rule | Clause | Reason |
|---|---|---|
| CPR-01 | 3.5 | Applies above the Goods and Services Threshold, which is on the intranet and not published in data/. |
| CPR-02 | 4.1 | Decision basis for every contract; council records outside this audit's sampled indicators, and the approval tiers it rests on are tested through CPR-04, CPR-60 and CPR-62. |
| CPR-03 | 4.2 | Budget cover is a budgetary-control matter outside this procurement audit's scope. |
| CPR-05 | 5.1.1 | The published spend over the publication level is the data this audit analyses; its completeness is not tested. |
| CPR-06 | 5.2 | Publication of invitations to tender sits in tender records outside the spend data; no indicator points at it. |
| CPR-08 | 5.3 | Monthly reporting of contract information to boards is council governance outside this audit's scope. |
| CPR-09 | 6.4 | Supplier suitability checks sit in tender evaluation records outside this audit's scope. |
| CPR-10 | 6.8 | Advertising on the Procurement Portal sits in tender records; no spend indicator points at it beyond the CDP notice tested under CPR-66. |
| CPR-11 | 6.10 | Applies above the Procurement Legislation thresholds, which tie to the unpublished intranet Threshold. |
| CPR-12 | 6.14 | Internal sign-off of CDP notices sits in procurement team records outside this audit's scope. |
| CPR-15 | 6.19 | Applies above the intranet Threshold, which is not published in data/. |
| CPR-16 | 6.20 | Electronic tender handling sits in Portal records outside this audit's scope. |
| CPR-17 | 6.21 | Late tender handling sits in Portal records outside this audit's scope. |
| CPR-18 | 6.22 | Tender opening records sit in the Portal outside this audit's scope. |
| CPR-19 | 6.24 | Evaluation criteria sit in tender records outside this audit's scope. |
| CPR-20 | 6.26 | Award basis sits in tender evaluation records outside this audit's scope. |
| CPR-32 | 9.1 | Applies above the intranet Threshold, which is not published in data/. |
| CPR-33 | 9.2 | Retention of procurement reports under CPR-32, which is not tested. |
| CPR-37 | 10.3 | Custody of sealed contracts by Legal Services is outside this audit's scope. |
| CPR-39 | 10.5 | Contract content (standard clauses) is outside this audit's scope. |
| CPR-40 | 10.6 | Approval of amended standard forms is a Legal Services record outside this audit's scope. |
| CPR-41 | 10.7 | Contract content (minimum clauses) is outside this audit's scope. |
| CPR-42 | 10.7.7 | Data protection impact assessments are outside this procurement audit's scope. |
| CPR-43 | 10.7.9 | Payment terms in contracts are outside this audit's scope. |
| CPR-44 | 10.7.10 | Contract specifications are outside this audit's scope. |
| CPR-45 | 11.1 | Indemnity relaxations are a Legal Services record outside this audit's scope. |
| CPR-46 | 11.2 | Performance bonds are contract-security records outside this audit's scope. |
| CPR-47 | 11.3 | Performance bonds are contract-security records outside this audit's scope. |
| CPR-48 | 11.4 | Bond risk assessments are contract-security records outside this audit's scope. |
| CPR-49 | 11.4.2 | Bond decisions are contract-security records outside this audit's scope. |
| CPR-50 | 11.5 | Contract risk and insurance assessment is outside this audit's scope. |
| CPR-51 | 11.5.2 | Insurance verification is outside this audit's scope. |
| CPR-52 | 11.8 | Sealing procedure is a Legal Services record outside this audit's scope. |
| CPR-53 | 11.9 | The sealing register is a Legal Services record outside this audit's scope. |
| CPR-54 | 11.11 | Applies above the intranet Threshold, which is not published in data/. |
| CPR-55 | 11.13 | Execution without seal is a Legal Services record outside this audit's scope. |
| CPR-56 | 11.14 | Instruction of Counsel is outside this procurement audit's scope. |
| CPR-63 | App A row 4 | Quarterly reporting to the Executive is council governance; the award approvals at that tier are tested under CPR-62. |
