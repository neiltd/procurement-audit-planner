#!/usr/bin/env python3
"""Tests for build_register.py on a small fixture.

The fixture has one good risk (R-01) and one broken risk (R-02, whose likelihood
and impact cite things that do not exist). The base case checks R-01 is rated
and R-02 dropped. Then each case plants one defect, or walks the auditor gate,
and checks the builder's verdict. Run:
  .venv/bin/python .claude/skills/risk-assessment/tests/test_build_register.py
"""
import copy
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BUILDER = Path(__file__).resolve().parents[1] / "build_register.py"
STRAT = "data/committee/strategy.pdf"
APPX = "data/committee/appendix.pdf"


def rules():
    return {"rules": [
        {"rule_id": "CPR-05", "clause": "App B row B1", "page": 12, "type": "procedure",
         "verbatim_quote": "Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources"},
        {"rule_id": "CPR-09", "clause": "6.16", "page": 7, "type": "anti-avoidance",
         "verbatim_quote": "No contract may be split to avoid the application of these Rules"}]}


def analytics():
    return {
        "thresholds": {"quote_threshold": {"value": 25000, "rule_id": "CPR-05"}},
        "tests": {
            "threshold_clustering": {"status": "ran", "counts": {"total": 368}, "gbp": {"total": 1382587.62},
                                     "parameters": {"tiers": [25000]}},
            "split_purchases": {"status": "ran", "counts": {"total": 0}, "gbp": {"total": 0.0}},
            "duplicates": {"status": "ran", "counts": {"total": 12}, "gbp": {"total": 410000.0}},
            "high_value_suppliers": {"status": "ran", "counts": {"total": 672}},
        }}


def history():
    s = {"source": STRAT}
    labels_l = ["Rare", "Unlikely", "Likely", "Almost Certain", "Certain"]
    labels_i = ["Negligible", "Minor", "Medium", "Major", "Critical"]
    fin = ["Less than 0.01% annual WBC budget £17.5k", "0.01% - 0.1% of annual WBC budget £17.5k - £175k",
           "0.1% - 0.3% annual WBC budget £175k -500k", "0.25% - 1% annual WBC budget £500k £2M",
           "> 1% annual WBC budget >£2m"]
    comp = ["Negligible possibility", "Low possibility", "Reasonable possibility", "High possibility", "Probable"]
    rows = {5: ["Moderate", "High", "Extreme", "Extreme", "Extreme"],
            4: ["Moderate", "High", "High", "Extreme", "Extreme"],
            3: ["Low", "Moderate", "High", "High", "Extreme"],
            2: ["Low", "Moderate", "Moderate", "High", "High"],
            1: ["Low", "Low", "Low", "Moderate", "Moderate"]}
    return {
        "audits": [
            {"id": "A-01", "section": "completed_audit", "title": "Contract Letting", "service": "Procurement",
             "opinion": "Reasonable Assurance", "period": "End of March 2025", "source": APPX, "pdf_page": 1},
            {"id": "A-02", "section": "completed_audit", "title": "Accounts Payable", "service": "Finance",
             "opinion": "Limited Assurance", "period": "End of December 2025", "source": APPX, "pdf_page": 1}],
        "agreed_actions": [],
        "risk_themes": [{"id": "T-01", "theme": "Contracts & Partnerships", "context": "sources of risk",
                         "source": STRAT, "pdf_page": 30}],
        "scoring_method": {
            "status": "found",
            "likelihood_scale": [{"score": n, "label": labels_l[n - 1], **s, "pdf_page": 15} for n in range(1, 6)],
            "impact_scale": [{"score": n, "label": labels_i[n - 1], **s, "pdf_page": 14,
                              "criteria": {"Financial loss to Council": fin[n - 1],
                                           "Compliance (litigation, regulatory, contract)": comp[n - 1]}}
                             for n in range(1, 6)],
            "matrix": [{"impact_score": i, "band_labels": rows[i], "scores_as_printed": [i * l for l in range(1, 6)],
                        **s, "pdf_page": 18} for i in range(5, 0, -1)],
            "bands": [{"band": "Extreme", "rag": "Red", "score_range": "15 -25", "escalation": "Add to CRR.",
                       "response": "Executive Director.", **s, "pdf_page": 19},
                      {"band": "Medium - High", "rag": "Amber", "score_range": "8-12",
                       "escalation": "Seek assurance.", "response": "Service Director.", **s, "pdf_page": 19},
                      {"band": "Moderate", "rag": None, "score_range": "4-6", "escalation": "None",
                       "response": "Monitor risk", **s, "pdf_page": 19},
                      {"band": "Low", "rag": "Green", "score_range": "Up to 3", "escalation": "None",
                       "response": "Annual review", **s, "pdf_page": 19}]},
        "discrepancies": [
            {"id": "D-01", "description": "Fig 4 says CRR at 9 or above; Table 4 says 15-25.",
             "evidence": [{**s, "pdf_page": 21, "quote": "Score 9 or above"},
                          {**s, "pdf_page": 19, "quote": "15 -25 Add to CRR."}]},
            {"id": "D-02", "description": "Two version numbers for the appetite guidance.",
             "evidence": [{**s, "pdf_page": 34, "quote": "V1.0"}]}],
        "gaps": [{"id": "G-01", "area": "agreed_actions", "text": "No actions listed", "sources_checked": [APPX]}],
    }


