#!/usr/bin/env python3
"""Build the risk register from the risk-assessor's judgments.

Reads outputs/risk-ratings.json (the agent's ratings, prose with citation tags
and {{$.path}} placeholders) together with analytics.json, history.json and
rules.json. Resolves every citation, fills every placeholder from analytics.json,
computes score, matrix label and band from the council's method in history.json,
and writes:

  outputs/risk-register.md         the register, ending with "Auditor decisions"
  outputs/auditor-comments.md      the auditor's decision template (decisions kept)
  outputs/risk-register.state.json the baseline a revision run is diffed against

A risk whose likelihood or impact justification has no resolvable citation is
dropped and listed. Every other defect is an error: nothing is written.

Usage:
  build_register.py [--root DIR]

Exit codes: 0 built, 1 errors found (nothing written), 2 cannot run (missing input).
Standard library only.
"""
import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

CITE_RE = re.compile(r"\[(rule|metric|history):([^\]\s]+)\]")
PLACEHOLDER_RE = re.compile(r"\{\{\s*(\$[^}|\s]*)\s*(?:\|\s*(\w+)\s*)?\}\}")
PATH_TOKEN_RE = re.compile(r"\.([^.\[\]]+)|\[(\d+)\]")

TOP_KEYS = {"method", "risks", "revision"}
METHOD_KEYS = {"choices", "not_affected"}
CHOICE_KEYS = {"discrepancy", "used", "marked", "reason", "mark"}
MARK_KEYS = {"min_score", "max_score", "text"}
NOT_AFFECTED_KEYS = {"discrepancy", "reason"}
RISK_KEYS = {"id", "title", "description", "likelihood", "impact", "repeat_uplift", "proposed_focus"}
LIKELIHOOD_KEYS = {"score", "justification"}
IMPACT_KEYS = {"score", "criterion", "justification", "exposure"}
UPLIFT_KEYS = {"audit", "justification"}
REVISION_KEYS = {"number", "changes"}
CHANGE_KEYS = {"risk", "fields", "decision", "note"}
FIELD_GROUPS = ["title", "description", "likelihood", "impact", "repeat_uplift", "proposed_focus"]

# Opinion words that make an audit adverse, matched case-insensitively.
ADVERSE_OPINIONS = ("limited", "weak", "no assurance", "minimal", "unsatisfactory")
# Tests that list a population rather than flag a signal; the rubric ignores them.
POPULATION_TESTS = {"high_value_suppliers"}
NON_SIGNAL_KEYS = {"parameters", "rule_ids", "status"}
DECISIONS = {"approve": "Approve", "reject": "Reject", "change": "Change"}
FALLBACK_LABELS = {1: "Very low", 2: "Low", 3: "Medium", 4: "High", 5: "Very high"}
FORMATS = {"gbp", "gbp2", "int", "num"}

TYPED_FIGURE_RE = re.compile(
    r"£\s?\d[\d,.]*[kKmM]?|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+(?:\.\d+)?\s?%|\b\d+\.\d+\b|\b\d{3,}\b")
FIGURE_EXEMPT_BEFORE = re.compile(r"(clause|para|paragraph|section|row|table|figure|appendix|page|p\.)\s*$", re.I)
YEAR_RE = re.compile(r"^(19|20)\d{2}$")
ACCUSATORY_RE = re.compile(
    r"\b(fraud\w*|corrupt\w*|wrongdoing|illegal\w*|unlawful\w*|misconduct|abus\w+|deliberate\w*|"
    r"dishonest\w*|theft|stole\w*|breach(?:ed|es)?)\b", re.I)

OUT_REGISTER = "outputs/risk-register.md"
OUT_COMMENTS = "outputs/auditor-comments.md"
OUT_STATE = "outputs/risk-register.state.json"


class Report:
    def __init__(self):
        self.errors, self.warnings, self.dropped = [], [], []

    def error(self, code, msg):
        self.errors.append(f"[{code}] {msg}")

    def warn(self, code, msg):
        self.warnings.append(f"[{code}] {msg}")


# ---------------------------------------------------------------- inputs

def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"CANNOT RUN: {path} is missing")
    except json.JSONDecodeError as e:
        print(f"CANNOT RUN: {path} is not valid JSON ({e})")
    sys.exit(2)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_path(doc, path):
    """Resolve a $.a.b[0].c path. Raises KeyError when it does not exist."""
    if not path.startswith("$"):
        raise KeyError(path)
    rest = path[1:]
    tokens = PATH_TOKEN_RE.findall(rest)
    if "".join(f".{k}" if k else f"[{i}]" for k, i in tokens) != rest:
        raise KeyError(path)
    node = doc
    for key, idx in tokens:
        if idx:
            if not isinstance(node, list) or int(idx) >= len(node):
                raise KeyError(path)
            node = node[int(idx)]
        elif isinstance(node, dict) and key in node:
            node = node[key]
        else:
            raise KeyError(path)
    return node


def path_tokens(path):
    return [k or i for k, i in PATH_TOKEN_RE.findall(path[1:])]


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def fmt_value(v, f):
    if f == "gbp":
        return f"£{v:,.0f}"
    if f == "gbp2":
        return f"£{v:,.2f}"
    if f == "int":
        return f"{round(v):,}"
    if isinstance(v, int) and not isinstance(v, bool):
        return f"{v:,}"
    if isinstance(v, float):
        return f"{v:,.2f}"
    return str(v)


# ---------------------------------------------------------------- method

def parse_range(text):
    t = text.replace("–", "-").replace("—", "-").strip()
    m = re.fullmatch(r"up\s+to\s+(\d+)", t, re.I)
    if m:
        return 1, int(m.group(1))
    m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", t)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def parse_gbp_amounts(text):
    out = []
    for num, unit in re.findall(r"(\d+(?:\.\d+)?)\s*([kKmM])\b", text):
        out.append(float(num) * (1_000 if unit.lower() == "k" else 1_000_000))
    return out


