# Week 5 notes: Task Set C (HR policy)

Northwind Systems HR assistant, prompt `hr-rag-v1`, model `openai/gpt-oss-20b` on Groq, hybrid BM25 + dense
retrieval (RRF, top 3), chunk store `80-780c5a69d018` (14 policy files, 80 chunks). Written 2026-10-08.

## 1. Seeded random sample

- Population: all **90** traces in `traces/traces.jsonl` (commit `ea23b79`, one per question in the traffic pool).
- Seed: **424242**, written in the README before any traffic existed.
- Command: `python -m scripts.sample_traces --seed 424242 --n 20`
- Rule: `random.Random(424242).sample(sorted(trace_ids), 20)`. Anyone can re-run it and get the same 20.
- Full list with questions: [sample_random_424242.md](sample_random_424242.md)

| # | trace_id | qid | # | trace_id | qid |
|---|---|---|---|---|---|
| 1 | `tr_b1163888dad8` | P025 | 11 | `tr_c8c4d8bc166a` | P047 |
| 2 | `tr_5bedf7521bc9` | P003 | 12 | `tr_872f7b3c3240` | P016 |
| 3 | `tr_70e480dfca88` | P046 | 13 | `tr_7e639afc6da6` | P080 |
| 4 | `tr_ff64ec880989` | P072 | 14 | `tr_8ef8234736af` | P071 |
| 5 | `tr_bda9238e2c99` | P076 | 15 | `tr_c33486812828` | P045 |
| 6 | `tr_68e7240fd2bc` | P039 | 16 | `tr_abf70e663942` | P087 |
| 7 | `tr_0f87b193b804` | P059 | 17 | `tr_30b5aa50d18e` | P014 |
| 8 | `tr_7bae0296d4ee` | P029 | 18 | `tr_ac52dcbada67` | P011 |
| 9 | `tr_4ad877f7c45f` | P053 | 19 | `tr_ee4802d0dcde` | P083 |
| 10 | `tr_2d598db33366` | P027 | 20 | `tr_6eb9c787ea49` | P042 |

## 2. Replay evidence

Trace picked by seed **991** from the 20 sampled ids:
`python -m scripts.replay_trace --seed 991 --from-sample analysis/sample_random_424242.md` gave `tr_5bedf7521bc9`.
Full file: [replay_tr_5bedf7521bc9.md](replay_tr_5bedf7521bc9.md).

- The prompt was rebuilt from the trace alone: the `hr-rag-v1` template, plus the text of the 3 recorded chunk_ids
  looked up in the chunk store, plus the stored query. It was never re-retrieved.
- Prompt sha256: stored `f4bcffe464c24040`, rebuilt `f4bcffe464c24040`, so it is **byte-identical**. Chunk store
  fingerprint is the same as at trace time.
- Model and params replayed from the trace: `openai/gpt-oss-20b`, `temperature 0.0, max_tokens 700, top_p 1.0, seed 7`.

| Run | finish_reason | completion tokens | Groq system_fingerprint | Output |
|---|---|---|---|---|
| Original | stop | 252 | `fp_75c733514d` | (below) |
| Replay 1 | stop | 252 | `fp_f8aab374e8` | identical, word for word |
| Replay 2 | stop | 252 | `fp_63473661d7` | identical, word for word |
| Replay 3 | length | 700 | `fp_4f7e7dc26e` | empty: all 700 tokens went to hidden reasoning |

Original output, and Replays 1 and 2:

```
You should give **10 weeks' notice** to your manager before the expected start of your maternity leave.
To be eligible, you must have worked **80 days in the 12 months preceding the expected date of birth**.

I cannot answer this based on the provided documents.
```

My first replay attempt (single run, before I added `--runs`) also came back empty. That makes 2 of 4 replays
identical and 2 of 4 empty, never a *different* answer.

**Fields I had to add** (added before any traffic was generated, commit `5659a6e`):
- the gpt-oss reasoning text (it comes back separately from the answer and was being dropped; it is redacted too)
- Groq `system_fingerprint` and response id
- `rrf_k` and each retriever's own score per chunk

Prompt version, chunk_ids + scores, model + params and raw output were already recorded.

**What I could not reconstruct:**
- Which Groq backend serves a call: every call landed on a different `system_fingerprint`, and `seed` does not
  pin it. So a trace reproduces the *prompt* exactly but cannot guarantee the *output*.
