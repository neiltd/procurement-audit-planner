# Audit program

Built 2026-10-08 by `.claude/skills/audit-program/build_pack.py` from `outputs/audit-plan.json`, on risk register revision 2. Every figure is filled from `outputs/analytics.json` or computed by the builder and listed in `outputs/pack-figures.json`. The analytics are risk indicators to investigate, not findings of wrongdoing by the council, a service or a supplier.

Each test pulls the transactions in `outputs/samples/<test>.csv`. A flagged item is a prompt to request evidence; a complete record closes it.

## R-01 Spend structured to stay just below the quote threshold

Score 12 (likelihood 4 × impact 3), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-01 Expected control

Purchases from the quote threshold up are let on at least three quotes invited via the Procurement Portal, including an SME or VCSE and a local supplier, and the procedure is documented [CPR-65] [CPR-67] [CPR-34].

#### T-01

**Test step.** For each sampled payment just below the quote threshold, identify the requirement it pays for and its total value; obtain the Portal quote record and confirm three quotes were invited before the order where the requirement reaches the threshold [CPR-65] [CPR-67], and that the procedure record is kept [CPR-34]. Clustered payments: [`$.tests.threshold_clustering.by_tier.25000.rows`].

**Sample.** 9 of 9 rows in `analytics-full/threshold_clustering.csv` where tier = 25000; tag in general_procurement, premises, agency_staff, sorted by amount descending, taking units from the top of the list. 9 transactions, £214,195 net, in `outputs/samples/T-01.csv`.
Why this sample: General procurement and premises first, as the proposed focus asks; largest payments, closest to the threshold, first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | TRIPLE VALUE IMPACT | 1 | £24,244 |
| 2 | DEVCOMMS SOUTH EAST | 1 | £24,227 |
| 3 | THE BETTER GROUP | 1 | £24,089 |
| 4 | BOOKINGLAB | 1 | £24,000 |
| 5 | ELIOR UK | 1 | £23,694 |
| 6 | READING WEST APARTHOTEL | 1 | £23,660 |
| 7 | VOLKERHIGHWAYS | 1 | £23,591 |
| 8 | ELIOR UK | 1 | £23,517 |
| 9 | ELIOR UK | 1 | £23,173 |

**PBC.** P-01, P-02

#### T-02

**Test step.** Lower-priority stratum: for each sampled placement payment just below the quote threshold, confirm whether the placement sits under a framework, block contract or recorded provider choice [CPR-79]; where none applies, obtain the Portal quote record [CPR-65].

**Sample.** 15 of 31 rows in `analytics-full/threshold_clustering.csv` where tier = 25000; tag = care_education_placement, sorted by amount descending, taking units from the top of the list. 15 transactions, £365,591 net, in `outputs/samples/T-02.csv`.
Why this sample: Recurring placement invoices are the lower-priority stratum the proposed focus names; largest first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | AFFINITY TRUST SUPPORT | 1 | £24,926 |
| 2 | SUKHBIR SINGH AND HARVINDER SINGH T A CALCOT SERVICES FOR CHILDREN CSFC | 1 | £24,789 |
| 3 | FOCUS SUPPORT | 1 | £24,719 |
| 4 | SUKHBIR SINGH AND HARVINDER SINGH T A CALCOT SERVICES FOR CHILDREN CSFC | 1 | £24,619 |
| 5 | UNITY RESIDENTIAL CARE SERVICES | 1 | £24,587 |
| 6 | ACORN CARE EDUCATION | 1 | £24,579 |
| 7 | THE BETTER GROUP | 1 | £24,476 |
| 8 | HUCKLEBERRY HOUSE | 1 | £24,453 |
| 9 | UTOPIA SUPPORTED HOUSING | 1 | £24,384 |
| 10 | ACORN CARE EDUCATION | 1 | £24,111 |
| 11 | CARE SERVICES TO YOU | 1 | £23,990 |
| 12 | CARE SERVICES TO YOU | 1 | £23,990 |
| 13 | CARE SERVICES TO YOU | 1 | £23,990 |
| 14 | CARE SERVICES TO YOU | 1 | £23,990 |
| 15 | CARE SERVICES TO YOU | 1 | £23,990 |

**PBC.** P-03, P-01

### C-02 Expected control

A requirement is valued as a whole and not split or disaggregated to stay below a threshold, and officers seek advice on repeat or similar purchases [CPR-13] [CPR-14].

#### T-03

**Test step.** For each sampled payment group whose total reaches the quote threshold while each payment stays under it, establish from the orders and invoices whether the payments form one requirement; if so, obtain the quote record for the combined value [CPR-65] and any advice sought on aggregation [CPR-14], and record whether the split is explained [CPR-13]. Groups at this tier: [`$.tests.split_purchases.by_tier.25000.groups`].

