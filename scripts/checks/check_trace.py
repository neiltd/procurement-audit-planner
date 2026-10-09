#!/usr/bin/env python3
"""Traceability check: rule -> risk -> control -> test is complete, and the challenge log is closed.

- Every rule in rules.json is cited by a rated risk (risk-ratings.json), a control
  or a test (audit-plan.json), or listed in not_tested with a reason.
- Every approved in-scope risk (Approve or Change in auditor-comments.md) has a
  control with a test, and appears in risk-control-matrix.md and audit-program.md;
  every planned test appears in audit-program.md.
- Every High risk (score 8 or above: the council's Medium - High and Extreme
  bands, labelled High or Extreme in its matrix) is in scope, or rejected with a
  reason in its auditor comment.
- outputs/challenges.md exists; every row of its table cites evidence that
  resolves, and no row is open. These items start with "challenges.md".

Usage: check_trace.py [--root DIR]
"""
import re
import sys
from pathlib import Path

from qa_common import CITE_RE, Report, Sources, load_json, parse_args, parse_decisions, Result

HIGH_SCORE = 8
CLOSED = {"resolved", "declined", "for the auditor"}
STAMP_RE = re.compile(r"^\s*\[\d{4}-\d{2}-\d{2}\]\s*")


def risk_texts(r):
    return [r.get("description"), r["likelihood"].get("justification"), r["impact"].get("justification"),
            r.get("proposed_focus"), (r.get("repeat_uplift") or {}).get("justification")]


def rules_in(text):
    return {ref for kind, ref in CITE_RE.findall(text or "") if kind == "rule"}


def check_challenges(path, src, r):
    if not path.exists():
        r.fail("challenges.md: outputs/challenges.md is missing")
        return 0
    lines = path.read_text(encoding="utf-8").splitlines()
    head = next((i for i, l in enumerate(lines) if l.startswith("|") and "status" in l.lower()), None)
    if head is None:
        r.fail("challenges.md: no table with a Status column")
        return 0
    cols = [c.strip().lower() for c in lines[head].strip().strip("|").split("|")]
    status_at = cols.index("status")
    n = 0
    for i in range(head + 2, len(lines)):
        line = lines[i]
        if not line.startswith("|"):
            break
        n += 1
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        label = f"challenges.md:{i + 1} #{cells[0]}"
        cites = CITE_RE.findall(line)
        if not cites:
            r.fail(f"{label}: cites no evidence ([rule:..], [metric:..] or [history:..])")
        for kind, ref in cites:
            if src.resolve(kind, ref) is None:
                r.fail(f"{label}: [{kind}:{ref}] does not resolve")
        status = cells[status_at].lower() if status_at < len(cells) else ""
        if status == "open":
            r.fail(f"{label}: status is open")
        elif status not in CLOSED:
            r.fail(f"{label}: status '{cells[status_at] if status_at < len(cells) else ''}' is not one of "
                   "resolved, declined, for the auditor")
    return n


def main():
    args = parse_args(__doc__)
    out = Path(args.root) / "outputs"
    r = Result("check_trace")
    need = ("rules.json", "analytics.json", "history.json", "risk-ratings.json", "risk-register.state.json",
            "auditor-comments.md", "audit-plan.json")
    for name in need:
        if not (out / name).exists():
            return r.cannot(f"outputs/{name} is missing")
    rules = {x["rule_id"] for x in load_json(out / "rules.json").get("rules", [])}
    ratings = {x["id"]: x for x in load_json(out / "risk-ratings.json")["risks"]}
    state = load_json(out / "risk-register.state.json")
    plan = load_json(out / "audit-plan.json")
    rep = Report()
    decisions = parse_decisions(out / "auditor-comments.md", rep)
    for e in rep.errors:
        r.fail(f"auditor-comments.md: {e}")
    src = Sources(load_json(out / "rules.json"), load_json(out / "analytics.json"), load_json(out / "history.json"))

    # Rule coverage.
    rated = state.get("rated", {})
    cited = set()
    for rid in rated:
        if rid in ratings:
            for t in risk_texts(ratings[rid]):
                cited |= rules_in(t)
    planned = {}
    for pr in plan.get("risks", []):
        planned[pr["risk"]] = pr
        for c in pr.get("controls", []):
            cited |= rules_in(c.get("control"))
            for t in c.get("tests", []):
                cited |= rules_in(t.get("step"))
    not_tested = {n.get("rule"): str(n.get("reason", "")).strip() for n in plan.get("not_tested", [])}
    for rid in sorted(rules):
        if rid in cited:
            continue
        if rid not in not_tested:
            r.fail(f"{rid}: not cited by a rated risk, a control or a test, and not listed as not tested")
        elif not not_tested[rid]:
            r.fail(f"{rid}: listed as not tested with no reason")

    # Scope -> control -> test -> documents.
    matrix = (out / "risk-control-matrix.md").read_text(encoding="utf-8") if (out / "risk-control-matrix.md").exists() else ""
    program = (out / "audit-program.md").read_text(encoding="utf-8") if (out / "audit-program.md").exists() else ""
    for name, text in (("risk-control-matrix.md", matrix), ("audit-program.md", program)):
        if not text:
            r.fail(f"outputs/{name} is missing")
    scope = [rid for rid in sorted(rated) if decisions.get(rid, {}).get("decision") in ("Approve", "Change")]
    for rid in sorted(rated):
        d = decisions.get(rid, {}).get("decision")
        if not d:
            r.fail(f"{rid}: no decision in auditor-comments.md")
    for rid in scope:
        pr = planned.get(rid)
        if not pr or not pr.get("controls"):
            r.fail(f"{rid}: approved, but audit-plan.json has no control for it")
        else:
            for c in pr["controls"]:
                if not c.get("tests"):
                    r.fail(f"{rid} {c.get('id')}: control has no test")
                for t in c.get("tests", []):
                    if program and not re.search(rf"^#### {re.escape(t['id'])}\b", program, re.M):
                        r.fail(f"{rid} {t['id']}: not in audit-program.md")
        if matrix and not re.search(rf"^\| {rid}\b", matrix, re.M):
            r.fail(f"{rid}: approved, but not in risk-control-matrix.md")
        if program and not re.search(rf"^## {rid}\b", program, re.M):
            r.fail(f"{rid}: approved, but not in audit-program.md")

    # High risks.
    high = [rid for rid, x in rated.items() if x.get("score", 0) >= HIGH_SCORE]
    for rid in sorted(high):
        d = decisions.get(rid, {})
        if d.get("decision") == "Reject" and not STAMP_RE.sub("", d.get("comment", "")).strip():
            r.fail(f"{rid}: High risk (score {rated[rid]['score']}) rejected with no reason in its comment")

    n_challenges = check_challenges(out / "challenges.md", src, r)
    return r.finish(f"{len(rules)} rules, {len(scope)} approved risk(s), {len(high)} High, "
                    f"{n_challenges} challenge(s)")


if __name__ == "__main__":
    sys.exit(main())
