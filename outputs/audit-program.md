# Audit program

Built 2026-10-09 by `.claude/skills/audit-program/build_pack.py` from `outputs/audit-plan.json`, on risk register revision 3. Every figure is filled from `outputs/analytics.json` or computed by the builder and listed in `outputs/pack-figures.json`. The analytics are risk indicators to investigate, not findings of wrongdoing by the council, a service or a supplier.

Each test pulls the transactions in `outputs/samples/<test>.csv`. A flagged item is a prompt to request evidence; a complete record closes it.

## R-01 Spend structured to stay just below the quote threshold

Score 12 (likelihood 4 × impact 3), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-01 Expected control

Purchases from the quote threshold up are let on at least three quotes invited via the Procurement Portal, including an SME or VCSE and a local supplier, and the procedure is documented [CPR-65] [CPR-67] [CPR-34].

#### T-01

**Test step.** For each sampled payment just below the quote threshold, identify the requirement it pays for and its total value; obtain the Portal quote record and confirm three quotes were invited before the order where the requirement reaches the threshold [CPR-65] [CPR-67], and that the procedure record is kept [CPR-34]. Clustered payments: [`$.tests.threshold_clustering.by_tier.25000.rows`].

**Sample.** 14 of 14 rows in `analytics-full/threshold_clustering.csv` where tier = 25000; tag not in care_education_placement, sorted by amount descending, taking units from the top of the list. 14 transactions, £332,670 net, in `outputs/samples/T-01.csv`.
Why this sample: Every clustered payment outside the placement tag: general procurement, premises and grants, as the proposed focus asks; largest payments, closest to the threshold, first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | CHARMAINE CAULFIELD | 1 | £24,850 |
| 2 | BEANSHEAF COMMUNITY PRE SCHOO | 1 | £24,705 |
| 3 | TRIPLE VALUE IMPACT | 1 | £24,244 |
| 4 | DEVCOMMS SOUTH EAST | 1 | £24,227 |
| 5 | THE BETTER GROUP | 1 | £24,089 |
| 6 | BOOKINGLAB | 1 | £24,000 |
| 7 | ELIOR UK | 1 | £23,694 |
| 8 | READING WEST APARTHOTEL | 1 | £23,660 |
| 9 | VOLKERHIGHWAYS | 1 | £23,591 |
| 10 | ELIOR UK | 1 | £23,517 |
| 11 | ELIOR UK | 1 | £23,173 |
| 12 | PIED PIPER PRE SCHOOL | 1 | £23,073 |
| 13 | WEST BERKSHIRE TRAINING CONSORTIUM | 1 | £22,964 |
| 14 | MINI OAKS PRESCHOOL | 1 | £22,882 |

**PBC.** P-01, P-02

#### T-02

**Test step.** Lower-priority stratum: for each sampled placement payment just below the quote threshold, confirm whether the placement sits under a framework, block contract or recorded provider choice [CPR-79]; where none applies, obtain the Portal quote record [CPR-65]. For CARE SERVICES TO YOU, whose clustered placement payments repeat one rate, request once the framework, block contract or recorded provider choice covering those placements [CPR-79].

**Sample.** 15 of 17 rows in `analytics-full/threshold_clustering.csv` where tier = 25000; tag = care_education_placement; supplier_norm ≠ CARE SERVICES TO YOU, sorted by amount descending, taking units from the top of the list. 15 transactions, £361,403 net, in `outputs/samples/T-02.csv`.
Why this sample: Recurring placement invoices are the lower-priority stratum the proposed focus names; largest first. CARE SERVICES TO YOU is left out of the drawn rows because its clustered payments repeat one rate, so its framework or contract is requested once in the step instead of filling the sample.

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
| 11 | PHOENIX CHILD CARE THE GRANGE SCHOOL | 1 | £23,210 |
| 12 | PHOENIX CHILD CARE THE GRANGE SCHOOL | 1 | £23,210 |
| 13 | PHOENIX CHILD CARE THE GRANGE SCHOOL | 1 | £23,210 |
| 14 | PHOENIX CHILD CARE THE GRANGE SCHOOL | 1 | £23,077 |
| 15 | FOCUS SUPPORT | 1 | £23,054 |

**PBC.** P-03, P-01

### C-02 Expected control

A requirement is valued as a whole and not split or disaggregated to stay below a threshold, and officers seek advice on repeat or similar purchases [CPR-13] [CPR-14].

#### T-03

**Test step.** For each sampled payment group whose total reaches the quote threshold while each payment stays under it, establish from the orders and invoices whether the payments form one requirement; if so, obtain the quote record for the combined value [CPR-65] and any advice sought on aggregation [CPR-14], and record whether the split is explained [CPR-13]. Groups at this tier: [`$.tests.split_purchases.by_tier.25000.groups`].