**Sample.** 15 of 65 rows in `analytics-full/split_purchases.csv` where tier = 25000; tag in general_procurement, premises, agency_staff; same_timestamp = False, sorted by payments ascending, max_payment descending, span_days ascending, taking units from the top of the list. 42 transactions, £625,034 net, in `outputs/samples/T-03.csv`.
Why this sample: General procurement and premises groups not explained by one payment run; groups of few payments, each closest to the threshold, in the tightest span first, where the splitting indicator is strongest.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | DEVCOMMS SOUTH EAST | 2 | £38,785 |
| 2 | READING WEST APARTHOTEL | 2 | £44,616 |
| 3 | RACKLINE | 2 | £25,510 |
| 4 | PRUDENTIAL | 2 | £35,156 |
| 5 | PRUDENTIAL | 2 | £33,817 |
| 6 | ELIOR UK | 3 | £53,393 |
| 7 | INSIGHT DIRECT UK | 3 | £37,014 |
| 8 | HOME FRONT | 3 | £50,197 |
| 9 | A E BUILDERS BASINGSTOKE | 3 | £33,497 |
| 10 | SOLUTIONS4HEALTH | 3 | £36,944 |
| 11 | CONVERGENT TECHNOLOGY | 3 | £27,161 |
| 12 | TRADING STANDARDS SOUTH EAST | 3 | £27,510 |
| 13 | COMMERCIAL SERVICES KENT | 3 | £26,549 |
| 14 | THE BETTER GROUP | 4 | £77,145 |
| 15 | ELIOR UK | 4 | £77,739 |

**PBC.** P-02, P-04, P-05

## R-02 Spend kept at or just below the one-quote level

Score 8 (likelihood 4 × impact 2), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-03 Expected control

Purchases above the one-quote level have at least one quote from an appropriate source, and every purchase has written evidence [CPR-64] [CPR-35].

#### T-04

**Test step.** For each sampled payment just at or below the one-quote level, obtain the order, invoice and the quote or written purchase evidence, and confirm the requirement's total value and whether a quote was sought [CPR-64] [CPR-35]. Clustered payments: [`$.tests.threshold_clustering.by_tier.1000.rows`].

**Sample.** 15 of 91 rows in `analytics-full/threshold_clustering.csv` where tier = 1000; tag in general_procurement, premises, agency_staff, sorted by amount descending, taking units at even intervals through the list. 15 transactions, £14,380 net, in `outputs/samples/T-04.csv`.
Why this sample: Outside the placement and grant tags, as the proposed focus asks; even steps through the stratum for coverage, since every payment sits in a narrow band.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | ALAN FULLER | 1 | £1,000 |
| 2 | ROADSIDE TECHNOLOGIES | 1 | £1,000 |
| 3 | BECKY TURNER | 1 | £1,000 |
| 4 | PRESTIGE NETWORK | 1 | £993 |
| 5 | KB REAL ESTATE MANAGEMENT | 1 | £990 |
| 6 | 360 SECURITY SUPPORT SERVICES | 1 | £981 |
| 7 | BERKSHIRE MECHANICAL SERVICES | 1 | £975 |
| 8 | PREMIER CARS | 1 | £968 |
| 9 | INSIGHT DIRECT UK | 1 | £958 |
| 10 | WSP UK | 1 | £942 |
| 11 | GLEN CLEANING COMPANY | 1 | £931 |
| 12 | BRITS AIRPORT CARS | 1 | £920 |
| 13 | EXPERT ACCESS SOLUTIONS | 1 | £914 |
| 14 | EVM DIRECT | 1 | £905 |
| 15 | GLEN CLEANING COMPANY | 1 | £902 |

**PBC.** P-02, P-06

### C-04 Expected control

Low-value requirements are not split across payments to stay below the one-quote level [CPR-13] [CPR-64].

#### T-05

**Test step.** For each sampled payment group whose total exceeds the one-quote level while each payment stays under it, establish whether the payments form one requirement and, if so, obtain the quote or written evidence for the combined value [CPR-64] [CPR-35] [CPR-13]. Groups at this tier: [`$.tests.split_purchases.by_tier.1000.groups`].

