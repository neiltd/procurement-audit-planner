#!/usr/bin/env python3
"""Tests for verify_quotes.py on a synthetic two-page rulebook PDF.

Builds the PDF and a valid rules file in a temp dir, checks the valid file
passes, then applies one deliberate error at a time and checks the verifier
fails with the expected error code. Run: .venv/bin/python <this file>
"""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

VERIFIER = Path(__file__).resolve().parents[1] / "verify_quotes.py"

# (x, y, text) per line; clause numbers and their text are separate runs so
# pdftotext -layout keeps the gap the inventory relies on.
PAGES = [
    [(72, 760, "Part []"), (72, 740, "Contract Rules"),
     (72, 710, "1"), (100, 710, "Introduction"),
     (90, 690, "1.1"), (140, 690, "“Threshold” refers to the relevant financial threshold"),
     (140, 676, "published on the Procurement intranet page."),
     (90, 656, "1.2"), (140, 656, "These Rules set out minimum requirements to be followed."),
     (72, 626, "2"), (100, 626, "Buying"),
     (90, 606, "2.1"), (140, 606, "There shall be no artificial splitting of a contract to avoid"),
     (140, 592, "the application of these Rules."),
     (90, 572, "2.2"), (140, 572, "Any contract award with a value over £500,000 is a Key Decision"),
     (140, 558, "of the Council."),
     (72, 538, "2.2.1"), (140, 538, "The Monitoring Officer must approve every waiver in writing.")],
    [(72, 760, "Contract Rules - Appendix B"),
     (72, 740, "Financial thresholds and mandatory processes"),
     (80, 710, "A"), (110, 710, "Above £1,000 and less than £25,000"),
     (330, 710, "At least one quote must be sought."),
     (80, 680, "B1"), (110, 680, "£25,000 or more and less than the Threshold"),
     (330, 680, "Three quotes via the Procurement Portal.")],
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


def rule(rid, clause, page, type_, quote, **kw):
    base = {
        "rule_id": rid, "clause": clause, "page": page, "type": type_, "scope": ["all"],
        "condition": "any procurement", "threshold_text": None,
        "threshold_low": None, "threshold_low_inclusive": None, "threshold_low_param": None,
        "threshold_high": None, "threshold_high_inclusive": None, "threshold_high_param": None,
        "required_action": "follow the rule", "approver": None,
        "evidence_source": ["council_records"], "evidence_detail": "procurement file",
        "verbatim_quote": quote,
    }
    base.update(kw)
    return base


def valid_rules(sha):
    return {
        "source": {"file": "fixture.pdf", "sha256": sha, "pages": 2},
        "parameters": {
            "THRESHOLD_GOODS_SERVICES": {
                "value": None, "clause": "1.1", "page": 1, "printed_as": "Threshold",
                "description": "Goods and services threshold; value published on the intranet"},
        },
        "rules": [
            rule("CPR-01", "2.1", 1, "anti-avoidance",
                 "There shall be no artificial splitting of a contract to avoid the application "
                 "of these Rules.", evidence_source=["spend_data"]),
            rule("CPR-02", "2.2", 1, "approval",
                 "Any contract award with a value over £500,000 is a Key Decision of the Council.",
                 threshold_text="over £500,000", threshold_low=500000,
                 threshold_low_inclusive=False, approver="Executive (Key Decision)"),
            rule("CPR-03", "2.2.1", 1, "approval",
                 "The Monitoring Officer must approve every waiver in writing.",
                 approver="Monitoring Officer"),
            rule("CPR-04", "App B row A", 2, "procedure", "At least one quote must be sought.",
                 threshold_text="Above £1,000 and less than £25,000",
                 threshold_low=1000, threshold_low_inclusive=False,
                 threshold_high=25000, threshold_high_inclusive=False),
            rule("CPR-05", "App B row B1", 2, "procedure",
                 "Three quotes via the Procurement Portal.", scope=["goods", "services"],
                 threshold_text="£25,000 or more and less than the Threshold",
                 threshold_low=25000, threshold_low_inclusive=True,
                 threshold_high_param="THRESHOLD_GOODS_SERVICES",
                 threshold_high_inclusive=False),
        ],
        "excluded": [
            {"clause": "1.1", "page": 1, "reason": "Definition; feeds parameters, no action"},
            {"clause": "1.2", "page": 1, "reason": "Statement of purpose; nothing to test"},
        ],
        "notes": [
            {"id": "N-01", "kind": "placeholder", "clause": "heading", "page": 1,
             "text": "Part number printed as a blank placeholder.", "rule_ids": [],
             "quote": "Part []"},
        ],
    }


def r(d, i):
    return d["rules"][i]


# (name, mutation, expected error code)
MUTATIONS = [
    ("quote on wrong page", lambda d: r(d, 2).update(page=2), "E-QUOTE"),
    ("quote reworded", lambda d: r(d, 0).update(
        verbatim_quote="There shall be no splitting of a contract to avoid the application "
                       "of these Rules."), "E-QUOTE"),
    ("quote too short", lambda d: r(d, 2).update(verbatim_quote="waiver"), "E-QUOTE"),
    ("rule id gap", lambda d: r(d, 2).update(rule_id="CPR-07"), "E-ID"),
    ("rule id duplicate", lambda d: r(d, 1).update(rule_id="CPR-01"), "E-ID"),
    ("undeclared parameter", lambda d: r(d, 4).update(
        threshold_high_param="THRESHOLD_WORKS"), "E-PARAM"),
    ("parameter filled from memory", lambda d: d["parameters"]["THRESHOLD_GOODS_SERVICES"]
        .update(value=214904), "E-PARAM"),
    ("unused parameter", lambda d: d["parameters"].update(THRESHOLD_LIGHT_TOUCH={
        "value": None, "clause": "1.1", "page": 1, "printed_as": "Threshold",
        "description": "unused"}), "E-PARAM"),
    ("threshold in pence", lambda d: r(d, 3).update(threshold_high=24999.99), "E-THRESH"),
    ("threshold not printed", lambda d: r(d, 1).update(threshold_low=50000), "E-THRESH"),
    ("missing inclusive flag", lambda d: r(d, 3).update(threshold_low_inclusive=None), "E-THRESH"),
    ("Threshold named but no parameter", lambda d: r(d, 4).update(
        threshold_high_param=None, threshold_high_inclusive=None), "E-THRESH"),
    ("threshold_text not on page", lambda d: r(d, 3).update(
        threshold_text="Above £1,000 and less than £30,000"), "E-THRESH"),
    ("clause not covered", lambda d: d["excluded"].pop(1), "E-COVER"),
    ("appendix row not covered", lambda d: d.update(
        rules=d["rules"][:4]), "E-COVER"),
    ("clause in rules and excluded", lambda d: d["excluded"].append(
        {"clause": "2.1", "page": 1, "reason": "duplicate"}), "E-COVER"),
    ("invented clause", lambda d: d["excluded"].append(
        {"clause": "3.4", "page": 1, "reason": "made up"}), "E-CLAUSE"),
    ("invented appendix row", lambda d: d["excluded"].append(
        {"clause": "App B row C", "page": 2, "reason": "made up"}), "E-CLAUSE"),
    ("bad type", lambda d: r(d, 0).update(type="rule"), "E-SCHEMA"),
    ("unknown key", lambda d: r(d, 0).update(note="x"), "E-SCHEMA"),
    ("scope mixes all", lambda d: r(d, 0).update(scope=["all", "works"]), "E-SCHEMA"),
    ("multi-line reason", lambda d: d["excluded"][0].update(reason="line one\nline two"),
     "E-SCHEMA"),
    ("note points at missing rule", lambda d: d["notes"][0].update(rule_ids=["CPR-99"]),
     "E-SCHEMA"),
    ("rules out of order", lambda d: d["rules"].reverse(), "E-ORDER"),
    ("stale source hash", lambda d: d["source"].update(sha256="0" * 64), "E-SOURCE"),
]


def verify(tmp, pdf, data):
    path = tmp / "rules.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    p = subprocess.run([sys.executable, str(VERIFIER), "--rules", str(path), "--pdf", str(pdf)],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    failures = []
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pdf = tmp / "fixture.pdf"
        build_pdf(pdf)
        good = valid_rules(hashlib.sha256(pdf.read_bytes()).hexdigest())

        code, out = verify(tmp, pdf, good)
        print(f"{'ok ' if code == 0 else 'BAD'} valid fixture passes (exit {code})")
        if code != 0:
            failures.append(("valid fixture", out))

        # A pence threshold converted to whole pounds passes once a note explains it.
        conv = copy.deepcopy(good)
        conv["notes"].append({"id": "N-02", "kind": "interpretation", "clause": "2.2", "page": 1,
                              "text": "Converted for test.", "rule_ids": ["CPR-02"]})
        r(conv, 1).update(threshold_low=500001, threshold_low_inclusive=True)
        code, out = verify(tmp, pdf, conv)
        print(f"{'ok ' if code == 0 else 'BAD'} explained conversion passes (exit {code})")
        if code != 0:
            failures.append(("explained conversion", out))

        for name, mutate, expected in MUTATIONS:
            d = copy.deepcopy(good)
            mutate(d)
            code, out = verify(tmp, pdf, d)
            ok = code == 1 and f"[{expected}]" in out
            print(f"{'ok ' if ok else 'BAD'} {name}: expect {expected}, exit {code}")
            if not ok:
                failures.append((name, out))

        code, out = verify(tmp, tmp / "missing.pdf", good)
        ok = code == 2
        print(f"{'ok ' if ok else 'BAD'} missing PDF exits 2 (exit {code})")
        if not ok:
            failures.append(("missing PDF", out))

    for name, out in failures:
        print(f"\n--- {name} ---\n{out}")
    print(f"\n{len(MUTATIONS) + 3 - len(failures)}/{len(MUTATIONS) + 3} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
