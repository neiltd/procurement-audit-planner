"""Shared helpers for the spend analysis: paths, supplier-name normalisation, header detection."""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SPEND_DIR = DATA / "spend"
CONTRACTS_CSV = DATA / "contracts.csv"
RULES_JSON = ROOT / "outputs" / "rules.json"
OUT = ROOT / "outputs"
FULL = OUT / "analytics-full"
SHEET = "Data to publish"

EXPECTED_COLS = ["Service", "Expenditure category", "Narrative", "Date", "Net amount", "Supplier name"]

_SUFFIXES = {"LTD", "LIMITED", "PLC", "LLP"}
_PUNCT = re.compile(r"[^\w\s]|_")
_WS = re.compile(r"\s+")


def normalise_supplier(name) -> str:
    """Uppercase, punctuation -> space, drop whole words LTD/LIMITED/PLC/LLP, collapse whitespace.

    The single normalisation used for both spend suppliers and Contracts Finder suppliers.
    """
    if name is None:
        return ""
    s = str(name)
    if s.lower() == "nan":
        return ""
    s = _PUNCT.sub(" ", s.upper())
    words = [w for w in _WS.split(s) if w and w not in _SUFFIXES]
    return " ".join(words)


def find_header_row(raw_df):
    """Return the 0-based index of the first row containing all EXPECTED_COLS, or None."""
    for i in range(min(len(raw_df), 50)):
        vals = {str(v).strip() for v in raw_df.iloc[i].tolist() if v is not None}
        if all(c in vals for c in EXPECTED_COLS):
            return i
    return None


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gbp(x) -> float:
    return round(float(x), 2)
