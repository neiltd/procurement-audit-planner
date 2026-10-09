"""Step 3/4: run the seven risk-indicator tests and write outputs/analytics.json.

All thresholds come from outputs/rules.json. Results are indicators to investigate, not findings.
Run order: clean.py -> contracts.py -> analyse.py -> self_check.py.
"""
import difflib
import json
import sys
from collections import defaultdict

import pandas as pd

from common import CONTRACTS_CSV, FULL, OUT, RULES_JSON, gbp, sha256

TIER_TYPES = {"procedure", "approval", "anti-avoidance"}
DATA_FLOOR = 500  # published data covers payments over GBP 500
TAGS = ["agency_staff", "grant", "premises", "care_education_placement", "general_procurement"]
TOP_ROW_IDS = 10


# ---------------------------------------------------------------- rules / thresholds
def load_rules():
    if not RULES_JSON.exists():
        sys.exit("STOP: outputs/rules.json missing")
    return json.loads(RULES_JSON.read_text())


def find_rule(rules, clause, rtype):
    hits = [r for r in rules["rules"] if r.get("clause") == clause and r.get("type") == rtype]
    if len(hits) != 1 or not isinstance(hits[0].get("threshold_low"), (int, float)):
        sys.exit(f"STOP: expected one {rtype} rule at clause {clause!r} with numeric threshold_low; got {len(hits)}")
    r = hits[0]
    return {"value": r["threshold_low"], "low_inclusive": bool(r.get("threshold_low_inclusive")),
            "rule_id": r["rule_id"], "clause": clause, "type": rtype}


def rule_ids_where(rules, pred):
    return [r["rule_id"] for r in rules["rules"] if pred(r)]


def build_tiers(rules):
    params = rules.get("parameters", {})
    by_val = defaultdict(lambda: {"rule_ids": [], "inclusivity": {}})
    skipped = defaultdict(list)
    for r in rules["rules"]:
        if r.get("type") not in TIER_TYPES:
            continue
        lo, hi = r.get("threshold_low"), r.get("threshold_high")
        if isinstance(lo, (int, float)):
            t = by_val[lo]
            t["rule_ids"].append(r["rule_id"])
            t["inclusivity"][r["rule_id"] + ":low"] = bool(r.get("threshold_low_inclusive"))
        if isinstance(hi, (int, float)):
            # "less than X" -> X belongs to the next tier (low-inclusive); "up to X" -> low-exclusive
            t = by_val[hi]
            t["rule_ids"].append(r["rule_id"])
            t["inclusivity"][r["rule_id"] + ":high"] = not bool(r.get("threshold_high_inclusive"))
        for side in ("threshold_low_param", "threshold_high_param"):
            p = r.get(side)
            if p and (params.get(p, {}) or {}).get("value") is None:
                skipped[p].append(r["rule_id"])
    tiers, dropped = [], []
    for v in sorted(by_val):
        info = by_val[v]
        rids = sorted(set(info["rule_ids"]))
        if v <= DATA_FLOOR:
            dropped.append({"value": v, "rule_ids": rids,
                            "reason": f"at or below GBP {DATA_FLOOR}: published spend starts above GBP {DATA_FLOOR}"})
            continue
        incl = set(info["inclusivity"].values())
        tier = {"value": v, "rule_ids": rids, "inclusivity_by_rule_bound": info["inclusivity"]}
        if len(incl) == 1:
            tier["low_inclusive"] = incl.pop()
        else:
            tier["low_inclusive"] = "mixed"
            tier["mixed_handling"] = ("rules disagree on whether the boundary value sits in the upper tier; "
                                      "clustering band is closed [0.9T, T]; split test uses payments < T and total >= T")
        tiers.append(tier)
    skipped_list = [{"param": p, "rule_ids": sorted(set(rids)), "reason": "figure not supplied (intranet)"}
                    for p, rids in sorted(skipped.items())]
    return tiers, dropped, skipped_list