- `reasoning_effort` is left at the provider default and is not recorded.
- The pre-redaction query, by design. For traces with redactions, the replay sends the redacted text, so the model
  sees something slightly different from what it originally saw.

## 3. Redaction

**Confirmed: employee identifiers are redacted inside `write_trace()` before a line is appended, never after.**
A scan of the committed `traces/traces.jsonl` finds 0 occurrences of the employee ID, either first name, any email
or the phone number, in any dash form. The 7 traces that contained identifiers carry redaction counts.

How that was reached, for the record:
- Names cannot be caught by a pattern. I added a roster (`NAME_ROSTER_PATH`, kept out of git) and made a missing
  roster an error instead of a silent pass.
- The first traffic run still leaked one ID. In P085 the model's *answer* echoed it back as `EMP‑48213` with a U+2011
  non-breaking hyphen, which the pattern did not know.
- That file was deleted uncommitted and never sampled. The pattern now accepts Unicode dashes (commit `1a2131e`),
  and all 90 traces were regenerated, rather than scrubbing the old file after the fact.

## 4. Open coding: one sentence per trace, written before any clustering

Zero code changes during this step. Coding started after commit `47cb842`. No file outside `analysis/` differs
between that commit and the commit that adds this section (`git diff --stat 47cb842 HEAD -- . ':!analysis'` is
empty).

