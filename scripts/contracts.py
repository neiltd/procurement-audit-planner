"""Step 2: parse the raw Contracts Finder export -> outputs/analytics-full/notices.csv (one row per
(notice, supplier)) and contracts_meta.json. Needs the spend window start from spend_clean.csv."""
import json
import sys

import pandas as pd

from common import CONTRACTS_CSV, FULL, normalise_supplier, sha256

SUPPLIER_COL = "Supplier [Name|Address|Ref type|Ref Number|Is SME|Is VCSE]"
KEEP_ORGS = {"WEST BERKSHIRE COUNCIL", "WEST BERKSHIRE"}
EXPORT_CAP = 1000


def parse_blocks(s):
    if s is None or (isinstance(s, float) and pd.isna(s)) or not str(s).strip():
        return []
    s = str(s).strip()
    if s.startswith("["):
        s = s[1:]
    if s.endswith("]"):
        s = s[:-1]
    out = []
    for blk in s.split("]["):
        parts = blk.split("|")
        if len(parts) != 6:
            raise ValueError(f"supplier block has {len(parts)} parts, expected 6: {blk[:80]!r}")
        out.append(parts)
    return out


def main(window_start=None):
    meta = {"present": CONTRACTS_CSV.exists()}
    if not CONTRACTS_CSV.exists():
        meta["reason"] = "data/contracts.csv not found"
        (FULL / "contracts_meta.json").write_text(json.dumps(meta, indent=2))
        print("contracts.csv absent; notice tests will be skipped")
        return meta
    if window_start is None:
        sc = pd.read_csv(FULL / "spend_clean.csv", usecols=["Date"], parse_dates=["Date"])
        window_start = sc["Date"].min().normalize()
    raw = pd.read_csv(CONTRACTS_CSV, dtype=str, keep_default_na=False)
    meta["sha256"] = sha256(CONTRACTS_CSV)
    meta["raw_rows"] = int(len(raw))
    org = raw["Organisation Name"].str.strip().str.upper()
    keep = org.isin(KEEP_ORGS)
    k = raw[keep].copy()
    meta["kept"] = int(keep.sum())
    meta["dropped"] = int((~keep).sum())
    meta["kept_by_org_name_as_written"] = raw.loc[keep, "Organisation Name"].value_counts().to_dict()
    meta["dropped_org_names"] = raw.loc[~keep, "Organisation Name"].value_counts().to_dict()

    for c in ["Start Date", "End Date", "Awarded Date"]:
        v = k[c].str.strip()
        k[c] = pd.to_datetime(v.where(v != ""), format="%d/%m/%Y", errors="coerce")
        bad = (v != "") & k[c].isna()
        if bad.any():
            sys.exit(f"STOP: contracts.csv {c}: {int(bad.sum())} values not %d/%m/%Y")
    pv = k["Published Date"].str.strip()
    k["Published Date"] = pd.to_datetime(pv.where(pv != ""), utc=True, format="ISO8601")
    av = k["Awarded Value"].str.strip().str.replace(",", "", regex=False)
    k["Awarded Value"] = pd.to_numeric(av.where(av != ""), errors="raise")

    ws = pd.Timestamp(window_start)
    k["live"] = k["End Date"].isna() | (k["End Date"] >= ws)

    rows, empty = [], []
    for _, r in k.iterrows():
        blocks = parse_blocks(r[SUPPLIER_COL])
        if not blocks:
            empty.append(r["Notice Identifier"])
            continue
        for i, p in enumerate(blocks):
            rows.append({
                "notice_id": r["Notice Identifier"], "block": i + 1, "n_suppliers": len(blocks),
                "supplier_raw": p[0].strip(), "supplier_norm": normalise_supplier(p[0]),
                "ref_type": p[2].strip(),
                "ch_number": p[3].strip() if p[2].strip().upper() == "COMPANIES_HOUSE" else "",
                "title": r["Title"], "org": r["Organisation Name"],
                "start_date": r["Start Date"], "end_date": r["End Date"], "awarded_date": r["Awarded Date"],
                "published_date": r["Published Date"], "awarded_value": r["Awarded Value"], "live": r["live"],
            })
    n = pd.DataFrame(rows)
    # CH number used only to merge duplicate suppliers within a notice
    n["dedup_key"] = n["ch_number"].where(n["ch_number"] != "", n["supplier_norm"])
    before = len(n)
    n = n.drop_duplicates(["notice_id", "dedup_key"])
    n["n_suppliers"] = n.groupby("notice_id")["dedup_key"].transform("size")
    meta["supplier_rows"] = int(len(n))
    meta["supplier_rows_merged_by_ch_number_or_name"] = int(before - len(n))
    meta["notices_with_empty_supplier"] = empty
    meta["notices_with_supplier"] = int(n["notice_id"].nunique())
    assert meta["notices_with_supplier"] + len(empty) == meta["kept"]
    meta["live_in_window"] = int(k["live"].sum())
    meta["zero_award_value_notices"] = int((k["Awarded Value"].fillna(0) == 0).sum())
    meta["window_start_used"] = str(ws.date())
    yrs = k["Published Date"].dt.year.value_counts().sort_index()
    meta["kept_by_year"] = {int(y): int(c) for y, c in yrs.items()}
    warnings = []
    if meta["raw_rows"] >= EXPORT_CAP:
        warnings.append(f"raw rows {meta['raw_rows']} >= {EXPORT_CAP}: export may have hit the download cap")
    today_year = pd.Timestamp.now().year
    lo = int(yrs.index.min()) if len(yrs) else today_year
    for y in range(lo, today_year):  # full publication years only
        c = int(yrs.get(y, 0))
        if c < 5:
            warnings.append(f"publication year {y} has only {c} kept notices (<5): export may be incomplete")
    meta["warnings"] = warnings
    meta["join_note"] = ("Spend data has no Companies House numbers: the spend-to-notice join is by "
                         "normalised supplier name only. CH numbers are used only to merge duplicate "
                         "supplier blocks within a notice.")
    n.to_csv(FULL / "notices.csv", index=False)
    (FULL / "contracts_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    print(json.dumps({x: meta[x] for x in ["raw_rows", "kept", "dropped", "dropped_org_names",
                                           "kept_by_org_name_as_written", "supplier_rows",
                                           "supplier_rows_merged_by_ch_number_or_name",
                                           "notices_with_empty_supplier", "live_in_window",
                                           "zero_award_value_notices", "kept_by_year", "warnings"]},
                     indent=1, default=str))
    return meta


if __name__ == "__main__":
    main()