def band_mask(amt, tier):
    T = tier["value"]
    lo = 0.9 * T
    if tier["low_inclusive"] is True:
        return (amt >= lo) & (amt < T)
    return (amt >= lo) & (amt <= T)


def below(amt, tier):
    return amt < tier["value"] if tier["low_inclusive"] is not False else amt <= tier["value"]


def reaches(total, tier):
    return total >= tier["value"] if tier["low_inclusive"] is not False else total > tier["value"]


def meets(v, thr):
    return v >= thr["value"] if thr["low_inclusive"] else v > thr["value"]


# ---------------------------------------------------------------- helpers
def summarise(df, gbp_col, tag_col="tag"):
    counts = {"total": int(len(df)),
              "by_tag": {t: int((df[tag_col] == t).sum()) for t in TAGS if (df[tag_col] == t).any()}}
    money = {"total": gbp(df[gbp_col].sum()) if len(df) else 0.0,
             "by_tag": {t: gbp(df.loc[df[tag_col] == t, gbp_col].sum()) for t in TAGS if (df[tag_col] == t).any()}}
    return counts, money


def top20(df, gbp_col, cols):
    if not len(df):
        return []
    t = df.sort_values(gbp_col, ascending=False).head(20)
    out = []
    for _, r in t.iterrows():
        d = {}
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                v = gbp(v)
            elif isinstance(v, pd.Timestamp):
                v = str(v.date())
            elif hasattr(v, "item"):
                v = v.item()
            d[c] = v
        if "row_ids" in d and isinstance(d["row_ids"], str):
            ids = d["row_ids"].split(";")
            d["row_ids"] = ids[:TOP_ROW_IDS]
            if len(ids) > TOP_ROW_IDS:
                d["row_ids_note"] = f"{TOP_ROW_IDS} largest of {len(ids)}; full list in CSV"
        out.append(d)
    return out


def write(df, name):
    p = FULL / f"{name}.csv"
    df.to_csv(p, index=False)
    return f"outputs/analytics-full/{name}.csv"


def skipped(reason, rule_ids=None):
    return {"status": "skipped", "reason": reason, "rule_ids": rule_ids or []}