**Sample.** 15 of 71 rows in `analytics-full/split_purchases.csv` where tier = 25000; same_timestamp = False; tag not in care_education_placement, sorted by payments ascending, max_payment descending, span_days ascending, taking units from the top of the list. 37 transactions, £538,180 net, in `outputs/samples/T-03.csv`.
Why this sample: Groups outside the placement tag (general procurement, premises and grants) not explained by one payment run; groups of few payments, each closest to the threshold, in the tightest span first, where the splitting indicator is strongest.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | BEANSHEAF COMMUNITY PRE SCHOO | 2 | £25,705 |
| 2 | DEVCOMMS SOUTH EAST | 2 | £38,785 |
| 3 | READING WEST APARTHOTEL | 2 | £44,616 |
| 4 | PANGBOURNE DAY NURSERY | 2 | £43,870 |
| 5 | RACKLINE | 2 | £25,510 |
| 6 | PRUDENTIAL | 2 | £35,156 |
| 7 | PRUDENTIAL | 2 | £33,817 |
| 8 | MALLARD COTTAGE CHILDCARE | 2 | £25,005 |
| 9 | ELIOR UK | 3 | £53,393 |
| 10 | INSIGHT DIRECT UK | 3 | £37,014 |
| 11 | HOME FRONT | 3 | £50,197 |
| 12 | A E BUILDERS BASINGSTOKE | 3 | £33,497 |
| 13 | SOLUTIONS4HEALTH | 3 | £36,944 |
| 14 | CONVERGENT TECHNOLOGY | 3 | £27,161 |
| 15 | TRADING STANDARDS SOUTH EAST | 3 | £27,510 |

**PBC.** P-02, P-04, P-05

## R-02 Spend kept at or just below the one-quote level

Score 8 (likelihood 4 × impact 2), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-03 Expected control

Purchases above the one-quote level have at least one quote from an appropriate source, and every purchase has written evidence [CPR-64] [CPR-35].

#### T-04

**Test step.** For each sampled payment just at or below the one-quote level, obtain the order, invoice and the quote or written purchase evidence, and confirm the requirement's total value and whether a quote was sought [CPR-64] [CPR-35]. Clustered payments: [`$.tests.threshold_clustering.by_tier.1000.rows`].

**Sample.** 15 of 103 rows in `analytics-full/threshold_clustering.csv` where tier = 1000; tag not in care_education_placement, sorted by amount descending, taking units at even intervals through the list. 15 transactions, £14,454 net, in `outputs/samples/T-04.csv`.
Why this sample: Outside the placement tag, as the proposed focus asks, grants included; even steps through the stratum for coverage, since every payment sits in a narrow band.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | ALAN FULLER | 1 | £1,000 |
| 2 | BCJD | 1 | £1,000 |
| 3 | ACORNS OPERATIONAL ACCOUNT | 1 | £1,000 |
| 4 | BERKSHIRE MECHANICAL SERVICES | 1 | £1,000 |
| 5 | SIKANDAR HAYAT T A PROMPT CARS | 1 | £996 |
| 6 | RYGOR COMMERCIALS | 1 | £990 |
| 7 | 360 SECURITY SUPPORT SERVICES | 1 | £981 |
| 8 | BERKSHIRE MECHANICAL SERVICES | 1 | £975 |
| 9 | PREMIER CARS | 1 | £968 |
| 10 | EARLY EDUCATION | 1 | £954 |
| 11 | READING TRANSPORT | 1 | £936 |
| 12 | SIKANDAR HAYAT T A PROMPT CARS | 1 | £930 |
| 13 | WSP UK | 1 | £916 |
| 14 | WSP UK | 1 | £906 |
| 15 | GLEN CLEANING COMPANY | 1 | £902 |

**PBC.** P-02, P-06

### C-04 Expected control

Low-value requirements are not split across payments to stay below the one-quote level [CPR-13] [CPR-64].

#### T-05

**Test step.** For each sampled payment group whose total exceeds the one-quote level while each payment stays under it, establish whether the payments form one requirement and, if so, obtain the quote or written evidence for the combined value [CPR-64] [CPR-35] [CPR-13]. Groups at this tier: [`$.tests.split_purchases.by_tier.1000.groups`].

