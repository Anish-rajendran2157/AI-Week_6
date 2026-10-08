"""Draw a seeded random sample of traces for hand-coding.

The seed and the exact selection are printed and written to analysis/, so the sample is
provable and anyone can redraw it. Sampling is over ALL traces on file, not over a
curated list.

    python -m scripts.sample_traces --seed 424242 --n 20
    python -m scripts.sample_traces --demo --n 10        # bonus: the curated demo set
"""
import argparse
import os
import random

from app.tracing.trace_store import read_traces

ANALYSIS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analysis")
DEMO_QIDS = None  # set lazily from app.eval.demo_set


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--demo", action="store_true", help="sample from the curated demo questions instead")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    traces = read_traces()
    label = "random"
    if args.demo:
        from app.eval.demo_set import DEMO_QIDS as demo
        traces = [t for t in traces if t.get("source_qid") in demo]
        label = "demo"

    ids = sorted(t["trace_id"] for t in traces)
    if len(ids) < args.n:
        raise SystemExit(f"only {len(ids)} traces available, need {args.n}")
    picked = random.Random(args.seed).sample(ids, args.n)
    by_id = {t["trace_id"]: t for t in traces}

    lines = [f"# Seeded {label} sample of {args.n} traces", "",
             f"- Population: {len(ids)} traces in `traces/traces.jsonl`",
             f"- Command: `python -m scripts.sample_traces --seed {args.seed} --n {args.n}"
             f"{' --demo' if args.demo else ''}`",
             f"- Seed: **{args.seed}** (Python `random.Random(seed).sample(sorted(trace_ids), {args.n})`)", "",
             "| # | trace_id | source_qid | channel | question |", "|---|---|---|---|---|"]
    for i, tid in enumerate(picked, 1):
        t = by_id[tid]
        q = t["query"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {i} | `{tid}` | {t.get('source_qid')} | {t.get('channel')} | {q} |")

    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    out = args.out or os.path.join(ANALYSIS_DIR, f"sample_{label}_{args.seed}.md")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
