"""Build eval/judge_v2.txt from judge_v1.txt plus 2 of judge v1's OWN disagreements as few-shot examples.

    python -m scripts.make_judge_v2 --examples C05 C17
    python -m scripts.make_judge_v2 --examples C05 C17 --why "..." --why "..."

Refuses unless eval/prediction.txt is committed (the prediction must predate the iteration) and
unless every example is a case where judge v1 disagreed with the hand label. The verdict shown in
each example is the HUMAN label; labels are never edited. The chosen ids go into
judge_v2.meta.json so run_eval can also report agreement on the held-out cases.
"""
import argparse
import os
import sys

from app.eval.cases import CASES_BY_ID
from app.eval.judge import judge_path, load_template
from app.eval.protocol import LABELS_PATH, PREDICTION_PATH, RESULTS_DIR, commit_of, load_json, now, save_json

ANCHOR = "Employee question:\n{question}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--examples", nargs=2, required=True, metavar="CID")
    ap.add_argument("--why", action="append", default=[], help="reason per example (default: your label note)")
    args = ap.parse_args()

    proof = commit_of(PREDICTION_PATH)
    if proof is None or proof["dirty"]:
        raise SystemExit("Write eval/prediction.txt and commit it before iterating the judge.")
    v1 = load_json(os.path.join(RESULTS_DIR, "judge_v1.json"))
    if v1 is None:
        raise SystemExit("Run judge v1 first: python -m scripts.run_eval --judge v1")
    labels = load_json(LABELS_PATH)["labels"]
    for cid in args.examples:
        if cid not in labels or labels[cid]["label"] == v1["verdicts"][cid]["verdict"]:
            raise SystemExit(f"{cid} is not a judge-v1 disagreement; few-shot examples must be the judge's own misses.")

    answers = load_json(os.path.join(os.path.dirname(LABELS_PATH), "answers.json"))["answers"]
    blocks = []
    for k, cid in enumerate(args.examples):
        why = (args.why[k] if k < len(args.why) else "") or labels[cid].get("note", "")
        if not why:
            raise SystemExit(f"No reason for {cid}: pass --why or add a note when labelling.")
        c = CASES_BY_ID[cid]
        blocks.append(
            f"Example {k + 1}\n"
            f"Employee question:\n{c.question}\n\n"
            f"Reference answer (current policy):\n{c.reference}\n\n"
            f"Assistant answer:\n{answers[cid]['answer'].strip() or '<empty answer>'}\n\n"
            f"Correct output: {{\"reason\": \"{why}\", \"verdict\": \"{labels[cid]['label']}\"}}")

    template = load_template("v1")
    if ANCHOR not in template:
        raise SystemExit("judge_v1.txt no longer has the 'Employee question:' anchor")
    shots = ("Worked examples. A previous version of this grader got both of these wrong; the verdict shown is "
             "the correct one.\n\n" + "\n\n---\n\n".join(blocks) + "\n\n---\n\nNow grade this answer.\n\n")
    open(judge_path("v2"), "w", encoding="utf-8").write(template.replace(ANCHOR, shots + ANCHOR, 1))
    save_json(judge_path("v2").replace(".txt", ".meta.json"), {
        "built_from": "judge_v1.txt", "few_shot_case_ids": args.examples, "built_at": now(),
        "prediction_commit": proof["commit"],
        "v1_verdicts_on_examples": {cid: v1["verdicts"][cid]["verdict"] for cid in args.examples},
        "human_labels_on_examples": {cid: labels[cid]["label"] for cid in args.examples}})
    print(f"Wrote eval/judge_v2.txt with few-shot {args.examples} (prediction commit {proof['commit'][:7]}).")
    print("Next: python -m scripts.run_eval --judge v2")


if __name__ == "__main__":
    main()