**Sample.** 15 of 113 rows in `analytics-full/split_purchases.csv` where tier = 1000; same_timestamp = False; tag not in care_education_placement, sorted by payments ascending, max_payment descending, span_days ascending, taking units from the top of the list. 30 transactions, £24,882 net, in `outputs/samples/T-05.csv`.
Why this sample: Outside the placement tag, grants included, and not explained by one payment run; groups of few payments, each closest to the one-quote level, in the tightest span first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | ACORNS OPERATIONAL ACCOUNT | 2 | £1,800 |
| 2 | BECKY TURNER | 2 | £1,750 |
| 3 | MECE FIRE SECURITY | 2 | £1,601 |
| 4 | POTTINGER S HIRE SERVICE | 2 | £1,716 |
| 5 | ADF ENVIRONMENTAL | 2 | £1,800 |
| 6 | AMBITION 24 HOURS | 2 | £1,572 |
| 7 | VOLKERHIGHWAYS | 2 | £1,776 |
| 8 | SPIRE RIDGE BOARDING KENNELS AND CATTERY | 2 | £1,674 |
| 9 | SEISMIC SEWAGE SYSTEMS | 2 | £1,540 |
| 10 | G7 BUSINESS SOLUTIONS | 2 | £1,505 |
| 11 | DWP DEBT MANAGEMENT | 2 | £1,702 |
| 12 | SOUTHERN MEDICAL | 2 | £1,767 |
| 13 | SSE ENERGY SOLUTIONS | 2 | £1,751 |
| 14 | BROADWAY CARS | 2 | £1,501 |
| 15 | M ALLUM PLUMBING HEATING ENGINEERS | 2 | £1,428 |

**PBC.** P-02, P-07

## R-03 Payment groups crossing the Key Decision and Executive approval levels

Score 12 (likelihood 3 × impact 4), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-05 Expected control

Contract awards above the Key Decision level are taken as Key Decisions on a board-approved report, and awards from the Executive level go to the Executive [CPR-04] [CPR-60] [CPR-61] [CPR-62].

#### T-06

**Test step.** First classify the contract by type (works, concession or light-touch, or goods and services) and place its value against the council's current Threshold figures; then test the tender record against the route that applies: for works, concession or light-touch contracts below the Threshold, five written tenders via the Portal [CPR-69] and the Portal advert with CDP information [CPR-70]; for any contract above the Threshold, the Procurement Legislation procedure [CPR-71] and the CDP advert [CPR-72]. For each sampled payment group at the Executive tier, identify the contract the payments are made under; obtain the Executive approval for the award [CPR-62]; search the waiver and exception register for the contract and, where an exception is recorded, confirm the S151 Officer and Monitoring Officer recommendation to the Executive [CPR-27]. Groups: [`$.tests.split_purchases.by_tier.2500000.groups`].

**Sample.** 3 of 3 rows in `analytics-full/split_purchases.csv` where tier = 2500000, sorted by group_total descending, taking units from the top of the list. 113 transactions, £10,261,095 net, in `outputs/samples/T-06.csv`.
Why this sample: Every group at the Executive tier; the population is smaller than the sample size.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | VEOLIA ES WEST BERKSHIRE CHAPS ONLY | 2 | £3,984,209 |
| 2 | VOLKERHIGHWAYS | 56 | £3,289,411 |
| 3 | VOLKERHIGHWAYS | 55 | £2,987,476 |

**PBC.** P-08, P-09, P-10, P-11, P-12

#### T-16

**Test step.** First classify the contract by type (works, concession or light-touch, or goods and services) and place its value against the council's current Threshold figures; then test the tender record against the route that applies: for works, concession or light-touch contracts below the Threshold, five written tenders via the Portal [CPR-69] and the Portal advert with CDP information [CPR-70]; for any contract above the Threshold, the Procurement Legislation procedure [CPR-71] and the CDP advert [CPR-72]. For each sampled payment group at the Key Decision tier, identify the contract the payments are made under; obtain the Key Decision record and award report [CPR-04] [CPR-60] [CPR-61]; search the waiver and exception register for the contract and, where an exception is recorded, confirm the recommendation to the Executive [CPR-27]; close groups that trace to an approved term contract. Groups: [`$.tests.split_purchases.by_tier.500000.groups`].

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

**Test step.** For each sampled general procurement supplier above the publication threshold with no live notice matched, request the contract, its award notice [CPR-66] [CPR-68] and its entry on the contracts register [CPR-07] [CPR-38]; where no contract is held, request the quote record [CPR-65], a waiver, or the prior written Monitoring Officer approval for an exclusion from competition [CPR-73]. Suppliers flagged: [`$.tests.off_contract.counts.by_tag.general_procurement`] general procurement. Using the council's current Threshold figures, place each supplier's contract value against the award tiers and obtain the award by the Service Director or nominated officer up to the Threshold [CPR-57], or, above it and below the Key Decision level, the S151 and Monitoring Officer recommendation [CPR-58] and the board-approved award report [CPR-59]; where an exclusion from competition exceeds the Threshold, obtain the board approval [CPR-80].