**Sample.** 15 of 111 rows in `analytics-full/split_purchases.csv` where tier = 1000; tag in general_procurement, premises, agency_staff; same_timestamp = False, sorted by payments ascending, max_payment descending, span_days ascending, taking units from the top of the list. 30 transactions, £24,634 net, in `outputs/samples/T-05.csv`.
Why this sample: Outside the placement and grant tags and not explained by one payment run; groups of few payments, each closest to the one-quote level, in the tightest span first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | BECKY TURNER | 2 | £1,750 |
| 2 | MECE FIRE SECURITY | 2 | £1,601 |
| 3 | POTTINGER S HIRE SERVICE | 2 | £1,716 |
| 4 | ADF ENVIRONMENTAL | 2 | £1,800 |
| 5 | AMBITION 24 HOURS | 2 | £1,572 |
| 6 | VOLKERHIGHWAYS | 2 | £1,776 |
| 7 | SPIRE RIDGE BOARDING KENNELS AND CATTERY | 2 | £1,674 |
| 8 | SEISMIC SEWAGE SYSTEMS | 2 | £1,540 |
| 9 | G7 BUSINESS SOLUTIONS | 2 | £1,505 |
| 10 | DWP DEBT MANAGEMENT | 2 | £1,702 |
| 11 | SOUTHERN MEDICAL | 2 | £1,767 |
| 12 | SSE ENERGY SOLUTIONS | 2 | £1,751 |
| 13 | BROADWAY CARS | 2 | £1,501 |
| 14 | M ALLUM PLUMBING HEATING ENGINEERS | 2 | £1,428 |
| 15 | CRESCENT SIGNS | 2 | £1,552 |

**PBC.** P-02, P-07

## R-03 Payment groups crossing the Key Decision and Executive approval levels

Score 12 (likelihood 3 × impact 4), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-05 Expected control

Contract awards above the Key Decision level are taken as Key Decisions on a board-approved report, and awards from the Executive level go to the Executive [CPR-04] [CPR-60] [CPR-61] [CPR-62].

#### T-06

**Test step.** For each sampled payment group at the Executive tier, identify the contract the payments are made under; obtain the Executive approval for the award [CPR-62], the council's current Threshold figures and the tender record showing the full competitive tender the contract's value requires [CPR-69] [CPR-71]; search the waiver and exception register for the contract and, where an exception is recorded, confirm the S151 Officer and Monitoring Officer recommendation to the Executive [CPR-27]. Groups: [`$.tests.split_purchases.by_tier.2500000.groups`].

**Sample.** 3 of 3 rows in `analytics-full/split_purchases.csv` where tier = 2500000, sorted by group_total descending, taking units from the top of the list. 113 transactions, £10,261,095 net, in `outputs/samples/T-06.csv`.
Why this sample: Every group at the Executive tier; the population is smaller than the sample size.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | VEOLIA ES WEST BERKSHIRE CHAPS ONLY | 2 | £3,984,209 |
| 2 | VOLKERHIGHWAYS | 56 | £3,289,411 |
| 3 | VOLKERHIGHWAYS | 55 | £2,987,476 |

**PBC.** P-08, P-09, P-10, P-11, P-12

#### T-16

**Test step.** For each sampled payment group at the Key Decision tier, identify the contract the payments are made under; obtain the Key Decision record and award report [CPR-04] [CPR-60] [CPR-61], the council's current Threshold figures and the tender record showing the full competitive tender the contract's value requires [CPR-69] [CPR-71]; search the waiver and exception register for the contract and, where an exception is recorded, confirm the recommendation to the Executive [CPR-27]; close groups that trace to an approved term contract. Groups: [`$.tests.split_purchases.by_tier.500000.groups`].

**Sample.** 8 of 8 rows in `analytics-full/split_purchases.csv` where tier = 500000; supplier_norm ≠ VOLKERHIGHWAYS, sorted by group_total descending, taking units from the top of the list. 642 transactions, £5,902,976 net, in `outputs/samples/T-16.csv`.
Why this sample: Every group at the Key Decision tier except the VOLKERHIGHWAYS groups, whose payments sit in its Executive-tier groups in T-06, so each payment group is tested once.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | BUPA CARE SERVICES | 248 | £1,259,715 |
| 2 | OAKLANDS SEN SCHOOL BERKSHIRE | 54 | £1,026,662 |
| 3 | AFFINITY TRUST SUPPORT | 182 | £813,497 |
| 4 | BUPA CARE SERVICES | 120 | £605,975 |
| 5 | PHOENIX CHILD CARE THE GRANGE SCHOOL | 23 | £566,089 |
| 6 | COMENSURA | 6 | £557,962 |
| 7 | RUSKIN MILL TRUST | 5 | £550,097 |
| 8 | SOFTWAREONE UK | 4 | £522,979 |

**PBC.** P-08, P-13, P-10, P-11, P-12

## R-04 Suppliers above the publication threshold with no live Contracts Finder notice

Score 9 (likelihood 3 × impact 3), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-06 Expected control

Contracts from the publication threshold up are let on Portal quotes, have a contract notice published on the CDP, are in writing, and are notified for the contracts register [CPR-65] [CPR-66] [CPR-68] [CPR-36] [CPR-07] [CPR-38].

#### T-07

