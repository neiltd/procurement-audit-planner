#!/usr/bin/env python3
"""Tests for the QA checks on a small fixture.

The fixture is the audit-program builder's two-risk fixture, built into a real
pack by build_pack.py, plus a council workbook, a register with rule excerpts,
a closed challenge log and a stub quote verifier. The base case checks every
check passes; each other case plants one defect (a bad figure, a missing row,
a workbook mismatch, a wrong excerpt, an open challenge...) and checks the
right check fails. Run:
  .venv/bin/python scripts/checks/tests/test_checks.py
"""
import copy
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parents[3]
CHECKS = REPO / "scripts" / "checks"
sys.path.insert(0, str(REPO / ".claude" / "skills" / "audit-program" / "tests"))
import test_build_pack as bp  # noqa: E402

SHEET = "Data to publish"
STUB_OK = "import sys; print('PASS: stub verifier'); sys.exit(0)"
STUB_BAD = "import sys; print('[E-QUOTE] CPR-05: quote not found on page 12'); print('FAIL: 1 error(s)'); sys.exit(1)"


def rid(i):
    return f"P02.xlsx:{SHEET}:{i}"


def spend_rows():
    """Thirty payments at sheet rows 2-31 (row 1 is the header)."""
    return [{"row_id": rid(i), "source_file": "P02.xlsx", "sheet_row": i, "Service": "Highways",
             "Expenditure category": "Supplies", "Narrative": "Materials", "Date": f"2026-05-{i - 1:02d} 10:00:00.000",
             "Net amount": 1000 + i + 0.25, "Supplier name": f"Supplier {i % 7} Ltd", "supplier_norm": f"SUPPLIER {i % 7}",
             "tag": "general_procurement" if i % 3 else "care_education_placement"} for i in range(2, 32)]