def norm_label(s):
    return re.sub(r"[^a-z]", "", (s or "").lower())


class Method:
    """The council's scoring method from history.json, or the fallback scale."""

    def __init__(self, history, rep):
        sm = history.get("scoring_method") or {}
        self.found = sm.get("status") == "found"
        self.conflicts = []        # builder-detected conflicts and fixed choices, for the header
        self.pages = set()         # (source, pdf_page) holding scale, matrix or band entries
        self.financial_key = None
        self.financial_lower = None
        if not self.found:
            self.l_labels = self.i_labels = FALLBACK_LABELS
            self.criteria = {}
            return
        try:
            self._load(sm, rep)
        except (KeyError, TypeError, ValueError) as e:
            rep.error("E-METHOD", f"history.json scoring_method is found but unusable: {e}")
            self.found = False
            self.l_labels = self.i_labels = FALLBACK_LABELS
            self.criteria = {}

    def _load(self, sm, rep):
        for k in ("likelihood_scale", "impact_scale", "matrix", "bands"):
            for e in sm[k]:
                self.pages.add((e["source"], e["pdf_page"]))
        self.source = sm["bands"][0]["source"]
        self.l_labels = {e["score"]: e["label"] for e in sm["likelihood_scale"]}
        self.i_labels = {e["score"]: e["label"] for e in sm["impact_scale"]}
        self.criteria = {e["score"]: e["criteria"] for e in sm["impact_scale"]}
        for name, labels in (("likelihood", self.l_labels), ("impact", self.i_labels)):
            if sorted(labels) != [1, 2, 3, 4, 5]:
                raise ValueError(f"{name} scale scores are {sorted(labels)}, expected 1-5")
        self.matrix = {e["impact_score"]: e for e in sm["matrix"]}
        if sorted(self.matrix) != [1, 2, 3, 4, 5] or any(len(e["band_labels"]) != 5 for e in sm["matrix"]):
            raise ValueError("matrix needs five impact rows of five cells")
        self.bands = []
        for b in sm["bands"]:
            rng = parse_range(b["score_range"])
            if rng is None:
                raise ValueError(f"band {b['band']!r} score range {b['score_range']!r} cannot be read")
            self.bands.append({**b, "lo": rng[0], "hi": rng[1]})
        self.band_page = sm["bands"][0]["pdf_page"]
        self.matrix_page = sm["matrix"][0]["pdf_page"]
        self.scale_page = sm["impact_scale"][0]["pdf_page"]

        self.conflicts.append(
            f"Likelihood and impact labels and scores come from the scale tables (p{self.scale_page}, "
            f"p{sm['likelihood_scale'][0]['pdf_page']}); a label printed elsewhere with a different score is not used.")
        self.conflicts.append(
            f"The band comes from the score ranges in the band table (p{self.band_page}), which also carry "
            f"escalation and response. The matrix (p{self.matrix_page}) cell label is shown in brackets where it differs.")

        misprinted = [f"{i}x{l}" for i, row in self.matrix.items() for l in range(1, 6)
                      if row["scores_as_printed"][l - 1] != i * l]
        if misprinted:
            self.conflicts.append(f"Matrix cells print a score other than likelihood x impact: {', '.join(misprinted)}. "
                                  "The register uses likelihood x impact.")
        products = sorted({i * l for i in range(1, 6) for l in range(1, 6)})
        for p in products:
            hits = [b["band"] for b in self.bands if b["lo"] <= p <= b["hi"]]
            if len(hits) != 1:
                self.conflicts.append(f"Score {p} falls in {len(hits)} bands of the band table ({', '.join(hits) or 'none'}).")
        differ = {}
        for i, row in self.matrix.items():
            for l in range(1, 6):
                band = self.band_for(i * l)
                label = row["band_labels"][l - 1]
                if band and norm_label(label) != norm_label(band["band"]):
                    differ.setdefault((label, band["band"]), set()).add(i * l)
        for (label, band), scores in sorted(differ.items()):
            self.conflicts.append(
                f"Matrix cells scoring {', '.join(map(str, sorted(scores)))} are labelled '{label}', where the band "
                f"table names that range '{band}'. The register uses '{band}' and marks the matrix label.")

        self.financial_key = next((k for k in self.criteria[1] if k.lower().startswith("financial")), None)
        if self.financial_key:
            lower = {}
            for s in range(1, 6):
                amounts = parse_gbp_amounts(self.criteria[s][self.financial_key])
                lower[s] = 0.0 if s == 1 else (min(amounts) if amounts else None)
            if all(lower[s] is not None for s in lower) and all(lower[s] < lower[s + 1] for s in range(1, 5)):
                self.financial_lower = lower
                self.conflicts.append(
                    f"Financial impact maps a £ exposure onto the £ amounts in the '{self.financial_key}' column; "
                    "an amount on a boundary takes the higher score. The column's % ranges are not used.")
            else:
                self.conflicts.append(f"The £ amounts in '{self.financial_key}' cannot be read as rising bands; "
                                      "financial exposure is not mapped.")

    def band_for(self, score):
        if not self.found:
            return None
        hits = [b for b in self.bands if b["lo"] <= score <= b["hi"]]
        return hits[0] if len(hits) == 1 else None

    def matrix_label(self, l, i):
        return self.matrix[i]["band_labels"][l - 1] if self.found else None

    def financial_score(self, amount):
        return max(s for s, lo in self.financial_lower.items() if amount >= lo)


# ---------------------------------------------------------------- citations and prose