**Sample.** 15 of 169 rows in `analytics-full/off_contract.csv` where tag = general_procurement, sorted by annualised_estimate descending, taking units from the top of the list. 289 transactions, £19,355,510 net, in `outputs/samples/T-07.csv`.
Why this sample: General procurement first, as the proposed focus asks; largest annualised estimate first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | VOLKERHIGHWAYS | 126 | £7,377,922 |
| 2 | VEOLIA ES WEST BERKSHIRE CHAPS ONLY | 3 | £6,186,065 |
| 3 | MILLBROOK HEALTHCARE | 4 | £3,459,365 |
| 4 | SOFTWAREONE UK | 4 | £522,979 |
| 5 | LIVITY LIFE | 9 | £513,075 |
| 6 | SIKANDAR HAYAT T A PROMPT CARS | 40 | £187,250 |
| 7 | ELIOR UK | 9 | £161,416 |
| 8 | BBOWT | 3 | £144,317 |
| 9 | BROADWAY CARS | 46 | £131,939 |
| 10 | ANCHOR PIPEWORK | 36 | £127,841 |
| 11 | KPMG | 3 | £119,155 |
| 12 | SCOTTISH SOUTHERN | 2 | £110,761 |
| 13 | EDUCATION SOFTWARE SOLUTIONS | 2 | £110,330 |
| 14 | WCL UK TRADING AS EVERYTHING ICT | 1 | £102,883 |
| 15 | BLOOM PROCUREMENT SERVICES | 1 | £100,211 |

**PBC.** P-14, P-15, P-16, P-17, P-10, P-18

#### T-19

**Test step.** For each sampled grant recipient above the publication threshold with no live notice matched, request the grant agreement, the award notice where the grant was let as a contract [CPR-66], the written agreement in an approved form [CPR-36] and its entry on the contracts register [CPR-07] [CPR-38]; where no agreement is held, request the quote record [CPR-65] or an approved waiver. Grant recipients flagged: [`$.tests.off_contract.counts.by_tag.grant`]. Using the council's current Threshold figures, place each supplier's contract value against the award tiers and obtain the award by the Service Director or nominated officer up to the Threshold [CPR-57], or, above it and below the Key Decision level, the S151 and Monitoring Officer recommendation [CPR-58] and the board-approved award report [CPR-59]; where an exclusion from competition exceeds the Threshold, obtain the board approval [CPR-80].

**Sample.** 15 of 124 rows in `analytics-full/off_contract.csv` where tag = grant, sorted by annualised_estimate descending, taking units from the top of the list. 29 transactions, £3,248,935 net, in `outputs/samples/T-19.csv`.
Why this sample: Grants as their own stratum, kept in R-04 by the auditor's scope decision; largest annualised estimate first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | JUBILEE DAY NURSERY | 3 | £408,595 |
| 2 | ACRES OF FUN DAY NURSERY AND PRE SCHOOL | 1 | £323,873 |
| 3 | ROCKING HORSE DAY NURSERY NEWBURY RACECOURSE | 2 | £320,464 |
| 4 | TIGERS DAY NURSERY | 4 | £244,339 |
| 5 | TIGERS AT THEALE DAY NURSERY | 2 | £240,746 |
| 6 | BROOKFIELDS SCHOOL | 1 | £236,744 |
| 7 | WOODLANDS DAY NURSERY | 2 | £221,334 |
| 8 | JUBILEE GEMS | 1 | £204,360 |
| 9 | LITTLE ME DAY NURSERY | 1 | £190,678 |
| 10 | JUST LEARNING TA BUSY BEES NEWBURY | 2 | £169,624 |
| 11 | QUACKERS DAY NURSERY | 1 | £149,005 |
| 12 | PASKAY | 3 | £140,375 |
| 13 | FLEDGLINGS DAY NURSERY T A FLEDGLINGS LODGE | 3 | £134,007 |
| 14 | MYRTLE TREE HOLDINGS T A AUDLEN HOUSE DAY NURSERY THATCHAM | 2 | £133,518 |
| 15 | SPRINGBURN CHILDCARE | 1 | £131,273 |

**PBC.** P-19, P-15, P-16, P-17, P-10, P-18

#### T-20

**Test step.** For each sampled premises or agency staff supplier above the publication threshold with no live notice matched, request the contract, its award notice [CPR-66] [CPR-68] and its entry on the contracts register [CPR-07] [CPR-38]; where no contract is held, request the quote record [CPR-65], a waiver, or the prior written Monitoring Officer approval for an exclusion from competition [CPR-73]. Premises suppliers flagged: [`$.tests.off_contract.counts.by_tag.premises`]. Using the council's current Threshold figures, place each supplier's contract value against the award tiers and obtain the award by the Service Director or nominated officer up to the Threshold [CPR-57], or, above it and below the Key Decision level, the S151 and Monitoring Officer recommendation [CPR-58] and the board-approved award report [CPR-59]; where an exclusion from competition exceeds the Threshold, obtain the board approval [CPR-80].

