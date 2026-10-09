#!/usr/bin/env python3
"""Build the audit planning pack from the planner's judgments.

Reads outputs/audit-plan.json (the planner's controls, test steps, sample
recipes, PBC items and memo prose with citation tags and {{$.path}}
placeholders) together with the approved register (risk-register.state.json,
auditor-comments.md, risk-ratings.json), rules.json, analytics.json,
history.json and the flagged lists in outputs/analytics-full/. Computes the
approved scope, resolves every citation, draws every sample deterministically,
checks every sampled transaction exists in analytics-full/spend_clean.csv, checks
every control has a test and every rule is accounted for, and writes:

  outputs/planning-memo.md        scope, the planner's memo sections, sample summary
  outputs/risk-control-matrix.md  risk -> control -> rule -> test, and rule coverage
  outputs/audit-program.md        test steps, samples, transactions to pull, PBC list
  outputs/samples/T-*.csv         the transactions each test pulls
  outputs/pack-figures.json       every figure this builder computed

Any defect is an error: nothing is written.

Usage:
  build_pack.py [--root DIR] [--gate]

--gate runs only the gate check: every register risk decided, the decisions
applied in a register revision, and the register built from the current inputs.

Exit codes: 0 built (or gate open), 1 errors found (or gate closed), 2 cannot run.
Standard library only. Shares its placeholder, citation and decision parsing with
.claude/skills/risk-assessment/build_register.py.
"""
import argparse
import csv
import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "risk-assessment"))
from build_register import (CITE_RE, FORMATS, PLACEHOLDER_RE, Report, Sources, cell,  # noqa: E402
                            check_prose, fmt_value, is_number, load_json, parse_decisions, resolve_path, sha256)

PLAN_KEYS = {"memo", "risks", "not_tested"}
MEMO_KEYS = {"sections"}
SECTION_KEYS = {"heading", "text"}
REQUIRED_SECTIONS = ("objective", "approach", "limitations")
RISK_KEYS = {"risk", "controls"}
CONTROL_KEYS = {"id", "control", "tests"}
TEST_KEYS = {"id", "step", "sample", "pbc"}
SAMPLE_KEYS = {"from", "records", "filter", "sort", "pick", "rationale"}
FILTER_KEYS = {"col", "op", "value"}
SORT_KEYS = {"col", "desc"}
NOT_TESTED_KEYS = {"rule", "reason"}
OPS = {"eq", "ne", "in", "not_in", "gt", "gte", "lt", "lte", "contains"}
OP_TEXT = {"eq": "=", "ne": "≠", "in": "in", "not_in": "not in", "gt": ">", "gte": "≥", "lt": "<", "lte": "≤",
           "contains": "contains"}
PICKS = {"top": "from the top of", "interval": "at even intervals through"}
CONTROL_ID_RE = re.compile(r"^C-\d{2,}$")
TEST_ID_RE = re.compile(r"^T-\d{2,}$")

# Units sampled per test, by risk score (likelihood x impact). The ranges follow
# the council's bands: Extreme 15-25, Medium - High 8-12, Moderate 4-6, Low up to 3.
SAMPLE_SIZES = ((15, 25), (8, 15), (4, 8), (1, 3))
RATED_INPUTS = ("analytics", "history", "rules", "risk-ratings")
SPEND_FILE = "spend_clean.csv"
SAMPLE_COLUMNS = ["test", "unit", "unit_supplier", "row_id", "source_file", "sheet_row", "Date", "Supplier name",
                  "Net amount", "Service", "Expenditure category", "Narrative"]

OUT_STATE = "outputs/risk-register.state.json"
OUT_COMMENTS = "outputs/auditor-comments.md"
OUT_PLAN = "outputs/audit-plan.json"
OUT_MEMO = "outputs/planning-memo.md"
OUT_MATRIX = "outputs/risk-control-matrix.md"
OUT_PROGRAM = "outputs/audit-program.md"
OUT_FIGURES = "outputs/pack-figures.json"
OUT_SAMPLES = "outputs/samples"

INDICATOR_NOTE = ("The analytics are risk indicators to investigate, not findings of wrongdoing by the council, "
                  "a service or a supplier.")


def size_for(score):
    return next(n for low, n in SAMPLE_SIZES if score >= low)


def num(x):
    if is_number(x):
        return float(x)
    try:
        return float(str(x).replace(",", "").strip())
    except ValueError:
        return None


# ---------------------------------------------------------------- gate

