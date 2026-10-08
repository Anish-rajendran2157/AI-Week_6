"""The one eval command: answers -> deterministic assertions -> judge -> pass rate by mode -> agreement.

    python -m scripts.run_eval --no-judge        # assertions only (safe before hand-labelling)
    python -m scripts.run_eval --judge v1        # needs committed eval/labels_25.json
    python -m scripts.run_eval                   # latest judge_vN.txt on file
    python -m scripts.run_eval --show-disagreements

Answers are generated once by the live app (prompt hr-rag-v2) into eval/answers.json and then
frozen, because the hand labels are bound to those exact answers. --regenerate re-runs the app
and is refused once labels exist. Judge verdicts are cached per (judge prompt, answers) hash.
"""
import argparse
import asyncio
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv(override=True)

from app.eval.protocol import EVAL_TRACE_PATH
os.environ["TRACE_PATH"] = EVAL_TRACE_PATH  # eval traffic must not pollute the Week-5 trace log

from app.eval import judge as J
from app.eval.assertions import ASSERTIONS, JUDGED_CRITERIA, MOVED_FROM_JUDGE, run_assertions
from app.eval.cases import CASES, CASES_BY_ID, MODES
from app.eval.protocol import (ANSWERS_PATH, LABELS_PATH, RESULTS_DIR, ROOT, file_sha256, label_sample,
                               labels_ready_for_judge, load_json, now, save_json, text_sha256)

WEEK5_TRACES = os.path.join(ROOT, "traces", "traces.jsonl")


def check_regressions():
    from app.tracing.trace_store import read_traces
    traces = {t["trace_id"]: t for t in read_traces(WEEK5_TRACES)}
    bad = [c.cid for c in CASES if c.source_trace and traces.get(c.source_trace, {}).get("query") != c.question]
    if bad:
        raise SystemExit(f"Regression cases not verbatim from their trace: {bad}")
    return sum(1 for c in CASES if c.source_trace)


def generate_answers():
    from app import config
    from app.generation.llm import DEFAULT_MODEL, DEFAULT_PARAMS
    from app.retrieval.chunk_store import chunk_store
    from app.services.rag_service import RAGService

    svc, out = RAGService(), {}
    for i, c in enumerate(CASES, 1):
        for attempt in range(4):
            try:
                res = asyncio.run(svc.answer_query(c.question, qid=c.cid, channel="eval", prompt_version="hr-rag-v2"))
                break
            except Exception as e:
                if attempt == 3:
                    raise
                print(f"  {c.cid} error {e!r}; retrying")
                time.sleep(10 * (attempt + 1))
        ids = [s["chunk_id"] for s in res["sources"]]
        out[c.cid] = {"question": c.question, "answer": res["answer"] or "", "trace_id": res["trace_id"],
                      "finish_reason": res.get("finish_reason"), "chunk_ids": ids,
                      "contexts": [chunk_store.get(i)["text"] for i in ids]}
        print(f"[{i}/{len(CASES)}] {c.cid} {res['trace_id']} finish={res.get('finish_reason')}")
        time.sleep(1.0)
    save_json(ANSWERS_PATH, {"meta": {
        "generated_at": now(), "prompt_version": "hr-rag-v2", "model": DEFAULT_MODEL, "params": DEFAULT_PARAMS,
        "retrieval_mode": config.RETRIEVAL_MODE, "dense_backend": config.DENSE_BACKEND,
        "chunk_store_fingerprint": chunk_store.fingerprint(), "trace_log": "traces/eval_traces.jsonl",
        "n": len(out)}, "answers": out})


def run_judge(version, answers, rejudge):
    proof = labels_ready_for_judge()
    template = J.load_template(version)
    path = os.path.join(RESULTS_DIR, f"judge_{version}.json")
    cached = load_json(path)
    key = {"template_sha256": text_sha256(template), "answers_sha256": file_sha256(ANSWERS_PATH),
           "judge_model": J.JUDGE_MODEL}
    if cached and not rejudge and all(cached.get(k) == v for k, v in key.items()):
        return cached
    print(f"Running judge {version} ({J.JUDGE_MODEL}) on {len(CASES)} answers; labels committed "
          f"{proof['commit'][:7]} at {proof['committed_at']}")
    started = now()
    verdicts = {}
    for c in CASES:
        verdicts[c.cid] = J.judge_one(template, c, answers[c.cid]["answer"])
        print(f"  {c.cid} {verdicts[c.cid]['verdict']}")
        time.sleep(0.5)
    result = {"judge_version": version, **key, "params": J.JUDGE_PARAMS, "run_started_at": started,
              "run_finished_at": now(), "labels_proof": proof, "verdicts": verdicts}
    save_json(path, result)
    return result