**Sample.** 15 of 28 rows in `analytics-full/off_contract.csv` where tag in premises, agency_staff, sorted by annualised_estimate descending, taking units from the top of the list. 328 transactions, £2,098,759 net, in `outputs/samples/T-20.csv`.
Why this sample: Premises and agency staff as their own stratum, so general procurement and grants do not crowd them out; largest annualised estimate first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | COMENSURA | 14 | £1,275,552 |
| 2 | A2 DOMINION | 2 | £136,612 |
| 3 | CONTINENTAL LANDSCAPES | 8 | £108,423 |
| 4 | KB REAL ESTATE MANAGEMENT | 67 | £105,375 |
| 5 | GLEN CLEANING COMPANY | 68 | £92,393 |
| 6 | READING WEST APARTHOTEL | 3 | £74,308 |
| 7 | CONNICK TREE CARE | 38 | £73,404 |
| 8 | BERKSHIRE MECHANICAL SERVICES | 45 | £68,040 |
| 9 | SOVEREIGN HOUSING GROUP | 44 | £33,284 |
| 10 | CASTLE WATER | 8 | £31,292 |
| 11 | KARD GROUP | 6 | £23,400 |
| 12 | TENNENT HOMES 2019 | 18 | £21,900 |
| 13 | MARSTON HOLDINGS | 2 | £19,746 |
| 14 | FIS PAYMENTS TRAVELODGE | 2 | £17,982 |
| 15 | PHS GROUP | 3 | £17,048 |

**PBC.** P-14, P-15, P-16, P-17, P-10, P-18

#### T-08

**Test step.** For each sampled supplier with a near-miss notice name, confirm whether the candidate notice covers the supplier; where it is a framework or DPS, obtain the advice confirming the council may use the scheme [CPR-31] and any approval for a direct call-off [CPR-75]; otherwise follow the T-07 requests [CPR-66]. Candidates: [`$.tests.off_contract.with_candidate_name`].

**Sample.** 14 of 14 rows in `analytics-full/off_contract.csv` where has_candidate = True; tag ≠ care_education_placement, sorted by annualised_estimate descending, taking units from the top of the list. 278 transactions, £810,843 net, in `outputs/samples/T-08.csv`.
Why this sample: The near-miss candidates the proposed focus names, outside the placement tag that R-08 covers; largest annualised estimate first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | SIKANDAR HAYAT T A PROMPT CARS | 40 | £187,250 |
| 2 | BROADWAY CARS | 46 | £131,939 |
| 3 | WCL UK TRADING AS EVERYTHING ICT | 1 | £102,883 |
| 4 | GLEN CLEANING COMPANY | 68 | £92,393 |
| 5 | D J TRAVEL | 16 | £67,967 |
| 6 | ABC TRAVEL WOKINGHAM T A ABC TRAVEL | 24 | £63,141 |
| 7 | SOUTHERN COACH LINES | 16 | £55,532 |
| 8 | MARK DILLON T A PENMAR TRANSPORT | 15 | £35,282 |
| 9 | S RICHARDS T AS K RICKETTS S RICHARDS TAXIS | 8 | £17,144 |
| 10 | MRS M F RICHARDSON T A MFR CONTRACTS | 13 | £15,365 |
| 11 | N MEHMOOD T A A STAR EXECUTIVE CARS | 7 | £12,489 |
| 12 | ELITE SECURITY GROUP | 9 | £10,178 |
| 13 | NADEEM MIRZA TRADING AS PARKER TRAVELS | 7 | £9,928 |
| 14 | POTTINGER S HIRE SERVICE | 8 | £9,352 |

**PBC.** P-15, P-20, P-14, P-16, P-17

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

**PBC.** P-21, P-22

## R-06 Annualised spend above the awarded contract value without a recorded variation

Score 9 (likelihood 3 × impact 3), Medium - High (Amber) [matrix: High]. Sample size per test: 15.

### C-08 Expected control

A variation of a contract's scope or value has prior written approval from the Monitoring Officer and S151 Officer, or the relevant board above the Threshold [CPR-77] [CPR-78].

#### T-10

**Test step.** Place each award against the council's current Threshold figures to set the variation route: below the Threshold, prior written Monitoring Officer and S151 Officer approval [CPR-77]; above it, board approval on their recommendation [CPR-78]. For each flagged supplier, obtain the award and total spend to date under the contract, compare them, and where spend runs beyond the award obtain the variation approval [CPR-77] [CPR-78] or extension record [CPR-76]. Suppliers flagged: [`$.tests.spend_vs_award.counts.total`].

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