def check_gate(root, rep):
    """Return the approved scope, or None with errors in rep when the gate is closed."""
    state_path = root / OUT_STATE
    if not state_path.exists():
        rep.error("E-GATE", f"{OUT_STATE} is missing: build the risk register first")
        return None
    state = json.loads(state_path.read_text(encoding="utf-8"))
    revision = state.get("revision", 0)
    if revision < 1:
        rep.error("E-GATE", f"the register is at revision {revision}, a draft; the auditor's decisions must be "
                            "applied in revision 1 or later")
    for k in RATED_INPUTS:
        p = root / "outputs" / f"{k}.json"
        if not p.exists():
            rep.error("E-GATE", f"outputs/{k}.json is missing")
        elif state.get("inputs", {}).get(k) != sha256(p):
            rep.error("E-GATE", f"outputs/{k}.json changed after register revision {revision} was built; "
                                "rebuild the register")
    decisions = parse_decisions(root / OUT_COMMENTS, rep)
    applied = state.get("applied_decisions", {})
    rated = state.get("rated", {})
    scope, rejected = [], []
    for rid in sorted(rated):
        d = decisions.get(rid, {}).get("decision")
        if not d:
            rep.error("E-GATE", f"{rid} has no decision in auditor-comments.md")
            continue
        if decisions[rid] != applied.get(rid):
            rep.error("E-GATE", f"{rid}: decision '{d}' is not applied in register revision {revision}; "
                                "re-run the risk-assessor")
            continue
        (rejected if d == "Reject" else scope).append(rid)
    general = decisions.get("GENERAL")
    if general and general["decision"] and general != applied.get("GENERAL"):
        rep.error("E-GATE", f"GENERAL: decision '{general['decision']}' is not applied in register revision "
                            f"{revision}; re-run the risk-assessor")
    if not scope and not rep.errors:
        rep.error("E-GATE", "the auditor approved no risks, so there is nothing to plan")
    return {"state": state, "revision": revision, "decisions": decisions, "rated": rated,
            "scope": scope, "rejected": rejected}


# ---------------------------------------------------------------- text

class Text:
    """Resolves citations and placeholders. {{$.x}} reads analytics.json, {{$pack.x}} reads pack figures."""

    def __init__(self, src, analytics):
        self.src, self.analytics, self.figures, self.filled = src, analytics, None, []

    def value(self, path):
        if path == "$pack" or path.startswith("$pack."):
            if self.figures is None:
                raise KeyError(path)
            return resolve_path(self.figures, "$" + path[len("$pack"):])
        return resolve_path(self.analytics, path)

    def check(self, text, where, rep, need=None):
        """Check placeholders, citations and wording; return the citations as (kind, ref)."""
        if not isinstance(text, str) or not text.strip():
            rep.error("E-SCHEMA", f"{where}: text is missing")
            return []
        for m in PLACEHOLDER_RE.finditer(text):
            path, f = m.group(1), m.group(2)
            if f and f not in FORMATS:
                rep.error("E-PLACEHOLDER", f"{where}: unknown format '|{f}' (use {', '.join(sorted(FORMATS))})")
                continue
            if path.startswith("$pack") and self.figures is None:
                rep.error("E-PLACEHOLDER", f"{where}: {{{{{path}}}}} pack figures are for memo sections only")
                continue
            try:
                v = self.value(path)
            except KeyError:
                home = "pack-figures.json" if path.startswith("$pack") else "analytics.json"
                rep.error("E-PLACEHOLDER", f"{where}: {{{{{path}}}}} does not exist in {home}")
                continue
            if isinstance(v, (dict, list)) or v is None:
                rep.error("E-PLACEHOLDER", f"{where}: {{{{{path}}}}} is not a single value")
            elif f and not is_number(v):
                rep.error("E-PLACEHOLDER", f"{where}: {{{{{path}}}}} is not a number, so '|{f}' cannot apply")
        if re.search(r"\{\{|\}\}", PLACEHOLDER_RE.sub("", text)):
            rep.error("E-PLACEHOLDER", f"{where}: malformed placeholder (write {{{{$.path}}}} or {{{{$.path|gbp}}}})")
        cites = CITE_RE.findall(text)
        for kind, ref in cites:
            if self.src.resolve(kind, ref) is None:
                rep.error("E-CITE", f"{where}: [{kind}:{ref}] does not resolve")
        if need and not any(k in need for k, _ in cites):
            rep.error("E-CITE", f"{where}: cites no {' or '.join(need)}")
        check_prose(text, where, rep)
        return cites

    def render(self, text, where):
        def ph(m):
            v = self.value(m.group(1))
            out = fmt_value(v, m.group(2))
            self.filled.append({"where": where, "path": m.group(1), "value": v, "printed": out})
            return out

        text = PLACEHOLDER_RE.sub(ph, text)
        return CITE_RE.sub(lambda m: f"[`{m.group(2)}`]" if m.group(1) == "metric" else f"[{m.group(2)}]", text)


