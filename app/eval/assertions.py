"""Deterministic assertions: the criteria an `if` and a lookup table check better than a model.

The first four used to be criteria in the judge prompt (eval/judge_v0_multicriteria.txt) and
were deleted from it when they moved here (eval/judge_v1.txt). The fifth is new: it checks a
figure against a list of numbers that exist only in a superseded 2023 file.

Each assertion returns None when it does not apply to the case, else (passed, detail).
"""
import re
from typing import Callable, Dict, List, Optional, Tuple

from app.eval.cases import EvalCase
from app.generation.prompts import REFUSAL_SENTENCE
from app.retrieval.policy_index import policies, resolve_section

Result = Optional[Tuple[bool, str]]

# gpt-oss writes U+2011 non-breaking hyphens ("HR‑LEAVE‑002") and narrow spaces; fold them first.
_DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−"), "-")
_SPACES = dict.fromkeys(map(ord, "    "), " ")

_CITE_RE = re.compile(r"\[\s*(HR-[A-Z]+-\d{3}(?:-[A-Z]{2})?)\b([^\]]*)\]")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_NUMERIC_NOTICE_RE = re.compile(r"\b\d+\s*-?\s*(?:calendar\s+|working\s+)?(?:days?|weeks?|months?)\b", re.I)
_WORDED_NOTICE_RE = re.compile(
    r"\b(?:one|two|three|four|five|six|eight|ten|twelve|thirty|sixty|ninety)\s*-?\s*"
    r"(?:calendar\s+|working\s+)?(?:days?|weeks?|months?)\b", re.I)
_ENTITLEMENT_RE = re.compile(r"\b\d+\s*(?:calendar\s+|working\s+|paid\s+)?(?:days?|weeks?|months?)\b"
                             r"|\b(?:INR|GBP|USD)\s*[\d,]+", re.I)


def normalise(text: str) -> str:
    return (text or "").translate(_DASHES).translate(_SPACES)


def parse_citations(answer: str) -> List[Dict]:
    """[HR-LEAVE-002 §3, effective 2025-04-01] -> {'policy_id', 'sections': ['3'], 'date'}.
    Tolerates several sections in one bracket ('§3, §4') and 'section 3' for '§3'."""
    out = []
    for pid, inner in _CITE_RE.findall(normalise(answer)):
        inner = re.sub(r"\bsec(?:tion)?\.?\s*", "§", inner, flags=re.I)
        sections = [s.strip(" ,;") for s in re.findall(r"§\s*([^,;§\]]+)", inner)]
        sections = [re.sub(r"\s*effective.*$", "", s, flags=re.I).strip() for s in sections]
        date = _DATE_RE.search(inner)
        out.append({"policy_id": pid, "sections": [s for s in sections if s],
                    "date": date.group(0) if date else None})
    return out


def section_ref_resolves(case: EvalCase, answer: str) -> Result:
    """A policy section reference is present, and every cited section exists in the corpus."""
    if not case.cite:
        return None
    cites = parse_citations(answer)
    if not cites:
        return False, "no [POLICY_ID §SECTION, ...] citation"
    bad = []
    for c in cites:
        if c["policy_id"] not in policies():
            bad.append(f"{c['policy_id']} (no such policy)")
        elif not c["sections"]:
            bad.append(f"{c['policy_id']} (no section)")
        else:
            bad += [f"{c['policy_id']} §{s}" for s in c["sections"] if resolve_section(c["policy_id"], s) is None]
    return (not bad), (f"{len(cites)} citation(s) resolve" if not bad else "unresolved: " + ", ".join(bad))


def version_cited_current(case: EvalCase, answer: str) -> Result:
    """Every citation carries the cited policy's own effective date, and the policy is the active
    version (unless the employee asked about the superseded policy by name)."""
    if not case.cite:
        return None
    cites = parse_citations(answer)
    if not cites:
        return False, "no citation, so no version cited"
    bad = []
    for c in cites:
        p = policies().get(c["policy_id"])
        if p is None:
            continue  # reported by section_ref_resolves
        if c["date"] is None:
            bad.append(f"{c['policy_id']} cites no effective date")
        elif c["date"] != p.effective_date:
            bad.append(f"{c['policy_id']} cites {c['date']}, policy is {p.effective_date}")
        elif p.status != "active" and not case.allow_superseded:
            bad.append(f"{c['policy_id']} is {p.status}")
    return (not bad), ("versions cited and current" if not bad else "; ".join(bad))


def notice_figure_numeric(case: EvalCase, answer: str) -> Result:
    """The notice-period figure is stated in digits with a unit ('2 months', '90 days'), never only in words."""
    if not case.notice_numeric:
        return None
    text = normalise(answer)
    numeric = _NUMERIC_NOTICE_RE.findall(text)
    worded = _WORDED_NOTICE_RE.findall(text)
    if worded:
        return False, f"worded figure(s): {worded[:3]}"
    return (bool(numeric)), (f"numeric: {numeric[:3]}" if numeric else "no numeric notice figure")


def refusal_path(case: EvalCase, answer: str) -> Result:
    """An out-of-jurisdiction question gets the refusal sentence and no entitlement figure or citation."""
    if not case.expect_refusal:
        return None
    text = normalise(answer)
    refused = REFUSAL_SENTENCE.lower().rstrip(".") in text.lower().replace("’", "'")
    figures = _ENTITLEMENT_RE.findall(text)
    cites = parse_citations(text)
    if not refused:
        return False, "refusal sentence missing"
    if figures or cites:
        return False, f"refused but still gave figures/citations: {(figures + [c['policy_id'] for c in cites])[:3]}"
    return True, "refusal path taken"


def no_superseded_figure(case: EvalCase, answer: str) -> Result:
    """None of the figures that exist only in the superseded 2023 file appears in the answer."""
    if not case.forbidden:
        return None
    fold = lambda s: re.sub(r"(?<=\d),(?=\d)", "", normalise(s)).lower()
    text = fold(answer)
    hits = [f for f in case.forbidden
            if re.search(r"(?<![\d.])" + re.escape(fold(f)) + r"(?![\d])", text)]
    return (not hits), ("no 2023-only figure" if not hits else f"2023-only figure(s): {hits}")


ASSERTIONS: Dict[str, Callable[[EvalCase, str], Result]] = {
    "section_ref_resolves": section_ref_resolves,
    "version_cited_current": version_cited_current,
    "notice_figure_numeric": notice_figure_numeric,
    "refusal_path": refusal_path,
    "no_superseded_figure": no_superseded_figure,
}

# The judge criteria these replaced (see eval/judge_v0_multicriteria.txt -> eval/judge_v1.txt).
MOVED_FROM_JUDGE = ("section_ref_resolves", "version_cited_current", "notice_figure_numeric", "refusal_path")
JUDGED_CRITERIA = ("policy_correct",)


def run_assertions(case: EvalCase, answer: str) -> Dict[str, Tuple[bool, str]]:
    out = {}
    for name, fn in ASSERTIONS.items():
        r = fn(case, answer or "")
        if r is not None:
            out[name] = r
    return out
