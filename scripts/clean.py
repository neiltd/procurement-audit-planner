"""Step 1: clean the monthly spend workbooks -> outputs/analytics-full/spend_clean.csv.

Every row read is either kept (with one tag) or excluded (with one reason). Writes
outputs/analytics-full/clean_meta.json for analyse.py to fold into analytics.json.
"""
import json
import re
import sys

import pandas as pd

from common import (EXPECTED_COLS, FULL, SHEET, SPEND_DIR, find_header_row, gbp,
                    normalise_supplier, sha256)
from tags import TAG_MAP, tag_row

PENSION_NARR = re.compile(r"\bLGPS\b|PENSION|DEFICIT CONTRIBUTION|\bAVC\b", re.I)
PUBLIC_NAME = re.compile(
    r"\bCOUNCIL\b|\bCNCL\b|\bROYAL BOROUGH OF\b|\bNHS\b|\bHMRC\b|\bHM REVENUE\b|\bPOLICE\b"
    r"|\bFIRE AND RESCUE\b|\bDEPARTMENT FOR\b|\bDEPT FOR\b|\bMINISTRY OF\b|\bHOME OFFICE\b"
    r"|\bCABINET OFFICE\b|\bHMCTS\b|\bOFSTED\b")
PUBLIC_NARR = re.compile(
    r"^Joint Arrangements \(with Other Local Authorities or NHS\)|^Payments to Other Local Authorities"
    r"|^Payments to NHS", re.I)

EXCLUSION_PATTERNS = {
    "redacted": "Supplier name == 'Redacted' after strip",
    "pension_statutory": PENSION_NARR.pattern + " on Narrative (AVC = pension additional voluntary contributions)",
    "public_body": "name: " + PUBLIC_NAME.pattern + " | narrative: " + PUBLIC_NARR.pattern,
}


def load_workbook(path):
    raw = pd.read_excel(path, sheet_name=SHEET, header=None)
    h = find_header_row(raw)
    if h is None:
        found = [str(v) for v in raw.iloc[0:5].values.ravel() if pd.notna(v)]
        sys.exit(f"STOP: {path.name}: header row with {EXPECTED_COLS} not found; values seen: {found}")
    header = [str(c).strip() for c in raw.iloc[h]]
    missing = [c for c in EXPECTED_COLS if c not in header]
    if missing:
        sys.exit(f"STOP: {path.name}: missing columns {missing}; found {header}")
    df = raw.iloc[h + 1:].copy()
    df.columns = header
    df = df[EXPECTED_COLS]
    df["sheet_row"] = df.index + 1  # raw 0-based index -> 1-based Excel row
    blank = df[EXPECTED_COLS].isna().all(axis=1)
    if blank.any():
        df = df[~blank]
    df["row_id"] = path.name + ":" + SHEET + ":" + df["sheet_row"].astype(str)
    df["source_file"] = path.name
    return df, h + 1, int(blank.sum())


def parse_dates(s, fname):
    is_dt = s.map(lambda v: isinstance(v, (pd.Timestamp,)) or hasattr(v, "year"))
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    out[is_dt] = pd.to_datetime(s[is_dt])
    if (~is_dt).any():
        out[~is_dt] = pd.to_datetime(s[~is_dt].astype(str).str.strip(), format="%m/%d/%y", errors="coerce")
    if out.isna().any():
        sys.exit(f"STOP: {fname}: {int(out.isna().sum())} unparseable dates")
    return out, int((~is_dt).sum())