class Fixture(bp.Fixture):
    def __init__(self, tmp):
        super().__init__(tmp)
        full = self.out / "analytics-full"
        bp.write_csv(full / "spend_clean.csv", spend_rows())
        bp.write_csv(full / "threshold_clustering.csv",
                     [{**r, "row_id": rid(i + 1)} for i, r in enumerate(bp.clustering_rows(), 1)])
        bp.write_csv(full / "duplicates.csv",
                     [{**r, "row_ids": ";".join(rid(int(x.rsplit(":", 1)[1]) + 1) for x in r["row_ids"].split(";"))}
                      for r in bp.duplicate_rows()])
        code, out = self.run()
        assert code == 0, out
        self.workbook()
        (self.out / "risk-register.md").write_text(
            "# Risk register\n\n**Evidence**\n\n"
            "- CPR-05 (App B row B1, p12): “Invitations to quote must be sent via the Procurement Portal to at least "
            "three appropriate sources”\n"
            "- CPR-09 (6.16, p7): “No contract may be split to avoid the application of these Rules”\n",
            encoding="utf-8")
        self.challenges("resolved", "[rule:CPR-05]")
        (self.root / "data").mkdir(exist_ok=True)
        (self.root / "data" / "contract-rules.pdf").write_bytes(b"%PDF stub")
        self.verifier(STUB_OK)

    def workbook(self, amend=None):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = SHEET
        ws.append(["Service", "Expenditure category", "Narrative", "Date", "Net amount", "Supplier name"])
        for r in spend_rows():
            row = [r["Service"], r["Expenditure category"], r["Narrative"], r["Date"], r["Net amount"],
                   r["Supplier name"]]
            if amend and r["sheet_row"] in amend:
                row = amend[r["sheet_row"]](row)
            ws.append(row)
        (self.root / "data" / "spend").mkdir(parents=True, exist_ok=True)
        wb.save(self.root / "data" / "spend" / "P02.xlsx")

    def challenges(self, status, cite):
        (self.out / "challenges.md").write_text(
            "# Challenges\n\n| # | Round | Type | Risk | Challenge | Ask | Planner response | Status | Verified in |\n"
            "|---|---|---|---|---|---|---|---|---|\n"
            f"| 1 | 1 | sample | R-01 | T-01 skips placements {cite} | add a stratum | accepted | {status} | v2 T-01 |\n",
            encoding="utf-8")

    def verifier(self, code):
        self.stub = self.root / "stub_verifier.py"
        self.stub.write_text(code, encoding="utf-8")

    def append(self, name, text):
        p = self.out / name
        p.write_text(p.read_text(encoding="utf-8") + text, encoding="utf-8")

    def check(self, name):
        cmd = [sys.executable, str(CHECKS / f"{name}.py"), "--root", str(self.root)]
        if name == "check_quotes":
            cmd += ["--verifier", str(self.stub)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr


CASES = []


def case(name):
    def wrap(fn):
        CASES.append((name, fn))
        return fn
    return wrap


@case("clean pack: all four checks pass")
def _(fx):
    outs = [fx.check(n) for n in ("check_quotes", "check_numbers", "check_trace", "check_samples")]
    return all(c == 0 for c, _ in outs), "\n".join(o for _, o in outs)


@case("check_numbers: a figure that matches a source passes")
def _(fx):
    fx.append("planning-memo.md", "\nThe quote threshold is £25,000 and 20 payments are flagged.\n")
    code, out = fx.check("check_numbers")
    return code == 0, out


@case("check_numbers: a planted bad figure fails")
def _(fx):
    fx.append("planning-memo.md", "\nFlagged spend totals £12,345 across the quarter.\n")
    code, out = fx.check("check_numbers")
    return code == 1 and "'£12,345' is not a value" in out and "planning-memo.md:" in out, out


@case("check_numbers: a bad figure inside the program fails; IDs, dates and refs are skipped")
def _(fx):
    fx.append("audit-program.md", "\nSee CPR-05 (p12, clause 7.4.3, row B1) on 2026-05-03, T-01 and "
                                  f"{rid(9)}; then 4,321 payments.\n")
    code, out = fx.check("check_numbers")
    return code == 1 and "'4,321'" in out and out.count("is not a value") == 1, out


@case("check_samples: a planted missing row fails")
def _(fx):
    p = fx.out / "samples" / "T-01.csv"
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    rows[0]["row_id"] = rid(999)
    bp.write_csv(p, rows)
    code, out = fx.check("check_samples")
    return code == 1 and f"{rid(999)} is not in spend_clean.csv" in out, out


@case("check_samples: a row ID in the program that is not in the spend data fails")
def _(fx):
    fx.append("audit-program.md", f"\nAlso pull {rid(555)}.\n")
    code, out = fx.check("check_samples")
    return code == 1 and f"audit-program.md:" in out and rid(555) in out, out


@case("check_samples: a workbook amount that differs fails")
def _(fx):
    first = next(csv.DictReader((fx.out / "samples" / "T-01.csv").open(encoding="utf-8")))
    fx.workbook({int(first["sheet_row"]): lambda row: row[:4] + [row[4] + 100] + row[5:]})
    code, out = fx.check("check_samples")
    return code == 1 and "workbook amount" in out, out


@case("check_samples: a sample row whose supplier differs from spend_clean fails")
def _(fx):
    p = fx.out / "samples" / "T-03.csv"
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    rows[0]["Supplier name"] = "Someone Else Ltd"
    bp.write_csv(p, rows)
    code, out = fx.check("check_samples")
    return code == 1 and "Supplier name 'Someone Else Ltd' differs" in out, out


@case("check_quotes: a register excerpt that differs from rules.json fails")
def _(fx):
    fx.append("risk-register.md", "- CPR-09 (6.16, p7): “No contract may be divided”\n")
    code, out = fx.check("check_quotes")
    return code == 1 and "does not match its verbatim_quote" in out, out


@case("check_quotes: a wrong page fails")
def _(fx):
    fx.append("risk-register.md", "- CPR-09 (6.16, p8): “No contract may be split…”\n")
    code, out = fx.check("check_quotes")
    return code == 1 and "cited as (6.16, p8)" in out, out


@case("check_quotes: a verifier failure fails")
def _(fx):
    fx.verifier(STUB_BAD)
    code, out = fx.check("check_quotes")
    return code == 1 and "verify_quotes: [E-QUOTE] CPR-05" in out, out


@case("check_trace: an open challenge fails")
def _(fx):
    fx.challenges("open", "[rule:CPR-05]")
    code, out = fx.check("check_trace")
    return code == 1 and "challenges.md:5 #1: status is open" in out, out


@case("check_trace: a challenge with no citation fails")
def _(fx):
    fx.challenges("resolved", "")
    code, out = fx.check("check_trace")
    return code == 1 and "cites no evidence" in out, out


@case("check_trace: a missing challenge log fails")
def _(fx):
    (fx.out / "challenges.md").unlink()
    code, out = fx.check("check_trace")
    return code == 1 and "challenges.md is missing" in out, out


@case("check_trace: an unaccounted rule fails")
def _(fx):
    plan = json.loads(fx.read("audit-plan.json"))
    plan["not_tested"] = []
    fx.write("audit-plan.json", plan)
    code, out = fx.check("check_trace")
    return code == 1 and "CPR-20: not cited by a rated risk" in out, out


@case("check_trace: an approved risk missing from the matrix fails")
def _(fx):
    p = fx.out / "risk-control-matrix.md"
    p.write_text("\n".join(l for l in p.read_text().splitlines() if not l.startswith("| R-02")), encoding="utf-8")
    code, out = fx.check("check_trace")
    return code == 1 and "R-02: approved, but not in risk-control-matrix.md" in out, out


@case("check_trace: a High risk rejected without a reason fails")
def _(fx):
    fx.comments({"R-01": ("Approve", "[2026-10-08]"), "R-02": ("Reject", "[2026-10-08]")})
    code, out = fx.check("check_trace")
    return code == 1 and "R-02: High risk (score 15) rejected with no reason" in out, out


@case("run_checks: one planted defect blocks the verdict")
def _(fx):
    fx.append("planning-memo.md", "\nFlagged spend totals £12,345.\n")
    fx.verifier(STUB_OK)
    p = subprocess.run([sys.executable, str(CHECKS / "run_checks.py"), "--root", str(fx.root)],
                       capture_output=True, text=True)
    # run_checks uses the real verifier, which cannot read the stub PDF, so check_quotes is blocked too.
    return p.returncode == 1 and "| check_numbers | FAIL |" in p.stdout and "| check_samples | PASS |" in p.stdout \
        and "VERDICT: BLOCKED" in p.stdout, p.stdout


def main():
    failures = 0
    for name, fn in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            ok, out = fn(Fixture(tmp))
        print(f"{'ok ' if ok else 'FAIL'} {name}")
        if not ok:
            print("   ", out.strip().replace("\n", "\n    "))
            failures += 1
    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
