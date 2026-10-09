#!/usr/bin/env python3
"""Number check: every figure in the pack documents is a value from a source file.

Scans outputs/planning-memo.md, risk-control-matrix.md and audit-program.md for
every figure with three or more digits or a £ sign, and requires each to equal,
at its printed precision, a number in analytics.json, pack-figures.json,
rules.json or outputs/samples/*.csv.

Skipped before scanning: code spans, spend row IDs, rule/risk/control/test/PBC
IDs (CPR-65, R-01, T-03), dates and times, years, clause and page references
(p12, page 12, clause 7.2, row B1, 7.4.3), and supplier names in the samples.

Usage: check_numbers.py [--root DIR]
"""
import re
import sys
from pathlib import Path

from qa_common import ROW_ID_PATTERN, Result, load_csv, load_json, num, parse_args

DOCS = ("planning-memo.md", "risk-control-matrix.md", "audit-program.md")
SKIP = [re.compile(p, re.I) for p in (
    r"`[^`\n]*`",                                                     # code spans: paths, metric names
    ROW_ID_PATTERN,                                                   # spend row IDs
    r"\b\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?",  # dates and times
    r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",                                   # dates
    r"\b[A-Z]{1,3}-\d+\b",                                            # CPR-65, R-01, T-03, P-02, A-15
    r"\b(?:pp?|pages?|clauses?|para(?:graph)?s?|sections?|rows?|tables?|figures?|appendix|app|part)\.?"
    r"\s*[A-Z]?\d[\d.]*[A-Z]?\d*\b",                                  # p12, page 12, clause 7.2, row B1
    r"\b\d+(?:\.\d+){2,}\b",                                          # 7.4.3
)]
FIGURE_RE = re.compile(r"£\s?\d[\d,]*(?:\.\d+)?|(?<![\w.])\d[\d,]*(?:\.\d+)?%?")
YEAR_RE = re.compile(r"^(19|20)\d{2}$")
MAX_DP = 4


def numbers(obj):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        yield float(obj)
    elif isinstance(obj, str):
        v = num(obj)
        if v is not None:
            yield v
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from numbers(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from numbers(v)


def main():
    args = parse_args(__doc__)
    root, out = Path(args.root), Path(args.root) / "outputs"
    r = Result("check_numbers")
    for name in ("analytics.json", "pack-figures.json", "rules.json"):
        if not (out / name).exists():
            return r.cannot(f"outputs/{name} is missing")
    docs = [d for d in DOCS if (out / d).exists()]
    for d in DOCS:
        if d not in docs:
            r.fail(f"outputs/{d} is missing")

    values, suppliers = [], set()
    for name in ("analytics.json", "pack-figures.json", "rules.json"):
        values += numbers(load_json(out / name))
    for f in sorted((out / "samples").glob("*.csv")):
        for row in load_csv(f):
            values += numbers(list(row.values()))
            suppliers.update(s for s in (row.get("unit_supplier"), row.get("Supplier name")) if s)
    known = {dp: {f"{abs(v):.{dp}f}" for v in values} for dp in range(MAX_DP + 1)}
    named = sorted((s for s in suppliers if re.search(r"\d{3}", s)), key=len, reverse=True)

    checked = 0
    for d in docs:
        for i, line in enumerate((out / d).read_text(encoding="utf-8").splitlines(), 1):
            for s in named:
                line = line.replace(s, " ")
            for pat in SKIP:
                line = pat.sub(" ", line)
            for m in FIGURE_RE.finditer(line):
                tok = m.group(0)
                digits = sum(c.isdigit() for c in tok)
                if "£" not in tok and digits < 3:
                    continue
                if "£" not in tok and YEAR_RE.match(tok):
                    continue
                checked += 1
                body = tok.replace("£", "").replace(",", "").rstrip("%").strip()
                dp = len(body.split(".")[1]) if "." in body else 0
                if dp > MAX_DP or body not in known[dp]:
                    r.fail(f"{d}:{i}: '{tok}' is not a value in analytics.json, pack-figures.json, rules.json "
                           "or outputs/samples/")
    return r.finish(f"{checked} figure(s) checked in {len(docs)} document(s)")


if __name__ == "__main__":
    sys.exit(main())
