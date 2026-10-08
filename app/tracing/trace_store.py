"""Append-only JSONL trace log.

One JSON object per line, one line per request. A trace holds everything needed to
replay the request without the original caller: prompt version + the exact rendered
prompt, retrieved chunk_ids with scores, model name + params, and the raw output.
"""
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from app.tracing.redaction import redact

TRACE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "traces")
TRACE_PATH = os.environ.get("TRACE_PATH", os.path.join(TRACE_DIR, "traces.jsonl"))

TRACE_SCHEMA_VERSION = "1.0"


def new_trace_id() -> str:
    return f"tr_{uuid.uuid4().hex[:12]}"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def write_trace(record: Dict[str, Any], path: str = TRACE_PATH) -> Dict[str, Any]:
    """Redact every free-text field, then append one line. Returns the stored record."""
    redactions: Dict[str, int] = {}

    def scrub(text):
        if not isinstance(text, str):
            return text
        clean, found = redact(text)
        for k, v in found.items():
            redactions[k] = redactions.get(k, 0) + v
        return clean

    record["query"] = scrub(record.get("query"))
    if "prompt" in record:
        record["prompt"]["rendered_prompt"] = scrub(record["prompt"].get("rendered_prompt", ""))
        record["prompt"]["sha256"] = sha256(record["prompt"]["rendered_prompt"])
    if "output" in record:
        record["output"]["raw"] = scrub(record["output"].get("raw", ""))
        record["output"]["reasoning"] = scrub(record["output"].get("reasoning"))

    record["redactions"] = redactions
    record["trace_schema_version"] = TRACE_SCHEMA_VERSION
    record.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def read_traces(path: str = TRACE_PATH):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