| # | trace_id | What I saw |
|---|---|---|
| 1 | `tr_b1163888dad8` | Gave the salary credit date for all three offices in a table (Chennai last working day; London 28th or prior working day; Austin 15th and last working day), and every date matches the handbook payroll table. |
| 2 | `tr_5bedf7521bc9` | A London employee was told to give "10 weeks' notice" and to have "80 days worked in the preceding 12 months" (both numbers are in the superseded 2023 India policy chunk, while the UK procedure says notify by the 15th week before the expected week of childbirth), and the answer then ends with a bare "I cannot answer this based on the provided documents" that contradicts the lines above it; the stored reasoning shows the model believed the India table was the UK one. |
| 3 | `tr_70e480dfca88` | An employee whose grandfather had died received only the fixed sentence "I cannot answer this based on the provided documents" (there is no bereavement policy in the corpus), with no acknowledgement and no pointer to People Ops. |
| 4 | `tr_ff64ec880989` | Asked for the 2023 policy's carry-forward limit, it answered "10 days" and attributed that to the 2023 Annual Leave Policy, but the only "10 days" in context was the FAQ's figure; the 2023 table (5 / 7 / 7 / 0 days by grade band) was not among the retrieved chunks. |
| 5 | `tr_bda9238e2c99` | A retrieved chunk names the Relocation Policy as the place transfers are handled, but the assistant gave only the fixed refusal sentence and did not tell the employee that a Relocation Policy exists or whom to ask (the policy itself is not in the corpus). |
| 6 | `tr_68e7240fd2bc` | Refused outright, although two retrieved chunks say core hours are 11:00 to 16:00 local and one gives the 14:00 to 17:00 UK window for cross-office meetings, which is exactly the constraint on shifting hours; it is true that the corpus has no "flexible working request" process. |
| 7 | `tr_0f87b193b804` | No office was given; the context held the full UK probation-notice table (1 / 2 / 4 weeks by grade) and an India chunk saying a request without an office cannot be answered from that file, and the assistant refused without asking which office or offering the per-office figures. |
| 8 | `tr_7bae0296d4ee` | Quoted the 30-day mid-year-addition rule correctly, then told an employee married "last month" that they "still have time", which the policy cannot confirm since last month may already be more than 30 days ago, and said "notify HR" where the handbook names no recipient and no enrolment steps. |
| 9 | `tr_4ad877f7c45f` | Refused; I could find nothing in any corpus file on whether probation counts toward gratuity or service, so the refusal matches the documents, but it does not suggest who could answer. |
| 10 | `tr_2d598db33366` | Correct per-office answer (parents covered only in Chennai; spouse and children in London and Austin) matching the handbook table, though it left out that London and Austin family cover is opt-in. |
| 11 | `tr_c8c4d8bc166a` | No office was given; it answered "Yes ... up to 26 weeks of unpaid maternity leave (52 total)", which is the UK table, without naming London or asking, and rewrote the UK column "statutory or unpaid" as "unpaid"; for a Chennai employee the 2025 India policy only allows an extension against unused annual leave. |
| 12 | `tr_872f7b3c3240` | Reproduced the five-level rating table and the 1.0x multiplier for rating 3 exactly as the handbook states; reading "mid rating" as rating 3 is the assistant's own interpretation and a reasonable one. |
| 13 | `tr_7e639afc6da6` | An out-of-scope request for counter-offer negotiation advice got the fixed refusal sentence and nothing else. |
| 14 | `tr_8ef8234736af` | Asked which leave policy applies now given a different 2023 entitlement, it answered about the India Parental Leave Policy (2025 supersedes 2023, Chennai payroll) and never mentioned the Annual Leave Policy, even though the annual-leave-2023 chunk in context says it covers leave years only up to FY2024-25. |
| 15 | `tr_c33486812828` | No office was given; the answer is the UK procedure (notify by "the 15th week before the expected week of childbirth", provide MATB1 or the matching certificate) presented as the company procedure with no mention of London, although the US adoption entitlement was also in context and the India procedure differs (4 weeks' notice, Form PL-IN). |
| 16 | `tr_abf70e663942` | The employee asked to be phoned about a notice-period query without stating the question; the assistant gave the fixed refusal and did not say that it cannot call or that someone would follow up (the phone number is redacted in the trace, as expected). |
| 17 | `tr_30b5aa50d18e` | Correct: GBP 190 per night for London and GBP 380 for two nights, matching the handbook travel table. |
| 18 | `tr_ac52dcbada67` | Answered "No", which is the right conclusion, but justified it with the FAQ's ad-hoc work-from-home rule ("a few days in a month") instead of the 2025 fully-remote rule (function head plus People Ops partner approval, not permitted for several role families), which was not among the retrieved chunks. |
| 19 | `tr_ee4802d0dcde` | An out-of-scope request for help finding accommodation near the Chennai office got the fixed refusal sentence and no pointer to anyone who might help. |
| 20 | `tr_6eb9c787ea49` | Blended the active 2025 and superseded 2023 home-office tables: it presented the 2023 internet figure (INR 1,000 / GBP 15 / USD 20) as the current rate for fully-remote staff and gave both setup amounts "depending on the policy version" without saying the 2025 one applies; the 2023 chunk's text itself carries no date or status. |

## 5. Seen outside the sample (not counted in the taxonomy)

- 4 of 90 traces stopped at `max_tokens` (P013, P050, P061, P066); 3 of them returned an **empty** answer. None
  fall in the random sample. P013 is a demo-set question (see bonus).
- A superseded 2023 chunk was in the top 3 for 33 of 90 traces (37%), and for 9 of the 20 sampled (45%).
- The fixed refusal sentence appears in 42 of 90 answers (47%), and in 9 of the 20 sampled.

## 6. Clustering: which trace went where

Each trace was clustered only after all 20 sentences were written. Counts in [taxonomy.md](taxonomy.md) use one main
mode per trace.

| Mode | Traces (sample #) | Count |
|---|---|---|
| 1. Superseded 2023 figure, or a 2023 label on a current figure | 2, 4, 20 | 3 |
| 2. Answers for an office or policy the employee never named | 11, 14, 15 | 3 |
| 3. Right headline plus a reassurance or reason the policy lacks | 8, 18 | 2 |
| 4. Dead-end fixed refusal, topic not in the policies | 3, 5, 9, 13, 16, 19 | 6 |
| 5. Refuses although the retrieved extracts held an answer | 6, 7 | 2 |
| No failure seen | 1, 10, 12, 17 | 4 |

Borderline calls, so a reviewer can disagree with them:
- **#9 and #13 sit in mode 4** even though refusing was correct there, because the employee still gets no next step.
- **#10 counts as no failure** despite leaving out "opt-in".
- **#14 sits in mode 2** because it chose the policy (parental) and the payroll (India) for the employee.

## 7. Dated prediction

Full text: [prediction.md](prediction.md). Committed **2026-10-08 16:08 +0530**, before any fix.

- **Commit:** `0720955` (`07209555cd158ccec3e32e838c6f843246746e8a`)
- **Mode attacked:** rank 1, the superseded 2023 policy (3/20, 15%).
- **Change:** both retrievers restricted to `status == active`.
- **Prediction:** on the same 20 questions, mode 1 falls to **at most 1/20 (5%)**, and superseded chunks in the top 3
  fall from **33/90 to 0/90**.
- **Side effects:** mode 2 ends at **3–4/20** and mode 5 at **2–3/20**. A result outside either range also counts
  as the prediction being wrong.

## 8. Why a public benchmark would not have surfaced the top 3 modes

Our top mode, quoting the superseded 2023 policy, exists only because our corpus holds two dated versions of the
same Northwind policy with different numbers, and a public benchmark ships one static corpus with one gold answer
per question, so it has no way to reward or punish picking the wrong version. Mode 2 appears only when the right
answer depends on a fact about the asker that the question leaves out (which office they work in), but benchmark
questions are written to be self-contained and unambiguous, so "can i extend maternity leave unpaid" with no
office is never asked. Mode 3 would actually score as correct on a benchmark, because an answer like
`tr_7bae0296d4ee` contains the gold fact ("within 30 days of the event"), and the harm (telling an employee married
"last month" that they still have time) is visible only to someone who reads the whole answer against the asker's
situation, which no leaderboard number does.

## 9. Bonus: the curated demo set

Command: `python -m scripts.sample_traces --seed 424242 --n 10 --demo`. The demo set is exactly 10 questions, so
this is all of them, in seeded order: [sample_demo_424242.md](sample_demo_424242.md). P025 is in both samples (the
same trace, `tr_b1163888dad8`).

| # | trace_id | qid | What I saw |
|---|---|---|---|
| D1 | `tr_d966c9963b5b` | P013 | The employee got an empty reply: the model used all 700 completion tokens without producing an answer (finish_reason `length`); the handbook has meal limits per day (INR 1,800 / GBP 40 / USD 65) but no "per diem" line and nothing on keeping receipts. |
| D2 | `tr_491c13f5026d` | P028 | Correct: INR 500,000 for Chennai, and it said plainly that the London and Austin rows name a scheme rather than a sum insured. |
| D3 | `tr_83204d56a1ec` | P037 | Correct: public holidays are published separately per office, from the 2025 annual leave chunk; it did not add that they are published in January. |
| D4 | `tr_d7a7be7d3784` | P015 | Restated the review year (1 April to 31 March, ratings in April, increments 1 June) correctly but named no year, leaving "next" for the employee to work out. |
| D5 | `tr_7b46d2a896a9` | P001 | Correct 2025 figures for Chennai (22 / 25 / 28 days by grade band) from the active policy; the fixed-term row (12) was left out. |
| D6 | `tr_4501bda36226` | P024 | Correct: payroll portal, or the emailed password-protected PDF with the password format, as in the handbook. |
| D7 | `tr_13f8d5cfec57` | P007 | No office was given; it presented the India resignation procedure (Workday, buy-out amount, no-dues clearance) as the company procedure without naming India, although the UK procedure (written notice to the reporting manager) was also in context. |
| D8 | `tr_140c09ac3efc` | P030 | Correct: the full referral bonus table, eligibility rule and tax note, all as in the handbook. |
| D9 | `tr_ee49a8e02089` | P005 | Correct: no note needed for 2 days in any office, with the per-office self-certification table from the 2025 sick leave policy. |
| D10 | `tr_b1163888dad8` | P025 | Same trace as random #1: correct salary dates for all three offices. |

**Top mode, random sample vs demo set:**

| Measure | Random sample (n=20) | Demo set (n=10) |
|---|---|---|
| Rank 1 mode: superseded 2023 policy | **15% (3/20)** | **0% (0/10)** |
| Most frequent mode: dead-end refusal | 30% (6/20) | 0% (0/10) |
| Any legal-exposure mode (1 to 3) | 40% (8/20) | 10% (1/10, D7) |
| No failure seen | 20% (4/20) | 80% (8/10) |

**What the team has been telling itself.** For the last month, the People Ops review has watched ten questions
that each name an office or touch a topic with only one policy version. All ten are answerable from a single table
and have looked good before. In this run, 8 of 10 came back clean, none quoted a 2023 figure and none was refused.
The story the team has been telling itself is that the assistant reads policy tables accurately and that "it
sometimes quotes the wrong policy" is an anecdote. On a random draw of the same week's traffic, 15% of answers lean
on the superseded 2023 policy, 40% carry a failure with legal exposure, and 30% end in a dead-end refusal. Real
employees do not name their office, they ask about leave and remote work, where two policy versions exist, and they
ask about things the policies do not cover at all. The demo set is not dishonest; it is selected, and it measures
the slice of traffic that was never at risk. Even so it was not spotless: P013 came back empty, and P007 gave the
India resignation procedure to someone who never said they were in India.
