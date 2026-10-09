#!/usr/bin/env python3
"""Tests for build_pack.py on a small fixture.

The fixture is an approved register with two risks: R-01 (score 12, sampled
from threshold_clustering.csv) and R-02 (score 15, sampled from duplicates.csv
plus an on-site records sample). The base case checks the pack builds with
samples sized by score. Then each case plants one defect, or walks the gate,
and checks the builder's verdict. Run:
  .venv/bin/python .claude/skills/audit-program/tests/test_build_pack.py
"""
import copy
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BUILDER = Path(__file__).resolve().parents[1] / "build_pack.py"
OUTPUTS = ("planning-memo.md", "risk-control-matrix.md", "audit-program.md", "pack-figures.json")


def rules():
    return {"rules": [
        {"rule_id": "CPR-05", "clause": "App B row B1", "page": 12, "type": "procedure",
         "verbatim_quote": "Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources"},
        {"rule_id": "CPR-09", "clause": "6.16", "page": 7, "type": "anti-avoidance",
         "verbatim_quote": "No contract may be split to avoid the application of these Rules"},
        {"rule_id": "CPR-12", "clause": "10.1", "page": 8, "type": "documentation",
         "verbatim_quote": "A written record of every purchase must be kept"},
        {"rule_id": "CPR-20", "clause": "11.11", "page": 10, "type": "contract-content",
         "verbatim_quote": "Contracts above the Threshold must be sealed"}]}


def analytics():
    return {"thresholds": {"quote_threshold": {"value": 25000}},
            "tests": {"threshold_clustering": {"status": "ran", "counts": {"total": 20}, "gbp": {"total": 480000.0}},
                      "duplicates": {"status": "ran", "counts": {"total": 3}, "gbp": {"total": 9000.0}}}}


def history():
    return {"audits": [{"id": "A-01", "title": "Contract Letting", "service": "Procurement",
                        "opinion": "Reasonable Assurance", "period": "2025", "source": "x.pdf", "pdf_page": 1}]}


RISKS = [
    {"id": "R-01", "title": "Payments clustering just below the quote threshold",
     "description": "{{$.tests.threshold_clustering.counts.total}} payments sit just below the threshold [rule:CPR-05].",
     "likelihood": {"score": 4, "justification": "L4 [metric:$.tests.threshold_clustering.counts.total]."},
     "impact": {"score": 3, "criterion": "Compliance", "justification": "C3 [rule:CPR-05] [rule:CPR-09]."},
     "repeat_uplift": None, "proposed_focus": "Request the quote record [rule:CPR-05]."},
    {"id": "R-02", "title": "Repeat payments of the same amount",
     "description": "{{$.tests.duplicates.counts.total}} pairs recur [rule:CPR-12].",
     "likelihood": {"score": 3, "justification": "L3 [metric:$.tests.duplicates.counts.total]."},
     "impact": {"score": 5, "criterion": "Financial loss", "justification": "Financial [rule:CPR-12]."},
     "repeat_uplift": None, "proposed_focus": "Match each payment to an invoice [rule:CPR-12]."}]

