#!/usr/bin/env python3
"""Tests for scripts/verify_history.py on a synthetic two-page committee PDF.

Builds the PDF and a valid history.json in a temp dir, checks the valid file
passes, then plants one error at a time and checks the verifier fails with the
expected error code. Run: .venv/bin/python scripts/tests/test_verify_history.py
"""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

VERIFIER = Path(__file__).resolve().parents[1] / "verify_history.py"
PDF_REL = "data/committee/fixture.pdf"

# (x, y, text) per line. Page 1 is a completed-work table whose cells sit in
# columns, so plain text separates a row's cells while -layout keeps them on
# one line. Page 2 holds a likelihood scale, one matrix row and a band.
PAGES = [
    [(72, 760, "Internal Audit Plan Update Report"), (420, 760, "Appendix A"),
     (72, 745, "(End of March 2025)"),
     (72, 720, "1) COMPLETED AUDITS"),
     (72, 700, "Directorate/Dept/Service"), (250, 700, "Audit Title"), (430, 700, "Overall Opinion"),
     (72, 680, "Finance, Property and"), (250, 680, "Contract Letting"), (430, 680, "Reasonable Assurance"),
     (72, 668, "Procurement"),
     (72, 648, "Schools"), (250, 648, "Garland"), (430, 648, "Weak"),
     (72, 620, "2) COMPLETED FOLLOW UPS"),
     (72, 600, "None")],
    [(72, 760, "Risk Management Strategy"),
     (72, 740, "4.3 Impact may be Negligible (1), Minor (2), Medium (2), Major (4), or Critical (5)."),
     (72, 715, "Likelihood"), (200, 715, "Incidents"), (430, 715, "Probability"),
     (72, 700, "3 Likely"), (200, 700, "Risk is likely to occur within a 12 month period"), (430, 700, "30% - 69%"),
     (72, 670, "5 Critical"), (160, 670, "Moderate"), (230, 670, "High"), (290, 670, "Extreme"),
     (350, 670, "Extreme"), (410, 670, "Extreme"),
     (72, 640, "Extreme (Red)"), (200, 640, "15 -25"), (260, 640, "Add to Corporate Risk Register")],
]


def pdf_string(text):
    raw = text.encode("cp1252")
    return b"(" + raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"


def build_pdf(path):
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", None,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    kids = []
    for lines in PAGES:
        stream = b"".join(b"BT /F1 10 Tf %d %d Td %s Tj ET\n" % (x, y, pdf_string(t))
                          for x, y, t in lines)
        objs.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"endstream")
        content_id = len(objs)
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % content_id)
        kids.append(len(objs))
    objs[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
        b" ".join(b"%d 0 R" % k for k in kids), len(kids))
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.write_bytes(bytes(out))


def valid_history(sha):
    src = {"source": PDF_REL}
    return {
        "sources": [{"file": PDF_REL, "sha256": sha, "pages": 2, "kind": "other",
                     "title": "Fixture", "date_or_period": "End of March 2025"}],
        "audits": [
            {"id": "A-01", "section": "completed_audit", **src, "pdf_page": 1,
             "directorate": None, "service": "Finance, Property and Procurement",
             "title": "Contract Letting", "opinion": "Reasonable Assurance",
             "period": "End of March 2025",
             "quote": "Finance, Property and Contract Letting Reasonable Assurance",
             "cells": ["Finance, Property and Procurement", "Contract Letting", "Reasonable Assurance"]},
            {"id": "A-02", "section": "completed_audit", **src, "pdf_page": 1,
             "directorate": "Schools", "service": None, "title": "Garland", "opinion": "Weak",
             "period": "End of March 2025", "quote": "Schools Garland Weak",
             "cells": ["Garland", "Weak"]},
        ],
        "agreed_actions": [],
        "risk_themes": [],
        "scoring_method": {
            "status": "found",
            "likelihood_scale": [{"score": 3, "label": "Likely",
                                  "definition": "Risk is likely to occur within a 12 month period",
                                  "probability": "30% - 69%", **src, "pdf_page": 2,
                                  "quote": "Risk is likely to occur within a 12 month period",
                                  "cells": ["3 Likely", "30% - 69%"]}],
            "impact_scale": [{"score": 3, "label": "Medium", "criteria": {}, **src, "pdf_page": 2,
                              "quote": "Major (4), or Critical (5)"}],
            "matrix": [{"impact_score": 5, "impact_label": "Critical",
                        "band_labels": ["Moderate", "High", "Extreme", "Extreme", "Extreme"],
                        **src, "pdf_page": 2,
                        "quote": "5 Critical Moderate High Extreme Extreme Extreme"}],
            "bands": [{"band": "Extreme", "rag": "Red", "score_range": "15 -25",
                       "escalation": "Add to Corporate Risk Register", **src, "pdf_page": 2,
                       "quote": "Extreme (Red) 15 -25 Add to Corporate Risk Register"}],
        },
        "strategic_risk_register": {"public": False, "note": "Exempt report; not in the papers"},
        "discrepancies": [{"id": "D-01", "description": "4.3 labels Medium as (2); the scale gives 3",
                           "evidence": [{**src, "pdf_page": 2, "quote": "Minor (2), Medium (2), Major (4)"}]}],
        "gaps": [
            {"id": "G-01", "area": "agreed_actions", "text": "No agreed actions in the papers",
             "sources_checked": [PDF_REL]},
            {"id": "G-02", "area": "risk_themes", "text": "No risk themes in the papers",
             "sources_checked": [PDF_REL]},
            {"id": "G-03", "area": "strategic_risk_register", "text": "Exempt; not public",
             "sources_checked": [PDF_REL]},
        ],
    }


