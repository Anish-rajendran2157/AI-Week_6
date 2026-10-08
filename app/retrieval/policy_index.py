"""Section index of the HR corpus, parsed from the policy markdown files themselves.

Two users:
- the hr-rag-v2 prompt labels every extract with its policy ID, effective date and the sections
  it spans, so the assistant has something real to cite;
- the eval assertions check that a cited (policy ID, section) pair exists and that the cited
  effective date is the policy's own. Built from the files, not the chunks, so a citation is
  checked against the actual document.
"""
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional

CORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "corpus")

_META_RE = re.compile(r"^(page_id|policy_id|effective_date|supersedes|status|region|page_type): (.+)$", re.M)
_HEADING_RE = re.compile(r"^## (?:(\d+)\.\s+)?(.+?)\s*$")


@dataclass
class Section:
    number: Optional[str]   # "3" for "## 3. Entitlement"; None for unnumbered handbook/FAQ headings
    title: str
    start: int              # offsets into Policy.text (whitespace-normalised, like chunk text)
    end: int = 0

    @property
    def ref(self) -> str:
        return self.number if self.number else self.title


@dataclass
class Policy:
    policy_id: str
    page_id: str
    title: str
    effective_date: str
    status: str
    region: str
    supersedes: str
    text: str
    sections: List[Section] = field(default_factory=list)


def _norm(s: str) -> str:
    return " ".join(s.split())


def _parse(path: str) -> Policy:
    raw = open(path, encoding="utf-8").read()
    meta = dict(_META_RE.findall(raw))
    tokens: List[str] = []
    sections: List[Section] = []
    for line in raw.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            start = len(" ".join(tokens)) + (1 if tokens else 0)
            sections.append(Section(number=m.group(1), title=m.group(2), start=start))
        tokens.extend(line.split())
    text = " ".join(tokens)
    for i, s in enumerate(sections):
        s.end = sections[i + 1].start if i + 1 < len(sections) else len(text)
    title = raw.splitlines()[0].lstrip("# ").strip()
    return Policy(policy_id=meta["policy_id"], page_id=meta["page_id"], title=title,
                  effective_date=meta["effective_date"], status=meta["status"], region=meta["region"],
                  supersedes=meta.get("supersedes", "none"), text=text, sections=sections)


@lru_cache(maxsize=1)
def policies() -> Dict[str, Policy]:
    out = {}
    for name in sorted(os.listdir(CORPUS_DIR)):
        if name.endswith(".md"):
            p = _parse(os.path.join(CORPUS_DIR, name))
            out[p.policy_id] = p
    return out


def by_page_id(page_id: str) -> Optional[Policy]:
    return next((p for p in policies().values() if p.page_id == page_id), None)


def _clean_title(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def resolve_section(policy_id: str, ref: str) -> Optional[Section]:
    """'3', '3.', '3.1', '3 Entitlement' resolve by number; 'Health insurance' resolves by title."""
    policy = policies().get(policy_id)
    if policy is None:
        return None
    ref = ref.strip().rstrip(".").strip()
    num = re.match(r"^(\d+)", ref)
    if num:
        return next((s for s in policy.sections if s.number == num.group(1)), None)
    want = _clean_title(ref)
    if not want:
        return None
    return next((s for s in policy.sections if _clean_title(s.title) == want
                 or _clean_title(s.title).startswith(want)), None)


def sections_for_chunk(page_id: str, chunk_text: str) -> List[Section]:
    """Sections a chunk overlaps, found by locating the chunk in its source file."""
    policy = by_page_id(page_id)
    if policy is None:
        return []
    text = _norm(chunk_text)
    start = policy.text.find(text[:80])
    if start < 0:
        return []
    end = start + len(text)
    return [s for s in policy.sections if s.start < end and s.end > start]
