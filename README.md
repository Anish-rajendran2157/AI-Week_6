# Week 6 — Validate the policy-answer judge (Task Set C, HR policy)

The Week 6 eval: 31 mode-tagged cases, 5 deterministic assertions, 1 judged criterion, and the
judge checked against blind hand labels. Everything lives in [eval/](eval/) and
[app/eval/](app/eval/).

| Piece | File |
|---|---|
| 31 cases, one Week-5 mode each (M1 to M5), 9 regression cases verbatim from failed Week-5 traces | [app/eval/cases.py](app/eval/cases.py) |
| Assertions: 4 moved out of the judge + 1 new | [app/eval/assertions.py](app/eval/assertions.py) |
| Judge before the split (5 criteria) | [eval/judge_v0_multicriteria.txt](eval/judge_v0_multicriteria.txt) |
| Judge v1: one binary criterion, POLICY-CORRECT | [eval/judge_v1.txt](eval/judge_v1.txt) |
| Judge v2: v1 + 2 of v1's own disagreements as few-shot | `eval/judge_v2.txt` (built by `scripts/make_judge_v2.py`) |
| Frozen answers being graded (prompt `hr-rag-v2`) | `eval/answers.json` |
| Blind hand labels (seeded 25 of 31) | `eval/labels_25.json` |

**Assertions vs judge: 5 assertions, 1 judged criterion.** These moved from the judge prompt into
code: `section_ref_resolves` (the citation is present and resolves to a real section),
`version_cited_current` (the handbook version is cited and is the active one),
`notice_figure_numeric`, and `refusal_path` (out-of-jurisdiction questions). One assertion is new:
`no_superseded_figure`, a lookup against figures that exist only in the 2023 files.

### Protocol (each step is enforced in code, and the commits prove the order)

```bash
python -m scripts.run_eval --no-judge          # 1. generate + freeze answers, assertions only
git add eval/answers.json traces/eval_traces.jsonl && git commit -m "Freeze eval answers"
python -m scripts.label_answers                # 2. blind labels: refuses if any judge result exists
git add eval/labels_25.json && git commit -m "Blind hand labels (before judge)"
python -m scripts.run_eval --judge v1          # 3. refuses unless the labels are committed and unmodified
python -m scripts.run_eval --judge v1 --show-disagreements
# 4. write eval/prediction.txt (one sentence) and commit it
python -m scripts.make_judge_v2 --examples C?? C?? --why "..." --why "..."   # refuses until prediction is committed
python -m scripts.run_eval --judge v2          # 5. prints agreement_before -> agreement_after
```

Each judge result in `eval/results/judge_vN.json` records the labels commit it was checked
against. Agreement for v2 is also reported on the 23 held-out cases, since the 2 few-shot cases
are now inside the prompt.

# Week 5 — Error Analysis: Reading Traces Like a Professional (Task Set C, HR policy)

Extends the Week 4 RAG app with a trace log, swaps the corpus to HR policy, and adds the
sampling / replay tooling the hand-coding step needs.

## Workflow

```bash
pip install -r requirements.txt

# 1. index the HR corpus (14 policy files -> 78 chunks, Pinecone namespace week5-hr)
python -m scripts.ingest_hr_corpus

# 2. generate a week of traffic (90 questions -> traces/traces.jsonl). Resumable.
python -m scripts.generate_traces

# 3. draw the provable sample (paste the seed in the write-up)
python -m scripts.sample_traces --seed 424242 --n 20

# 4. replay one sampled trace from the trace alone
python -m scripts.replay_trace --seed 991 --from-sample analysis/sample_random_424242.md

# bonus: the curated demo set
python -m scripts.sample_traces --seed 424242 --n 10 --demo
```

Then hand-code all 20 into `analysis/notes.md` and cluster into `analysis/taxonomy.md`.
**No code changes during coding** — that zero is graded.

## What a trace holds

One JSON object per line in `traces/traces.jsonl`, with everything a replay needs:
`trace_id`, timestamp, channel, redacted query, prompt version + exact rendered prompt +
its sha256, retrieved `chunk_id`s with scores and fusion ranks (plus each chunk's
`policy_id`, `effective_date`, `status`, `region`), chunk-store fingerprint, model name
and params, and the raw output with latency and token usage.

`scripts/replay_trace.py` rebuilds the prompt from the recorded `chunk_id`s and prompt
version — never from the live retriever — so a sha256 match proves the trace alone was
sufficient, and the fingerprint comparison catches reindexing.

## Redaction

Identifiers are redacted in [app/tracing/redaction.py](app/tracing/redaction.py) **before
the line is written**, never cleaned up afterwards. Covered: employee IDs (`EMP-48213`),
emails, phone numbers in several formats, and national ID shapes. ISO dates and policy IDs
are deliberately preserved, since mangling them would corrupt a replay.

**Known gap:** a bare first name in free text cannot be caught by a pattern. Set
`NAME_ROSTER_PATH` to a file of names (one per line) to redact those too. Without a
roster, first names survive — recorded here rather than hidden.

## Corpus

14 HR policy files for the fictional Northwind Systems, deliberately built with the
messiness that makes RAG fail in diagnosable ways: 3 superseded/replacement pairs with
different numbers (2023 vs 2025), region-specific variants (IN/UK/US) for notice period,
probation and parental leave, an FAQ and a handbook extract that overlap and contradict
the policy files, numbers that appear only in table rows, and a Relocation Policy
referenced by 4 files that does not exist in the corpus.

The prompt (`hr-rag-v1`) says nothing about effective dates, superseded policies or
regions. Finding out what that costs is this week's job; fixing it is next week's.
