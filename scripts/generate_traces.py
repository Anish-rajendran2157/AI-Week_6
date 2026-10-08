"""Replay the question pool through the HR assistant to build a realistic trace log.

This is the "week of traffic" step. It is NOT an evaluation: nothing here knows the right
answer, and no question is labelled. Resumable - questions already traced are skipped.

    python -m scripts.generate_traces
    python -m scripts.generate_traces --limit 10
"""
import argparse
import random
import time

from dotenv import load_dotenv
load_dotenv(override=True)

from app.eval.question_pool import QUESTION_POOL
from app.services.rag_service import RAGService
from app.tracing.trace_store import TRACE_PATH, read_traces

TRAFFIC_SEED = 20251007  # order traffic arrives in; recorded for reproducibility


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--sleep", type=float, default=1.0, help="pause between calls (Groq rate limits)")
    args = ap.parse_args()

    done = {t.get("source_qid") for t in read_traces()}
    pool = list(QUESTION_POOL)
    random.Random(TRAFFIC_SEED).shuffle(pool)
    todo = [q for q in pool if q.qid not in done]
    if args.limit:
        todo = todo[:args.limit]

    print(f"{len(done)} already traced, {len(todo)} to go -> {TRACE_PATH}")
    svc = RAGService()
    import asyncio

    for i, q in enumerate(todo, 1):
        for attempt in range(4):
            try:
                res = asyncio.run(svc.answer_query(q.question, qid=q.qid, channel=q.channel))
                print(f"[{i}/{len(todo)}] {q.qid} {res['trace_id']} :: {q.question[:60]}")
                break
            except Exception as e:
                wait = 10 * (attempt + 1)
                print(f"[{i}/{len(todo)}] {q.qid} error ({e!r}); retrying in {wait}s")
                if attempt == 3:
                    print(f"   giving up on {q.qid}")
                else:
                    time.sleep(wait)
        time.sleep(args.sleep)

    print(f"\nTotal traces on file: {len(read_traces())}")


if __name__ == "__main__":
    main()