def run(root, data):
    (root / "outputs").mkdir(exist_ok=True)
    (root / "outputs" / "history.json").write_text(json.dumps(data), encoding="utf-8")
    p = subprocess.run([sys.executable, str(VERIFIER), "--root", str(root)],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def planted(h):
    """(name, mutate, expected code) for each planted error."""
    def m(fn):
        def apply(x):
            fn(x)
            return x
        return apply
    return [
        ("quote on the wrong page", m(lambda x: x["audits"][0].update(pdf_page=2)), "E-QUOTE"),
        ("quote with one word changed", m(lambda x: x["audits"][0].update(
            quote="Finance, Property and Contract Letting Substantial Assurance")), "E-QUOTE"),
        ("cell not on the page", m(lambda x: x["audits"][1]["cells"].__setitem__(1, "Limited Assurance")), "E-CELL"),
        ("a score added to an audit", m(lambda x: x["audits"][0].update(risk_rating=4)), "E-SCHEMA"),
        ("id sequence gap", m(lambda x: x["audits"][1].update(id="A-03")), "E-ID"),
        ("source not in sources", m(lambda x: x["audits"][0].update(source="data/committee/other.pdf")), "E-SOURCE"),
        ("stale sha256", m(lambda x: x["sources"][0].update(sha256="0" * 64)), "E-SOURCE"),
        ("pdf_page out of range", m(lambda x: x["audits"][0].update(pdf_page=9)), "E-PAGE"),
        ("missing pdf_page", m(lambda x: x["audits"][0].pop("pdf_page")), "E-SCHEMA"),
        ("empty section with no gap", m(lambda x: x["gaps"].pop(0)), "E-GAP"),
        ("register absence not declared", m(lambda x: x["gaps"].pop(2)), "E-GAP"),
        ("register marked public", m(lambda x: x["strategic_risk_register"].update(public=True)), "E-SCHEMA"),
        ("discrepancy without evidence", m(lambda x: x["discrepancies"][0].update(evidence=[])), "E-EVIDENCE"),
        ("matrix labels out of order", m(lambda x: x["scoring_method"]["matrix"][0].update(
            band_labels=["High", "Moderate", "Extreme", "Extreme", "Extreme"])), "E-CELL"),
        ("scoring found but bands empty", m(lambda x: x["scoring_method"].update(bands=[])), "E-SCORING"),
    ]


def main():
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pdf = root / PDF_REL
        pdf.parent.mkdir(parents=True)
        build_pdf(pdf)
        sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        base = valid_history(sha)

        code, out = run(root, base)
        ok = code == 0 and out.startswith("PASS")
        print(f"{'ok ' if ok else 'FAIL'} valid history passes")
        if not ok:
            print(out)
            failures += 1

        for name, mutate, expected in planted(base):
            code, out = run(root, mutate(copy.deepcopy(base)))
            ok = code == 1 and f"[{expected}]" in out
            print(f"{'ok ' if ok else 'FAIL'} {name} -> {expected}")
            if not ok:
                print("   ", out.strip().replace("\n", "\n    "))
                failures += 1

        (root / "outputs" / "history.json").unlink()
        p = subprocess.run([sys.executable, str(VERIFIER), "--root", str(root)],
                           capture_output=True, text=True)
        ok = p.returncode == 2
        print(f"{'ok ' if ok else 'FAIL'} missing history.json -> exit 2")
        failures += not ok

    print("ALL PASS" if not failures else f"{failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
