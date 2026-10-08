import os
import time
from typing import Any, Dict

from groq import Groq

try:
    client = Groq()
except Exception:
    client = None

DEFAULT_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-20b")
# Pinned so a replayed trace is comparable to the original.
DEFAULT_PARAMS = {"temperature": 0.0, "max_tokens": 700, "top_p": 1.0, "seed": 7}


def generate_response(prompt: str, model: str = DEFAULT_MODEL, **overrides) -> str:
    return generate_with_metadata(prompt, model, **overrides)["raw"]


def generate_with_metadata(prompt: str, model: str = DEFAULT_MODEL, **overrides) -> Dict[str, Any]:
    """Returns the raw text plus the model params and usage a trace needs to be replayable."""
    params = {**DEFAULT_PARAMS, **overrides}
    if not client:
        return {"raw": "Groq client is not initialized. Please set GROQ_API_KEY environment variable.",
                "model": model, "params": params, "latency_ms": 0, "finish_reason": "no_client", "usage": {}}

    started = time.perf_counter()
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        **params,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    choice = completion.choices[0]
    usage = getattr(completion, "usage", None)
    return {
        "raw": choice.message.content,
        # gpt-oss returns its reasoning separately from the answer; keep it for diagnosis.
        "reasoning": getattr(choice.message, "reasoning", None),
        "response_id": getattr(completion, "id", None),
        "system_fingerprint": getattr(completion, "system_fingerprint", None),
        "model": model,
        "params": params,
        "latency_ms": latency_ms,
        "finish_reason": getattr(choice, "finish_reason", None),
        "usage": {"prompt_tokens": getattr(usage, "prompt_tokens", None),
                  "completion_tokens": getattr(usage, "completion_tokens", None)} if usage else {},
    }