GOOD = {
    "id": "R-01",
    "title": "Payments clustering just below the quote threshold",
    "description": ("{{$.tests.threshold_clustering.counts.total}} payments worth "
                    "{{$.tests.threshold_clustering.gbp.total|gbp}} sit just below "
                    "{{$.thresholds.quote_threshold.value|gbp}} [metric:$.tests.threshold_clustering.counts.total]."),
    "likelihood": {"score": 3, "justification":
                   "One test flags payments in the band below the threshold "
                   "[metric:$.tests.threshold_clustering.counts.total] (rubric L3)."},
    "impact": {"score": 3, "criterion": "Compliance (litigation, regulatory, contract)", "justification":
               "Contracts at this value need three quotes via the portal [rule:CPR-05]; a missed quote "
               "gives a reasonable possibility of challenge."},
    "repeat_uplift": None,
    "proposed_focus": "Pull the flagged payments and request the quote record for each [rule:CPR-05].",
}

BROKEN = {
    "id": "R-02",
    "title": "Split purchases",
    "description": "Groups of payments that together cross a threshold.",
    "likelihood": {"score": 3, "justification": "Split groups found [metric:$.tests.split_groups.counts.total]."},
    "impact": {"score": 3, "criterion": "Compliance (litigation, regulatory, contract)",
               "justification": "Splitting avoids the rules [rule:CPR-99]."},
    "repeat_uplift": None,
    "proposed_focus": "Review the groups.",
}

METHOD = {"choices": [{"discrepancy": "D-01", "used": "Table 4 (15-25 goes to the CRR)",
                       "marked": "Figure 4 (9 or above)", "reason": "Table 4 is the scoring table.",
                       "mark": {"min_score": 9, "max_score": 14, "text": "would go to the CRR under Figure 4"}}],
          "not_affected": []}


def ratings(risks=None):
    return {"method": copy.deepcopy(METHOD), "risks": copy.deepcopy(risks or [GOOD, BROKEN])}