def agreement(version, verdicts, labels):
    ids = labels["protocol"]["case_ids"]
    meta = load_json(J.judge_path(version).replace(".txt", ".meta.json")) or {}
    fewshot = set(meta.get("few_shot_case_ids", []))

    def score(subset):
        pairs = [(labels["labels"][i]["label"], verdicts[i]["verdict"]) for i in subset]
        n, agree = len(pairs), sum(h == j for h, j in pairs)
        po = agree / n
        ph = sum(h == "PASS" for h, _ in pairs) / n
        pj = sum(j == "PASS" for _, j in pairs) / n
        pe = ph * pj + (1 - ph) * (1 - pj)
        kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
        return {"n": n, "agree": agree, "pct": round(100 * po, 1), "kappa": round(kappa, 2)}

    conf = {f"judge {j} / human {h}": sum(1 for i in ids if labels["labels"][i]["label"] == h
                                          and verdicts[i]["verdict"] == j)
            for j in ("PASS", "FAIL") for h in ("PASS", "FAIL")}
    errors = [i for i in ids if verdicts[i]["verdict"] == "ERROR"]
    out = {"version": version, "all": score(ids), "confusion": conf, "judge_errors": errors,
           "disagreements": [i for i in ids if labels["labels"][i]["label"] != verdicts[i]["verdict"]],
           "few_shot_case_ids": sorted(fewshot)}
    if fewshot:
        out["held_out"] = score([i for i in ids if i not in fewshot])
    return out