PLAN = {
    "memo": {"sections": [
        {"heading": "Objective", "text": "Seek assurance that purchases follow the Contract Procedure Rules."},
        {"heading": "Approach", "text": "Test {{$pack.counts.transactions}} sampled transactions worth "
                                        "{{$pack.counts.transactions_gbp|gbp}} against the expected controls; "
                                        "{{$.tests.threshold_clustering.counts.total}} payments are flagged."},
        {"heading": "Limitations", "text": "Spend data covers one quarter; indicators only."}]},
    "risks": [
        {"risk": "R-01", "controls": [
            {"id": "C-01", "control": "Purchases from the quote threshold are let on three Portal quotes [rule:CPR-05].",
             "tests": [{"id": "T-01", "step": "For each sampled payment, obtain the Portal quote record and confirm "
                                              "three quotes were invited [rule:CPR-05].",
                        "sample": {"from": "threshold_clustering.csv",
                                   "filter": [{"col": "tag", "op": "in", "value": ["general_procurement", "premises"]}],
                                   "sort": [{"col": "amount", "desc": True}], "pick": "top",
                                   "rationale": "General procurement first, largest amounts first."},
                        "pbc": ["Procurement Portal quote record for each sampled payment"]}]},
            {"id": "C-02", "control": "Requirements are not divided to fall under a threshold [rule:CPR-09].",
             "tests": [{"id": "T-02", "step": "Ask whether the sampled payments form one requirement "
                                              "[rule:CPR-09] [metric:$.tests.threshold_clustering.counts.total].",
                        "sample": {"from": "threshold_clustering.csv", "pick": "interval",
                                   "sort": [{"col": "row_id"}]},
                        "pbc": ["Procurement Portal quote record for each sampled payment",
                                "Purchase orders for the sampled payments"]}]}]},
        {"risk": "R-02", "controls": [
            {"id": "C-03", "control": "Every payment matches a distinct invoice and purchase record [rule:CPR-12].",
             "tests": [{"id": "T-03", "step": "Match each payment in the sampled pairs to a distinct invoice "
                                              "[rule:CPR-12].",
                        "sample": {"from": "duplicates.csv", "sort": [{"col": "gbp_repeat_value", "desc": True}]},
                        "pbc": ["Invoices for the sampled payments"]},
                       {"id": "T-04", "step": "Review the duplicate payment exception report [rule:CPR-12].",
                        "sample": {"records": "the AP duplicate payment exception report"},
                        "pbc": ["AP duplicate payment exception report for the quarter"]}]}]}],
    "not_tested": [{"rule": "CPR-20", "reason": "Tied to the intranet Threshold, which is not in data/."}]}


def spend_rows():
    rows = []
    for i in range(1, 31):
        rows.append({"row_id": f"P02.xlsx:Data to publish:{i}", "source_file": "P02.xlsx", "sheet_row": i,
                     "Service": "Highways", "Expenditure category": "Supplies", "Narrative": "Materials",
                     "Date": f"2026-05-{i:02d} 10:00:00.000", "Net amount": 1000 + i,
                     "Supplier name": f"Supplier {i % 7} Ltd", "supplier_norm": f"SUPPLIER {i % 7}",
                     "tag": "general_procurement" if i % 3 else "care_education_placement"})
    return rows


def clustering_rows():
    return [{"row_id": f"P02.xlsx:Data to publish:{i}", "supplier_norm": f"SUPPLIER {i % 7}",
             "tag": "general_procurement" if i % 3 else "care_education_placement",
             "amount": 22500 + i * 100, "tier": 25000} for i in range(1, 21)]