**Test step.** For each sampled supplier above the publication threshold with no live notice matched, request the contract, its award notice [CPR-66] [CPR-68] and its entry on the contracts register [CPR-07] [CPR-38]; where no contract is held, request the quote record [CPR-65], a waiver, or the prior written Monitoring Officer approval for an exclusion from competition [CPR-73]. Suppliers flagged: [`$.tests.off_contract.counts.by_tag.general_procurement`] general procurement.

**Sample.** 15 of 197 rows in `analytics-full/off_contract.csv` where tag in general_procurement, premises, agency_staff, sorted by annualised_estimate descending, taking units from the top of the list. 303 transactions, £20,564,580 net, in `outputs/samples/T-07.csv`.
Why this sample: General procurement, premises and agency staff suppliers: everything outside the placement and grant tags; largest annualised estimate first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | VOLKERHIGHWAYS | 126 | £7,377,922 |
| 2 | VEOLIA ES WEST BERKSHIRE CHAPS ONLY | 3 | £6,186,065 |
| 3 | MILLBROOK HEALTHCARE | 4 | £3,459,365 |
| 4 | COMENSURA | 14 | £1,275,552 |
| 5 | SOFTWAREONE UK | 4 | £522,979 |
| 6 | LIVITY LIFE | 9 | £513,075 |
| 7 | SIKANDAR HAYAT T A PROMPT CARS | 40 | £187,250 |
| 8 | ELIOR UK | 9 | £161,416 |
| 9 | BBOWT | 3 | £144,317 |
| 10 | A2 DOMINION | 2 | £136,612 |
| 11 | BROADWAY CARS | 46 | £131,939 |
| 12 | ANCHOR PIPEWORK | 36 | £127,841 |
| 13 | KPMG | 3 | £119,155 |
| 14 | SCOTTISH SOUTHERN | 2 | £110,761 |
| 15 | EDUCATION SOFTWARE SOLUTIONS | 2 | £110,330 |

**PBC.** P-14, P-15, P-16, P-17

#### T-08

**Test step.** For each sampled supplier with a near-miss notice name, confirm whether the candidate notice covers the supplier; where it is a framework or DPS, obtain the advice confirming the council may use the scheme [CPR-31] and any approval for a direct call-off [CPR-75]; otherwise follow the T-07 requests [CPR-66]. Candidates: [`$.tests.off_contract.with_candidate_name`].

**Sample.** 15 of 16 rows in `analytics-full/off_contract.csv` where has_candidate = True; tag ≠ grant, sorted by annualised_estimate descending, taking units from the top of the list. 281 transactions, £884,360 net, in `outputs/samples/T-08.csv`.
Why this sample: The near-miss candidates the proposed focus names; outside the grant tag.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | SIKANDAR HAYAT T A PROMPT CARS | 40 | £187,250 |
| 2 | BROADWAY CARS | 46 | £131,939 |
| 3 | WCL UK TRADING AS EVERYTHING ICT | 1 | £102,883 |
| 4 | GLEN CLEANING COMPANY | 68 | £92,393 |
| 5 | D J TRAVEL | 16 | £67,967 |
| 6 | ABC TRAVEL WOKINGHAM T A ABC TRAVEL | 24 | £63,141 |
| 7 | SOUTHERN COACH LINES | 16 | £55,532 |
| 8 | SWAN ADVOCACY | 8 | £51,216 |
| 9 | MARK DILLON T A PENMAR TRANSPORT | 15 | £35,282 |
| 10 | THE ADVOCACY PEOPLE FORMERLY SEAP | 3 | £31,653 |
| 11 | S RICHARDS T AS K RICKETTS S RICHARDS TAXIS | 8 | £17,144 |
| 12 | MRS M F RICHARDSON T A MFR CONTRACTS | 13 | £15,365 |
| 13 | N MEHMOOD T A A STAR EXECUTIVE CARS | 7 | £12,489 |
| 14 | ELITE SECURITY GROUP | 9 | £10,178 |
| 15 | NADEEM MIRZA TRADING AS PARKER TRAVELS | 7 | £9,928 |

**PBC.** P-15, P-18

## R-05 Payments to suppliers whose every matched notice ended before the spend window

Score 9 (likelihood 3 × impact 3), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-07 Expected control

Payments continue after a contract's end only under an extension the contract provides for, approved by the S151 Officer, or under a new award notified for the contracts register [CPR-76] [CPR-38].

#### T-09

**Test step.** For each flagged supplier, compare the payment dates with the matched notices' end dates, then obtain the S151 extension approval [CPR-76] or the current contract and its award record [CPR-38]. Suppliers flagged: [`$.tests.expired_notice_spend.counts.total`].

