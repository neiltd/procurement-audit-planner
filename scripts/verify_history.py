#!/usr/bin/env python3
"""Verify outputs/history.json against the committee PDFs it cites.

Checks the schema (records only: no keys outside each section's whitelist),
sequential IDs, source hashes, and that every quote and every table cell lies
on its stated PDF page. Also checks that empty sections and the non-public
Strategic Risk Register are declared as gaps. Standard library only; needs
pdftotext and pdfinfo.

Usage:
  verify_history.py [--history PATH] [--root DIR]

Paths inside history.json are relative to --root (default: the repo root).
Exit codes: 0 pass, 1 errors found, 2 cannot run (missing file or tool).
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

MIN_QUOTE_CHARS = 10

TOP_KEYS = {"sources", "audits", "agreed_actions", "risk_themes", "scoring_method",
            "strategic_risk_register", "discrepancies", "gaps"}
SOURCE_KEYS = {"file", "sha256", "pages", "kind", "title", "date_or_period"}
SOURCE_KINDS = {"completed_work_appendix", "audit_plan_report", "risk_management_strategy", "other"}
PROVENANCE = {"source", "pdf_page", "quote"}

# Per-section whitelists: the agent records what the papers say and nothing else.
SECTIONS = {
    "audits": ("A", PROVENANCE | {"id", "section", "directorate", "service", "title",
                                  "opinion", "implementation_progress", "period", "cells"}),
    "agreed_actions": ("ACT", PROVENANCE | {"id", "theme", "audit_title", "due_date",
                                            "status", "owner", "cells"}),
    "risk_themes": ("T", PROVENANCE | {"id", "theme", "description", "context"}),
    "discrepancies": ("D", {"id", "description", "evidence"}),
    "gaps": ("G", {"id", "area", "text", "sources_checked"}),
}
GAP_AREAS = {"audits", "agreed_actions", "risk_themes", "scoring_method",
             "strategic_risk_register", "audit_plan_detail", "other"}
AUDIT_SECTIONS = {"completed_audit", "follow_up", "advisory"}

SCORING_KEYS = {"status", "evaluation_levels", "likelihood_scale", "impact_scale",
                "matrix", "bands", "appetite", "tolerance"}
SCORING_LISTS = {
    "evaluation_levels": PROVENANCE | {"level", "definition"},
    "likelihood_scale": PROVENANCE | {"score", "label", "definition", "probability", "cells"},
    "impact_scale": PROVENANCE | {"score", "label", "criteria", "cells"},
    "matrix": PROVENANCE | {"impact_score", "impact_label", "band_labels", "scores_as_printed"},
    "bands": PROVENANCE | {"band", "rag", "score_range", "escalation", "response", "cells"},
    "appetite": PROVENANCE | {"category", "level", "statement", "cells"},
    "tolerance": PROVENANCE | {"definition"},
}
SRR_KEYS = {"public", "note"}

CHAR_MAP = {ord(k): v for k, v in {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "‐": "-", "‑": "-", "–": "-", "—": "-", " ": " ",
}.items()}


class Cannot(Exception):
    """Input or tool missing: exit 2, not a verification failure."""


def norm(text):
    """NFKC, straight quotes, plain dashes, bullets dropped, whitespace collapsed."""
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


def load_pdf(path):
    """Searchable text per page: normalised plain and layout variants."""
    m = re.search(r"^Pages:\s+(\d+)", run(["pdfinfo", str(path)]), re.M)
    if not m:
        raise Cannot(f"pdfinfo reported no page count for {path}")
    n = int(m.group(1))
    variants = [set() for _ in range(n)]
    for flags in ([], ["-layout"]):
        chunks = run(["pdftotext", *flags, "-enc", "UTF-8", str(path), "-"]).split("\f")
        if len(chunks) < n:
            raise Cannot(f"pdftotext returned {len(chunks)} pages for {path}, pdfinfo says {n}")
        for i in range(n):
            t = norm(chunks[i])
            variants[i] |= {t, re.sub(r"(\w)- (\w)", r"\1-\2", t)}
    return n, variants


class Verifier:
    def __init__(self, data, root):
        self.d, self.root = data, root
        self.pdfs = {}          # file -> (n_pages, variants)
        self.errors = []

    def err(self, code, where, msg):
        self.errors.append(f"[{code}] {where}: {msg}")

    def on_page(self, text, file, page):
        t = norm(text)
        return any(t in v for v in self.pdfs[file][1][page - 1])

    def keys(self, obj, allowed, where, required=frozenset()):
        if not isinstance(obj, dict):
            self.err("E-SCHEMA", where, "must be an object")
            return False
        extra = obj.keys() - allowed
        missing = required - obj.keys()
        if extra:
            self.err("E-SCHEMA", where, f"keys not allowed here {sorted(extra)} "
                     "(history.json records the papers; it adds no fields of its own)")
        if missing:
            self.err("E-SCHEMA", where, f"missing keys {sorted(missing)}")
        return not missing

    # --- provenance -----------------------------------------------------------

    def provenance(self, obj, where):
        """obj carries source, pdf_page, quote (and optional cells): check them."""
        if not self.keys(obj, obj.keys(), where, PROVENANCE):
            return
        f, p, q = obj["source"], obj["pdf_page"], obj["quote"]
        if f not in self.pdfs:
            self.err("E-SOURCE", where, f"source {f!r} is not listed in sources")
            return
        n = self.pdfs[f][0]
        if isinstance(p, bool) or not isinstance(p, int) or not 1 <= p <= n:
            self.err("E-PAGE", where, f"pdf_page must be an integer 1..{n} for {f}, got {p!r}")
            return
        if not isinstance(q, str) or len(norm(q)) < MIN_QUOTE_CHARS:
            self.err("E-QUOTE", where, f"quote must be a string of at least {MIN_QUOTE_CHARS} characters")
        elif not self.on_page(q, f, p):
            hits = [i for i in range(1, n + 1) if self.on_page(q, f, i)]
            hint = f"; found on page {hits}" if hits else "; not found on any page"
            self.err("E-QUOTE", where, f"quote not on {f} page {p}{hint}")
        cells = obj.get("cells")
        if cells is not None:
            if not isinstance(cells, list) or not all(isinstance(c, str) and c.strip() for c in cells):
                self.err("E-SCHEMA", where, "cells must be a list of non-empty strings")
            else:
                for c in cells:
                    if not self.on_page(c, f, p):
                        self.err("E-CELL", where, f"cell {c!r} not on {f} page {p}")

    # --- sections -------------------------------------------------------------

    def check(self):
        d = self.d
        if not self.keys(d, TOP_KEYS, "top level", TOP_KEYS):
            return
        self.check_sources(d["sources"])
        if not self.pdfs:
            return
        for name, (prefix, allowed) in SECTIONS.items():
            self.check_list(name, d[name], prefix, allowed)
        for i, a in enumerate(d["audits"] if isinstance(d["audits"], list) else []):
            if isinstance(a, dict) and a.get("section") not in AUDIT_SECTIONS:
                self.err("E-SCHEMA", a.get("id", f"audits[{i}]"),
                         f"section must be one of {sorted(AUDIT_SECTIONS)}")
        self.check_discrepancies(d["discrepancies"])
        self.check_gaps(d["gaps"])
        self.check_scoring(d["scoring_method"])
        self.check_srr(d["strategic_risk_register"])
        self.check_required_gaps()

    def check_sources(self, sources):
        if not isinstance(sources, list) or not sources:
            self.err("E-SCHEMA", "sources", "must be a non-empty array")
            return
        for i, s in enumerate(sources):
            where = f"sources[{i}]"
            if not self.keys(s, SOURCE_KEYS, where, SOURCE_KEYS):
                continue
            path = self.root / s["file"]
            if not path.is_file():
                self.err("E-SOURCE", where, f"file not found: {s['file']}")
                continue
            if s["kind"] not in SOURCE_KINDS:
                self.err("E-SCHEMA", where, f"kind must be one of {sorted(SOURCE_KINDS)}")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            if s["sha256"] != sha:
                self.err("E-SOURCE", where, f"sha256 does not match {s['file']} ({sha[:12]}…)")
            self.pdfs[s["file"]] = load_pdf(path)
            if s["pages"] != self.pdfs[s["file"]][0]:
                self.err("E-SOURCE", where, f"pages {s['pages']!r} but the PDF has "
                         f"{self.pdfs[s['file']][0]}")

    def check_list(self, name, items, prefix, allowed):
        if not isinstance(items, list):
            self.err("E-SCHEMA", name, "must be an array")
            return
        for i, it in enumerate(items, 1):
            expected = f"{prefix}-{i:02d}"
            where = it.get("id", f"{name}[{i - 1}]") if isinstance(it, dict) else f"{name}[{i - 1}]"
            if not self.keys(it, allowed, where, {"id"}):
                continue
            if it["id"] != expected:
                self.err("E-ID", where, f"expected id {expected} (IDs run 1..n with no gaps)")
            if PROVENANCE <= allowed:
                self.provenance(it, where)

    def check_discrepancies(self, items):
        for i, it in enumerate(items if isinstance(items, list) else []):
            if not isinstance(it, dict):
                continue
            where = it.get("id", f"discrepancies[{i}]")
            if not isinstance(it.get("description"), str) or not it["description"].strip():
                self.err("E-SCHEMA", where, "description must be a non-empty string")
            ev = it.get("evidence")
            if not isinstance(ev, list) or not ev:
                self.err("E-EVIDENCE", where, "evidence must list at least one quoted passage")
                continue
            for j, e in enumerate(ev):
                if self.keys(e, PROVENANCE | {"cells"}, f"{where}.evidence[{j}]", PROVENANCE):
                    self.provenance(e, f"{where}.evidence[{j}]")

    def check_gaps(self, items):
        for i, g in enumerate(items if isinstance(items, list) else []):
            if not isinstance(g, dict):
                continue
            where = g.get("id", f"gaps[{i}]")
            if g.get("area") not in GAP_AREAS:
                self.err("E-SCHEMA", where, f"area must be one of {sorted(GAP_AREAS)}")
            sc = g.get("sources_checked")
            if not isinstance(sc, list) or not sc or not set(sc) <= set(self.pdfs):
                self.err("E-SCHEMA", where, "sources_checked must list files from sources")

    def check_scoring(self, sm):
        if not self.keys(sm, SCORING_KEYS, "scoring_method", {"status"}):
            return
        if sm["status"] not in {"found", "not_found"}:
            self.err("E-SCHEMA", "scoring_method.status", "must be 'found' or 'not_found'")
            return
        for name, allowed in SCORING_LISTS.items():
            items = sm.get(name, [])
            if not isinstance(items, list):
                self.err("E-SCHEMA", f"scoring_method.{name}", "must be an array")
                continue
            if sm["status"] == "found" and name in {"likelihood_scale", "impact_scale", "matrix", "bands"} \
                    and not items:
                self.err("E-SCORING", f"scoring_method.{name}", "empty while status is 'found'; "
                         "record it or declare a gap")
            for i, it in enumerate(items):
                where = f"scoring_method.{name}[{i}]"
                if self.keys(it, allowed, where, PROVENANCE):
                    self.provenance(it, where)
            if name == "matrix":
                for i, row in enumerate(items):
                    labels = row.get("band_labels") if isinstance(row, dict) else None
                    if isinstance(labels, list) and isinstance(row.get("quote"), str) \
                            and norm(" ".join(labels)) not in norm(row["quote"]):
                        self.err("E-CELL", f"scoring_method.matrix[{i}]",
                                 "band_labels, joined in order, are not in the row's quote")

    def check_srr(self, srr):
        if self.keys(srr, SRR_KEYS, "strategic_risk_register", SRR_KEYS) \
                and srr["public"] is not False:
            self.err("E-SCHEMA", "strategic_risk_register.public",
                     "the Strategic Risk Register is exempt; record public: false")

    def check_required_gaps(self):
        d = self.d
        areas = {g.get("area") for g in d["gaps"] if isinstance(g, dict)} \
            if isinstance(d["gaps"], list) else set()
        need = {"strategic_risk_register"}
        for name in ("audits", "agreed_actions", "risk_themes"):
            if isinstance(d[name], list) and not d[name]:
                need.add(name)
        if isinstance(d["scoring_method"], dict) and d["scoring_method"].get("status") == "not_found":
            need.add("scoring_method")
        for area in sorted(need - areas):
            self.err("E-GAP", "gaps", f"no gap recorded for area {area!r} "
                     "(an empty section or absent source must be declared)")


def main():
    root_default = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", type=Path, default=root_default)
    ap.add_argument("--history", type=Path, default=None)
    a = ap.parse_args()
    hist = a.history or a.root / "outputs" / "history.json"
    try:
        if not hist.is_file():
            raise Cannot(f"history file not found: {hist}")
        try:
            data = json.loads(hist.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise Cannot(f"{hist} is not valid JSON: {e}")
        v = Verifier(data, a.root)
        v.check()
    except Cannot as e:
        print(f"CANNOT RUN: {e}", file=sys.stderr)
        return 2
    if v.errors:
        print(f"FAIL: {len(v.errors)} error(s)")
        print("\n".join(v.errors))
        return 1
    d = data
    print(f"PASS: {len(d['audits'])} audits, {len(d['agreed_actions'])} actions, "
          f"{len(d['risk_themes'])} themes, {len(d['discrepancies'])} discrepancies, "
          f"{len(d['gaps'])} gaps; scoring method {d['scoring_method']['status']}; "
          "every quote and cell found on its page")
    return 0


if __name__ == "__main__":
    sys.exit(main())