class Fixture:
    def __init__(self, tmp):
        self.root = Path(tmp)
        (self.root / "outputs").mkdir()
        for name, doc in (("analytics", analytics()), ("history", history()), ("rules", rules())):
            self.write(f"{name}.json", doc)

    def write(self, name, doc):
        (self.root / "outputs" / name).write_text(json.dumps(doc), encoding="utf-8")

    def read(self, name):
        return (self.root / "outputs" / name).read_text(encoding="utf-8")

    def run(self, rat=None):
        if rat is not None:
            self.write("risk-ratings.json", rat)
        p = subprocess.run([sys.executable, str(BUILDER), "--root", str(self.root)], capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    def decide(self, **rows):
        """Fill Decision/Comment cells: decide(R_01=("Change", "likelihood 4"))."""
        text = self.read("auditor-comments.md")
        for key, (dec, com) in rows.items():
            rid = key.replace("_", "-")
            text = re.sub(rf"^(\| {rid} \|(?:[^|]*\|){{5}}).*$", rf"\1 {dec} | {com} |", text, flags=re.M)
        (self.root / "outputs" / "auditor-comments.md").write_text(text, encoding="utf-8")


def mutate(fn):
    r = ratings()
    fn(r)
    return r


CHECKS = []


def case(name):
    def wrap(fn):
        CHECKS.append((name, fn))
        return fn
    return wrap


@case("good risk rated, broken risk dropped")
def _(fx):
    code, out = fx.run(ratings())
    reg, com = fx.read("risk-register.md"), fx.read("auditor-comments.md")
    return all([code == 0, "BUILT revision 0: 1 risk(s) rated, 1 dropped" in out,
                "DROPPED R-02" in out, "### R-01" in reg, "### R-02" not in reg,
                "Excluded: no resolvable citation" in reg and "R-02 Split purchases" in reg,
                "368 payments worth £1,382,588 sit just below £25,000" in reg,
                "Score 9, Medium - High (Amber) [matrix: High]" in reg,
                "† D-01: would go to the CRR under Figure 4" in reg,
                "| R-01 |" in com and "| R-02 |" not in com,
                "## Auditor decisions" in reg.split("## Risks")[-1]]), out


@case("header names every method conflict")
def _(fx):
    code, out = fx.run(ratings())
    head = fx.read("risk-register.md").split("## Summary")[0]
    return all([code == 0, "labelled 'High', where the band table names that range 'Medium - High'" in head,
                "D-01: uses Table 4" in head, "marks Figure 4" in head,
                "% ranges are not used" in head]), out


@case("scoring-page discrepancy left unnamed -> E-CONFLICT")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["method"].update(choices=[])))
    return code == 1 and "[E-CONFLICT] D-01" in out and "nothing written" in out, out


@case("discrepancy off the scoring pages need not be named")
def _(fx):
    code, out = fx.run(ratings())
    return code == 0 and "D-02" not in out, out


@case("broken citation in a kept risk's prose -> E-CITE")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0].update(
        proposed_focus="Pull the payments [rule:CPR-77].")))
    return code == 1 and "[E-CITE] R-01.proposed_focus: [rule:CPR-77]" in out, out


@case("placeholder to a missing path -> E-PLACEHOLDER")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0].update(
        description="{{$.tests.threshold_clustering.counts.rows}} payments [rule:CPR-05].")))
    return code == 1 and "[E-PLACEHOLDER]" in out, out


@case("typed figure in prose -> warning, still built")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0].update(
        description="368 payments worth £1.38m sit below the threshold [rule:CPR-05].")))
    return code == 0 and out.count("[W-FIGURE]") == 2, out


@case("accusatory word -> warning")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0].update(
        description="Possible fraud below the threshold [rule:CPR-05].")))
    return code == 0 and "[W-LANGUAGE]" in out, out


@case("likelihood 3 on a zero metric -> E-RUBRIC")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0]["likelihood"].update(
        justification="Groups found [metric:$.tests.split_purchases.counts.total].")))
    return code == 1 and "[E-RUBRIC] R-01: likelihood 3 needs" in out, out


@case("likelihood 3 on the population list only -> E-RUBRIC")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0]["likelihood"].update(
        justification="Many suppliers [metric:$.tests.high_value_suppliers.counts.total].")))
    return code == 1 and "[E-RUBRIC]" in out, out


@case("likelihood 4 on one test -> E-RUBRIC")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0]["likelihood"].update(score=4)))
    return code == 1 and "two different tests" in out, out


@case("likelihood 4 on two tests passes")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0]["likelihood"].update(score=4, justification=(
        "[metric:$.tests.threshold_clustering.counts.total] and [metric:$.tests.duplicates.counts.total]."))))
    return code == 0, out


@case("base likelihood 5 -> E-RUBRIC")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0]["likelihood"].update(score=5)))
    return code == 1 and "only through the repeat-finding uplift" in out, out


@case("uplift on a Reasonable audit -> E-UPLIFT")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0].update(
        repeat_uplift={"audit": "A-01", "justification": "Contract Letting [history:A-01]."})))
    return code == 1 and "[E-UPLIFT]" in out and "not adverse" in out, out