def duplicate_rows():
    return [{"type": "different_dates", "supplier_norm": f"SUPPLIER {g}", "amount": 3000,
             "gbp_repeat_value": 3000 * (g + 1),
             "row_ids": ";".join(f"P02.xlsx:Data to publish:{20 + g * 3 + k}" for k in range(1, 4))}
            for g in range(3)]


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Fixture:
    def __init__(self, tmp):
        self.root = Path(tmp)
        self.out = self.root / "outputs"
        (self.out / "analytics-full").mkdir(parents=True)
        for name, doc in (("analytics", analytics()), ("history", history()), ("rules", rules()),
                          ("risk-ratings", {"risks": copy.deepcopy(RISKS)})):
            self.write(f"{name}.json", doc)
        write_csv(self.out / "analytics-full" / "spend_clean.csv", spend_rows())
        write_csv(self.out / "analytics-full" / "threshold_clustering.csv", clustering_rows())
        write_csv(self.out / "analytics-full" / "duplicates.csv", duplicate_rows())
        self.approve(R_01=("Approve", "[2026-10-08]"), R_02=("Approve", "[2026-10-08]"))

    def write(self, name, doc):
        (self.out / name).write_text(json.dumps(doc), encoding="utf-8")

    def read(self, name):
        return (self.out / name).read_text(encoding="utf-8")

    def comments(self, decisions):
        lines = ["# Auditor decisions", "", "| Risk | Title | L | I | Score | Band | Decision | Comment |",
                 "|---|---|---|---|---|---|---|---|"]
        for r in RISKS:
            d, c = decisions.get(r["id"], ("", ""))
            lines.append(f"| {r['id']} | {r['title']} | 0 | 0 | 0 | b | {d} | {c} |")
        (self.out / "auditor-comments.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def approve(self, revision=1, **rows):
        """Write decisions and a register state that applied them, as build_register.py would."""
        decisions = {k.replace("_", "-"): v for k, v in rows.items()}
        self.comments(decisions)
        scores = {"R-01": (4, 3, 12, "Medium - High (Amber)"), "R-02": (3, 5, 15, "Extreme (Red)")}
        state = {
            "revision": revision,
            "inputs": {k: sha(self.out / f"{k}.json") for k in ("analytics", "history", "rules", "risk-ratings")},
            "applied_decisions": {rid: {"decision": d, "comment": c} for rid, (d, c) in decisions.items() if d},
            "rated": {rid: {"likelihood": l, "impact": i, "score": s, "band": b,
                            "decision": decisions.get(rid, ("", ""))[0]} for rid, (l, i, s, b) in scores.items()}}
        self.write("risk-register.state.json", state)

    def run(self, plan=None, gate=False):
        self.write("audit-plan.json", PLAN if plan is None else plan)
        cmd = [sys.executable, str(BUILDER), "--root", str(self.root)] + (["--gate"] if gate else [])
        p = subprocess.run(cmd, capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    def wrote_nothing(self):
        return not any((self.out / n).exists() for n in OUTPUTS) and not (self.out / "samples").exists()


def plan_with(fn):
    p = copy.deepcopy(PLAN)
    fn(p)
    return p


CHECKS = []


def case(name):
    def wrap(fn):
        CHECKS.append((name, fn))
        return fn
    return wrap


@case("two approved risks build; samples sized by score")
def _(fx):
    code, out = fx.run()
    if code != 0:
        return False, out
    figs = json.loads(fx.read("pack-figures.json"))
    s = figs["samples"]
    t1 = list(csv.DictReader((fx.out / "samples" / "T-01.csv").open(encoding="utf-8")))
    prog, memo, matrix = fx.read("audit-program.md"), fx.read("planning-memo.md"), fx.read("risk-control-matrix.md")
    return all([
        "BUILT pack on register revision 1: 2 risk(s), 3 control(s), 4 test(s)" in out,
        figs["risks"]["R-01"]["sample_size"] == 15 and figs["risks"]["R-02"]["sample_size"] == 25,
        s["T-01"]["population"] == 14 and s["T-01"]["units"] == 14,       # filter leaves 14 of 20, all taken
        s["T-02"]["population"] == 20 and s["T-02"]["units"] == 15,       # score 12 -> 15 units
        s["T-03"]["units"] == 3 and s["T-03"]["transactions"] == 9,       # 3 groups of 3 payments
        s["T-04"]["kind"] == "records" and not (fx.out / "samples" / "T-04.csv").exists(),
        t1[0]["row_id"] == "P02.xlsx:Data to publish:20",                  # largest amount first
        "## PBC list" in prog.split("## R-02")[-1] and "| P-01 | Procurement Portal quote record" in prog
        and "| T-01, T-02 |" in prog,
        f"Test {figs['counts']['transactions']} sampled transactions" in memo,
        "| CPR-20 | 11.11 |" in matrix, "4 rules in `outputs/rules.json`, 4 accounted for" in matrix,
    ]), out


@case("rebuild draws the same samples")
def _(fx):
    fx.run()
    first = {p.name: p.read_text() for p in (fx.out / "samples").glob("*.csv")}
    code, out = fx.run()
    again = {p.name: p.read_text() for p in (fx.out / "samples").glob("*.csv")}
    return code == 0 and first == again and len(first) == 3, out


@case("gate open: --gate passes")
def _(fx):
    code, out = fx.run(gate=True)
    return code == 0 and "GATE OPEN on register revision 1: in scope R-01, R-02" in out, out


@case("gate: an undecided risk closes it")
def _(fx):
    fx.approve(R_01=("Approve", "[2026-10-08]"))
    code, out = fx.run(gate=True)
    return code == 1 and "R-02 has no decision" in out and "GATE CLOSED" in out, out


@case("gate: a register at revision 0 closes it")
def _(fx):
    fx.approve(revision=0, R_01=("Approve", "x"), R_02=("Approve", "x"))
    code, out = fx.run()
    return code == 1 and "revision 0, a draft" in out and fx.wrote_nothing(), out


@case("gate: a decision made after the revision closes it")
def _(fx):
    fx.comments({"R-01": ("Approve", "[2026-10-08]"), "R-02": ("Change", "likelihood 4")})
    code, out = fx.run(gate=True)
    return code == 1 and "R-02: decision 'Change' is not applied" in out, out


@case("gate: ratings edited after the register closes it")
def _(fx):
    rat = {"risks": copy.deepcopy(RISKS)}
    rat["risks"][0]["title"] = "Edited"
    fx.write("risk-ratings.json", rat)
    code, out = fx.run(gate=True)
    return code == 1 and "risk-ratings.json changed after register revision 1" in out, out


@case("missing risk: an approved risk with no plan entry fails")
def _(fx):
    code, out = fx.run(plan_with(lambda p: p["risks"].pop(1)))
    return code == 1 and "R-02 is approved but has no entry" in out and fx.wrote_nothing(), out


@case("uncited control fails")
def _(fx):
    def strip(p):
        p["risks"][0]["controls"][0]["control"] = "Purchases from the quote threshold are let on three quotes."
    code, out = fx.run(plan_with(strip))
    return code == 1 and "C-01: cites no rule" in out and fx.wrote_nothing(), out


@case("unaccounted rule fails")
def _(fx):
    code, out = fx.run(plan_with(lambda p: p.update(not_tested=[])))
    return code == 1 and "CPR-20 is not cited by an approved risk, a control or a test" in out \
        and fx.wrote_nothing(), out


@case("not_tested without a reason fails")
def _(fx):
    code, out = fx.run(plan_with(lambda p: p["not_tested"][0].update(reason=" ")))
    return code == 1 and "not_tested CPR-20: a reason is required" in out, out


@case("control with no test fails")
def _(fx):
    code, out = fx.run(plan_with(lambda p: p["risks"][0]["controls"][1].update(tests=[])))
    return code == 1 and "C-02: control has no test" in out, out


@case("test step with no rule or metric fails")
def _(fx):
    code, out = fx.run(plan_with(lambda p: p["risks"][1]["controls"][0]["tests"][0].update(step="Match invoices.")))
    return code == 1 and "T-03: cites no rule or metric" in out, out


@case("citation that does not resolve fails")
def _(fx):
    code, out = fx.run(plan_with(lambda p: p["risks"][1]["controls"][0]["tests"][0].update(
        step="Match invoices [rule:CPR-99].")))
    return code == 1 and "T-03: [rule:CPR-99] does not resolve" in out, out


@case("sampled transaction missing from spend_clean.csv fails")
def _(fx):
    rows = clustering_rows()
    rows[-1]["row_id"] = "P09.xlsx:Data to publish:999"
    write_csv(fx.out / "analytics-full" / "threshold_clustering.csv", rows)
    code, out = fx.run()
    return code == 1 and "P09.xlsx:Data to publish:999, not found in spend_clean.csv" in out \
        and fx.wrote_nothing(), out


@case("filter that leaves nothing fails")
def _(fx):
    code, out = fx.run(plan_with(lambda p: p["risks"][0]["controls"][0]["tests"][0]["sample"].update(
        filter=[{"col": "tag", "op": "eq", "value": "grant"}])))
    return code == 1 and "T-01: the filter leaves no rows" in out, out


@case("rejected risk: out of scope, and planning it fails")
def _(fx):
    fx.approve(R_01=("Approve", "[2026-10-08]"), R_02=("Reject", "covered by the AP audit"))
    code, out = fx.run()
    ok_rejected = code == 1 and "R-02 was rejected by the auditor" in out

    def only_r01(p):
        p["risks"].pop(1)
        p["not_tested"].append({"rule": "CPR-12", "reason": "Its only risk, R-02, was rejected by the auditor."})
    code2, out2 = fx.run(plan_with(only_r01))
    memo = fx.read("planning-memo.md") if code2 == 0 else ""
    return ok_rejected and code2 == 0 and "| R-02 | Repeat payments of the same amount | covered by the AP audit |" \
        in memo, out + out2


@case("typed figure and accusing word warn")
def _(fx):
    def bad(p):
        p["memo"]["sections"][2]["text"] = "Spend of £48,000 may show fraud."
    code, out = fx.run(plan_with(bad))
    return code == 0 and "W-FIGURE" in out and "W-LANGUAGE" in out, out


def main():
    failures = 0
    for name, fn in CHECKS:
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