**Sample.** 7 of 7 rows in `analytics-full/expired_notice_spend.csv` where no filter, sorted by total_3m descending, taking units from the top of the list. 58 transactions, £190,367 net, in `outputs/samples/T-09.csv`.
Why this sample: Every flagged supplier; the population is smaller than the sample size.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | HOPE CLAY CONSTRUCTION | 1 | £91,307 |
| 2 | BERKSHIRE MECHANICAL SERVICES | 45 | £68,040 |
| 3 | G7 BUSINESS SOLUTIONS | 8 | £16,365 |
| 4 | CACI | 1 | £12,072 |
| 5 | MORTON PATTISON | 1 | £1,102 |
| 6 | DAVIS AND ASSOCIATES CONSULTANCY | 1 | £800 |
| 7 | TACTICAL FACILITIES MANAGEMENT | 1 | £682 |

**PBC.** P-19, P-20

## R-06 Annualised spend above the awarded contract value without a recorded variation

Score 9 (likelihood 3 × impact 3), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-08 Expected control

A variation of a contract's scope or value has prior written approval from the Monitoring Officer and S151 Officer, or the relevant board above the Threshold [CPR-77] [CPR-78].

#### T-10

**Test step.** For each flagged supplier, obtain the award and total spend to date under the contract, compare them, and where spend runs beyond the award obtain the variation approval [CPR-77] [CPR-78] or extension record [CPR-76]. Suppliers flagged: [`$.tests.spend_vs_award.counts.total`].

**Sample.** 7 of 7 rows in `analytics-full/spend_vs_award.csv` where no filter, sorted by ratio descending, taking units from the top of the list. 30 transactions, £633,768 net, in `outputs/samples/T-10.csv`.
Why this sample: Every flagged supplier, highest spend-to-award ratio first; the population is smaller than the sample size.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | NEC SOFTWARE SOLUTIONS UK | 10 | £314,384 |
| 2 | BOOKINGLAB | 1 | £24,000 |
| 3 | EXACOM SYSTEMS | 1 | £12,106 |
| 4 | SMS ENVIRONMENTAL | 7 | £7,759 |
| 5 | SOFTCAT | 2 | £11,005 |
| 6 | IDOX SOFTWARE | 2 | £51,226 |
| 7 | TWO SAINTS | 7 | £213,288 |

**PBC.** P-21, P-22, P-23

## R-07 Repeat payments of the same amount to the same supplier within a week

Score 15 (likelihood 3 × impact 5), Extreme (Red). Sample size per test: 25.

### C-09 Expected control

Every payment rests on written evidence of a distinct purchase: its own invoice and order, so the same charge is not paid twice [CPR-35].

#### T-11

**Test step.** For each sampled supplier and amount pair repeated on different dates, match each payment to a distinct invoice and purchase record [CPR-35]; where two payments share an invoice, obtain the credit note or recovery record. General procurement pairs flagged: [`$.tests.duplicates.different_dates.items_by_tag.general_procurement`].

**Sample.** 23 of 23 rows in `analytics-full/duplicates.csv` where type = different_dates; tag in general_procurement, agency_staff, sorted by gbp_repeat_value descending, taking units from the top of the list. 55 transactions, £540,202 net, in `outputs/samples/T-11.csv`.
Why this sample: General procurement pairs, split from premises so neither tag's largest suppliers crowd out the other; largest repeat value first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | VOLKERHIGHWAYS | 2 | £203,852 |
| 2 | VOLKERHIGHWAYS | 2 | £108,483 |
| 3 | TWO SAINTS | 2 | £54,295 |
| 4 | VOLKERHIGHWAYS | 2 | £35,765 |
| 5 | ROADSIDE TECHNOLOGIES | 4 | £22,376 |
| 6 | BROADWAY CARS | 3 | £15,990 |
| 7 | PAVILLION PUBLISHING AND MEDIA | 2 | £18,169 |
| 8 | BROADWAY CARS | 3 | £11,700 |
| 9 | BROADWAY CARS | 3 | £10,920 |
| 10 | LOCAL GOVERNMENT PROPERTY CONSULTANTS LGPC | 2 | £9,850 |
| 11 | BRITISH TELECOM | 2 | £8,728 |
| 12 | FD TRAVELS T A SCHOOL EXPRESS | 2 | £8,036 |
| 13 | FD TRAVELS T A SCHOOL EXPRESS | 2 | £5,488 |
| 14 | AMR CONSULT | 2 | £5,331 |
| 15 | CRESCENT SIGNS | 2 | £4,600 |
| 16 | VALLEY CARS | 2 | £4,008 |
| 17 | READING REFUGEE SUPPORT GROUP | 4 | £2,397 |
| 18 | CHIPSIDE | 4 | £2,080 |
| 19 | AERO PROPERTY CONSULTANTS | 2 | £2,560 |
| 20 | COMPASS EXECUTIVE CARS UK | 2 | £1,488 |
| 21 | READING REFUGEE SUPPORT GROUP | 2 | £1,486 |
| 22 | EDGE TRAINING AND CONSULTANCY | 2 | £1,400 |
| 23 | MR I GRAHAM T A COMMUNITY SAFETY TRAINING | 2 | £1,200 |