@case("uplift on a Limited audit raises likelihood by one")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0].update(
        repeat_uplift={"audit": "A-02", "justification": "Accounts Payable was Limited [history:A-02]."})))
    reg = fx.read("risk-register.md") if code == 0 else ""
    return code == 0 and "Likelihood 4 Almost Certain (base 3, +1 for a repeat finding: A-02" in reg \
        and "Score 12," in reg, out


@case("financial exposure that maps to another score -> E-EXPOSURE")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0].update(impact={
        "score": 2, "criterion": "Financial loss to Council", "exposure": "$.tests.duplicates.gbp.total",
        "justification": "Repeat payments [metric:$.tests.duplicates.gbp.total]."})))
    return code == 1 and "maps to financial impact 3, not 2" in out, out


@case("financial impact without exposure -> E-EXPOSURE")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0]["impact"].update(criterion="Financial loss to Council")))
    return code == 1 and "needs impact.exposure" in out, out


@case("unknown key on a risk -> E-SCHEMA")
def _(fx):
    code, out = fx.run(mutate(lambda r: r["risks"][0].update(score=9)))
    return code == 1 and "[E-SCHEMA] R-01: unknown key 'score'" in out, out


@case("missing risk-ratings.json -> exit 2")
def _(fx):
    code, out = fx.run()
    return code == 2 and "CANNOT RUN" in out, out


@case("revision: Change applied, override marked, decisions kept")
def _(fx):
    fx.run(ratings())
    fx.decide(R_01=("Change", "likelihood 4: the cluster is large"))
    code1, out1 = fx.run()  # decisions but no revision block yet
    r = ratings()
    r["risks"][0]["likelihood"]["score"] = 4
    r["revision"] = {"number": 1, "changes": [{"risk": "R-01", "fields": ["likelihood"], "decision": "R-01",
                                                "note": "Raised to 4 at the auditor's request."}]}
    code2, out2 = fx.run(r)
    reg, com = fx.read("risk-register.md"), fx.read("auditor-comments.md")
    code3, out3 = fx.run()  # rebuild with nothing new is idempotent
    return all([code1 == 1, "needs \"revision\"" in out1, code2 == 0,
                "## Revision 1" in reg, "R-01: likelihood 3 → 4, as asked" in reg,
                "Auditor override (revision 1):** likelihood 3 → 4" in reg,
                "| Change | likelihood 4: the cluster is large |" in com,
                "Gate: ready" in reg, code3 == 0]), "\n".join([out1, out2, out3])


@case("revision: decision left unapplied -> E-REVISION")
def _(fx):
    fx.run(ratings())
    fx.decide(R_01=("Change", "narrow the focus to agency staff"))
    r = ratings()
    r["revision"] = {"number": 1, "changes": []}
    code, out = fx.run(r)
    return code == 1 and "is not applied in revision.changes" in out, out


@case("revision: change nobody asked for -> E-REVISION")
def _(fx):
    fx.run(ratings())
    fx.decide(R_01=("Approve", ""))
    r = ratings()
    r["risks"][0]["proposed_focus"] = "Pull every payment [rule:CPR-05]."
    r["revision"] = {"number": 1, "changes": []}
    code, out = fx.run(r)
    return code == 1 and "R-01: proposed_focus changed, but no auditor decision asked" in out, out


@case("revision: edit after approval without a new decision -> E-REVISION")
def _(fx):
    fx.run(ratings())
    fx.decide(R_01=("Approve", ""))
    r = ratings()
    r["revision"] = {"number": 1, "changes": []}
    ok1 = fx.run(r)[0] == 0
    r["risks"][0]["title"] = "Clustering below the threshold"
    code, out = fx.run(r)
    return ok1 and code == 1 and "R-01: title changed, but there is no new auditor decision" in out, out


@case("decisions survive a rewrite of auditor-comments.md")
def _(fx):
    fx.run(ratings())
    fx.decide(R_01=("Reject", "covered by the AP audit"))
    r = ratings()
    r["revision"] = {"number": 1, "changes": []}
    code, out = fx.run(r)
    com, reg = fx.read("auditor-comments.md"), fx.read("risk-register.md")
    return all([code == 0, "| Reject | covered by the AP audit |" in com,
                "R-01 rejected by the auditor" in reg, "rejected (out of scope)" in reg]), out


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