def pct(a, b):
    return f"{a}/{b} {100 * a / b:3.0f}%" if b else "  -   "


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", help="judge prompt version, e.g. v1 (default: latest eval/judge_vN.txt)")
    ap.add_argument("--no-judge", action="store_true", help="assertions only")
    ap.add_argument("--regenerate", action="store_true", help="re-run the app to rebuild eval/answers.json")
    ap.add_argument("--rejudge", action="store_true", help="ignore cached judge verdicts")
    ap.add_argument("--show-disagreements", action="store_true")
    args = ap.parse_args()

    n_reg = check_regressions()
    if args.regenerate or not os.path.exists(ANSWERS_PATH):
        if os.path.exists(LABELS_PATH):
            raise SystemExit("Refusing to regenerate answers: labels_25.json is bound to the current answers.")
        print(f"Generating answers for {len(CASES)} cases with the live app...")
        generate_answers()
    data = load_json(ANSWERS_PATH)
    answers = data["answers"]

    asserts = {c.cid: run_assertions(c, answers[c.cid]["answer"]) for c in CASES}
    version = None if args.no_judge else (args.judge or J.available_versions()[-1])
    judged = run_judge(version, answers, args.rejudge)["verdicts"] if version else None

    L = []
    L.append(f"Week 6 eval | {len(CASES)} cases ({n_reg} regression, replayed verbatim from failed Week-5 traces) | "
             f"answers {data['meta']['prompt_version']} @ {data['meta']['generated_at']}")
    L.append(f"Judge: {version + ' (' + J.JUDGE_MODEL + ')' if version else 'not run (--no-judge)'}")
    L.append(f"Criteria: {len(ASSERTIONS)} deterministic assertions ({len(MOVED_FROM_JUDGE)} moved out of the "
             f"judge) vs {len(JUDGED_CRITERIA)} judged criterion ({', '.join(JUDGED_CRITERIA)})")
    L.append("")
    L.append(f"{'mode':<5} {'failure probed':<34} {'n':>3}  {'assertions':>11}  {'judge':>11}  {'PASS (both)':>11}")
    tot = [0, 0, 0, 0]
    for m, label in MODES.items():
        cs = [c for c in CASES if c.mode == m]
        a = sum(all(ok for ok, _ in asserts[c.cid].values()) for c in cs)
        j = sum(judged[c.cid]["verdict"] == "PASS" for c in cs) if judged else 0
        b = sum(all(ok for ok, _ in asserts[c.cid].values()) and (not judged or judged[c.cid]["verdict"] == "PASS")
                for c in cs)
        tot = [tot[0] + len(cs), tot[1] + a, tot[2] + j, tot[3] + b]
        L.append(f"{m:<5} {label:<34} {len(cs):>3}  {pct(a, len(cs)):>11}  "
                 f"{pct(j, len(cs)) if judged else '-':>11}  {pct(b, len(cs)) if judged else '-':>11}")
    L.append(f"{'ALL':<5} {'(read the mode rows, not this one)':<34} {tot[0]:>3}  {pct(tot[1], tot[0]):>11}  "
             f"{pct(tot[2], tot[0]) if judged else '-':>11}  {pct(tot[3], tot[0]) if judged else '-':>11}")
    L.append("")
    L.append("Per assertion (applies / passes):")
    for name in ASSERTIONS:
        applies = [c.cid for c in CASES if name in asserts[c.cid]]
        passed = sum(asserts[cid][name][0] for cid in applies)
        tag = "moved from judge" if name in MOVED_FROM_JUDGE else "new"
        L.append(f"  {name:<24} {passed:>2}/{len(applies):<2}  [{tag}]")
    L.append("")
    L.append("Failing cases:")
    for c in CASES:
        fails = [f"{n}: {d}" for n, (ok, d) in asserts[c.cid].items() if not ok]
        if judged and judged[c.cid]["verdict"] != "PASS":
            fails.append(f"judge {judged[c.cid]['verdict']}: {judged[c.cid]['reason'][:110]}")
        if fails:
            L.append(f"  {c.cid} {c.mode}  " + "\n            ".join(fails))

    if judged:
        labels = load_json(LABELS_PATH)
        ag = agreement(version, judged, labels)
        all_ag = load_json(os.path.join(RESULTS_DIR, "agreement.json")) or {}
        all_ag[version] = ag
        save_json(os.path.join(RESULTS_DIR, "agreement.json"), all_ag)
        proof = load_json(os.path.join(RESULTS_DIR, f"judge_{version}.json"))["labels_proof"]
        L.append("")
        L.append(f"Judge {version} vs blind hand labels (labels commit {proof['commit'][:7]}, "
                 f"{proof['committed_at']}):")
        L.append(f"  agreement {ag['all']['pct']}% ({ag['all']['agree']}/{ag['all']['n']}), "
                 f"Cohen's kappa {ag['all']['kappa']}")
        if "held_out" in ag:
            L.append(f"  held-out (excluding few-shot cases {', '.join(ag['few_shot_case_ids'])}): "
                     f"{ag['held_out']['pct']}% ({ag['held_out']['agree']}/{ag['held_out']['n']})")
        L.append("  " + ", ".join(f"{k}: {v}" for k, v in ag["confusion"].items()))
        L.append("  disagreements: " + (", ".join(
            f"{i} (human {labels['labels'][i]['label']}, judge {judged[i]['verdict']})"
            for i in ag["disagreements"]) or "none"))
        if "v1" in all_ag and version != "v1":
            a, b = all_ag["v1"], all_ag[version]
            L.append(f"\nagreement_before (v1) -> agreement_after ({version}): {a['all']['pct']}% -> {b['all']['pct']}%"
                     + (f"   [held-out only: {a['all']['pct']}% -> {b['held_out']['pct']}%]" if "held_out" in b else ""))
        if args.show_disagreements:
            for i in ag["disagreements"]:
                c = CASES_BY_ID[i]
                L += ["", "=" * 100, f"{i} [{c.mode}]  human {labels['labels'][i]['label']}  vs  judge "
                      f"{judged[i]['verdict']}", f"Q: {c.question}", f"REFERENCE: {c.reference}",
                      f"ANSWER:\n{answers[i]['answer'].strip()}", f"HUMAN NOTE: {labels['labels'][i].get('note') or '-'}",
                      f"JUDGE REASON: {judged[i]['reason']}"]

    text = "\n".join(L)
    print(text)
    out = os.path.join(RESULTS_DIR, f"eval_table_{version or 'assertions'}.txt")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    open(out, "w", encoding="utf-8").write(text + "\n")
    print(f"\nWrote {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