**PBC.** P-02, P-24

#### T-17

**Test step.** For each sampled supplier and amount pair repeated on different dates, match each payment to a distinct invoice and purchase record [CPR-35]; where two payments share an invoice, obtain the credit note or recovery record. Premises pairs flagged: [`$.tests.duplicates.different_dates.items_by_tag.premises`].

**Sample.** 25 of 28 rows in `analytics-full/duplicates.csv` where type = different_dates; tag = premises, sorted by gbp_repeat_value descending, taking units from the top of the list. 94 transactions, £117,456 net, in `outputs/samples/T-17.csv`.
Why this sample: Premises pairs as their own stratum, so the sample reaches nearly every premises supplier; largest repeat value first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | KB REAL ESTATE MANAGEMENT | 9 | £12,555 |
| 2 | KB REAL ESTATE MANAGEMENT | 9 | £12,150 |
| 3 | KB REAL ESTATE MANAGEMENT | 8 | £10,800 |
| 4 | KB REAL ESTATE MANAGEMENT | 6 | £11,160 |
| 5 | KB REAL ESTATE MANAGEMENT | 6 | £10,800 |
| 6 | KB REAL ESTATE MANAGEMENT | 6 | £10,800 |
| 7 | CONNICK TREE CARE | 6 | £6,056 |
| 8 | DIMENSIONS NSO | 2 | £5,897 |
| 9 | KB REAL ESTATE MANAGEMENT | 2 | £5,700 |
| 10 | SPARE CRIB GLOBAL | 4 | £3,220 |
| 11 | GLEN CLEANING COMPANY | 3 | £2,705 |
| 12 | GLEN CLEANING COMPANY | 3 | £2,339 |
| 13 | GLEN CLEANING COMPANY | 2 | £3,068 |
| 14 | TENNENT HOMES 2019 | 3 | £1,800 |
| 15 | TENNENT HOMES 2019 | 3 | £1,800 |
| 16 | TENNENT HOMES 2019 | 3 | £1,800 |
| 17 | CONNICK TREE CARE | 2 | £2,266 |
| 18 | BERKSHIRE MECHANICAL SERVICES | 3 | £1,635 |
| 19 | GLEN CLEANING COMPANY | 2 | £1,782 |
| 20 | PRIMANAGE | 2 | £1,740 |
| 21 | BERKSHIRE MECHANICAL SERVICES | 2 | £1,600 |
| 22 | TENNENT HOMES 2019 | 2 | £1,500 |
| 23 | TENNENT HOMES 2019 | 2 | £1,500 |
| 24 | TENNENT HOMES 2019 | 2 | £1,500 |
| 25 | ELITE SECURITY GROUP | 2 | £1,282 |

**PBC.** P-02, P-24

#### T-12

**Test step.** For each sampled placement pair repeated on different dates, confirm from the invoices and case records that each payment relates to a different client or period [CPR-35]. Placement pairs flagged: [`$.tests.duplicates.different_dates.items_by_tag.care_education_placement`].

**Sample.** 25 of 204 rows in `analytics-full/duplicates.csv` where type = different_dates; tag = care_education_placement, sorted by gbp_repeat_value descending, taking units from the top of the list. 137 transactions, £2,544,445 net, in `outputs/samples/T-12.csv`.
Why this sample: Placement pairs, which the register expects to be per-client fees; largest repeat value first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | OAKLANDS SEN SCHOOL BERKSHIRE | 36 | £732,148 |
| 2 | OAKLANDS SEN SCHOOL BERKSHIRE | 13 | £266,954 |
| 3 | PHOENIX CHILD CARE THE GRANGE SCHOOL | 10 | £219,882 |
| 4 | SUKHBIR SINGH AND HARVINDER SINGH T A CALCOT SERVICES FOR CHILDREN CSFC | 6 | £112,612 |
| 5 | PHOENIX CHILD CARE THE GRANGE SCHOOL | 3 | £98,134 |
| 6 | HUCKLEBERRY HOUSE | 3 | £92,756 |
| 7 | PARADIGM CARE SERVICES | 4 | £68,000 |
| 8 | CARE SERVICES TO YOU | 3 | £71,969 |
| 9 | CARE SERVICES TO YOU | 3 | £71,969 |
| 10 | PHOENIX CHILD CARE THE GRANGE SCHOOL | 3 | £69,630 |
| 11 | AMEGREEN CHILDRENS SERVICES | 2 | £68,862 |
| 12 | AMEGREEN CHILDRENS SERVICES | 2 | £68,862 |
| 13 | AMEGREEN CHILDRENS SERVICES | 2 | £66,641 |
| 14 | AMEGREEN CHILDRENS SERVICES | 2 | £66,641 |
| 15 | AFFINITY TRUST SUPPORT | 9 | £35,640 |
| 16 | LIAISE LODDON | 3 | £44,165 |
| 17 | THE UNICORN SCHOOL | 3 | £41,313 |
| 18 | BRIGHTER LIVING CARE | 2 | £53,470 |
| 19 | BRIGHTER LIVING CARE | 2 | £53,192 |
| 20 | FLOURISHING FAMILIES ASSESSMENT SERVICE | 5 | £32,750 |
| 21 | ACORN CARE EDUCATION | 2 | £51,067 |
| 22 | AFFINITY TRUST SUPPORT | 3 | £36,828 |
| 23 | CARE SERVICES TO YOU | 2 | £47,980 |
| 24 | CARE SERVICES TO YOU | 2 | £47,980 |
| 25 | CHILTERN WAY ACADEMY | 12 | £25,000 |

