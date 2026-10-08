"""LLM judge for the single binary criterion POLICY-CORRECT.

The prompt lives in eval/judge_vN.txt so each version is a file that can be diffed. A different
model family from the assistant (gpt-oss-20b) so the judge is not grading its own style.
"""
import json
import os
import re
import time
from typing import Dict

from app.eval.cases import EvalCase
from app.eval.protocol import EVAL_DIR, text_sha256
from app.generation.llm import client

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "qwen/qwen3.8-27b")
JUDGE_PARAMS = {"temperature": 0.0, "max_tokens": 2000, "top_p": 1.0, "seed": 7}


def judge_path(version: str) -> str:
    return os.path.join(EVAL_DIR, f"judge_{version}.txt")


def available_versions():
    names = [f[len("judge_"):-4] for f in os.listdir(EVAL_DIR) if re.fullmatch(r"judge_v\d+\.txt", f)]
    return sorted(names, key=lambda v: int(v[1:]))


def load_template(version: str) -> str:
    with open(judge_path(version), encoding="utf-8") as f:
        return f.read()


def render(template: str, case: EvalCase, answer: str) -> str:
    # str.replace, not str.format: the template carries a literal JSON example with braces.
    return (template.replace("{question}", case.question)
                    .replace("{reference}", case.reference)
                    .replace("{answer}", (answer or "").strip() or "<empty answer>"))


def _parse(raw: str) -> Dict[str, str]:
    try:
        obj = json.loads(raw)
        verdict = str(obj.get("verdict", "")).strip().upper()
        if verdict in ("PASS", "FAIL"):
            return {"verdict": verdict, "reason": str(obj.get("reason", "")).strip()}
    except (json.JSONDecodeError, AttributeError):
        pass
    m = re.search(r"\b(PASS|FAIL)\b", raw or "")
    return {"verdict": m.group(1) if m else "ERROR", "reason": (raw or "").strip()[:300]}


def judge_one(template: str, case: EvalCase, answer: str) -> Dict[str, str]:
    if client is None:
        raise SystemExit("Groq client not initialised; set GROQ_API_KEY.")
    prompt = render(template, case, answer)
    for attempt in range(5):
        try:
            completion = client.chat.completions.create(
                model=JUDGE_MODEL, messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}, **JUDGE_PARAMS)
            raw = completion.choices[0].message.content or ""
            return {**_parse(raw), "raw": raw, "prompt_sha256": text_sha256(prompt)[:16]}
        except Exception as e:  # rate limits on the free tier
            if attempt == 4:
                return {"verdict": "ERROR", "reason": repr(e), "raw": "", "prompt_sha256": text_sha256(prompt)[:16]}
            time.sleep(8 * (attempt + 1))
