#!/usr/bin/env python3
"""Run the four QA checks and print one results table and a verdict.

Runs check_quotes, check_numbers, check_trace and check_samples in that order,
prints a table of results, then every problem each check reported, then

  VERDICT: READY FOR SIGN-OFF     (every check passed)
  VERDICT: BLOCKED                (any check failed or could not run)

Usage: run_checks.py [--root DIR]
Exit codes: 0 ready for sign-off, 1 blocked.
"""
import subprocess
import sys
from pathlib import Path

from qa_common import parse_args

CHECKS = ("check_quotes", "check_numbers", "check_trace", "check_samples")
HERE = Path(__file__).resolve().parent


def run(name, root):
    p = subprocess.run([sys.executable, str(HERE / f"{name}.py"), "--root", root], capture_output=True, text=True)
    lines = (p.stdout + p.stderr).rstrip().splitlines()
    last = next((l for l in reversed(lines) if l.startswith("RESULT ")), None)
    if last is None:
        return "CANNOT RUN", f"no RESULT line (exit {p.returncode})", lines
    body = last[len("RESULT "):]
    status = "CANNOT RUN" if body.startswith("CANNOT RUN") else body.split()[0]
    summary = body.split(": ", 1)[1] if ": " in body else body
    details = [l for l in lines if l is not last and l != last]
    return status, summary, details


def main():
    args = parse_args(__doc__)
    results = [(name, *run(name, args.root)) for name in CHECKS]
    print("| Check | Result | Summary |")
    print("|---|---|---|")
    for name, status, summary, _ in results:
        print(f"| {name} | {status} | {summary.replace('|', '/')} |")
    for name, status, _, details in results:
        if status != "PASS":
            print(f"\n{name} ({status}):")
            print("\n".join(details) if details else "  (no detail printed)")
    failed = [name for name, status, _, _ in results if status != "PASS"]
    if failed:
        print(f"\nVERDICT: BLOCKED ({', '.join(failed)})")
        return 1
    print("\nVERDICT: READY FOR SIGN-OFF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