**PBC.** P-25

#### T-18

**Test step.** Obtain the unredacted listing of payments published with the supplier name redacted in the spend window (2,015 rows); select payments, largest first, and match each to a distinct invoice and purchase record [CPR-35].

**Sample.** Select 25 items from the council's unredacted listing of payments published as 'Redacted' in the spend window. The population sits in council records, so the builder draws nothing; record the items chosen in the working papers.
Why this sample: Redacted-supplier payments were excluded from every analytics test, so the population sits in council records.

**PBC.** P-26, P-02

## R-08 High-value care and education placements with no published contract notice

Score 9 (likelihood 3 × impact 3), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-10 Expected control

Each individual placement excluded from competition has the reasons for the choice of provider recorded on the case notes, and Provider Selection Regime decisions are recorded [CPR-79] [CPR-74].

#### T-13

**Test step.** For each sampled placement supplier with no live notice, obtain the framework or block contract the placements sit under; where none applies, request the case-note record of provider choice for the placements paid in the window [CPR-79] or the PSR decision record [CPR-74]. Suppliers flagged: [`$.tests.off_contract.counts.by_tag.care_education_placement`].

**Sample.** 15 of 316 rows in `analytics-full/off_contract.csv` where tag = care_education_placement, sorted by annualised_estimate descending, taking units from the top of the list. 1,635 transactions, £11,216,255 net, in `outputs/samples/T-13.csv`.
Why this sample: Placement suppliers with no live notice; largest annualised estimate first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | BUPA CARE SERVICES | 370 | £1,874,166 |
| 2 | AFFINITY TRUST SUPPORT | 263 | £1,098,337 |
| 3 | OAKLANDS SEN SCHOOL BERKSHIRE | 54 | £1,026,662 |
| 4 | RUSKIN MILL TRUST | 9 | £795,198 |
| 5 | AMEGREEN CHILDRENS SERVICES | 27 | £750,437 |
| 6 | BRIGHTER LIVING CARE | 74 | £747,183 |
| 7 | SUKHBIR SINGH AND HARVINDER SINGH T A CALCOT SERVICES FOR CHILDREN CSFC | 26 | £639,382 |
| 8 | WE ARE THE CARE COMPANY | 349 | £589,012 |
| 9 | THE BETTER GROUP | 26 | £588,490 |
| 10 | PHOENIX CHILD CARE THE GRANGE SCHOOL | 25 | £567,709 |
| 11 | VOYAGE CARE | 80 | £554,679 |
| 12 | GCH ALDER T A HUNGERFORD CARE HOME | 104 | £545,532 |
| 13 | WEST BERKSHIRE MENCAP | 115 | £505,286 |
| 14 | PURLEY PARK TRUST | 94 | £471,284 |
| 15 | ACORN CARE EDUCATION | 19 | £462,898 |

**PBC.** P-03, P-27

## R-09 Waivers and exceptions to the Rules not approved or recorded in advance

Score 9 (likelihood 3 × impact 3), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-11 Expected control

Waivers and exceptions are sought only in advance, granted by the Monitoring Officer or S151 Officer on recorded urgency or discretion grounds, fully documented, and reported to the relevant board or the Executive where required [CPR-21] [CPR-22] [CPR-23] [CPR-24] [CPR-27] [CPR-28] [CPR-29] [CPR-30].

#### T-14

**Test step.** From the waiver and exception register, take every waiver or exception for a contract above the Key Decision level first, then select from the rest granted in or before the spend window; for each, confirm the request predates the purchase [CPR-24], the grounds and written reasons are recorded [CPR-21] [CPR-22] [CPR-28], the S151 Officer approved and recorded the circumstances [CPR-23] [CPR-30], and any exception report went to the board or the Executive where required [CPR-29] [CPR-27].