# ---------------------------------------------------------------- main
def main():
    rules = load_rules()
    cmeta_p = FULL / "clean_meta.json"
    if not cmeta_p.exists():
        sys.exit("STOP: run clean.py first")
    cmeta = json.loads(cmeta_p.read_text())
    sp = pd.read_csv(FULL / "spend_clean.csv", parse_dates=["Date"])
    sp["amount"] = sp["Net amount"].astype(float)

    months = len(cmeta["spend_files"])
    factor = 12 / months
    ws, we = sp["Date"].min().normalize(), sp["Date"].max().normalize()
    has_time = bool((sp["Date"] != sp["Date"].dt.normalize()).any())

    quote = find_rule(rules, "App B row B1", "procedure")
    pub = find_rule(rules, "App B row B1", "publication")
    tiers, dropped_tiers, skipped_tiers = build_tiers(rules)
    anti = rule_ids_where(rules, lambda r: r.get("type") == "anti-avoidance")
    app_c_d = rule_ids_where(rules, lambda r: r.get("clause") == "App C row D")
    app_c_e = rule_ids_where(rules, lambda r: r.get("clause") == "App C row E")
    tier_rids = sorted({x for t in tiers for x in t["rule_ids"]})

    # supplier-level frame (used by several tests)
    by_sup_tag = sp.groupby(["supplier_norm", "tag"])["amount"].sum().reset_index()
    dom_tag = by_sup_tag.sort_values("amount", ascending=False).drop_duplicates("supplier_norm") \
        .set_index("supplier_norm")["tag"]
    sp_sorted = sp.sort_values("amount", ascending=False)
    sup = sp.groupby("supplier_norm").agg(total_3m=("amount", "sum"), payments=("amount", "size"),
                                          first_date=("Date", "min"), last_date=("Date", "max"),
                                          supplier_name_example=("Supplier name", "first"))
    sup["tags"] = sp.groupby("supplier_norm")["tag"].agg(lambda s: ";".join(sorted(set(s))))
    sup["row_ids"] = sp_sorted.groupby("supplier_norm")["row_id"].agg(lambda s: ";".join(s))
    sup["tag"] = dom_tag
    sup["annualised_estimate"] = sup["total_3m"] * factor
    sup = sup.reset_index()

    tests = {}

    # 1 threshold_clustering ------------------------------------------------
    parts = []
    for t in tiers:
        m = band_mask(sp["amount"], t)
        x = sp[m].copy()
        x["tier"] = t["value"]
        x["band"] = (f"[{0.9 * t['value']:.2f}, {t['value']})" if t["low_inclusive"] is True
                     else f"[{0.9 * t['value']:.2f}, {t['value']}]")
        x["tier_rule_ids"] = ";".join(t["rule_ids"])
        parts.append(x)
    tc = pd.concat(parts) if parts else sp.head(0).assign(tier=[], band=[], tier_rule_ids=[])
    tc = tc.sort_values("amount", ascending=False)
    cols = ["row_id", "supplier_norm", "Supplier name", "tag", "Service", "Narrative", "Date", "amount",
            "tier", "band", "tier_rule_ids"]
    counts, money = summarise(tc, "amount")
    by_tier = {str(t["value"]): {"rows": int((tc["tier"] == t["value"]).sum()),
                                 "gbp": gbp(tc.loc[tc["tier"] == t["value"], "amount"].sum())} for t in tiers}
    tests["threshold_clustering"] = {
        "status": "ran", "rule_ids": sorted(set(tier_rids + anti)),
        "parameters": {"tiers": [t["value"] for t in tiers], "band": "[0.9T, T) if low bound inclusive, [0.9T, T] if exclusive"},
        "counts": counts, "gbp": money, "by_tier": by_tier,
        "top20": top20(tc, "amount", ["row_id", "supplier_norm", "tag", "Date", "amount", "tier"]),
        "full_list": write(tc[cols], "threshold_clustering")}

    # 2 split_purchases -----------------------------------------------------
    WINDOW_DAYS = 30
    groups = []
    for t in tiers:
        elig = sp[below(sp["amount"], t)]
        for s, g in elig.groupby("supplier_norm"):
            if len(g) < 2:
                continue
            g = g.sort_values(["Date", "row_id"])
            dates = g["Date"].dt.normalize().values  # calendar-day gaps
            amts = g["amount"].values
            idx = g.index.values
            cands = []
            for i in range(len(g)):
                end = dates[i] + pd.Timedelta(days=WINDOW_DAYS).to_timedelta64()
                j = i
                while j + 1 < len(g) and dates[j + 1] <= end:
                    j += 1
                if j > i:
                    tot = amts[i:j + 1].sum()
                    if reaches(tot, t):
                        cands.append((tot, j - i + 1, set(idx[i:j + 1])))
            cands.sort(key=lambda c: (-c[0], -c[1]))
            used = set()
            for tot, n, members in cands:
                if members & used:
                    continue
                used |= members
                rows = sp.loc[sorted(members)].sort_values("amount", ascending=False)
                tag_amt = rows.groupby("tag")["amount"].sum().sort_values(ascending=False)
                groups.append({
                    "tier": t["value"], "supplier_norm": s, "tag": tag_amt.index[0],
                    "tags": ";".join(sorted(rows["tag"].unique())), "payments": int(n),
                    "group_total": float(tot), "max_payment": float(rows["amount"].max()),
                    "first_date": rows["Date"].min(), "last_date": rows["Date"].max(),
                    "span_days": int((rows["Date"].max().normalize() - rows["Date"].min().normalize()).days),
                    "same_timestamp": bool(rows["Date"].nunique() == 1),
                    "row_ids": ";".join(rows["row_id"]), "tier_rule_ids": ";".join(t["rule_ids"])})
    spg = pd.DataFrame(groups)
    if len(spg):
        spg = spg.sort_values("group_total", ascending=False)
        counts, money = summarise(spg, "group_total")
        by_tier = {str(t["value"]): {"groups": int((spg["tier"] == t["value"]).sum()),
                                     "gbp": gbp(spg.loc[spg["tier"] == t["value"], "group_total"].sum()),
                                     "same_timestamp_groups": int(((spg["tier"] == t["value"]) & spg["same_timestamp"]).sum())}
                   for t in tiers}
    else:
        counts, money, by_tier = {"total": 0, "by_tag": {}}, {"total": 0.0, "by_tag": {}}, {}
    tests["split_purchases"] = {
        "status": "ran", "rule_ids": sorted(set(anti + tier_rids)),
        "parameters": {"window_days": WINDOW_DAYS, "window_rule": "last payment calendar date - first payment calendar date <= 30 days",
                       "min_payments": 2, "tiers": [t["value"] for t in tiers],
                       "dedupe": "per supplier and tier, non-overlapping groups taken largest total first"},
        "counts": counts, "gbp": money, "by_tier": by_tier,
        "same_timestamp_groups": int(spg["same_timestamp"].sum()) if len(spg) else 0,
        "gbp_note": "gbp = sum of group totals; a payment can appear in groups for different tiers",
        "top20": top20(spg, "group_total", ["supplier_norm", "tag", "tier", "payments", "group_total",
                                            "first_date", "last_date", "same_timestamp", "row_ids"]),
        "full_list": write(spg, "split_purchases") if len(spg) else write(pd.DataFrame(columns=["tier"]), "split_purchases")}

    # notices ---------------------------------------------------------------
    contracts_present = CONTRACTS_CSV.exists() and (FULL / "notices.csv").exists()
    cm = json.loads((FULL / "contracts_meta.json").read_text()) if (FULL / "contracts_meta.json").exists() else {"present": False}
    if contracts_present:
        nt = pd.read_csv(FULL / "notices.csv", parse_dates=["start_date", "end_date", "awarded_date"])
        nt["supplier_norm"] = nt["supplier_norm"].fillna("")
        live = nt[nt["live"]]
        live_names = set(live["supplier_norm"])
        all_names = set(nt["supplier_norm"])

        def candidates_for(name):
            out = []
            for nn in sorted(set(live["supplier_norm"])):
                if not nn or nn == name:
                    continue
                ratio = difflib.SequenceMatcher(None, name, nn).ratio()
                short = min(len(name), len(nn))
                contained = short >= 6 and (name in nn or nn in name)
                if ratio >= 0.85 or contained:
                    out.append((nn, round(ratio, 3), "ratio>=0.85" if ratio >= 0.85 else "contained>=6"))
            return out

    # 3 off_contract ----------------------------------------------------------
    pop = sup[sup["annualised_estimate"].map(lambda v: meets(v, pub))].copy()
    if contracts_present:
        pop["exact_live_match"] = pop["supplier_norm"].isin(live_names)
        oc = pop[~pop["exact_live_match"]].copy()
        cand_rows = []
        for s in oc["supplier_norm"]:
            for nn, ratio, how in candidates_for(s):
                ids = live.loc[live["supplier_norm"] == nn, "notice_id"].unique()
                cand_rows.append({"supplier_norm": s, "notice_supplier_norm": nn, "ratio": ratio,
                                  "method": how, "notice_ids": ";".join(ids)})
        cands = pd.DataFrame(cand_rows, columns=["supplier_norm", "notice_supplier_norm", "ratio", "method", "notice_ids"])
        cands.to_csv(FULL / "off_contract_candidates.csv", index=False)
        oc["has_candidate"] = oc["supplier_norm"].isin(set(cands["supplier_norm"]))
        oc["exact_match_expired_notice_only"] = oc["supplier_norm"].isin(all_names)
        oc = oc.sort_values("total_3m", ascending=False)
        counts, money = summarise(oc, "total_3m")
        tests["off_contract"] = {
            "status": "ran", "rule_ids": [pub["rule_id"], quote["rule_id"]],
            "parameters": {"publication_threshold": pub["value"], "comparison": ">=" if pub["low_inclusive"] else ">",
                           "basis": "annualised estimate (3-month total x annualise_factor)",
                           "match": "exact normalised name to a live notice; candidates (difflib ratio >= 0.85 or "
                                    "containment >= 6 chars) listed separately and stay unmatched"},
            "population_note": "Contracts Finder publishes only above about GBP 25,000; only suppliers whose annualised "
                               "estimate reaches the publication threshold are tested. Smaller suppliers are never questioned.",
            "export_coverage_note": "The notice export covers publication dates from 2021 only; long-running contracts "
                                    "awarded earlier have no notice here, so 'no live notice found' is a prompt to "
                                    "request contract evidence, not evidence that none exists.",
            "population": {"suppliers_tested": int(len(pop)), "exact_live_match": int(pop["exact_live_match"].sum())},
            "counts": counts, "gbp": money,
            "gbp_annualised_estimate": gbp(oc["annualised_estimate"].sum()),
            "with_candidate_name": int(oc["has_candidate"].sum()),
            "candidate_pairs": int(len(cands)),
            "candidates_list": "outputs/analytics-full/off_contract_candidates.csv",
            "top20": top20(oc, "total_3m", ["supplier_norm", "tag", "total_3m", "annualised_estimate", "payments",
                                            "has_candidate", "row_ids"]),
            "full_list": write(oc[["supplier_norm", "supplier_name_example", "tag", "tags", "total_3m",
                                   "annualised_estimate", "payments", "has_candidate",
                                   "exact_match_expired_notice_only", "row_ids"]], "off_contract")}
    else:
        tests["off_contract"] = skipped("data/contracts.csv not present: notice match not possible", [pub["rule_id"]])

    # 4 duplicates ------------------------------------------------------------
    d = sp.copy()
    d["day"] = d["Date"].dt.normalize()
    keycols = ["supplier_norm", "amount"]
    same = d.groupby(keycols + ["Date"]).filter(lambda g: len(g) >= 2)
    st_items = (same.sort_values("row_id").groupby(keycols + ["Date"])
                .agg(rows=("row_id", "size"), tag=("tag", lambda s: s.value_counts().index[0]),
                     row_ids=("row_id", ";".join)).reset_index())
    st_items["type"] = "same_timestamp"
    st_items["first_date"] = st_items["Date"]
    st_items["last_date"] = st_items["Date"]
    st_items["distinct_dates"] = 1
    # different dates: link distinct dates for the same supplier+amount with gaps <= 7 days
    dd_rows = []
    for (s, a), g in d.groupby(keycols):
        dates = sorted(g["Date"].unique())
        if len(dates) < 2:
            continue
        clusters, cur = [], [dates[0]]
        for x in dates[1:]:
            if (pd.Timestamp(x).normalize() - pd.Timestamp(cur[-1]).normalize()) <= pd.Timedelta(days=7):
                cur.append(x)
            else:
                clusters.append(cur)
                cur = [x]
        clusters.append(cur)
        for c in clusters:
            if len(c) < 2:
                continue
            rows = g[g["Date"].isin(c)].sort_values(["Date", "row_id"])
            dd_rows.append({"supplier_norm": s, "amount": a, "rows": int(len(rows)),
                            "tag": rows["tag"].value_counts().index[0], "row_ids": ";".join(rows["row_id"]),
                            "type": "different_dates", "first_date": rows["Date"].min(),
                            "last_date": rows["Date"].max(), "distinct_dates": len(c)})
    dd_items = pd.DataFrame(dd_rows, columns=["supplier_norm", "amount", "rows", "tag", "row_ids", "type",
                                              "first_date", "last_date", "distinct_dates"])
    dup = pd.concat([st_items.drop(columns=["Date"]), dd_items], ignore_index=True)
    dup["gbp_rows_total"] = dup["amount"] * dup["rows"]
    dup["gbp_repeat_value"] = dup["amount"] * (dup["rows"] - 1)
    dup = dup.sort_values("gbp_rows_total", ascending=False)
    counts, money = summarise(dup, "gbp_rows_total")
    split = {}
    for typ in ["same_timestamp", "different_dates"]:
        x = dup[dup["type"] == typ]
        c, m = summarise(x, "gbp_rows_total")
        split[typ] = {"items": int(len(x)), "rows": int(x["rows"].sum()), "gbp_rows_total": m["total"],
                      "gbp_repeat_value": gbp(x["gbp_repeat_value"].sum()), "items_by_tag": c["by_tag"],
                      "gbp_by_tag": m["by_tag"],
                      "top20": top20(x, "gbp_rows_total", ["supplier_norm", "tag", "amount", "rows", "first_date",
                                                           "last_date", "gbp_rows_total", "row_ids"])}
    tests["duplicates"] = {
        "status": "ran", "rule_ids": [],
        "rule_note": "payment-control indicator; no Contract Procedure Rule sets this test",
        "parameters": {"window_days": 7, "key": "normalised supplier + identical net amount",
                       "same_timestamp": "identical Date value (one payment run)",
                       "different_dates": "distinct payment timestamps chained with calendar-day gaps <= 7 (may include two runs on one day)",
                       "date_has_time_component": has_time},
        "counts": counts, "gbp": money,
        "gbp_note": "gbp = amount x rows in each item; gbp_repeat_value = amount x (rows - 1). An item of each type can share rows.",
        "same_timestamp": {k: v for k, v in split["same_timestamp"].items()},
        "different_dates": {k: v for k, v in split["different_dates"].items()},
        "top20": top20(dup, "gbp_rows_total", ["type", "supplier_norm", "tag", "amount", "rows", "first_date",
                                               "gbp_rows_total", "row_ids"]),
        "full_list": write(dup[["type", "supplier_norm", "tag", "amount", "rows", "distinct_dates", "first_date",
                                "last_date", "gbp_rows_total", "gbp_repeat_value", "row_ids"]], "duplicates")}

    # 5 expired_notice_spend --------------------------------------------------
    if contracts_present:
        matched = nt[nt["supplier_norm"].isin(set(sup["supplier_norm"]))]
        agg = matched.groupby("supplier_norm").agg(
            notices=("notice_id", lambda s: ";".join(sorted(set(s)))), n_notices=("notice_id", "nunique"),
            any_live=("live", "any"), latest_end=("end_date", "max"),
            any_blank_end=("end_date", lambda s: bool(s.isna().any())))
        exp = agg[(~agg["any_live"]) & (~agg["any_blank_end"]) & (agg["latest_end"] < ws)].reset_index()
        exp = exp.merge(sup[["supplier_norm", "tag", "tags", "total_3m", "annualised_estimate", "payments",
                             "first_date", "last_date", "row_ids"]], on="supplier_norm")
        exp["days_since_end_at_first_payment"] = (exp["first_date"] - exp["latest_end"]).dt.days
        exp = exp.sort_values("total_3m", ascending=False)
        counts, money = summarise(exp, "total_3m")
        tests["expired_notice_spend"] = {
            "status": "ran", "rule_ids": app_c_d,
            "parameters": {"window_start": str(ws.date()), "match": "exact normalised name, all matched notices",
                           "condition": "every matched notice End Date < window start"},
            "note": "Indicator for App C row D (extension needs S151 approval); a newer contract may exist without a notice.",
            "matched_suppliers": int(len(agg)),
            "counts": counts, "gbp": money,
            "top20": top20(exp, "total_3m", ["supplier_norm", "tag", "total_3m", "annualised_estimate", "latest_end",
                                             "notices", "row_ids"]),
            "full_list": write(exp, "expired_notice_spend")}
    else:
        tests["expired_notice_spend"] = skipped("data/contracts.csv not present", app_c_d)

    # 6 spend_vs_award --------------------------------------------------------
    RATIO_FLAG = 1.25
    if contracts_present:
        lm = live[live["supplier_norm"].isin(set(sup["supplier_norm"]))]
        per = lm.groupby("supplier_norm")["notice_id"].nunique()
        one = per[per == 1].index
        e = lm[lm["supplier_norm"].isin(one) & (lm["n_suppliers"] == 1) & (lm["awarded_value"] > 0)
               & lm["start_date"].notna() & lm["end_date"].notna()].copy()
        e["years"] = (e["end_date"] - e["start_date"]).dt.days / 365.25
        e = e[e["years"] > 0]
        e = e.merge(sup[["supplier_norm", "tag", "total_3m", "annualised_estimate", "payments", "row_ids"]],
                    on="supplier_norm")
        e["award_per_year"] = e["awarded_value"] / e["years"]
        e["ratio"] = e["annualised_estimate"] / e["award_per_year"]
        e = e.sort_values("ratio", ascending=False)
        e.to_csv(FULL / "spend_vs_award_eligible.csv", index=False)
        fl = e[e["ratio"] >= RATIO_FLAG].sort_values("total_3m", ascending=False)
        counts, money = summarise(fl, "total_3m")
        tests["spend_vs_award"] = {
            "status": "ran", "rule_ids": app_c_e,
            "parameters": {"ratio_flag": RATIO_FLAG, "years": "(End - Start).days / 365.25",
                           "ratio": "annualised estimate / (Awarded Value / years)",
                           "eligible": "exact match to exactly one live notice, single supplier, Awarded Value > 0"},
            "note": "Indicator for App C row E (variation approval); award values may be estimates or maxima.",
            "eligible_suppliers": int(len(e)), "eligible_list": "outputs/analytics-full/spend_vs_award_eligible.csv",
            "counts": counts, "gbp": money,
            "top20": top20(fl, "total_3m", ["supplier_norm", "tag", "notice_id", "awarded_value", "years",
                                            "annualised_estimate", "ratio", "row_ids"]),
            "full_list": write(fl[["supplier_norm", "tag", "notice_id", "title", "start_date", "end_date",
                                   "awarded_value", "years", "award_per_year", "total_3m", "annualised_estimate",
                                   "ratio", "payments", "row_ids"]], "spend_vs_award")}
    else:
        tests["spend_vs_award"] = skipped("data/contracts.csv not present", app_c_e)

    # 7 high_value_suppliers --------------------------------------------------
    hv = sup[sup["annualised_estimate"].map(lambda v: meets(v, quote))].copy()
    if contracts_present:
        cand_set = set(pd.read_csv(FULL / "off_contract_candidates.csv")["supplier_norm"]) \
            if (FULL / "off_contract_candidates.csv").exists() else set()
        extra = {}
        for s in hv["supplier_norm"]:
            if s not in live_names and s not in cand_set and candidates_for(s):
                extra[s] = True
        hv["notice_match"] = ["exact" if s in live_names else
                              ("candidate" if (s in cand_set or s in extra) else "none")
                              for s in hv["supplier_norm"]]
        hv["exact_match_expired_notice_only"] = hv["supplier_norm"].map(lambda s: s not in live_names and s in all_names)
    else:
        hv["notice_match"] = "not_checked"
    hv = hv.sort_values("total_3m", ascending=False)
    counts, money = summarise(hv, "total_3m")
    tests["high_value_suppliers"] = {
        "status": "ran", "rule_ids": sorted({quote["rule_id"], pub["rule_id"]}),
        "parameters": {"quote_threshold": quote["value"], "comparison": ">=" if quote["low_inclusive"] else ">",
                       "basis": "annualised estimate"},
        "counts": counts, "gbp": money,
        "gbp_annualised_estimate": gbp(hv["annualised_estimate"].sum()),
        "notice_match": hv["notice_match"].value_counts().to_dict(),
        "top20": top20(hv, "total_3m", ["supplier_norm", "tag", "total_3m", "annualised_estimate", "payments",
                                        "notice_match", "row_ids"]),
        "full_list": write(hv[["supplier_norm", "supplier_name_example", "tag", "tags", "total_3m",
                               "annualised_estimate", "payments", "notice_match"]
                              + (["exact_match_expired_notice_only"] if contracts_present else [])
                              + ["row_ids"]], "high_value_suppliers")}

    # ---------------------------------------------------------------- JSON
    contracts_block = {"present": bool(cm.get("present"))}
    if cm.get("present"):
        contracts_block.update({k: cm.get(k) for k in [
            "raw_rows", "kept", "dropped", "dropped_org_names", "kept_by_org_name_as_written", "live_in_window",
            "kept_by_year", "warnings", "supplier_rows", "notices_with_empty_supplier",
            "zero_award_value_notices", "join_note", "sha256"]})
        contracts_block["notes"] = []
        cy = pd.Timestamp.now().year
        if str(cy) in {str(k) for k in cm.get("kept_by_year", {})}:
            contracts_block["notes"].append(
                f"{cy} is a partial publication year ({cm['kept_by_year'].get(str(cy), cm['kept_by_year'].get(cy))} "
                "kept notices); not tested against the <5 warning.")
        contracts_block["full_list"] = "outputs/analytics-full/notices.csv"
    else:
        contracts_block["reason"] = cm.get("reason", "data/contracts.csv not found")

    for name in tests:
        if tests[name]["status"] == "skipped":
            continue
    analytics = {
        "inputs": {"spend_files": [{k: f[k] for k in ("file", "sha256", "header_row", "rows_read", "rows_kept",
                                                      "rows_excluded", "blank_rows_skipped", "text_dates_parsed_mdy")}
                                   for f in cmeta["spend_files"]],
                   "contracts": contracts_block,
                   "rules_sha256": sha256(RULES_JSON)},
        "window": {"start": str(ws.date()), "end": str(we.date()), "months": months,
                   "annualise_factor": round(factor, 4),
                   "annualised_label": "annualised estimate = 3-month total x annualise_factor"},
        "cleaning": {"rows_read": cmeta["rows_read"], "gbp_read": cmeta["gbp_read"],
                     "exclusions": cmeta["exclusions"], "exclusions_full_list": cmeta["exclusions_full_list"],
                     "rows_analysed": cmeta["rows_analysed"], "gbp_analysed": cmeta["gbp_analysed"],
                     "notes": cmeta["notes"], "full_list": "outputs/analytics-full/spend_clean.csv"},
        "tags": cmeta["tags"],
        "thresholds": {"quote_threshold": quote, "publication_threshold": pub, "tiers": tiers,
                       "dropped_tiers": dropped_tiers if dropped_tiers else [],
                       "dropped_tiers_note": f"tiers at or below GBP {DATA_FLOOR} are dropped (data starts above GBP {DATA_FLOOR}); "
                                             f"{len(dropped_tiers)} dropped",
                       "skipped": skipped_tiers,
                       "source": "outputs/rules.json; tiers from numeric threshold_low/threshold_high on procedure, approval and anti-avoidance rules"},
        "tests": tests,
        "language_note": "All results are risk indicators to investigate. None states or implies wrongdoing.",
    }
    prev = OUT / "analytics.json"
    if prev.exists():
        old = json.loads(prev.read_text())
        if "self_check" in old:
            analytics["self_check"] = {"script": "scripts/self_check.py", "result": "PENDING (re-run after analyse.py)"}
    (OUT / "analytics.json").write_text(json.dumps(analytics, indent=2, default=str))

    # console summary (aggregates only)
    print("window", ws.date(), we.date(), "months", months, "factor", factor, "time component:", has_time)
    print("tiers", [(t["value"], t["low_inclusive"]) for t in tiers], "dropped", dropped_tiers)
    print("skipped tiers", [(s["param"], s["rule_ids"]) for s in skipped_tiers])
    for k, v in tests.items():
        if v["status"] == "ran":
            print(k, v["counts"]["total"], v["gbp"]["total"], v["counts"]["by_tag"])
        else:
            print(k, "SKIPPED", v["reason"])


if __name__ == "__main__":
    main()