**PBC.** P-23, P-24, P-25, P-10

## R-07 Repeat payments of the same amount to the same supplier within a week

Score 15 (likelihood 3 × impact 5), Extreme (Red). Sample size per test: 25.

### C-09 Expected control

Every payment rests on written evidence of a distinct purchase: its own invoice and order, so the same charge is not paid twice [CPR-35].

#### T-11

**Test step.** For each sampled supplier and amount pair repeated on different dates, match each payment to a distinct invoice and purchase record [CPR-35]; where two payments share an invoice, obtain the credit note or recovery record. General procurement pairs flagged: [`$.tests.duplicates.different_dates.items_by_tag.general_procurement`].

**Sample.** 24 of 24 rows in `analytics-full/duplicates.csv` where type = different_dates; tag in general_procurement, agency_staff, grant, sorted by gbp_repeat_value descending, taking units from the top of the list. 57 transactions, £541,802 net, in `outputs/samples/T-11.csv`.
Why this sample: General procurement pairs, with agency staff and grants, split from premises so neither stratum's largest suppliers crowd out the other; largest repeat value first.

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
| 20 | PIED PIPER PRE SCHOOL | 2 | £1,600 |
| 21 | COMPASS EXECUTIVE CARS UK | 2 | £1,488 |
| 22 | READING REFUGEE SUPPORT GROUP | 2 | £1,486 |
| 23 | EDGE TRAINING AND CONSULTANCY | 2 | £1,400 |
| 24 | MR I GRAHAM T A COMMUNITY SAFETY TRAINING | 2 | £1,200 |

**PBC.** P-02, P-26

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

**PBC.** P-02, P-26

#### T-12

**Test step.** For each sampled placement pair repeated on different dates, confirm from the invoices and case records that each payment relates to a different client or period [CPR-35]. Placement pairs flagged: [`$.tests.duplicates.different_dates.items_by_tag.care_education_placement`].

**Sample.** 25 of 204 rows in `analytics-full/duplicates.csv` where type = different_dates; tag = care_education_placement, sorted by gbp_repeat_value descending, taking units at even intervals through the list. 111 transactions, £1,047,037 net, in `outputs/samples/T-12.csv`.
Why this sample: Placement pairs, which the register expects to be per-client fees; even steps through the repeat-value-sorted list, so the sample reaches more providers than the largest few.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | OAKLANDS SEN SCHOOL BERKSHIRE | 36 | £732,148 |
| 2 | CARE SERVICES TO YOU | 3 | £71,969 |
| 3 | THE UNICORN SCHOOL | 3 | £41,313 |
| 4 | CHILTERN WAY ACADEMY | 12 | £25,000 |
| 5 | FOREST BRIDGE SCHOOL | 2 | £28,313 |
| 6 | THE UNICORN SCHOOL | 2 | £23,990 |
| 7 | AFFINITY TRUST SUPPORT | 2 | £20,504 |
| 8 | AFFINITY TRUST SUPPORT | 4 | £10,560 |
| 9 | TOPLINE CARE SOLUTIONS | 4 | £9,097 |
| 10 | ISP CHILDCARE | 2 | £13,064 |
| 11 | AFFINITY TRUST SUPPORT | 3 | £8,316 |
| 12 | AFFINITY TRUST SUPPORT | 6 | £6,077 |
| 13 | AFFINITY TRUST SUPPORT | 2 | £9,330 |
| 14 | REDDY CARE | 2 | £8,476 |
| 15 | SUNBEAM FOSTERING AGENCY | 2 | £7,583 |
| 16 | ABI SUPPORT | 5 | £3,985 |
| 17 | CARE OUTLOOK | 2 | £5,919 |
| 18 | I V CARE T A GOOD OAKS HOME CARE READING | 5 | £3,188 |
| 19 | CHILTERN WAY ACADEMY | 2 | £4,474 |
| 20 | I V CARE T A GOOD OAKS HOME CARE READING | 2 | £3,825 |
| 21 | DEVELOP MY CHILD | 2 | £3,000 |
| 22 | ABI SUPPORT | 2 | £2,231 |
| 23 | YOUR SERENITY | 2 | £1,900 |
| 24 | PURESOUL CARE | 2 | £1,522 |
| 25 | GOLDCREST CARE SERVICES | 2 | £1,252 |

**PBC.** P-27, P-28

#### T-18

**Test step.** Obtain the unredacted listing of payments published with the supplier name redacted in the spend window (2,015 rows); select payments, largest first, and match each to a distinct invoice and purchase record [CPR-35].

**Sample.** Select 25 items from the council's unredacted listing of payments published as 'Redacted' in the spend window. The population sits in council records, so the builder draws nothing; record the items chosen in the working papers.
Why this sample: Redacted-supplier payments were excluded from every analytics test, so the population sits in council records.