**Sample.** Select 15 items from the council's waiver and exception register covering the spend window. The population sits in council records, so the builder draws nothing; record the items chosen in the working papers.
Why this sample: No spend test can see a waiver; the population sits in council records. Exceptions above the Key Decision level come first, as the auditor's override on R-09 names them as the highest stakes.

**PBC.** P-12, P-28

#### T-15

**Test step.** For each sampled supplier above the publication threshold with no live notice, search the waiver and exception register; where a waiver is recorded, test it as in T-14 [CPR-23] [CPR-24]; where none is recorded, refer the supplier to T-07 [CPR-66]. Suppliers flagged: [`$.tests.off_contract.counts.total`].

**Sample.** 15 of 197 rows in `analytics-full/off_contract.csv` where tag in general_procurement, premises, agency_staff, sorted by annualised_estimate descending, taking units at even intervals through the list. 200 transactions, £7,789,872 net, in `outputs/samples/T-15.csv`.
Why this sample: The cross-check the proposed focus asks for; even steps through the off-contract list so it reaches beyond the largest suppliers T-07 takes.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | VOLKERHIGHWAYS | 126 | £7,377,922 |
| 2 | SCOTTISH SOUTHERN | 2 | £110,761 |
| 3 | WSP UK | 24 | £73,901 |
| 4 | SOUTHERN COACH LINES | 16 | £55,532 |
| 5 | ACHIEVING FOR CHILDREN | 1 | £34,390 |
| 6 | RACKLINE | 2 | £25,510 |
| 7 | MARSTON HOLDINGS | 2 | £19,746 |
| 8 | KEYSTREAM GROUP | 2 | £17,545 |
| 9 | ADAMS SUTHERLAND | 1 | £15,350 |
| 10 | CELADOR APARTMENTS | 5 | £13,699 |
| 11 | KENNET AVON GROUP | 7 | £11,735 |
| 12 | MR RIAZ SHEIKH | 4 | £9,998 |
| 13 | FUNTASTIC KIDS | 2 | £9,153 |
| 14 | CHUBB FIRE SECURITY | 4 | £7,870 |
| 15 | FIELDWORK REST PLAY | 2 | £6,760 |

**PBC.** P-12, P-28

## PBC list

Request these from the council before fieldwork.

| # | Item | For tests |
|---|---|---|
| P-01 | Procurement Portal quote record for each sampled payment | T-01, T-02 |
| P-02 | Purchase order and invoice for each sampled payment | T-01, T-03, T-04, T-05, T-11, T-17, T-18 |
| P-03 | Framework, block contract or case-note record of provider choice for each sampled placement | T-02, T-13 |
| P-04 | Procurement Portal quote record for each sampled payment group | T-03 |
| P-05 | Procurement advice on aggregation for each sampled supplier, if sought | T-03 |
| P-06 | Quote or written purchase evidence for each sampled payment | T-04 |
| P-07 | Quote or written purchase evidence for each sampled payment group | T-05 |
| P-08 | Contract under which each sampled supplier is paid | T-06, T-16 |
| P-09 | Executive approval for each sampled contract at the Executive tier | T-06 |
| P-10 | The council's current Threshold figures | T-06, T-16 |
| P-11 | Tender record for each sampled contract | T-06, T-16 |
| P-12 | Waiver and exception register covering the spend window | T-06, T-16, T-14, T-15 |
| P-13 | Key Decision record and award report for each sampled contract | T-16 |
| P-14 | Signed contract for each sampled supplier | T-07 |
| P-15 | Contract award notice for each sampled supplier | T-07, T-08 |
| P-16 | Contracts register entry for each sampled supplier | T-07 |
| P-17 | Procurement Portal quote record, approved waiver or Monitoring Officer exclusion approval for each sampled supplier with no contract | T-07 |
| P-18 | Framework or DPS access advice and call-off approval for each sampled supplier under a scheme | T-08 |
| P-19 | S151 extension approval for each sampled supplier | T-09 |
| P-20 | Current contract and award record for each sampled supplier | T-09 |
| P-21 | Contract and award value for each sampled supplier | T-10 |
| P-22 | Total spend to date under the contract for each sampled supplier | T-10 |
| P-23 | Variation or extension approval for each sampled supplier | T-10 |
| P-24 | Credit note or recovery record for any payment matched to an invoice already paid | T-11, T-17 |
| P-25 | Invoice for each sampled payment, with the client or period it covers | T-12 |
| P-26 | Unredacted listing of payments published as 'Redacted' in the spend window | T-18 |
| P-27 | PSR decision record for each sampled supplier under the Provider Selection Regime | T-13 |
| P-28 | Waiver request, approval and exception report for each sampled waiver | T-14, T-15 |