class Sources:
    def __init__(self, rules, analytics, history):
        self.rules = {r["rule_id"]: r for r in rules.get("rules", [])}
        self.analytics = analytics
        self.history = {}
        for section in ("audits", "agreed_actions", "risk_themes", "discrepancies", "gaps"):
            for e in history.get(section, []):
                self.history[e["id"]] = (section, e)

    def resolve(self, kind, ref):
        """Return a one-line evidence string, or None when the citation does not resolve."""
        if kind == "rule":
            r = self.rules.get(ref)
            if not r:
                return None
            q = r["verbatim_quote"]
            return f"{ref} ({r['clause']}, p{r['page']}): “{q[:180]}{'…' if len(q) > 180 else ''}”"
        if kind == "metric":
            try:
                v = resolve_path(self.analytics, ref)
            except KeyError:
                return None
            if isinstance(v, (dict, list)) or v is None:
                return None
            return f"`{ref}` = {fmt_value(v, None)}"
        if kind == "history":
            hit = self.history.get(ref)
            if not hit:
                return None
            section, e = hit
            if section == "audits":
                op = e.get("opinion") or "no opinion"
                prog = f", implementation {e['implementation_progress']}" if e.get("implementation_progress") else ""
                return (f"{ref}: {e['title']} ({e.get('service') or e.get('directorate') or 'n/a'}), {op}{prog}, "
                        f"{e.get('period')}; {e['source']} p{e['pdf_page']}")
            if section == "risk_themes":
                return f"{ref}: {e['theme']} ({e.get('context')}); {e['source']} p{e['pdf_page']}"
            if section == "agreed_actions":
                return f"{ref}: {e.get('theme')}, due {e.get('due_date')}, {e.get('status')}; {e['source']} p{e['pdf_page']}"
            if section == "discrepancies":
                return f"{ref}: {e['description']}"
            return f"{ref}: {e['text']}"
        return None


def citations(text):
    return CITE_RE.findall(text or "")


def render_inline(text, analytics):
    def ph(m):
        v = resolve_path(analytics, m.group(1))
        return fmt_value(v, m.group(2))

    text = PLACEHOLDER_RE.sub(ph, text)
    return CITE_RE.sub(lambda m: f"[`{m.group(2)}`]" if m.group(1) == "metric" else f"[{m.group(2)}]", text)


def check_placeholders(text, analytics, where, rep):
    for m in PLACEHOLDER_RE.finditer(text or ""):
        path, f = m.group(1), m.group(2)
        if f and f not in FORMATS:
            rep.error("E-PLACEHOLDER", f"{where}: unknown format '|{f}' (use {', '.join(sorted(FORMATS))})")
            continue
        try:
            v = resolve_path(analytics, path)
        except KeyError:
            rep.error("E-PLACEHOLDER", f"{where}: {{{{{path}}}}} does not exist in analytics.json")
            continue
        if isinstance(v, (dict, list)) or v is None:
            rep.error("E-PLACEHOLDER", f"{where}: {{{{{path}}}}} is not a single value")
        elif f and not is_number(v):
            rep.error("E-PLACEHOLDER", f"{where}: {{{{{path}}}}} is not a number, so '|{f}' cannot apply")
    if re.search(r"\{\{|\}\}", PLACEHOLDER_RE.sub("", text or "")):
        rep.error("E-PLACEHOLDER", f"{where}: malformed placeholder (write {{{{$.path}}}} or {{{{$.path|gbp}}}})")


def check_prose(text, where, rep):
    bare = CITE_RE.sub(" ", PLACEHOLDER_RE.sub(" ", text or ""))
    for m in TYPED_FIGURE_RE.finditer(bare):
        tok = m.group(0)
        if YEAR_RE.match(tok) or FIGURE_EXEMPT_BEFORE.search(bare[max(0, m.start() - 12):m.start()]):
            continue
        rep.warn("W-FIGURE", f"{where}: typed figure '{tok}'; use a {{{{$.path}}}} placeholder")
    for m in ACCUSATORY_RE.finditer(bare):
        rep.warn("W-LANGUAGE", f"{where}: '{m.group(0)}' reads as an accusation; describe an indicator to investigate")


# ---------------------------------------------------------------- decisions and state

