"""Replay one trace FROM THE TRACE ALONE and show the original output beside the replay.

The replay rebuilds the prompt from the trace's chunk_ids + prompt version (never from the
live retriever), so it also proves whether the recorded chunk list is sufficient. It then
re-sends it with the model and params the trace recorded.

    python -m scripts.replay_trace --seed 991 --from-sample analysis/sample_random_424242.md
    python -m scripts.replay_trace --trace-id tr_abc123
"""
import argparse
import difflib
import os
import random
import re

from dotenv import load_dotenv
load_dotenv(override=True)

from app.generation.llm import generate_with_metadata
from app.generation.prompts import PROMPT_TEMPLATES
from app.retrieval.chunk_store import chunk_store
from app.tracing.trace_store import read_traces, sha256

ANALYSIS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analysis")


def rebuild_prompt(trace: dict) -> tuple[str, list[str]]:
    """Reconstruct the prompt from the trace's recorded fields. Returns (prompt, missing)."""
    missing = []
    version = trace.get("prompt", {}).get("version")
    template = PROMPT_TEMPLATES.get(version)
    if template is None:
        missing.append(f"prompt template for version {version!r} not available")
        return "", missing

    texts = []
    for c in trace["retrieval"]["chunks"]:
        stored = chunk_store.get(c["chunk_id"])
        if stored is None:
            missing.append(f"chunk {c['chunk_id']} no longer in the index")
            texts.append("")
        else:
            texts.append(stored["text"])
    context = "\n\n---\n\n".join(texts)
    return template.format(context=context, question=trace["query"]), missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace-id")
    ap.add_argument("--seed", type=int, help="pick one trace at random from the sample/population")
    ap.add_argument("--from-sample", help="restrict the random pick to trace_ids in this sample file")
    ap.add_argument("--runs", type=int, default=3, help="how many times to replay")
    args = ap.parse_args()

    traces = {t["trace_id"]: t for t in read_traces()}
    if args.trace_id:
        tid = args.trace_id
    elif args.seed is not None:
        pool = sorted(traces)
        if args.from_sample:
            in_sample = set(re.findall(r"`(tr_[0-9a-f]+)`", open(args.from_sample, encoding="utf-8").read()))
            pool = [t for t in pool if t in in_sample]
        tid = random.Random(args.seed).choice(pool)
        print(f"Seed {args.seed} over {len(pool)} trace_ids -> {tid}")
    else:
        raise SystemExit("pass --trace-id or --seed")

    trace = traces[tid]
    prompt, missing = rebuild_prompt(trace)
    stored_hash = trace["prompt"].get("sha256")
    rebuilt_hash = sha256(prompt)
    fingerprint_now = chunk_store.fingerprint()

    # Several runs, because one replay cannot tell a reconstruction gap from provider non-determinism.
    runs = [generate_with_metadata(prompt, model=trace["model"]["name"], **trace["model"]["params"])
            for _ in range(args.runs)]
    original = trace["output"]["raw"] or ""
    same = [(r["raw"] or "").strip() == original.strip() for r in runs]

    def meta(finish, usage, fp):
        return f"finish_reason `{finish}`, tokens {usage}, system_fingerprint `{fp}`"

    L = [f"# Replay evidence - `{tid}`", "",
         f"- Question (as stored, post-redaction): {trace['query']}",
         f"- Prompt version: `{trace['prompt']['version']}`",
         f"- Model: `{trace['model']['name']}` params `{trace['model']['params']}`",
         f"- Retrieved chunk_ids + scores: " + ", ".join(
             f"`{c['chunk_id']}`({c['score']})" for c in trace["retrieval"]["chunks"]),
         f"- Chunk store fingerprint: trace `{trace['retrieval'].get('chunk_store_fingerprint')}` vs now `{fingerprint_now}`"
         f" -> {'SAME index' if trace['retrieval'].get('chunk_store_fingerprint') == fingerprint_now else 'INDEX CHANGED'}",
         f"- Prompt sha256: stored `{stored_hash}` vs rebuilt `{rebuilt_hash}`"
         f" -> {'byte-identical' if stored_hash == rebuilt_hash else 'DIFFERS'}",
         f"- Redactions at write time: {trace.get('redactions') or 'none'}"
         + (" -> replay sends the redacted query; the pre-redaction text is never stored, by design"
            if trace.get("redactions") else ""),
         f"- Could not reconstruct: {'; '.join(missing) if missing else 'nothing'}",
         f"- Replays identical to the original: **{sum(same)} of {len(runs)}**", "",
         "## Original output", "",
         "- " + meta(trace["output"].get("finish_reason"), trace["output"].get("usage"),
                     trace["model"].get("system_fingerprint")), "",
         "```", original.strip() or "<empty>", "```", ""]
    for i, (r, ok) in enumerate(zip(runs, same), 1):
        replayed = (r["raw"] or "").strip()
        L += [f"## Replay {i} ({'identical' if ok else 'differs'})", "",
              "- " + meta(r["finish_reason"], r["usage"], r.get("system_fingerprint")), "",
              "```", replayed or "<empty>", "```", ""]
        if not ok and replayed:
            diff = list(difflib.unified_diff(original.strip().splitlines(), replayed.splitlines(),
                                             "original", f"replay {i}", lineterm="", n=1))
            L += ["```diff", *diff[:60], "```", ""]

    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    out = os.path.join(ANALYSIS_DIR, f"replay_{tid}.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[:12]))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