def rule_ids(cites):
    return {ref for kind, ref in cites if kind == "rule"}


# ---------------------------------------------------------------- plan

def unknown_keys(obj, allowed, where, rep, required=()):
    """Report unknown and missing keys; return False when obj is unusable."""
    if not isinstance(obj, dict):
        rep.error("E-SCHEMA", f"{where}: expected an object")
        return False
    for k in sorted(set(obj) - allowed):
        rep.error("E-SCHEMA", f"{where}: unknown key '{k}'")
    missing = [k for k in required if k not in obj]
    for k in missing:
        rep.error("E-SCHEMA", f"{where}: '{k}' is missing")
    return not missing


def validate_plan(plan, gate, rep):
    if not unknown_keys(plan, PLAN_KEYS, "audit-plan.json", rep):
        return
    memo = plan.get("memo")
    if unknown_keys(memo, MEMO_KEYS, "memo", rep):
        sections = memo.get("sections")
        if not isinstance(sections, list) or not sections:
            rep.error("E-SCHEMA", "memo.sections must be a non-empty list")
        else:
            for i, s in enumerate(sections):
                if unknown_keys(s, SECTION_KEYS, f"memo.sections[{i}]", rep, ("heading", "text")) and not s["heading"]:
                    rep.error("E-SCHEMA", f"memo.sections[{i}]: heading is missing")
            heads = " ".join(str(s.get("heading", "")).lower() for s in sections if isinstance(s, dict))
            for h in REQUIRED_SECTIONS:
                if h not in heads:
                    rep.error("E-SCHEMA", f"memo: no section headed '{h.capitalize()}'")

    risks = plan.get("risks")
    if not isinstance(risks, list):
        rep.error("E-SCHEMA", "risks must be a list")
        return
    seen_risks, seen_ids = set(), set()
    for i, r in enumerate(risks):
        if not unknown_keys(r, RISK_KEYS, f"risks[{i}]", rep, ("risk", "controls")):
            continue
        rid = r.get("risk")
        if rid in seen_risks:
            rep.error("E-SCOPE", f"{rid} appears twice in audit-plan.json")
        seen_risks.add(rid)
        if rid in gate["rejected"]:
            rep.error("E-SCOPE", f"{rid} was rejected by the auditor and cannot be planned")
        elif rid not in gate["scope"]:
            rep.error("E-SCOPE", f"{rid} is not an approved risk in the register")
        controls = r.get("controls")
        if not isinstance(controls, list) or not controls:
            rep.error("E-TRACE", f"{rid}: no expected control")
            continue
        for c in controls:
            if not unknown_keys(c, CONTROL_KEYS, f"{rid} control", rep, ("id", "control", "tests")):
                continue
            cid = c.get("id", "")
            if not CONTROL_ID_RE.match(str(cid)):
                rep.error("E-SCHEMA", f"{rid}: control id '{cid}' is not C-01 style")
            if cid in seen_ids:
                rep.error("E-SCHEMA", f"{cid} is used twice")
            seen_ids.add(cid)
            tests = c.get("tests")
            if not isinstance(tests, list) or not tests:
                rep.error("E-TRACE", f"{cid}: control has no test")
                continue
            for t in tests:
                if not unknown_keys(t, TEST_KEYS, f"{cid} test", rep, ("id", "step", "sample", "pbc")):
                    continue
                tid = t.get("id", "")
                if not TEST_ID_RE.match(str(tid)):
                    rep.error("E-SCHEMA", f"{cid}: test id '{tid}' is not T-01 style")
                if tid in seen_ids:
                    rep.error("E-SCHEMA", f"{tid} is used twice")
                seen_ids.add(tid)
                pbc = t.get("pbc")
                if not isinstance(pbc, list) or not pbc or not all(isinstance(p, str) and p.strip() for p in pbc):
                    rep.error("E-SCHEMA", f"{tid}: pbc must list at least one item the test needs")
                s = t.get("sample")
                if not unknown_keys(s, SAMPLE_KEYS, f"{tid} sample", rep):
                    continue
                if ("from" in s) == ("records" in s):
                    rep.error("E-SAMPLE", f"{tid}: sample needs exactly one of 'from' (a file in analytics-full) "
                                          "or 'records' (a council record population)")
                if "records" in s and any(k in s for k in ("filter", "sort", "pick")):
                    rep.error("E-SAMPLE", f"{tid}: a 'records' sample is drawn on site; filter, sort and pick "
                                          "apply only to 'from'")
                if s.get("pick", "top") not in PICKS:
                    rep.error("E-SAMPLE", f"{tid}: pick '{s.get('pick')}' is not one of {', '.join(PICKS)}")
                for f in s.get("filter", []):
                    if unknown_keys(f, FILTER_KEYS, f"{tid} filter", rep, ("col", "op", "value")) and f.get("op") not in OPS:
                        rep.error("E-SAMPLE", f"{tid}: filter op '{f.get('op')}' is not one of {', '.join(sorted(OPS))}")
                for o in s.get("sort", []):
                    unknown_keys(o, SORT_KEYS, f"{tid} sort", rep, ("col",))
    for rid in gate["scope"]:
        if rid not in seen_risks:
            rep.error("E-SCOPE", f"{rid} is approved but has no entry in audit-plan.json")
    nt = plan.get("not_tested", [])
    if not isinstance(nt, list):
        rep.error("E-SCHEMA", "not_tested must be a list")
    else:
        for i, n in enumerate(nt):
            if unknown_keys(n, NOT_TESTED_KEYS, f"not_tested[{i}]", rep, ("rule", "reason")) and not str(n.get("reason", "")).strip():
                rep.error("E-RULE", f"not_tested {n.get('rule')}: a reason is required")


