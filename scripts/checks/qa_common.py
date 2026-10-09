"""Shared helpers for the QA checks in scripts/checks/.

Every check prints one line per problem ("  - ...") and ends with exactly one
result line, which run_checks.py reads:

  RESULT PASS <check>: <summary>
  RESULT FAIL <check>: <summary>; <n> problem(s)
  RESULT CANNOT RUN <check>: <why>

Exit codes: 0 pass, 1 fail, 2 cannot run. Citation and decision parsing come
from .claude/skills/risk-assessment/build_register.py, so QA reads them the
same way the builders do.
"""
import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "risk-assessment"))
from build_register import CITE_RE, Report, Sources, parse_decisions  # noqa: E402,F401

ROW_ID_PATTERN = r"[\w.\-]+\.xlsx:[^:\n|`]+:\d+"


def parse_args(doc, extra=None):
    ap = argparse.ArgumentParser(description=doc.strip().split("\n")[0])
    ap.add_argument("--root", default=str(REPO), help="project root holding outputs/ and data/")
    if extra:
        extra(ap)
    return ap.parse_args()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(x):
    try:
        return float(str(x).replace(",", "").replace("£", "").strip())
    except ValueError:
        return None


class Result:
    def __init__(self, name):
        self.name, self.problems = name, []

    def fail(self, msg):
        self.problems.append(msg)

    def finish(self, summary):
        for p in self.problems:
            print(f"  - {p}")
        if self.problems:
            print(f"RESULT FAIL {self.name}: {summary}; {len(self.problems)} problem(s)")
            return 1
        print(f"RESULT PASS {self.name}: {summary}")
        return 0

    def cannot(self, why):
        for p in self.problems:
            print(f"  - {p}")
        print(f"RESULT CANNOT RUN {self.name}: {why}")
        return 2
