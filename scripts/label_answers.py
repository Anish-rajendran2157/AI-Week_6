"""Blind hand-labelling of 25 frozen answers on the judge's single binary criterion.

Shows only: the question, the reference (current policy) and the assistant's answer. It never
shows the case's mode tag, the assertion results or any judge output, and it refuses to start
once a judge result exists. Saves after every label, so it can be stopped and resumed.

    python -m scripts.label_answers
    python -m scripts.label_answers --review      # print your labels, change nothing

When it finishes, commit the file BEFORE running the judge:
    git add eval/labels_25.json && git commit -m "Blind hand labels (before judge)"
"""
import argparse
import subprocess
import sys
import textwrap

from app.eval.cases import CASES_BY_ID
from app.eval.protocol import (ANSWERS_PATH, CRITERION, LABEL_N, LABEL_SEED, LABELS_PATH, commit_of,
                               file_sha256, judge_results_exist, label_sample, load_json, now, save_json)


def wrap(text, indent="    "):
    return "\n".join(textwrap.fill(p, 100, initial_indent=indent, subsequent_indent=indent) if p.strip() else ""
                     for p in text.splitlines())


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", action="store_true")
    args = ap.parse_args()

    labels = load_json(LABELS_PATH)
    if args.review:
        if not labels:
            raise SystemExit("no labels yet")
        for cid in labels["protocol"]["case_ids"]:
            l = labels["labels"].get(cid)
            print(f"{cid}  {l['label'] if l else '----'}  {(l or {}).get('note', '')}")
        return

    if judge_results_exist():
        raise SystemExit(f"Judge results already exist ({judge_results_exist()}). Labels made now would not be "
                         "blind. Labelling must happen before any judge run.")
    if load_json(ANSWERS_PATH) is None:
        raise SystemExit("No eval/answers.json yet: python -m scripts.run_eval --no-judge")
    answers_proof = commit_of(ANSWERS_PATH)
    if answers_proof is None or answers_proof["dirty"]:
        raise SystemExit("Commit eval/answers.json first, so the labels are bound to a fixed set of answers.")
    proof = commit_of(LABELS_PATH)
    if proof is not None and not proof["dirty"] and labels and len(labels["labels"]) == LABEL_N:
        raise SystemExit(f"labels_25.json is complete and committed ({proof['commit'][:7]}). Not relabelling.")

    answers = load_json(ANSWERS_PATH)["answers"]
    ids = label_sample()
    if labels is None:
        labeller = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
        labels = {"protocol": {
            "criterion": CRITERION, "labeller": labeller, "blind": True,
            "shown_to_labeller": ["question", "reference", "answer"],
            "hidden_from_labeller": ["mode tag", "assertion results", "judge prompt output"],
            "sample": f"random.Random({LABEL_SEED}).sample(sorted(case_ids), {LABEL_N})",
            "case_ids": ids, "answers_file": "eval/answers.json", "answers_sha256": file_sha256(ANSWERS_PATH),
            "answers_commit": answers_proof["commit"], "started_at": now(), "completed_at": None},
            "labels": {}}
        save_json(LABELS_PATH, labels)

    print("CRITERION\n" + wrap(CRITERION) + "\n")
    print("Keys: p = PASS, f = FAIL, q = save and quit. A one-line note is asked after each label.\n")
    todo = [cid for cid in ids if cid not in labels["labels"]]
    for k, cid in enumerate(todo, len(ids) - len(todo) + 1):
        case, ans = CASES_BY_ID[cid], answers[cid]["answer"].strip() or "<empty answer>"
        print("=" * 104)
        print(f"[{k}/{len(ids)}] {cid}\n")
        print("QUESTION\n" + wrap(case.question) + "\n")
        print("REFERENCE (current policy)\n" + wrap(case.reference) + "\n")
        print("ASSISTANT ANSWER\n" + wrap(ans) + "\n")
        while True:
            key = input("PASS or FAIL? [p/f/q] ").strip().lower()
            if key in ("p", "f", "q"):
                break
        if key == "q":
            print(f"Saved {len(labels['labels'])}/{len(ids)}. Re-run to continue.")
            return
        note = input("why (one line, used if this becomes a few-shot example): ").strip()
        labels["labels"][cid] = {"label": "PASS" if key == "p" else "FAIL", "note": note, "labelled_at": now()}
        save_json(LABELS_PATH, labels)

    labels["protocol"]["completed_at"] = now()
    save_json(LABELS_PATH, labels)
    n_pass = sum(l["label"] == "PASS" for l in labels["labels"].values())
    print(f"\nDone: {len(ids)} labels ({n_pass} PASS, {len(ids) - n_pass} FAIL) -> eval/labels_25.json")
    print('Now, BEFORE any judge run:\n  git add eval/labels_25.json && git commit -m "Blind hand labels (before judge)"')


if __name__ == "__main__":
    main()