**PBC.** P-29, P-02

#### T-21

**Test step.** For each sampled supplier and amount pair paid more than once in the same payment run, match each payment to a distinct invoice and purchase record [CPR-35]; where two payments share an invoice, obtain the credit note or recovery record. General procurement pairs in one run: [`$.tests.duplicates.same_timestamp.items_by_tag.general_procurement`]; premises: [`$.tests.duplicates.same_timestamp.items_by_tag.premises`].

**Sample.** 25 of 41 rows in `analytics-full/duplicates.csv` where type = same_timestamp; tag in general_procurement, premises, sorted by gbp_repeat_value descending, taking units from the top of the list. 58 transactions, £115,647 net, in `outputs/samples/T-21.csv`.
Why this sample: Same-run repeats outside placements, where one invoice keyed twice in a run is the indicator; placement same-run repeats are left out, as the register reads them as per-client payment runs. Largest repeat value first.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | ROADSIDE TECHNOLOGIES | 2 | £18,207 |
| 2 | ROADSIDE TECHNOLOGIES | 2 | £11,188 |
| 3 | SEISMIC SEWAGE SYSTEMS | 2 | £10,720 |
| 4 | BROADWAY CARS | 2 | £10,660 |
| 5 | KB REAL ESTATE MANAGEMENT | 3 | £5,400 |
| 6 | COMPASS EXECUTIVE CARS UK | 2 | £4,356 |
| 7 | DANIEL GRIFFITHS T A BLUEBIRD PASSENGER SERVICES | 2 | £4,100 |
| 8 | AMR CONSULT | 2 | £4,093 |
| 9 | GO GREEN TAXIS | 3 | £2,888 |
| 10 | PERCEPTIVE ON LINE T A AMATIS NETWORKS | 4 | £2,543 |
| 11 | FD TRAVELS T A SCHOOL EXPRESS | 2 | £3,772 |
| 12 | PERCEPTIVE ON LINE T A AMATIS NETWORKS | 4 | £2,403 |
| 13 | SPARE CRIB GLOBAL | 3 | £2,415 |
| 14 | DANIEL GRIFFITHS T A BLUEBIRD PASSENGER SERVICES | 2 | £3,000 |
| 15 | DANIEL GRIFFITHS T A BLUEBIRD PASSENGER SERVICES | 2 | £3,000 |
| 16 | COMPASS EXECUTIVE CARS UK | 2 | £2,970 |
| 17 | DANIEL GRIFFITHS T A BLUEBIRD PASSENGER SERVICES | 2 | £2,800 |
| 18 | BPR TRADING AS WE ARE LEAN AND AGILE | 2 | £2,800 |
| 19 | KB REAL ESTATE MANAGEMENT | 2 | £2,790 |
| 20 | COMPASS EXECUTIVE CARS UK | 2 | £2,772 |
| 21 | FD TRAVELS T A SCHOOL EXPRESS | 2 | £2,760 |
| 22 | SIMONE SURVEYS | 3 | £2,034 |
| 23 | KB REAL ESTATE MANAGEMENT | 2 | £2,700 |
| 24 | KB REAL ESTATE MANAGEMENT | 2 | £2,700 |
| 25 | FD TRAVELS T A SCHOOL EXPRESS | 2 | £2,576 |

**PBC.** P-02, P-26

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

**PBC.** P-03, P-30

## R-09 Waivers and exceptions to the Rules not approved or recorded in advance

Score 6 (likelihood 2 × impact 3), Moderate. Sample size per test: 8.

### C-11 Expected control

Waivers and exceptions are sought only in advance, granted by the Monitoring Officer or S151 Officer on recorded urgency or discretion grounds, fully documented, and reported to the relevant board or the Executive where required [CPR-21] [CPR-22] [CPR-23] [CPR-24] [CPR-27] [CPR-28] [CPR-29] [CPR-30].

#### T-14

**Test step.** From the waiver and exception register, take every waiver or exception for a contract above the Key Decision level first, then select from the rest granted in or before the spend window; for each, confirm the request predates the purchase [CPR-24], the grounds and written reasons are recorded [CPR-21] [CPR-22] [CPR-28], the S151 Officer approved and recorded the circumstances [CPR-23] [CPR-30], and any exception report went to the board or the Executive where required [CPR-29] [CPR-27]. Using the council's current Threshold figures, confirm each exception was approved at its tier: by the S151 Officer up to the Threshold [CPR-25], or, above it and up to the Key Decision level, after consulting the Monitoring Officer and Executive Director with a board-approved exception report [CPR-26].