def main():
    files = sorted(SPEND_DIR.glob("*.xlsx"))
    if not files:
        sys.exit("STOP: no data/spend/*.xlsx")
    FULL.mkdir(parents=True, exist_ok=True)
    frames, file_meta = [], []
    for f in files:
        df, header_row, n_blank = load_workbook(f)
        df["Date"], n_text = parse_dates(df["Date"], f.name)
        amt = pd.to_numeric(df["Net amount"], errors="coerce")
        if amt.isna().any():
            sys.exit(f"STOP: {f.name}: {int(amt.isna().sum())} non-numeric Net amount values")
        df["Net amount"] = amt.astype(float)
        file_meta.append({"file": f.name, "sha256": sha256(f), "header_row": header_row,
                          "rows_read": int(len(df)), "blank_rows_skipped": n_blank,
                          "text_dates_parsed_mdy": n_text})
        frames.append(df)
    d = pd.concat(frames, ignore_index=True)
    for c in ["Service", "Expenditure category", "Narrative", "Supplier name"]:
        d[c] = d[c].where(d[c].notna(), "").astype(str).str.strip()
    d["supplier_norm"] = d["Supplier name"].map(normalise_supplier)

    reason = pd.Series("", index=d.index)
    reason[d["Supplier name"] == "Redacted"] = "redacted"
    m = (reason == "") & d["Narrative"].str.contains(PENSION_NARR)
    reason[m] = "pension_statutory"
    m = (reason == "") & (d["supplier_norm"].str.contains(PUBLIC_NAME) | d["Narrative"].str.contains(PUBLIC_NARR))
    reason[m] = "public_body"
    d["exclusion_reason"] = reason

    excl = d[reason != ""]
    kept = d[reason == ""].copy()
    kept["tag"] = [tag_row(s, c, n) for s, c, n in
                   zip(kept["Service"], kept["Expenditure category"], kept["Narrative"])]

    # reconciliation per file
    for fm in file_meta:
        k = int((kept["source_file"] == fm["file"]).sum())
        e = int((excl["source_file"] == fm["file"]).sum())
        assert k + e == fm["rows_read"], (fm["file"], k, e, fm["rows_read"])
        fm["rows_kept"], fm["rows_excluded"] = k, e

    excl_agg = (excl.groupby(["exclusion_reason", "supplier_norm"])["Net amount"]
                .agg(rows="size", gbp="sum").reset_index().sort_values(["exclusion_reason", "gbp"],
                                                                      ascending=[True, False]))
    excl_agg["gbp"] = excl_agg["gbp"].round(2)
    excl_agg.to_csv(FULL / "exclusions.csv", index=False)

    cols = ["row_id", "source_file", "sheet_row", "Service", "Expenditure category", "Narrative",
            "Date", "Net amount", "Supplier name", "supplier_norm", "tag"]
    kept[cols].to_csv(FULL / "spend_clean.csv", index=False)

    combo = (kept.groupby(["Service", "Expenditure category", "Narrative", "tag"])["Net amount"]
             .agg(rows="size", gbp="sum").reset_index())
    combo["gbp"] = combo["gbp"].round(2)
    combo.to_csv(FULL / "tag_combinations.csv", index=False)

    exclusions = []
    for r in ["redacted", "pension_statutory", "public_body"]:
        x = excl[excl["exclusion_reason"] == r]
        exclusions.append({"reason": r, "rows": int(len(x)), "gbp": gbp(x["Net amount"].sum()),
                           "suppliers": int(x["supplier_norm"].nunique()), "pattern": EXCLUSION_PATTERNS[r]})
    tag_totals = {t: {"rows": int((kept["tag"] == t).sum()),
                      "gbp": gbp(kept.loc[kept["tag"] == t, "Net amount"].sum())}
                  for t in ["agency_staff", "grant", "premises", "care_education_placement", "general_procurement"]}
    meta = {
        "spend_files": file_meta,
        "rows_read": int(len(d)), "gbp_read": gbp(d["Net amount"].sum()),
        "exclusions": exclusions,
        "exclusions_full_list": "outputs/analytics-full/exclusions.csv",
        "rows_analysed": int(len(kept)), "gbp_analysed": gbp(kept["Net amount"].sum()),
        "negative_or_zero_rows_analysed": int((kept["Net amount"] <= 0).sum()),
        "notes": ["Grants kept (Rules 1.6.2 treat a grant as a contract).",
                  "SCHOOL/ACADEMY/NURSERY names kept: mostly independent SEN schools, early-years and care providers."],
        "tags": {"map": TAG_MAP, "priority": ["agency_staff", "grant", "premises",
                                              "care_education_placement", "general_procurement"],
                 "combinations_file": "outputs/analytics-full/tag_combinations.csv",
                 "totals": tag_totals},
        "date_min": str(kept["Date"].min().date()), "date_max": str(kept["Date"].max().date()),
    }
    (FULL / "clean_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    print(json.dumps({k: meta[k] for k in ["rows_read", "gbp_read", "exclusions", "rows_analysed",
                                           "gbp_analysed", "negative_or_zero_rows_analysed",
                                           "date_min", "date_max"]}, indent=1))
    print(json.dumps(tag_totals, indent=1))
    print([{k: fm[k] for k in ("file", "header_row", "rows_read", "rows_kept", "rows_excluded",
                               "blank_rows_skipped", "text_dates_parsed_mdy")} for fm in file_meta])


if __name__ == "__main__":
    main()
