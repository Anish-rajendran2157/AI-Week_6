"""Redaction applied BEFORE anything is written to the trace file.

Every string that reaches the trace (query, rendered prompt, raw model output) passes
through redact(). Nothing is scrubbed after the fact, because a trace file that was
written raw and cleaned later has already leaked.
"""
import os
import re
from typing import Dict, Tuple

# Model output often uses typographic dashes (U+2011 non-breaking hyphen, en dash, minus)
# where the employee typed "-". A pattern that only knows ASCII "-" let "EMP‑48213" from a
# model answer through in the first traffic run, so every separator accepts all of them.
_DASH = "\\-\u2010-\u2015\u2212\ufe58\ufe63\uff0d"  # for use inside [...]
_SEP = r"[\s." + _DASH + r"]"

# Order matters: email before phone, so the digits inside an address are not eaten first.
PATTERNS = (
    ("employee_id", re.compile(r"\bEMP[_\s" + _DASH + r"]?\d{3,}\b", re.I), "[EMPLOYEE_ID]"),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "[EMAIL]"),
    # Explicit shapes only. A loose "7+ digits with separators" rule also eats dates like
    # 2025-04-01, which would corrupt a replay, so ISO dates are excluded first.
    ("phone", re.compile(
        r"(?<![\w" + _DASH + r"])(?!\d{4}[" + _DASH + r"]\d{2}[" + _DASH + r"]\d{2})("
        r"\+\d{1,3}" + _SEP + r"?\d{2,5}" + _SEP + r"?\d{3,5}" + _SEP + r"?\d{0,5}"  # +91 98765 43210
        r"|\(\d{3}\)\s?\d{3}" + _SEP + r"?\d{4}"                                    # (512) 555-0137
        r"|\d{3}" + _SEP + r"\d{3}" + _SEP + r"\d{4}"                               # 512-555-0137
        r"|\d{3}" + _SEP + r"\d{4}"                                                 # 555-0137
        r"|\d{10}"                                                                  # 9876543210
        r")(?![\w" + _DASH + r"])"), "[PHONE]"),
    ("aadhaar", re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[NATIONAL_ID]"),
    ("ssn", re.compile(r"\b\d{3}[" + _DASH + r"]\d{2}[" + _DASH + r"]\d{4}\b"), "[NATIONAL_ID]"),
)

# Names cannot be caught by a regex. A roster file (one name per line) is the only
# honest way to redact them; without it, first names in free text survive. This is a
# known gap, recorded in analysis/notes.md rather than hidden.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROSTER_PATH = os.environ.get("NAME_ROSTER_PATH", "")
if _ROSTER_PATH and not os.path.isabs(_ROSTER_PATH):
    _ROSTER_PATH = os.path.join(_PROJECT_ROOT, _ROSTER_PATH)


def _roster_pattern():
    if not _ROSTER_PATH:
        return None
    if not os.path.exists(_ROSTER_PATH):
        # A configured roster that cannot be found would let every name through silently.
        raise FileNotFoundError(f"NAME_ROSTER_PATH is set but {_ROSTER_PATH} does not exist")
    names = [n.strip() for n in open(_ROSTER_PATH, encoding="utf-8") if n.strip()]
    if not names:
        return None
    return re.compile(r"\b(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")\b", re.I)


def redact(text: str) -> Tuple[str, Dict[str, int]]:
    """Return (redacted_text, {kind: count})."""
    if not text:
        return text, {}
    found: Dict[str, int] = {}
    for kind, pattern, placeholder in PATTERNS:
        text, n = pattern.subn(placeholder, text)
        if n:
            found[kind] = found.get(kind, 0) + n
    roster = _roster_pattern()
    if roster is not None:
        text, n = roster.subn("[NAME]", text)
        if n:
            found["name"] = n
    return text, found
