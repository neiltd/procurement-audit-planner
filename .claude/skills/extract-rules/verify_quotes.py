#!/usr/bin/env python3
"""Verify outputs/rules.json against data/contract-rules.pdf.

Checks the schema, sequential rule IDs, declared parameters, threshold values
against their printed text, clause coverage, and that every quote appears on
its stated PDF page. Standard library only; needs pdftotext and pdfinfo.

Usage:
  verify_quotes.py [--rules PATH] [--pdf PATH]
  verify_quotes.py --inventory [--pdf PATH]     # list the clauses the PDF contains

Exit codes: 0 pass, 1 errors found, 2 cannot run (missing file or tool).
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from decimal import Decimal
from pathlib import Path

RULE_TYPES = {"procedure", "approval", "anti-avoidance", "documentation",
              "contract-content", "publication"}
SCOPES = {"all", "goods", "services", "works", "concessions", "light_touch"}
EVIDENCE = {"spend_data", "contracts_finder", "council_records"}
NOTE_KINDS = {"contradiction", "gap", "placeholder", "drafting-error", "interpretation"}

TOP_KEYS = {"source", "parameters", "rules", "excluded", "notes"}
SOURCE_KEYS = {"file", "sha256", "pages"}
PARAM_KEYS = {"value", "clause", "page", "printed_as", "description"}
PARAM_OPTIONAL = {"resolves_by_scope"}
RULE_KEYS = {
    "rule_id", "clause", "page", "type", "scope", "condition", "threshold_text",
    "threshold_low", "threshold_low_inclusive", "threshold_low_param",
    "threshold_high", "threshold_high_inclusive", "threshold_high_param",
    "required_action", "approver", "evidence_source", "evidence_detail",
    "verbatim_quote",
}
EXCLUDED_KEYS = {"clause", "page", "reason"}
NOTE_KEYS = {"id", "kind", "clause", "page", "text", "rule_ids"}
NOTE_OPTIONAL = {"quote"}

MIN_QUOTE_CHARS = 20
MAX_REASON_CHARS = 200

NUMERIC_CLAUSE = re.compile(r"^\d+(?:\.\d+)+$")
APPENDIX_REF = re.compile(r"^App ([A-Z]) (row ([A-Z]\d?|\d+)|note|footnote \S+)$")
CLAUSE_LINE = re.compile(r"^\s*(\d+(?:\.\d+)+)\s{2,}\S")
APPENDIX_HEADING = re.compile(r"^\s*(?:.*-\s*)?Appendix ([A-Z])\s*$")
ROW_LABEL = re.compile(r"^\s{0,8}([A-Z]\d?)(?:\s{2,}\S|\s*$)")  # label may sit alone on its line
MONEY = re.compile(r"£\s?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?\s?(million)?", re.I)
PARAM_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")

CHAR_MAP = {ord(k): v for k, v in {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "‐": "-", "‑": "-", "–": "-", "—": "-", " ": " ",
}.items()}


class Cannot(Exception):
    """Input or tool missing: exit 2, not a verification failure."""


def norm(text):
    """Normalise for quote matching: NFKC, straight quotes, plain dashes,
    bullets dropped, whitespace collapsed. Wording must still match exactly."""
    text = unicodedata.normalize("NFKC", text).translate(CHAR_MAP)
    text = "".join(" " if 0xE000 <= ord(c) <= 0xF8FF or c in "•▪◦" else c for c in text)
    return re.sub(r"\s+", " ", text).strip()


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, check=True).stdout.decode("utf-8")
    except FileNotFoundError:
        raise Cannot(f"{cmd[0]} not found; install poppler")
    except subprocess.CalledProcessError as e:
        raise Cannot(f"{' '.join(cmd)} failed: {e.stderr.decode('utf-8', 'replace').strip()}")


def load_pdf(pdf):
    if not pdf.is_file():
        raise Cannot(f"PDF not found: {pdf}")
    m = re.search(r"^Pages:\s+(\d+)", run(["pdfinfo", str(pdf)]), re.M)
    if not m:
        raise Cannot(f"pdfinfo reported no page count for {pdf}")
    n = int(m.group(1))
    pages = {}
    for mode, flags in (("plain", []), ("layout", ["-layout"])):
        chunks = run(["pdftotext", *flags, "-enc", "UTF-8", str(pdf), "-"]).split("\f")
        if len(chunks) < n:
            raise Cannot(f"pdftotext {mode} returned {len(chunks)} pages, pdfinfo says {n}")
        pages[mode] = chunks[:n]
    searchable = []
    for i in range(n):
        variants = set()
        for mode in ("plain", "layout"):
            t = norm(pages[mode][i])
            variants.add(t)
            variants.add(re.sub(r"(\w)- (\w)", r"\1-\2", t))  # word-hyphen split over a line
        searchable.append(variants)
    return n, pages["layout"], searchable


def inventory(layout_pages):
    """Numbered clauses and appendix table rows the PDF contains, in order."""
    clauses, rows = [], []
    appendix = None
    for pno, text in enumerate(layout_pages, 1):
        for line in text.splitlines():
            h = APPENDIX_HEADING.match(line)
            if h:
                appendix = h.group(1)
                continue
            if appendix is None:
                m = CLAUSE_LINE.match(line)
                if m:
                    clauses.append((m.group(1), pno))
            else:
                m = ROW_LABEL.match(line)
                if m:
                    rows.append((f"App {appendix} row {m.group(1)}", pno))
    return clauses, rows


def amounts(text):
    out = set()
    for whole, pence, million in MONEY.findall(text or ""):
        v = Decimal(whole.replace(",", "") + ("." + pence if pence else ""))
        out.add(v * 1_000_000 if million else v)
    return out


class Verifier:
    def __init__(self, data, pdf, n_pages, layout_pages, searchable):
        self.d, self.pdf, self.n = data, pdf, n_pages
        self.layout, self.search = layout_pages, searchable
        self.errors = []

    def err(self, code, where, msg):
        self.errors.append(f"[{code}] {where}: {msg}")

    def on_page(self, text, page):
        t = norm(text)
        return any(t in v for v in self.search[page - 1])

    def page_ok(self, page, where):
        if isinstance(page, bool) or not isinstance(page, int) or not 1 <= page <= self.n:
            self.err("E-SCHEMA", where, f"page must be an integer 1..{self.n}, got {page!r}")
            return False
        return True

    def keys(self, obj, required, where, optional=frozenset()):
        if not isinstance(obj, dict):
            self.err("E-SCHEMA", where, "must be an object")
            return False
        missing = required - obj.keys()
        extra = obj.keys() - required - optional
        if missing:
            self.err("E-SCHEMA", where, f"missing keys {sorted(missing)}")
        if extra:
            self.err("E-SCHEMA", where, f"unknown keys {sorted(extra)}")
        return not missing

    def text(self, obj, key, where, nullable=False):
        v = obj.get(key)
        if v is None and nullable:
            return None
        if not isinstance(v, str) or not v.strip():
            self.err("E-SCHEMA", where, f"{key} must be a non-empty string"
                     + (" or null" if nullable else ""))
            return None
        return v

    # --- sections -----------------------------------------------------------

    def check(self):
        d = self.d
        if not self.keys(d, TOP_KEYS, "top level"):
            return
        self.check_source(d["source"])
        params = self.check_parameters(d["parameters"])
        rule_ids = self.check_rules(d["rules"], params)
        self.check_excluded(d["excluded"])
        self.check_notes(d["notes"], rule_ids)
        self.check_threshold_values(d["rules"], d["notes"])
        self.check_coverage(d["rules"], d["excluded"])

    def check_source(self, s):
        if not self.keys(s, SOURCE_KEYS, "source"):
            return
        sha = hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        if s["sha256"] != sha:
            self.err("E-SOURCE", "source.sha256", f"does not match {self.pdf} ({sha[:12]}…); "
                     "rules.json was built from a different PDF")
        if s["pages"] != self.n:
            self.err("E-SOURCE", "source.pages", f"{s['pages']!r} but the PDF has {self.n}")

    def check_parameters(self, params):
        if not isinstance(params, dict):
            self.err("E-SCHEMA", "parameters", "must be an object")
            return {}
        for name, p in params.items():
            where = f"parameters.{name}"
            if not PARAM_NAME.match(name):
                self.err("E-PARAM", where, "name must be UPPER_SNAKE_CASE")
            if not self.keys(p, PARAM_KEYS, where, PARAM_OPTIONAL):
                continue
            if p["value"] is not None:
                self.err("E-PARAM", where, f"value must be null (the PDF names it but gives no "
                         f"figure), got {p['value']!r}")
            if self.page_ok(p["page"], where):
                printed = self.text(p, "printed_as", where)
                if printed and not self.on_page(printed, p["page"]):
                    self.err("E-PARAM", where, f"printed_as {printed!r} not on page {p['page']}")
            self.text(p, "clause", where)
            self.text(p, "description", where)
            rbs = p.get("resolves_by_scope")
            if rbs is not None:
                if not isinstance(rbs, dict) or not rbs:
                    self.err("E-PARAM", where, "resolves_by_scope must be a non-empty object")
                    continue
                for scope, target in rbs.items():
                    if scope not in SCOPES - {"all"}:
                        self.err("E-PARAM", where, f"resolves_by_scope key {scope!r} not a scope")
                    if target not in params or params[target].get("resolves_by_scope"):
                        self.err("E-PARAM", where, f"resolves_by_scope → {target!r} is not a "
                                 "declared simple parameter")
        return params

    def check_rules(self, rules, params):
        if not isinstance(rules, list) or not rules:
            self.err("E-SCHEMA", "rules", "must be a non-empty array")
            return set()
        width = max(2, len(str(len(rules))))
        ids, used_params, last_page = set(), set(), 0
        for i, r in enumerate(rules, 1):
            expected = f"CPR-{i:0{width}d}"
            rid = r.get("rule_id") if isinstance(r, dict) else None
            where = rid or f"rules[{i - 1}]"
            if rid != expected:
                self.err("E-ID", where, f"expected rule_id {expected} (IDs run 1..n with no gaps "
                         "or repeats, in document order)")
            ids.add(rid)
            if not self.keys(r, RULE_KEYS, where):
                continue
            self.check_clause_ref(r["clause"], where)
            if self.page_ok(r["page"], where):
                if r["page"] < last_page:
                    self.err("E-ORDER", where, f"page {r['page']} after page {last_page}; "
                             "keep rules in document order")
                last_page = max(last_page, r["page"])
            if r["type"] not in RULE_TYPES:
                self.err("E-SCHEMA", where, f"type {r['type']!r} not in {sorted(RULE_TYPES)}")
            sc = r["scope"]
            if (not isinstance(sc, list) or not sc or not set(sc) <= SCOPES
                    or ("all" in sc and len(sc) > 1) or len(set(sc)) != len(sc)):
                self.err("E-SCHEMA", where, f"scope must be [\"all\"] or a list drawn from "
                         f"{sorted(SCOPES - {'all'})}, got {sc!r}")
            ev = r["evidence_source"]
            if not isinstance(ev, list) or not ev or not set(ev) <= EVIDENCE:
                self.err("E-SCHEMA", where, f"evidence_source must be a non-empty list from "
                         f"{sorted(EVIDENCE)}, got {ev!r}")
            for k in ("condition", "required_action", "evidence_detail"):
                self.text(r, k, where)
            self.text(r, "approver", where, nullable=True)
            quote = self.text(r, "verbatim_quote", where)
            if quote and isinstance(r["page"], int) and 1 <= r["page"] <= self.n:
                if len(norm(quote)) < MIN_QUOTE_CHARS:
                    self.err("E-QUOTE", where, f"quote shorter than {MIN_QUOTE_CHARS} characters")
                elif not self.on_page(quote, r["page"]):
                    hits = [p for p in range(1, self.n + 1) if self.on_page(quote, p)]
                    hint = f"; found on page {hits}" if hits else "; not found on any page"
                    self.err("E-QUOTE", where, f"verbatim_quote not on page {r['page']}{hint}")
            used_params |= self.check_bounds(r, where, params)
        for name, p in params.items():
            if name not in used_params and not any(
                    isinstance(q, dict) and name in (q.get("resolves_by_scope") or {}).values()
                    and qn in used_params for qn, q in params.items()):
                self.err("E-PARAM", f"parameters.{name}", "declared but no rule references it")
        return ids

    def check_bounds(self, r, where, params):
        used = set()
        any_bound = False
        for side in ("low", "high"):
            v, inc = r[f"threshold_{side}"], r[f"threshold_{side}_inclusive"]
            p = r[f"threshold_{side}_param"]
            if v is not None and p is not None:
                self.err("E-THRESH", where, f"threshold_{side} has both a value and a parameter")
            if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 0):
                self.err("E-THRESH", where, f"threshold_{side} must be a whole number of GBP, "
                         f"got {v!r}")
            if p is not None:
                used.add(p)
                if p not in params:
                    self.err("E-PARAM", where, f"threshold_{side}_param {p!r} is not declared "
                             "in parameters")
            if v is not None or p is not None:
                any_bound = True
                if not isinstance(inc, bool):
                    self.err("E-THRESH", where, f"threshold_{side}_inclusive must be true/false "
                             "when the bound is set")
            elif inc is not None:
                self.err("E-THRESH", where, f"threshold_{side}_inclusive must be null when "
                         "the bound is null")
        lo, hi = r["threshold_low"], r["threshold_high"]
        if all(isinstance(x, int) and not isinstance(x, bool) for x in (lo, hi)) and lo > hi:
            self.err("E-THRESH", where, f"threshold_low {lo} above threshold_high {hi}")
        tt = r["threshold_text"]
        if any_bound:
            if not isinstance(tt, str) or not tt.strip():
                self.err("E-THRESH", where, "threshold_text required when a bound is set")
            elif isinstance(r["page"], int) and 1 <= r["page"] <= self.n \
                    and not self.on_page(tt, r["page"]):
                self.err("E-THRESH", where, f"threshold_text {tt!r} not on page {r['page']}")
        elif tt is not None:
            self.err("E-THRESH", where, "threshold_text set but both bounds are null")
        if isinstance(tt, str) and re.search(r"\bthreshold\b", tt, re.I) \
                and r["threshold_low_param"] is None and r["threshold_high_param"] is None:
            self.err("E-THRESH", where, "threshold_text names a Threshold but no bound uses a "
                     "parameter")
        return used

    def check_threshold_values(self, rules, notes):
        explained = set()
        for n in notes if isinstance(notes, list) else []:
            if isinstance(n, dict) and n.get("kind") == "interpretation":
                explained |= set(n.get("rule_ids") or [])
        for r in rules if isinstance(rules, list) else []:
            if not isinstance(r, dict) or not RULE_KEYS <= r.keys():
                continue
            printed = amounts(r["threshold_text"])
            for side in ("low", "high"):
                v = r[f"threshold_{side}"]
                if isinstance(v, int) and not isinstance(v, bool) and Decimal(v) not in printed \
                        and r["rule_id"] not in explained:
                    self.err("E-THRESH", r["rule_id"], f"threshold_{side} {v} is not an amount "
                             f"printed in threshold_text {sorted(map(str, printed))}; add an "
                             "'interpretation' note naming this rule if it is a conversion")

    def check_excluded(self, excluded):
        if not isinstance(excluded, list):
            self.err("E-SCHEMA", "excluded", "must be an array")
            return
        seen = set()
        for i, e in enumerate(excluded):
            where = f"excluded[{i}]"
            if not self.keys(e, EXCLUDED_KEYS, where):
                continue
            where = f"excluded {e['clause']}"
            if e["clause"] in seen:
                self.err("E-COVER", where, "listed twice")
            seen.add(e["clause"])
            self.check_clause_ref(e["clause"], where)
            self.page_ok(e["page"], where)
            reason = self.text(e, "reason", where)
            if reason and ("\n" in reason or len(reason) > MAX_REASON_CHARS):
                self.err("E-SCHEMA", where, f"reason must be one line of at most "
                         f"{MAX_REASON_CHARS} characters")

    def check_notes(self, notes, rule_ids):
        if not isinstance(notes, list):
            self.err("E-SCHEMA", "notes", "must be an array")
            return
        for i, n in enumerate(notes, 1):
            expected = f"N-{i:02d}"
            where = n.get("id", f"notes[{i - 1}]") if isinstance(n, dict) else f"notes[{i - 1}]"
            if not self.keys(n, NOTE_KEYS, where, NOTE_OPTIONAL):
                continue
            if n["id"] != expected:
                self.err("E-ID", where, f"expected note id {expected}")
            if n["kind"] not in NOTE_KINDS:
                self.err("E-SCHEMA", where, f"kind {n['kind']!r} not in {sorted(NOTE_KINDS)}")
            self.text(n, "clause", where)
            self.text(n, "text", where)
            if not isinstance(n["rule_ids"], list) or not set(n["rule_ids"]) <= rule_ids:
                self.err("E-SCHEMA", where, f"rule_ids must list existing rule IDs, got "
                         f"{n['rule_ids']!r}")
            if self.page_ok(n["page"], where) and "quote" in n:
                if not isinstance(n["quote"], str) or not self.on_page(n["quote"], n["page"]):
                    self.err("E-QUOTE", where, f"quote not on page {n['page']}")

    def check_clause_ref(self, clause, where):
        if not isinstance(clause, str):
            self.err("E-SCHEMA", where, "clause must be a string")
        elif not (NUMERIC_CLAUSE.match(clause) or APPENDIX_REF.match(clause)):
            self.err("E-CLAUSE", where, f"clause {clause!r} is neither a numbered clause (6.16) "
                     "nor an appendix reference (App B row B1, App C note)")

    def check_coverage(self, rules, excluded):
        clauses, rows = inventory(self.layout)
        in_pdf = {c for c, _ in clauses}
        rows_in_pdf = {c for c, _ in rows}
        appendices_with_rows = {c.split()[1] for c in rows_in_pdf}
        ruled = {r.get("clause") for r in rules if isinstance(r, dict)} if isinstance(rules, list) else set()
        excl = {e.get("clause") for e in excluded if isinstance(e, dict)} if isinstance(excluded, list) else set()
        listed = {c for c in ruled | excl if isinstance(c, str)}
        for c in sorted(ruled & excl, key=str):
            self.err("E-COVER", c, "appears in both rules and excluded")
        for c in listed:
            if NUMERIC_CLAUSE.match(c) and c not in in_pdf:
                self.err("E-CLAUSE", c, "no clause with this number in the PDF")
            m = APPENDIX_REF.match(c)
            if m and m.group(3) and not m.group(3).isdigit() \
                    and m.group(1) in appendices_with_rows and c not in rows_in_pdf:
                self.err("E-CLAUSE", c, "no row with this label in the appendix")
        for c, page in clauses:
            parts = c.split(".")
            ancestors = {".".join(parts[:k]) for k in range(2, len(parts))}
            if c in listed or ancestors & listed or any(x.startswith(c + ".") for x in listed):
                continue
            self.err("E-COVER", c, f"clause on page {page} is in neither rules nor excluded")
        for c, page in rows:
            if c not in listed:
                self.err("E-COVER", c, f"appendix row on page {page} is in neither rules nor "
                         "excluded")


def main():
    here = Path(__file__).resolve()
    root = here.parents[3]
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rules", type=Path, default=root / "outputs" / "rules.json")
    ap.add_argument("--pdf", type=Path, default=root / "data" / "contract-rules.pdf")
    ap.add_argument("--inventory", action="store_true",
                    help="print the clauses and appendix rows found in the PDF, then exit")
    a = ap.parse_args()
    try:
        n, layout, searchable = load_pdf(a.pdf)
        if a.inventory:
            clauses, rows = inventory(layout)
            for c, p in clauses + rows:
                print(f"{c}\tpage {p}")
            print(f"# {len(clauses)} numbered clauses, {len(rows)} appendix rows "
                  "(Appendix A bands and unlabelled notes are not detected; add them by reading)")
            return 0
        if not a.rules.is_file():
            raise Cannot(f"rules file not found: {a.rules}")
        try:
            data = json.loads(a.rules.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise Cannot(f"{a.rules} is not valid JSON: {e}")
    except Cannot as e:
        print(f"CANNOT RUN: {e}", file=sys.stderr)
        return 2
    v = Verifier(data, a.pdf, n, layout, searchable)
    v.check()
    if v.errors:
        print(f"FAIL: {len(v.errors)} error(s)")
        print("\n".join(v.errors))
        return 1
    print(f"PASS: {len(data['rules'])} rules, {len(data['excluded'])} excluded, "
          f"{len(data['notes'])} notes, {len(data['parameters'])} parameters; every quote "
          "found on its page")
    return 0


if __name__ == "__main__":
    sys.exit(main())
