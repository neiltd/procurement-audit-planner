#!/usr/bin/env python3
"""Sample check: every sampled transaction exists in the cleaned spend data and in the council's workbook.

For every row of outputs/samples/*.csv, and every spend row ID printed in
outputs/audit-program.md:
- the row ID is in outputs/analytics-full/spend_clean.csv, and a sample row's
  supplier, amount, file and sheet row equal that spend_clean row;
- the workbook data/spend/<source_file>, sheet named in the row ID, holds at
  that sheet row the same supplier name and net amount.

Usage: check_samples.py [--root DIR]
"""
import re
import sys
from pathlib import Path

import openpyxl

from qa_common import ROW_ID_PATTERN, Result, load_csv, num, parse_args

SUPPLIER, AMOUNT = "Supplier name", "Net amount"
PENNY = 0.005


class Workbooks:
    """Reads each workbook once; maps (file, sheet, row) -> (supplier, amount)."""

    def __init__(self, spend_dir):
        self.dir, self.cache = spend_dir, {}

    def sheet(self, file, sheet):
        key = (file, sheet)
        if key not in self.cache:
            path = self.dir / file
            if not path.exists():
                self.cache[key] = f"data/spend/{file} is missing"
                return self.cache[key]
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            if sheet not in wb.sheetnames:
                self.cache[key] = f"data/spend/{file} has no sheet '{sheet}'"
                return self.cache[key]
            rows, cols = {}, None
            for n, row in enumerate(wb[sheet].iter_rows(values_only=True), 1):
                if cols is None:
                    names = [str(c).strip() if c is not None else "" for c in row]
                    if SUPPLIER in names and AMOUNT in names:
                        cols = names.index(SUPPLIER), names.index(AMOUNT)
                    continue
                rows[n] = (row[cols[0]], row[cols[1]])
            wb.close()
            self.cache[key] = rows if cols else f"data/spend/{file} sheet '{sheet}' has no header row"
        return self.cache[key]


def main():
    args = parse_args(__doc__)
    root = Path(args.root)
    out = root / "outputs"
    r = Result("check_samples")
    spend_path = out / "analytics-full" / "spend_clean.csv"
    if not spend_path.exists():
        return r.cannot("outputs/analytics-full/spend_clean.csv is missing")
    spend = {x["row_id"]: x for x in load_csv(spend_path)}
    books = Workbooks(root / "data" / "spend")

    todo = []  # (where, row_id, sample row or None)
    files = sorted((out / "samples").glob("*.csv"))
    if not files:
        r.fail("outputs/samples/ holds no sample files")
    for f in files:
        for i, row in enumerate(load_csv(f), 2):
            todo.append((f"samples/{f.name}:{i}", row.get("row_id", ""), row))
    program = out / "audit-program.md"
    if program.exists():
        for i, line in enumerate(program.read_text(encoding="utf-8").splitlines(), 1):
            for m in re.finditer(ROW_ID_PATTERN, line):
                todo.append((f"audit-program.md:{i}", m.group(0), None))
    else:
        r.fail("outputs/audit-program.md is missing")

    checked = set()
    for where, rid, row in todo:
        s = spend.get(rid)
        if s is None:
            r.fail(f"{where}: {rid or '(no row_id)'} is not in spend_clean.csv")
            continue
        if row is not None:
            for col in (SUPPLIER, "source_file", "sheet_row"):
                if str(row.get(col, "")).strip() != str(s[col]).strip():
                    r.fail(f"{where}: {rid} {col} '{row.get(col)}' differs from spend_clean.csv '{s[col]}'")
            a, b = num(row.get(AMOUNT, "")), num(s[AMOUNT])
            if a is None or b is None or abs(a - b) > PENNY:
                r.fail(f"{where}: {rid} {AMOUNT} '{row.get(AMOUNT)}' differs from spend_clean.csv '{s[AMOUNT]}'")
        if rid in checked:
            continue
        checked.add(rid)
        sheet = rid[len(s["source_file"]) + 1:].rsplit(":", 1)[0]
        rows = books.sheet(s["source_file"], sheet)
        if isinstance(rows, str):
            r.fail(f"{where}: {rid}: {rows}")
            continue
        cell = rows.get(int(s["sheet_row"]))
        if cell is None:
            r.fail(f"{where}: {rid}: workbook has no row {s['sheet_row']}")
            continue
        supplier, amount = str(cell[0] or "").strip(), num(cell[1] if cell[1] is not None else "")
        if supplier != str(s[SUPPLIER]).strip():
            r.fail(f"{where}: {rid}: workbook supplier '{supplier}' differs from spend_clean.csv '{s[SUPPLIER]}'")
        if amount is None or abs(amount - num(s[AMOUNT])) > PENNY:
            r.fail(f"{where}: {rid}: workbook amount '{cell[1]}' differs from spend_clean.csv '{s[AMOUNT]}'")
    return r.finish(f"{len(todo)} sampled row(s) in {len(files)} file(s); {len(checked)} distinct transaction(s) "
                    "traced to the workbooks")


if __name__ == "__main__":
    sys.exit(main())
