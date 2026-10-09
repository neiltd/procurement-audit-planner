#!/usr/bin/env python3
"""Quote check: every rule quote exists in the PDF and the register quotes rules.json exactly.

1. Runs the extract-rules verifier on outputs/rules.json against
   data/contract-rules.pdf (schema, clause coverage, each verbatim_quote on its page).
2. Checks every rule excerpt in outputs/risk-register.md
   ("- CPR-65 (App B row B1, p12): “...”") against rules.json: the rule exists,
   clause and page match, and the excerpt is the verbatim_quote or, when it
   ends in "…", its exact opening.

Usage: check_quotes.py [--root DIR] [--verifier PATH]
"""
import re
import subprocess
import sys
from pathlib import Path

from qa_common import REPO, Result, load_json, parse_args

VERIFIER = REPO / ".claude" / "skills" / "extract-rules" / "verify_quotes.py"
EXCERPT_RE = re.compile(r"^- (CPR-\d+) \((.+?), p(\d+)\): “(.*)”\s*$")


def main():
    args = parse_args(__doc__, lambda ap: ap.add_argument("--verifier", default=str(VERIFIER)))
    root = Path(args.root)
    r = Result("check_quotes")
    rules_path, pdf = root / "outputs" / "rules.json", root / "data" / "contract-rules.pdf"
    for p in (rules_path, pdf):
        if not p.exists():
            return r.cannot(f"{p.relative_to(root)} is missing")

    p = subprocess.run([sys.executable, args.verifier, "--rules", str(rules_path), "--pdf", str(pdf)],
                       capture_output=True, text=True)
    out = (p.stdout + p.stderr).strip().splitlines()
    if p.returncode == 2:
        return r.cannot(f"verify_quotes.py could not run: {' '.join(out)}")
    if p.returncode != 0:
        for line in out:
            if line.strip() and not line.startswith("FAIL:"):
                r.fail(f"verify_quotes: {line.strip()}")
        if not r.problems:
            r.fail(f"verify_quotes exited {p.returncode}: {' '.join(out)}")
    verifier_line = next((line for line in reversed(out) if line.startswith(("PASS", "FAIL"))), "no summary")

    rules = {x["rule_id"]: x for x in load_json(rules_path).get("rules", [])}
    reg = root / "outputs" / "risk-register.md"
    if not reg.exists():
        r.fail("outputs/risk-register.md is missing")
        return r.finish(f"verifier: {verifier_line}")
    n = 0
    for i, line in enumerate(reg.read_text(encoding="utf-8").splitlines(), 1):
        m = EXCERPT_RE.match(line)
        if not m:
            continue
        n += 1
        rid, clause, page, quote = m.groups()
        rule = rules.get(rid)
        where = f"risk-register.md:{i} {rid}"
        if not rule:
            r.fail(f"{where}: not in rules.json")
            continue
        if clause != rule["clause"] or int(page) != rule["page"]:
            r.fail(f"{where}: cited as ({clause}, p{page}), rules.json has ({rule['clause']}, p{rule['page']})")
        full = rule["verbatim_quote"]
        ok = full.startswith(quote[:-1]) if quote.endswith("…") else quote == full
        if not ok:
            r.fail(f"{where}: excerpt “{quote[:60]}…” does not match its verbatim_quote in rules.json")
    if n == 0:
        r.fail("risk-register.md: no rule excerpts found (expected lines like '- CPR-65 (clause, p12): “...”')")
    return r.finish(f"verifier: {verifier_line}; {n} register excerpt(s) checked")


if __name__ == "__main__":
    sys.exit(main())