# ---------------------------------------------------------------- samples

def load_csv(path):
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames or [], list(reader)


def matches(row, f):
    v, want, op = row[f["col"]], f["value"], f["op"]

    def eq(a, b):
        b = ("True" if b else "False") if isinstance(b, bool) else b
        na, nb = num(a), num(b)
        if na is not None and nb is not None:
            return na == nb
        return str(a).strip() == str(b).strip()

    if op in ("in", "not_in"):
        hit = any(eq(v, w) for w in want)
        return hit if op == "in" else not hit
    if op in ("eq", "ne"):
        return eq(v, want) == (op == "eq")
    if op == "contains":
        return str(want).lower() in str(v).lower()
    nv, nw = num(v), num(want)
    if nv is None:
        return False
    return {"gt": nv > nw, "gte": nv >= nw, "lt": nv < nw, "lte": nv <= nw}[op]


def sort_key(v):
    n = num(v)
    return (0, n, "") if n is not None else (1, 0.0, str(v))


def draw(tid, s, size, full_dir, spend, rep):
    """Draw a sample deterministically. Return the sample record, or None on error."""
    if "records" in s:
        return {"kind": "records", "population": s["records"], "size": size, "units": []}
    name = s["from"]
    path = full_dir / name
    if "/" in name or not name.endswith(".csv") or not path.exists():
        rep.error("E-SAMPLE", f"{tid}: '{name}' is not a CSV in outputs/analytics-full/")
        return None
    cols, rows = load_csv(path)
    id_col = "row_id" if "row_id" in cols else "row_ids" if "row_ids" in cols else None
    if not id_col:
        rep.error("E-SAMPLE", f"{tid}: {name} has no row_id or row_ids column, so it lists no transactions")
        return None
    bad = False
    for f in s.get("filter", []):
        if f["col"] not in cols:
            rep.error("E-SAMPLE", f"{tid}: filter column '{f['col']}' is not in {name}")
            bad = True
        elif f["op"] in ("in", "not_in") and not isinstance(f["value"], list):
            rep.error("E-SAMPLE", f"{tid}: filter '{f['op']}' on '{f['col']}' needs a list value")
            bad = True
        elif f["op"] in ("gt", "gte", "lt", "lte") and num(f["value"]) is None:
            rep.error("E-SAMPLE", f"{tid}: filter '{f['op']}' on '{f['col']}' needs a number")
            bad = True
    for o in s.get("sort", []):
        if o["col"] not in cols:
            rep.error("E-SAMPLE", f"{tid}: sort column '{o['col']}' is not in {name}")
            bad = True
    if bad:
        return None
    pop = [(i, r) for i, r in enumerate(rows, 2) if all(matches(r, f) for f in s.get("filter", []))]
    if not pop:
        rep.error("E-SAMPLE", f"{tid}: the filter leaves no rows in {name}")
        return None
    for o in reversed(s.get("sort", [])):
        pop.sort(key=lambda ir: sort_key(ir[1][o["col"]]), reverse=bool(o.get("desc")))
    n = min(size, len(pop))
    if s.get("pick", "top") == "interval":
        picked = [pop[k * len(pop) // n] for k in range(n)]
    else:
        picked = pop[:n]

    units, seen = [], set()
    for rank, (line, r) in enumerate(picked, 1):
        ids = [x.strip() for x in r[id_col].split(";") if x.strip()]
        missing = [x for x in ids if x not in spend]
        if not ids or missing:
            rep.error("E-SAMPLE", f"{tid}: {name} line {line} lists {', '.join(missing) or 'no row id'}, "
                                  f"not found in {SPEND_FILE}")
            continue
        fresh = [x for x in ids if x not in seen]
        seen.update(fresh)
        units.append({"unit": rank, "line": line, "supplier": r.get("supplier_norm", ""), "row_ids": fresh,
                      "repeated": len(ids) - len(fresh),
                      "gbp": round(sum(num(spend[x]["Net amount"]) or 0.0 for x in fresh), 2)})
    return {"kind": "file", "file": name, "population": len(pop), "size": size, "units": units}


def filter_text(s):
    parts = []
    for f in s.get("filter", []):
        v = ", ".join(map(str, f["value"])) if isinstance(f["value"], list) else str(f["value"])
        parts.append(f"{f['col']} {OP_TEXT[f['op']]} {v}")
    return "; ".join(parts) or "no filter"


def sort_text(s):
    return ", ".join(f"{o['col']} {'descending' if o.get('desc') else 'ascending'}" for o in s.get("sort", [])) \
        or "file order"


# ---------------------------------------------------------------- render

def header(revision, today):
    return (f"Built {today} by `.claude/skills/audit-program/build_pack.py` from `{OUT_PLAN}`, on risk register "
            f"revision {revision}. Every figure is filled from `outputs/analytics.json` or computed by the builder "
            f"and listed in `{OUT_FIGURES}`. {INDICATOR_NOTE}\n")


def render_memo(ctx):
    g, figs, txt = ctx["gate"], ctx["figures"], ctx["text"]
    out = ["# Planning memo: procurement audit, West Berkshire Council", "",
           header(g["revision"], ctx["today"]),
           "## Scope", "",
           f"The auditor's decisions in `{OUT_COMMENTS}` (register revision {g['revision']}) put "
           f"{figs['counts']['risks_in_scope']} risk(s) in scope and {figs['counts']['risks_rejected']} out.", "",
           "| Risk | Title | L | I | Score | Band | Decision | Controls | Tests | Sample size per test |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for rid in g["scope"]:
        r, f = ctx["risks"][rid], figs["risks"][rid]
        out.append(f"| {rid} | {cell(r['_title'])} | {f['likelihood']} | {f['impact']} | {f['score']} | "
                   f"{cell(f['band'])} | {g['decisions'][rid]['decision']} | {f['controls']} | {f['tests']} | "
                   f"{f['sample_size']} |")
    if g["rejected"]:
        out += ["", "Out of scope, by the auditor's decision:", "", "| Risk | Title | Auditor's comment |",
                "|---|---|---|"]
        for rid in g["rejected"]:
            out.append(f"| {rid} | {cell(ctx['risks'][rid]['_title'])} | {cell(g['decisions'][rid]['comment'])} |")
    general = g["decisions"].get("GENERAL")
    if general and general["comment"]:
        out += ["", f"General scope comment from the auditor: “{general['comment']}”"]
    for i, s in enumerate(ctx["plan"]["memo"]["sections"]):
        out += ["", f"## {s['heading']}", "", txt.render(s["text"], f"memo.sections[{i}]")]
    out += ["", "## Samples", "",
            "Sample size per test follows the risk score: "
            + ", ".join(f"score {lo}+ → {n}" for lo, n in SAMPLE_SIZES)
            + ". Samples are drawn by a fixed filter and sort, so a rebuild draws the same items.", "",
            "| Test | Risk | Drawn from | Population | Sampled | Transactions | Net £ |",
            "|---|---|---|---|---|---|---|"]
    for tid, f in figs["samples"].items():
        if f["kind"] == "records":
            out.append(f"| {tid} | {f['risk']} | {cell(f['population_text'])} (on site) | n/a | {f['size']} | "
                       f"n/a | n/a |")
        else:
            out.append(f"| {tid} | {f['risk']} | `analytics-full/{f['file']}` | {f['population']:,} | {f['units']} | "
                       f"{f['transactions']:,} | {fmt_value(f['gbp'], 'gbp')} |")
    return "\n".join(out) + "\n"


def render_matrix(ctx):
    g, figs, txt, plan = ctx["gate"], ctx["figures"], ctx["text"], ctx["plan"]
    out = ["# Risk and control matrix", "", header(g["revision"], ctx["today"]),
           "| Risk | Score | Expected control | Rules | Tests |", "|---|---|---|---|---|"]
    for r in plan["risks"]:
        rid, f = r["risk"], figs["risks"][r["risk"]]
        for c in r["controls"]:
            rules = ", ".join(sorted(rule_ids(CITE_RE.findall(c["control"]))))
            tests = ", ".join(t["id"] for t in c["tests"])
            out.append(f"| {rid} {cell(ctx['risks'][rid]['_title'])} | {f['score']}, {cell(f['band'])} | "
                       f"{c['id']}: {cell(txt.render(c['control'], c['id']))} | {rules} | {tests} |")
    cov = figs["coverage"]
    out += ["", "## Rule coverage", "",
            f"{cov['rules_total']} rules in `outputs/rules.json`, {cov['accounted']} accounted for. Cited by an "
            f"approved risk: {cov['cited_by_risk']}; by a control: {cov['cited_by_control']}; by a test step: "
            f"{cov['cited_by_test']} (a rule can be cited in more than one place). Not tested, with a reason: "
            f"{cov['not_tested']}.", ""]
    if plan.get("not_tested"):
        out += ["### Rules not tested", "", "| Rule | Clause | Reason |", "|---|---|---|"]
        for n in plan["not_tested"]:
            rule = ctx["rules"].get(n["rule"], {})
            out.append(f"| {n['rule']} | {cell(rule.get('clause', ''))} | {cell(txt.render(n['reason'], n['rule']))} |")
    return "\n".join(out) + "\n"


def render_program(ctx):
    g, figs, txt, plan = ctx["gate"], ctx["figures"], ctx["text"], ctx["plan"]
    out = ["# Audit program", "", header(g["revision"], ctx["today"]),
           "Each test pulls the transactions in `outputs/samples/<test>.csv`. A flagged item is a prompt to request "
           "evidence; a complete record closes it.", ""]
    for r in plan["risks"]:
        rid, f = r["risk"], figs["risks"][r["risk"]]
        out += [f"## {rid} {ctx['risks'][rid]['_title']}", "",
                f"Score {f['score']} (likelihood {f['likelihood']} × impact {f['impact']}), {f['band']}. "
                f"Sample size per test: {f['sample_size']}.", ""]
        for c in r["controls"]:
            out += [f"### {c['id']} Expected control", "", txt.render(c["control"], c["id"]), ""]
            for t in c["tests"]:
                tid, s, sf = t["id"], t["sample"], figs["samples"][t["id"]]
                out += [f"#### {tid}", "", f"**Test step.** {txt.render(t['step'], tid)}", ""]
                if sf["kind"] == "records":
                    out.append(f"**Sample.** Select {sf['size']} items from {s['records']}. The population sits in "
                               "council records, so the builder draws nothing; record the items chosen in the "
                               "working papers.")
                else:
                    pick = PICKS[s.get("pick", "top")]
                    out.append(f"**Sample.** {sf['units']} of {sf['population']:,} rows in "
                               f"`analytics-full/{sf['file']}` where {filter_text(s)}, sorted by {sort_text(s)}, "
                               f"taking units {pick} the list. {sf['transactions']:,} transactions, "
                               f"{fmt_value(sf['gbp'], 'gbp')} net, in `{OUT_SAMPLES}/{tid}.csv`.")
                if s.get("rationale"):
                    out.append(f"Why this sample: {txt.render(s['rationale'], tid + ' rationale')}")
                out.append("")
                if sf["kind"] == "file":
                    out += ["| # | Supplier | Transactions | Net £ |", "|---|---|---|---|"]
                    for u in ctx["samples"][tid]["units"]:
                        note = f" (+{u['repeated']} already pulled)" if u["repeated"] else ""
                        out.append(f"| {u['unit']} | {cell(u['supplier'])} | {len(u['row_ids'])}{note} | "
                                   f"{fmt_value(u['gbp'], 'gbp')} |")
                    out.append("")
                out += [f"**PBC.** {', '.join(ctx['pbc_by_test'][tid])}", ""]
    out += ["## PBC list", "", "Request these from the council before fieldwork.", "",
            "| # | Item | For tests |", "|---|---|---|"]
    for p in ctx["pbc"]:
        out.append(f"| {p['id']} | {cell(p['item'])} | {', '.join(p['tests'])} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    ap.add_argument("--gate", action="store_true", help="run only the gate check")
    args = ap.parse_args()
    root = Path(args.root)

    rep = Report()
    gate = check_gate(root, rep)
    if args.gate or rep.errors:
        return finish_gate(rep, gate)

    docs = {k: load_json(root / "outputs" / f"{k}.json") for k in ("analytics", "history", "rules", "risk-ratings")}
    plan = load_json(root / OUT_PLAN)
    full_dir = root / "outputs" / "analytics-full"
    spend_path = full_dir / SPEND_FILE
    if not spend_path.exists():
        print(f"CANNOT RUN: {spend_path} is missing")
        return 2
    spend_cols, spend_rows = load_csv(spend_path)
    spend = {r["row_id"]: r for r in spend_rows}

    analytics, rules_doc, ratings = docs["analytics"], docs["rules"], docs["risk-ratings"]
    src = Sources(rules_doc, analytics, docs["history"])
    txt = Text(src, analytics)
    risks = {r["id"]: r for r in ratings["risks"]}
    for rid in gate["rated"]:
        if rid not in risks:
            rep.error("E-GATE", f"{rid} is in the register but not in risk-ratings.json")
    validate_plan(plan, gate, rep)
    if rep.errors:
        return finish(rep)
    for rid, r in risks.items():
        r["_title"] = txt.render(r["title"], f"{rid} title")

    # Citations and rule coverage.
    cited = {"risk": set(), "control": set(), "test": set()}
    for rid in gate["scope"]:
        r = risks[rid]
        for t in (r.get("description"), r["likelihood"].get("justification"), r["impact"].get("justification"),
                  r.get("proposed_focus"), (r.get("repeat_uplift") or {}).get("justification")):
            cited["risk"] |= rule_ids(CITE_RE.findall(t or ""))
    for r in plan["risks"]:
        for c in r["controls"]:
            cited["control"] |= rule_ids(txt.check(c["control"], c["id"], rep, need=("rule",)))
            for t in c["tests"]:
                cited["test"] |= rule_ids(txt.check(t["step"], t["id"], rep, need=("rule", "metric")))
                if t["sample"].get("rationale"):
                    txt.check(t["sample"]["rationale"], f"{t['id']} rationale", rep)
                for p in t["pbc"]:
                    check_prose(p, f"{t['id']} pbc", rep)
    rules = {r["rule_id"]: r for r in rules_doc.get("rules", [])}
    covered = cited["risk"] | cited["control"] | cited["test"]
    not_tested = {}
    for n in plan.get("not_tested", []):
        rid = n["rule"]
        if rid not in rules:
            rep.error("E-RULE", f"not_tested lists {rid}, which is not in rules.json")
        elif rid in not_tested:
            rep.error("E-RULE", f"not_tested lists {rid} twice")
        else:
            not_tested[rid] = n["reason"]
            txt.check(n["reason"], f"not_tested {rid}", rep)
            if rid in covered:
                rep.warn("W-RULE", f"{rid} is cited in the plan and also listed as not tested; drop one")
    for rid in rules:
        if rid not in covered and rid not in not_tested:
            rep.error("E-RULE", f"{rid} is not cited by an approved risk, a control or a test, and not listed in "
                                "not_tested with a reason")

    # Samples.
    rated = gate["rated"]
    samples, pbc, pbc_index, pbc_by_test = {}, [], {}, {}
    for r in plan["risks"]:
        size = size_for(rated[r["risk"]]["score"])
        for c in r["controls"]:
            for t in c["tests"]:
                d = draw(t["id"], t["sample"], size, full_dir, spend, rep)
                if d:
                    d["risk"] = r["risk"]
                    samples[t["id"]] = d
                ids = []
                for item in t["pbc"]:
                    key = " ".join(item.lower().split())
                    if key not in pbc_index:
                        pbc_index[key] = len(pbc)
                        pbc.append({"id": f"P-{len(pbc) + 1:02d}", "item": item.strip(), "tests": []})
                    p = pbc[pbc_index[key]]
                    if t["id"] not in p["tests"]:
                        p["tests"].append(t["id"])
                    ids.append(p["id"])
                pbc_by_test[t["id"]] = ids
    if rep.errors:
        return finish(rep)

    # Figures.
    figures = {
        "built": datetime.date.today().isoformat(),
        "register_revision": gate["revision"],
        "sample_sizes_by_score": [{"min_score": lo, "units": n} for lo, n in SAMPLE_SIZES],
        "risks": {}, "samples": {},
    }
    for r in plan["risks"]:
        rid = r["risk"]
        figures["risks"][rid] = {**{k: rated[rid][k] for k in ("likelihood", "impact", "score", "band")},
                                 "sample_size": size_for(rated[rid]["score"]),
                                 "controls": len(r["controls"]),
                                 "tests": sum(len(c["tests"]) for c in r["controls"])}
    for tid, d in samples.items():
        if d["kind"] == "records":
            figures["samples"][tid] = {"risk": d["risk"], "kind": "records", "population_text": d["population"],
                                       "size": d["size"]}
        else:
            figures["samples"][tid] = {
                "risk": d["risk"], "kind": "file", "file": d["file"], "population": d["population"],
                "size": d["size"], "units": len(d["units"]),
                "transactions": sum(len(u["row_ids"]) for u in d["units"]),
                "gbp": round(sum(u["gbp"] for u in d["units"]), 2),
                "sample_file": f"{OUT_SAMPLES}/{tid}.csv",
                "unit_list": [{"unit": u["unit"], "supplier": u["supplier"], "transactions": len(u["row_ids"]),
                               "repeated": u["repeated"], "gbp": u["gbp"]} for u in d["units"]]}
    file_samples = [f for f in figures["samples"].values() if f["kind"] == "file"]
    figures["counts"] = {
        "risks_in_scope": len(gate["scope"]), "risks_rejected": len(gate["rejected"]),
        "controls": sum(f["controls"] for f in figures["risks"].values()),
        "tests": sum(f["tests"] for f in figures["risks"].values()),
        "tests_sampled_from_data": len(file_samples),
        "tests_sampled_on_site": len(figures["samples"]) - len(file_samples),
        "sample_units": sum(f["units"] for f in file_samples),
        "transactions": sum(f["transactions"] for f in file_samples),
        "transactions_gbp": round(sum(f["gbp"] for f in file_samples), 2),
        "pbc_items": len(pbc)}
    figures["coverage"] = {
        "rules_total": len(rules), "cited_by_risk": len(cited["risk"] & set(rules)),
        "cited_by_control": len(cited["control"] & set(rules)), "cited_by_test": len(cited["test"] & set(rules)),
        "not_tested": len(not_tested), "accounted": len((covered & set(rules)) | set(not_tested))}

    # The memo may cite pack figures, so it is checked once they exist.
    txt.figures = figures
    for i, s in enumerate(plan["memo"]["sections"]):
        txt.check(s.get("text"), f"memo.sections[{i}]", rep)
    if rep.errors:
        return finish(rep)

    ctx = {"gate": gate, "plan": plan, "figures": figures, "text": txt, "risks": risks, "rules": rules,
           "samples": samples, "pbc": pbc, "pbc_by_test": pbc_by_test, "today": figures["built"]}
    memo, matrix, program = render_memo(ctx), render_matrix(ctx), render_program(ctx)
    figures["filled_from_analytics"] = [f for f in txt.filled if not f["path"].startswith("$pack")]
    figures["filled_from_pack"] = [f for f in txt.filled if f["path"].startswith("$pack")]

    (root / OUT_MEMO).write_text(memo, encoding="utf-8")
    (root / OUT_MATRIX).write_text(matrix, encoding="utf-8")
    (root / OUT_PROGRAM).write_text(program, encoding="utf-8")
    sample_dir = root / OUT_SAMPLES
    sample_dir.mkdir(parents=True, exist_ok=True)
    for old in sample_dir.glob("T-*.csv"):
        old.unlink()
    for tid, d in samples.items():
        if d["kind"] != "file":
            continue
        with (sample_dir / f"{tid}.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=SAMPLE_COLUMNS, extrasaction="ignore")
            w.writeheader()
            for u in d["units"]:
                for x in u["row_ids"]:
                    w.writerow({**spend[x], "test": tid, "unit": u["unit"], "unit_supplier": u["supplier"]})
    (root / OUT_FIGURES).write_text(json.dumps(figures, indent=1, ensure_ascii=False), encoding="utf-8")
    return finish(rep, built=(gate["revision"], figures["counts"]))


def finish_gate(rep, gate):
    if rep.errors:
        for e in rep.errors:
            print(e)
        print(f"GATE CLOSED: {len(rep.errors)} problem(s)")
        return 1
    rejected = f"; rejected {', '.join(gate['rejected'])}" if gate["rejected"] else ""
    print(f"GATE OPEN on register revision {gate['revision']}: in scope {', '.join(gate['scope'])}{rejected}")
    return 0


def finish(rep, built=None):
    for w in rep.warnings:
        print(f"WARN {w}")
    if rep.errors:
        for e in rep.errors:
            print(e)
        print(f"FAIL: {len(rep.errors)} error(s); nothing written")
        return 1
    revision, c = built
    print(f"BUILT pack on register revision {revision}: {c['risks_in_scope']} risk(s), {c['controls']} control(s), "
          f"{c['tests']} test(s), {c['transactions']} transaction(s) sampled, {c['pbc_items']} PBC item(s), "
          f"{len(rep.warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
