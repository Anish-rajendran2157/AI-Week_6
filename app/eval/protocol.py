"""Blind-labelling protocol: file locations, the seeded label sample, and git ordering checks.

The order is enforced in code, not left to discipline:
  answers.json committed -> labels_25.json committed -> judge v1 run -> prediction.txt committed -> judge v2
- label_answers refuses to start once any judge result exists.
- run_eval refuses to call the judge until labels_25.json is complete, committed and unmodified,
  and bound (by sha256) to the exact answers file being judged.
- make_judge_v2 refuses until prediction.txt is committed.
Each judge result records the labels commit it was checked against, so the order is provable.
"""
import hashlib
import json
import os
import random
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.eval.cases import CASES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
EVAL_DIR = os.path.join(ROOT, "eval")
ANSWERS_PATH = os.path.join(EVAL_DIR, "answers.json")
LABELS_PATH = os.path.join(EVAL_DIR, "labels_25.json")
PREDICTION_PATH = os.path.join(EVAL_DIR, "prediction.txt")
RESULTS_DIR = os.path.join(EVAL_DIR, "results")
EVAL_TRACE_PATH = os.path.join(ROOT, "traces", "eval_traces.jsonl")

LABEL_SEED = 606   # Week 6; fixed before any answer was generated
LABEL_N = 25

CRITERION = ("POLICY-CORRECT: could an HR People Ops partner send this answer to this employee unchanged? "
             "Judge against the reference. FAIL on any wrong or unsupported figure/deadline/rule/approver, "
             "another office's policy applied without naming it or asking, an added reassurance or reason, a "
             "refusal when the reference has an answer, no next step when the topic is not covered, or an "
             "empty/cut-off answer. Ignore tone, length and citation format.")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def file_sha256(path: str) -> str:
    # CRLF-insensitive: git normalises line endings, and a checkout must not break the label binding.
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def label_sample() -> List[str]:
    """The 25 case ids that get hand labels: seeded, over every case id, sorted for display."""
    ids = sorted(c.cid for c in CASES)
    return sorted(random.Random(LABEL_SEED).sample(ids, LABEL_N))


def load_json(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def commit_of(path: str) -> Optional[Dict[str, str]]:
    """Last commit touching `path`, or None if never committed. 'dirty' if the working copy differs."""
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    line = _git("log", "-1", "--format=%H|%cI|%s", "--", rel)
    if not line:
        return None
    sha, when, subject = line.split("|", 2)
    dirty = bool(_git("status", "--porcelain", "--", rel))
    return {"commit": sha, "committed_at": when, "subject": subject, "dirty": dirty}


def judge_results_exist() -> List[str]:
    if not os.path.isdir(RESULTS_DIR):
        return []
    return sorted(f for f in os.listdir(RESULTS_DIR) if f.startswith("judge_") and f.endswith(".json"))


def labels_ready_for_judge() -> Dict:
    """Raises SystemExit with the reason if the judge may not run yet; returns the proof otherwise."""
    labels = load_json(LABELS_PATH)
    if labels is None:
        raise SystemExit("No eval/labels_25.json. Hand-label first: python -m scripts.label_answers")
    missing = [cid for cid in labels["protocol"]["case_ids"] if cid not in labels["labels"]]
    if missing:
        raise SystemExit(f"labels_25.json is incomplete ({len(missing)} unlabelled). Finish labelling first.")
    proof = commit_of(LABELS_PATH)
    if proof is None or proof["dirty"]:
        raise SystemExit("labels_25.json must be committed, unmodified, before the judge runs:\n"
                         "  git add eval/labels_25.json && git commit -m \"Blind hand labels (before judge)\"")
    if labels["protocol"]["answers_sha256"] != file_sha256(ANSWERS_PATH):
        raise SystemExit("labels_25.json was made against a different answers.json; the labels no longer apply.")
    return {**proof, "labels_sha256": file_sha256(LABELS_PATH)}