def parse_decisions(path, rep):
    """Map risk id (or GENERAL) -> {decision, comment} from auditor-comments.md."""
    out = {}
    if not path.exists():
        return out
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not re.match(r"^\|\s*(R-\d+|GENERAL)\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            rep.error("E-DECISION", f"auditor-comments.md line {n}: expected 8 columns, found {len(cells)}")
            continue
        rid, raw, comment = cells[0], cells[6], "|".join(cells[7:]).strip()
        word = re.sub(r"[^a-z]", "", raw.lower())
        canon = next((v for k, v in DECISIONS.items() if word.startswith(k)), None) if word else ""
        if canon is None:
            rep.error("E-DECISION", f"auditor-comments.md {rid}: decision '{raw}' is not Approve, Reject or Change")
            continue
        if canon == "Change" and not comment:
            rep.error("E-DECISION", f"auditor-comments.md {rid}: Change needs a comment saying what to change")
        out[rid] = {"decision": canon, "comment": comment}
    return out


def decided(decisions):
    return {k: v for k, v in decisions.items() if v["decision"]}


def fingerprint(risk):
    return {g: json.dumps(risk.get(g), sort_keys=True, ensure_ascii=False) for g in FIELD_GROUPS}


def cell(s):
    return str(s).replace("|", "/").replace("\n", " ").strip()


# ---------------------------------------------------------------- validation

def validate_schema(ratings, rep):
    for k in set(ratings) - TOP_KEYS:
        rep.error("E-SCHEMA", f"risk-ratings.json: unknown top-level key '{k}'")
    if not isinstance(ratings.get("risks"), list) or not ratings["risks"]:
        rep.error("E-SCHEMA", "risk-ratings.json: 'risks' must be a non-empty list")
        return False
    ok = True
    seen = set()
    for n, r in enumerate(ratings["risks"]):
        rid = r.get("id", f"risks[{n}]")
        for k in set(r) - RISK_KEYS:
            rep.error("E-SCHEMA", f"{rid}: unknown key '{k}'")
        if not re.fullmatch(r"R-\d{2,}", str(r.get("id", ""))):
            rep.error("E-SCHEMA", f"{rid}: id must look like R-01")
            ok = False
        if rid in seen:
            rep.error("E-SCHEMA", f"{rid}: duplicate id")
        seen.add(rid)
        for k in ("title", "description", "proposed_focus"):
            if not isinstance(r.get(k), str) or not r[k].strip():
                rep.error("E-SCHEMA", f"{rid}: '{k}' must be non-empty text")
        for part, keys in (("likelihood", LIKELIHOOD_KEYS), ("impact", IMPACT_KEYS)):
            p = r.get(part)
            if not isinstance(p, dict):
                rep.error("E-SCHEMA", f"{rid}: '{part}' must be an object")
                ok = False
                continue
            for k in set(p) - keys:
                rep.error("E-SCHEMA", f"{rid}: unknown key '{part}.{k}'")
            if p.get("score") not in (1, 2, 3, 4, 5) or isinstance(p.get("score"), bool):
                rep.error("E-SCHEMA", f"{rid}: {part}.score must be an integer 1-5")
                ok = False
            if not isinstance(p.get("justification"), str):
                rep.error("E-SCHEMA", f"{rid}: {part}.justification must be text")
                ok = False
        if not isinstance((r.get("impact") or {}).get("criterion"), str):
            rep.error("E-SCHEMA", f"{rid}: impact.criterion must name a column of the impact scale")
        up = r.get("repeat_uplift")
        if up is not None:
            if not isinstance(up, dict) or set(up) != UPLIFT_KEYS:
                rep.error("E-SCHEMA", f"{rid}: repeat_uplift must be null or {{audit, justification}}")
                r["repeat_uplift"] = None
    return ok


def validate_method_choices(ratings, method, history, rep):
    m = ratings.get("method") or {}
    for k in set(m) - METHOD_KEYS:
        rep.error("E-SCHEMA", f"method: unknown key '{k}'")
    known = {d["id"]: d for d in history.get("discrepancies", [])}
    scoring = sorted(d["id"] for d in known.values()
                     if any((e.get("source"), e.get("pdf_page")) in method.pages for e in d.get("evidence", [])))
    named = {}
    for kind, keys in (("choices", CHOICE_KEYS), ("not_affected", NOT_AFFECTED_KEYS)):
        for c in m.get(kind, []):
            did = c.get("discrepancy")
            for k in set(c) - keys:
                rep.error("E-SCHEMA", f"method.{kind} {did}: unknown key '{k}'")
            required = keys - {"mark"}
            if not required <= set(c) or any(not str(c[k]).strip() for k in required):
                rep.error("E-SCHEMA", f"method.{kind} {did}: needs {', '.join(sorted(required))}")
            if did not in known:
                rep.error("E-CONFLICT", f"method.{kind}: {did} is not a discrepancy in history.json")
            if did in named:
                rep.error("E-CONFLICT", f"method: {did} is named in both {named[did]} and {kind}")
            named[did] = kind
            mark = c.get("mark")
            if mark is not None:
                if (not isinstance(mark, dict) or set(mark) != MARK_KEYS
                        or not all(is_number(mark[k]) for k in ("min_score", "max_score"))):
                    rep.error("E-SCHEMA", f"method.choices {did}: mark must be {{min_score, max_score, text}}")
                    c["mark"] = None
    for did in scoring:
        if did not in named:
            rep.error("E-CONFLICT", f"{did} sits on a scoring-method page but is in neither method.choices "
                                    "nor method.not_affected; say which side the register uses")
    return scoring


def check_risk(r, src, method, overrides, rep):
    """Validate one risk. Returns computed fields, or None when the risk is dropped."""
    rid = r["id"]
    resolved = {}
    unresolved = []
    fields = {"title": r["title"], "description": r["description"], "proposed_focus": r["proposed_focus"],
              "likelihood": r["likelihood"]["justification"], "impact": r["impact"]["justification"]}
    if r.get("repeat_uplift"):
        fields["repeat_uplift"] = r["repeat_uplift"]["justification"]
    for name, text in fields.items():
        for kind, ref in citations(text):
            line = src.resolve(kind, ref)
            if line is None:
                unresolved.append((name, f"[{kind}:{ref}]"))
            else:
                resolved.setdefault(f"{kind}:{ref}", line)

    for part in ("likelihood", "impact"):
        good = [c for c in citations(fields[part]) if src.resolve(*c) is not None]
        if not good:
            bad = [t for n, t in unresolved if n == part]
            why = f"unresolved {', '.join(bad)}" if bad else "no citation"
            rep.dropped.append((rid, r["title"], f"{part} justification has no resolvable citation ({why})"))
            return None
    for name, tag in unresolved:
        rep.error("E-CITE", f"{rid}.{name}: {tag} does not resolve")

    for name, text in fields.items():
        check_placeholders(text, src.analytics, f"{rid}.{name}", rep)
        check_prose(text, f"{rid}.{name}", rep)

    l_base, i_score = r["likelihood"]["score"], r["impact"]["score"]
    l_override = any(o["field"] == "likelihood" for o in overrides)
    i_override = any(o["field"] == "impact" for o in overrides)

    # Likelihood rubric: signals are numeric metrics above zero under a flagging test.
    signal_tests = set()
    for kind, ref in citations(fields["likelihood"]):
        if kind != "metric":
            continue
        toks = path_tokens(ref)
        try:
            v = resolve_path(src.analytics, ref)
        except KeyError:
            continue
        if (len(toks) >= 3 and toks[0] == "tests" and toks[1] not in POPULATION_TESTS
                and toks[2] not in NON_SIGNAL_KEYS and is_number(v) and v > 0):
            signal_tests.add(toks[1])
    if not l_override:
        if l_base == 5:
            rep.error("E-RUBRIC", f"{rid}: base likelihood 5 is reached only through the repeat-finding uplift")
        elif l_base >= 3 and not signal_tests:
            rep.error("E-RUBRIC", f"{rid}: likelihood {l_base} needs a cited test metric above zero "
                                  "(rubric L3); none in the likelihood justification")
        elif l_base == 4 and len(signal_tests) < 2:
            rep.error("E-RUBRIC", f"{rid}: likelihood 4 needs signals from two different tests (rubric L4); "
                                  f"found {sorted(signal_tests) or 'none'}")

    l_final, uplift = l_base, None
    up = r.get("repeat_uplift")
    if up:
        hit = src.history.get(up["audit"])
        if not hit or hit[0] != "audits":
            rep.error("E-UPLIFT", f"{rid}: repeat_uplift.audit {up['audit']} is not an audit in history.json")
        else:
            a = hit[1]
            words = f"{a.get('opinion') or ''}".lower()
            if not any(w in words for w in ADVERSE_OPINIONS):
                rep.error("E-UPLIFT", f"{rid}: repeat_uplift cites {up['audit']} ({a['title']}), whose opinion "
                                      f"'{a.get('opinion')}' is not adverse")
            elif ("history", up["audit"]) not in citations(up["justification"]):
                rep.error("E-UPLIFT", f"{rid}: repeat_uplift.justification must cite [history:{up['audit']}]")
            else:
                l_final = min(5, l_base + 1)
                uplift = a

    criterion = r["impact"]["criterion"]
    exposure = None
    if method.found:
        if criterion not in method.criteria[1]:
            rep.error("E-SCHEMA", f"{rid}: impact.criterion '{criterion}' is not a column of the impact scale "
                                  f"({'; '.join(method.criteria[1])})")
        elif criterion == method.financial_key and method.financial_lower and not r["impact"].get("exposure"):
            rep.error("E-EXPOSURE", f"{rid}: a financial impact needs impact.exposure, a $.path to the £ at stake")
    if r["impact"].get("exposure"):
        path = r["impact"]["exposure"]
        try:
            amount = resolve_path(src.analytics, path)
        except KeyError:
            amount = None
        if not is_number(amount):
            rep.error("E-EXPOSURE", f"{rid}: impact.exposure {path} is not a number in analytics.json")
        elif not method.found or criterion != method.financial_key or not method.financial_lower:
            rep.error("E-EXPOSURE", f"{rid}: impact.exposure applies only to the financial criterion")
        else:
            mapped = method.financial_score(amount)
            exposure = (path, amount, mapped)
            if mapped != i_score and not i_override:
                rep.error("E-EXPOSURE", f"{rid}: exposure {fmt_value(amount, 'gbp')} maps to financial impact "
                                        f"{mapped}, not {i_score}")

    score = l_final * i_score
    return {"resolved": resolved, "l_base": l_base, "l_final": l_final, "i": i_score, "score": score,
            "uplift": uplift, "exposure": exposure, "criterion": criterion, "signal_tests": sorted(signal_tests)}


def apply_revision(ratings, risks, decisions, state, rep):
    """Check the revision against the baseline. Returns (revision number, summary lines, overrides)."""
    prev_decided = (state or {}).get("applied_decisions", {})
    now_decided = decided(decisions)
    overrides = {k: list(v) for k, v in (state or {}).get("overrides", {}).items()}
    block = ratings.get("revision")
    if block is not None:
        for k in set(block) - REVISION_KEYS:
            rep.error("E-SCHEMA", f"revision: unknown key '{k}'")

    if not state:
        if now_decided:
            rep.error("E-REVISION", f"auditor-comments.md holds decisions but {OUT_STATE} is missing, so what the "
                                    "auditor reviewed cannot be compared; restore it or clear the decisions")
        if block:
            rep.error("E-REVISION", "risk-ratings.json has a revision block but there is no earlier register")
        return 0, [], overrides

    prev_fp = state["fingerprints"]
    cur = {r["id"]: r for r in risks}
    diffs = {}
    for rid, r in cur.items():
        if rid not in prev_fp:
            diffs[rid] = {"new"}
        else:
            changed = {g for g, v in fingerprint(r).items() if v != prev_fp[rid].get(g)}
            if changed:
                diffs[rid] = changed
    removed = sorted(set(prev_fp) - set(cur))

    if not prev_decided and not now_decided:
        if block:
            rep.error("E-REVISION", "risk-ratings.json has a revision block but no auditor decision exists yet")
        return 0, [], overrides  # still a draft: the agent may change anything

    for rid in removed:
        rep.error("E-REVISION", f"{rid} was in the reviewed register and is gone; a rejected risk stays in the file")

    revision = state["revision"]
    new = {k: v for k, v in now_decided.items() if prev_decided.get(k) != v}
    cleared = sorted(set(prev_decided) - set(now_decided))
    if not new and not cleared:
        if block and block.get("number") != revision:
            rep.error("E-REVISION", f"revision.number is {block.get('number')} but no new auditor decision "
                                    f"exists; the register is at revision {revision}")
        for rid, groups in sorted(diffs.items()):
            rep.error("E-REVISION", f"{rid}: {', '.join(sorted(groups))} changed, but there is no new auditor "
                                    "decision asking for it")
        return revision, state.get("revision_summary", []), overrides

    revision += 1
    if not block or block.get("number") != revision:
        rep.error("E-REVISION", f"new auditor decisions exist: risk-ratings.json needs \"revision\": "
                                f"{{\"number\": {revision}, \"changes\": [...]}}")
        return revision, [], overrides

    covered = {}
    for n, ch in enumerate(block.get("changes", [])):
        for k in set(ch) - CHANGE_KEYS:
            rep.error("E-SCHEMA", f"revision.changes[{n}]: unknown key '{k}'")
        rid, ref, fields = ch.get("risk"), ch.get("decision"), ch.get("fields") or []
        d = new.get(ref)
        if not d or d["decision"] != "Change":
            rep.error("E-REVISION", f"revision.changes[{n}] ({rid}) cites decision '{ref}', which is not a new "
                                    "Change decision in auditor-comments.md")
            continue
        if ref not in (rid, "GENERAL"):
            rep.error("E-REVISION", f"revision.changes[{n}]: decision {ref} is on another risk; cite {rid} or GENERAL")
        for f in fields:
            if f not in FIELD_GROUPS and f != "new":
                rep.error("E-SCHEMA", f"revision.changes[{n}]: field '{f}' is not one of {FIELD_GROUPS + ['new']}")
            elif f not in diffs.get(rid, set()):
                rep.error("E-REVISION", f"revision.changes[{n}]: {rid}.{f} is listed as changed but is unchanged")
            else:
                covered.setdefault(rid, set()).add(f)
                covered.setdefault(("ref", ref), set()).add(rid)
        if not fields:
            rep.error("E-REVISION", f"revision.changes[{n}] ({rid}) lists no fields")

    for rid, groups in sorted(diffs.items()):
        extra = groups - covered.get(rid, set())
        if extra:
            rep.error("E-REVISION", f"{rid}: {', '.join(sorted(extra))} changed, but no auditor decision asked "
                                    "for it (or the change is not listed in revision.changes)")
    for rid, d in sorted(new.items()):
        if d["decision"] == "Change" and ("ref", rid) not in covered:
            rep.error("E-REVISION", f"decision on {rid} (Change: \"{d['comment']}\") is not applied in revision.changes")

    summary = [f"Responds to the decisions in `{OUT_COMMENTS}`."]
    prev_scores = state.get("scores", {})
    for rid, d in sorted(new.items()):
        if d["decision"] == "Reject":
            summary.append(f"{rid} rejected by the auditor; it stays listed and is out of scope.")
        elif d["decision"] == "Approve":
            summary.append(f"{rid} approved.")
    for rid in cleared:
        summary.append(f"{rid}: the auditor cleared an earlier decision.")
    for ch in block.get("changes", []):
        rid, fields = ch.get("risk"), ch.get("fields") or []
        if rid not in cur:
            continue
        comment = new.get(ch.get("decision"), {}).get("comment", "")
        parts = []
        for f in fields:
            if f in ("likelihood", "impact") and rid in prev_scores:
                old, newv = prev_scores[rid][f], cur[rid][f]["score"]
                if old != newv:
                    parts.append(f"{f} {old} → {newv}")
                    overrides.setdefault(rid, []).append({"field": f, "from": old, "to": newv, "revision": revision,
                                                          "decision": ch.get("decision"), "comment": comment})
                    continue
            parts.append("added" if f == "new" else f"{f} changed")
        note = f" {ch['note']}" if ch.get("note") else ""
        summary.append(f"{rid}: {', '.join(parts)}, as asked (\"{comment}\").{note}")
    return revision, summary, overrides


# ---------------------------------------------------------------- rendering

def render_register(ctx):
    method, rated, rep = ctx["method"], ctx["rated"], ctx["rep"]
    a = ctx["analytics"]
    L = []
    rev = ctx["revision"]
    L.append(f"# Risk register: procurement audit planning (revision {rev})")
    L.append("")
    L.append(f"Built {ctx['today']} by `.claude/skills/risk-assessment/build_register.py` from `outputs/risk-ratings.json`. "
             "Every figure is filled from `outputs/analytics.json`; every citation resolves to rules.json, "
             "analytics.json or history.json. These are risk indicators to investigate, not findings of wrongdoing.")
    L.append("")
    if rev:
        L.append(f"## Revision {rev}")
        L.append("")
        L += [f"- {s}" for s in ctx["summary"]]
        L.append("")
    L.append("## Scoring method")
    L.append("")
    if method.found:
        ls = ", ".join(f"{s} {method.l_labels[s]}" for s in range(1, 6))
        is_ = ", ".join(f"{s} {method.i_labels[s]}" for s in range(1, 6))
        L.append(f"The council's own method, from `{method.source}` (history.json `scoring_method`). "
                 f"Likelihood: {ls}. Impact: {is_}. Score = likelihood × impact.")
        L.append("")
        L.append("| Band | RAG | Scores | Escalation | Response |")
        L.append("|---|---|---|---|---|")
        for b in method.bands:
            L.append(f"| {cell(b['band'])} | {cell(b.get('rag') or 'not printed')} | {cell(b['score_range'])} | "
                     f"{cell(b.get('escalation'))} | {cell(b.get('response'))} |")
    else:
        L.append("**Fallback scale.** history.json reports no usable council scoring method, so the register uses "
                 "1-5 Very low … Very high for both likelihood and impact, score = likelihood × impact, and no bands.")
    L.append("")
    L.append("Likelihood is rated with the rubric in the risk-assessment skill: 3 needs a test signal, "
             "4 needs signals from two tests, and 5 only comes from a repeat finding (an adverse audit opinion on the "
             "same theme raises likelihood by one point, stated on the risk).")
    L.append("")
    L.append("### Conflicts in the method")
    L.append("")
    L.append("Where the council's papers disagree with themselves, the register uses one side and marks the other.")
    L.append("")
    for c in method.conflicts:
        L.append(f"- {c}")
    for c in ctx["choices"]:
        mark = c.get("mark")
        tail = (f" Risks scoring {mark['min_score']}-{mark['max_score']} are marked: “{mark['text']}”."
                if mark else "")
        L.append(f"- {c['discrepancy']}: uses {c['used']}; marks {c['marked']}. {c['reason']}{tail}")
    for c in ctx["not_affected"]:
        L.append(f"- {c['discrepancy']}: no effect on any rating. {c['reason']}")
    if not (method.conflicts or ctx["choices"] or ctx["not_affected"]):
        L.append("- None found.")
    L.append("")

    L.append("## Summary")
    L.append("")
    L.append("| Risk | Title | L | I | Score | Band | Status |")
    L.append("|---|---|---|---|---|---|---|")
    for r, c in rated:
        L.append(f"| {r['id']} | {cell(render_inline(r['title'], a))} | {c['l_final']} | {c['i']} | {c['score']} | "
                 f"{cell(band_text(method, c))} | {status_text(r['id'], ctx)} |")
    L.append("")
    if rep.dropped:
        L.append("### Excluded: no resolvable citation")
        L.append("")
        for rid, title, why in rep.dropped:
            L.append(f"- {rid} {title}: {why}.")
        L.append("")

    L.append("## Risks")
    for r, c in rated:
        rid = r["id"]
        L.append("")
        L.append(f"### {rid} {render_inline(r['title'], a)}")
        L.append("")
        L.append(render_inline(r["description"], a))
        L.append("")
        lt = f"{c['l_final']} {method.l_labels[c['l_final']]}"
        if c["uplift"]:
            u = c["uplift"]
            lt += (f" (base {c['l_base']}, +1 for a repeat finding: {u['id']} {u['title']}, "
                   f"{u.get('opinion')}, {u.get('period')})")
        L.append(f"**Likelihood {lt}.** {render_inline(r['likelihood']['justification'], a)}")
        if c["uplift"]:
            L.append("")
            L.append(f"*Repeat finding.* {render_inline(r['repeat_uplift']['justification'], a)}")
        L.append("")
        it = f"{c['i']} {method.i_labels[c['i']]}, on {c['criterion']}"
        if method.found and c["criterion"] in method.criteria[c["i"]]:
            it += f" (council scale: “{method.criteria[c['i']][c['criterion']]}”)"
        L.append(f"**Impact {it}.** {render_inline(r['impact']['justification'], a)}")
        if c["exposure"]:
            path, amount, mapped = c["exposure"]
            L.append("")
            L.append(f"*Exposure* `{path}` = {fmt_value(amount, 'gbp')}, which maps to impact {mapped} on the £ amounts; "
                     "it is the value passing through the flagged population, an upper bound, not a loss.")
        L.append("")
        L.append(f"**Score {c['score']}, {band_text(method, c)}.**{band_actions(method, c)}")
        for mark in c["marks"]:
            L.append(f"\n† {mark}")
        for o in ctx["overrides"].get(rid, []):
            L.append(f"\n**Auditor override (revision {o['revision']}):** {o['field']} {o['from']} → {o['to']}. "
                     f"Auditor's comment: “{o['comment']}”")
        L.append("")
        L.append("**Evidence**")
        L.append("")
        for line in c["resolved"].values():
            L.append(f"- {line}")
        L.append("")
        L.append(f"**Proposed focus.** {render_inline(r['proposed_focus'], a)}")

    L.append("")
    L.append("## Auditor decisions")
    L.append("")
    L.append(f"Decisions are recorded in `{OUT_COMMENTS}`: Approve, Reject or Change (with a comment saying what "
             "to change). The risk-assessor applies them in a new revision, and this builder fails if a decision "
             "is left unapplied or anything changes that the auditor did not ask for.")
    L.append("")
    L.append("| Risk | Decision | Comment | Status |")
    L.append("|---|---|---|---|")
    for rid in [r["id"] for r, _ in rated] + (["GENERAL"] if "GENERAL" in ctx["decisions"] else []):
        d = ctx["decisions"].get(rid, {"decision": "", "comment": ""})
        L.append(f"| {rid} | {d['decision'] or '(blank)'} | {cell(d['comment']) or ''} | {status_text(rid, ctx)} |")
    L.append("")
    L.append(f"Gate: {ctx['gate']['text']}")
    L.append("")
    return "\n".join(L)


def band_text(method, c):
    if not method.found:
        return "no council bands (fallback)"
    b = method.band_for(c["score"])
    if not b:
        return "no band (gap in the band table)"
    t = f"{b['band']}" + (f" ({b['rag']})" if b.get("rag") else "")
    ml = method.matrix_label(c["l_final"], c["i"])
    if norm_label(ml) != norm_label(b["band"]):
        t += f" [matrix: {ml}]"
    return t


def band_actions(method, c):
    b = method.band_for(c["score"]) if method.found else None
    if not b:
        return ""
    def sentence(s):
        return str(s).strip().rstrip(".") + "."
    return f" Escalation: {sentence(b.get('escalation'))} Response: {sentence(b.get('response'))}"


def status_text(rid, ctx):
    d = ctx["decisions"].get(rid, {}).get("decision", "")
    if rid == "GENERAL":
        return "applied" if d == "Change" else ("noted" if d else "")
    if not d:
        return "awaiting auditor"
    return {"Approve": "approved", "Reject": "rejected (out of scope)",
            "Change": f"changed as asked (rev {ctx['revision']})"}[d]


def render_comments(rated, decisions, revision, today, orphans):
    L = ["# Auditor decisions: risk register", "",
         f"Register revision {revision}, built {today}. Read `{OUT_REGISTER}`, then fill in the Decision and Comment "
         "cells below. Decision is one of **Approve**, **Reject** or **Change**. For Change, say in the Comment "
         "what to change (for example \"likelihood 4: the split groups are not explained\" or \"narrow the focus to "
         "agency staff\"). Use the GENERAL row for scope comments or a risk to add. Leave the other columns as they "
         "are; the builder rewrites them and keeps your decisions.", "",
         "| Risk | Title | L | I | Score | Band | Decision | Comment |",
         "|---|---|---|---|---|---|---|---|"]
    for r, c in rated:
        d = decisions.get(r["id"], {"decision": "", "comment": ""})
        L.append(f"| {r['id']} | {cell(r['_title'])} | {c['l_final']} | {c['i']} | {c['score']} | "
                 f"{cell(c['band'])} | {d['decision']} | {cell(d['comment'])} |")
    g = decisions.get("GENERAL", {"decision": "", "comment": ""})
    L.append(f"| GENERAL | Scope, or a risk to add | | | | | {g['decision']} | {cell(g['comment'])} |")
    if orphans:
        L += ["", "## Decisions on risks no longer rated", "",
              "These risks are not in the current register (dropped for lack of a citation, or renamed). "
              "Their decisions are kept here for the record and are not applied.", "",
              "| Risk | Title | L | I | Score | Band | Decision | Comment |",
              "|---|---|---|---|---|---|---|---|"]
        for rid, d in sorted(orphans.items()):
            L.append(f"| {rid} | (not rated) | | | | | {d['decision']} | {cell(d['comment'])} |")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    args = ap.parse_args()
    root = Path(args.root)
    paths = {k: root / "outputs" / f"{k}.json" for k in ("analytics", "history", "rules", "risk-ratings")}
    docs = {k: load_json(p) for k, p in paths.items()}
    analytics, history, rules, ratings = (docs[k] for k in ("analytics", "history", "rules", "risk-ratings"))

    rep = Report()
    method = Method(history, rep)
    src = Sources(rules, analytics, history)
    validate_schema(ratings, rep)
    if rep.errors:
        return finish(rep)
    validate_method_choices(ratings, method, history, rep)

    decisions = parse_decisions(root / OUT_COMMENTS, rep)
    state_path = root / OUT_STATE
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    revision, summary, overrides = apply_revision(ratings, ratings["risks"], decisions, state, rep)

    choices = (ratings.get("method") or {}).get("choices", [])
    rated = []
    for r in ratings["risks"]:
        c = check_risk(r, src, method, overrides.get(r["id"], []), rep)
        if c is None:
            continue
        c["marks"] = [f"{ch['discrepancy']}: {ch['mark']['text']}" for ch in choices
                      if ch.get("mark") and ch["mark"]["min_score"] <= c["score"] <= ch["mark"]["max_score"]]
        c["band"] = band_text(method, c)
        rated.append((r, c))
    if rep.errors:
        return finish(rep)

    rated_ids = {r["id"] for r, _ in rated}
    for r, _ in rated:
        r["_title"] = render_inline(r["title"], analytics)
    orphans = {k: v for k, v in decisions.items() if k != "GENERAL" and k not in rated_ids and v["decision"]}
    for rid in orphans:
        rep.warn("W-ORPHAN", f"auditor-comments.md has a decision on {rid}, which is not rated")
    undecided = [rid for rid in sorted(rated_ids) if not decisions.get(rid, {}).get("decision")]
    if revision == 0:
        gate = {"ready": False, "text": "not ready: revision 0 awaits the auditor's decisions."}
    elif undecided:
        gate = {"ready": False, "text": f"not ready: no decision on {', '.join(undecided)}."}
    else:
        gate = {"ready": True, "text": f"ready: every rated risk has a decision, applied in revision {revision}."}

    today = datetime.date.today().isoformat()
    ctx = {"method": method, "rated": rated, "rep": rep, "analytics": analytics, "revision": revision,
           "summary": summary, "overrides": overrides, "decisions": decisions, "gate": gate, "today": today,
           "choices": choices, "not_affected": (ratings.get("method") or {}).get("not_affected", [])}
    (root / OUT_REGISTER).write_text(render_register(ctx), encoding="utf-8")
    (root / OUT_COMMENTS).write_text(render_comments(rated, decisions, revision, today, orphans), encoding="utf-8")
    state = {
        "revision": revision,
        "built": today,
        "inputs": {k: sha256(p) for k, p in paths.items()},
        "fingerprints": {r["id"]: fingerprint(r) for r in ratings["risks"]},
        "scores": {r["id"]: {"likelihood": r["likelihood"]["score"], "impact": r["impact"]["score"]}
                   for r in ratings["risks"]},
        "applied_decisions": decided(decisions),
        "overrides": overrides,
        "revision_summary": summary,
        "rated": {r["id"]: {"likelihood": c["l_final"], "impact": c["i"], "score": c["score"], "band": c["band"],
                            "decision": decisions.get(r["id"], {}).get("decision", "")} for r, c in rated},
        "dropped": [rid for rid, _, _ in rep.dropped],
        "gate": gate,
    }
    state_path.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
    return finish(rep, built=(revision, len(rated), gate))


def finish(rep, built=None):
    for rid, title, why in rep.dropped:
        print(f"DROPPED {rid} {title}: {why}")
    for w in rep.warnings:
        print(f"WARN {w}")
    if rep.errors:
        for e in rep.errors:
            print(e)
        print(f"FAIL: {len(rep.errors)} error(s); nothing written")
        return 1
    revision, n, gate = built
    print(f"BUILT revision {revision}: {n} risk(s) rated, {len(rep.dropped)} dropped, "
          f"{len(rep.warnings)} warning(s). Gate {gate['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