**Sample.** Select 8 items from the council's waiver and exception register covering the spend window. The population sits in council records, so the builder draws nothing; record the items chosen in the working papers.
Why this sample: No spend test can see a waiver; the population sits in council records. Exceptions above the Key Decision level come first, as they carry the highest stakes.

**PBC.** P-11, P-31, P-10

#### T-15

**Test step.** For each sampled supplier above the publication threshold with no live notice, search the waiver and exception register; where a waiver is recorded, test it as in T-14 [CPR-23] [CPR-24]; where none is recorded, refer the supplier to the R-04 tests (T-07, T-19, T-20) [CPR-66]. Suppliers flagged: [`$.tests.off_contract.counts.total`].

**Sample.** 8 of 321 rows in `analytics-full/off_contract.csv` where tag not in care_education_placement, sorted by annualised_estimate descending, taking units at even intervals through the list. 180 transactions, £7,576,518 net, in `outputs/samples/T-15.csv`.
Why this sample: The cross-check the proposed focus asks for, over the R-04 population outside the placement tag; even steps through the list so it reaches beyond the largest suppliers T-07, T-19 and T-20 take.

| # | Supplier | Transactions | Net £ |
|---|---|---|---|
| 1 | VOLKERHIGHWAYS | 126 | £7,377,922 |
| 2 | THE NEWBURY COMMUNITY RESOURCE CENTRE | 31 | £89,248 |
| 3 | PRO AIR GB | 1 | £39,490 |
| 4 | KARD GROUP | 6 | £23,400 |
| 5 | AMR CONSULT | 8 | £16,150 |
| 6 | ENJOY TRAINING T AS REBEL BUSINESS SCHOOL | 2 | £12,950 |
| 7 | ELITE SYSTEMS GB | 1 | £9,678 |
| 8 | AERO PROPERTY CONSULTANTS | 5 | £7,680 |

**PBC.** P-11, P-31

## PBC list

Request these from the council before fieldwork.

| # | Item | For tests |
|---|---|---|
| P-01 | Procurement Portal quote record for each sampled payment | T-01, T-02 |
| P-02 | Purchase order and invoice for each sampled payment | T-01, T-03, T-04, T-05, T-11, T-17, T-18, T-21 |
| P-03 | Framework, block contract or case-note record of provider choice for each sampled placement | T-02, T-13 |
| P-04 | Procurement Portal quote record for each sampled payment group | T-03 |
| P-05 | Procurement advice on aggregation for each sampled supplier, if sought | T-03 |
| P-06 | Quote or written purchase evidence for each sampled payment | T-04 |
| P-07 | Quote or written purchase evidence for each sampled payment group | T-05 |
| P-08 | Contract under which each sampled supplier is paid | T-06, T-16 |
| P-09 | Executive approval for each sampled contract at the Executive tier | T-06 |
| P-10 | The council's current Threshold figures | T-06, T-16, T-07, T-19, T-20, T-10, T-14 |
| P-11 | Waiver and exception register covering the spend window | T-06, T-16, T-14, T-15 |
| P-12 | Tender and advertising record for each sampled contract | T-06, T-16 |
| P-13 | Key Decision record and award report for each sampled contract | T-16 |
| P-14 | Signed contract for each sampled supplier | T-07, T-20, T-08 |
| P-15 | Contract award notice for each sampled supplier | T-07, T-19, T-20, T-08 |
| P-16 | Contracts register entry for each sampled supplier | T-07, T-19, T-20, T-08 |
| P-17 | Procurement Portal quote record, approved waiver or Monitoring Officer exclusion approval for each sampled supplier with no contract | T-07, T-19, T-20, T-08 |
| P-18 | Award approval and award report for each sampled supplier's contract | T-07, T-19, T-20 |
| P-19 | Grant agreement for each sampled grant recipient | T-19 |
| P-20 | Framework or DPS access advice and call-off approval for each sampled supplier under a scheme | T-08 |
| P-21 | S151 extension approval for each sampled supplier | T-09 |
| P-22 | Current contract and award record for each sampled supplier | T-09 |
| P-23 | Contract and award value for each sampled supplier | T-10 |
| P-24 | Total spend to date under the contract for each sampled supplier | T-10 |
| P-25 | Variation or extension approval for each sampled supplier | T-10 |
| P-26 | Credit note or recovery record for any payment matched to an invoice already paid | T-11, T-17, T-21 |
| P-27 | Invoice for each sampled payment, with the client or period it covers | T-12 |
| P-28 | Placement or case record confirming the client and period for each sampled payment | T-12 |
| P-29 | Unredacted listing of payments published as 'Redacted' in the spend window | T-18 |
| P-30 | PSR decision record for each sampled supplier under the Provider Selection Regime | T-13 |
| P-31 | Waiver request, approval and exception report for each sampled waiver | T-14, T-15 |
