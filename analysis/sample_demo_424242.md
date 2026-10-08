# Seeded demo sample of 10 traces

- Population: 10 traces in `traces/traces.jsonl`
- Command: `python -m scripts.sample_traces --seed 424242 --n 10 --demo`
- Seed: **424242** (Python `random.Random(seed).sample(sorted(trace_ids), 10)`)

| # | trace_id | source_qid | channel | question |
|---|---|---|---|---|
| 1 | `tr_d966c9963b5b` | P013 | portal | What is the per diem for domestic travel and do I need to keep meal receipts? |
| 2 | `tr_491c13f5026d` | P028 | slack | health insurance sum insured amount? |
| 3 | `tr_83204d56a1ec` | P037 | portal | Do public holidays differ between the Chennai, London and Austin offices or is there one common list? |
| 4 | `tr_d7a7be7d3784` | P015 | slack | when is the next performance review cycle |
| 5 | `tr_7b46d2a896a9` | P001 | portal | How many earned leave days do I get per year in the Chennai office? |
| 6 | `tr_4501bda36226` | P024 | slack | payslip not showing for last month, where do i download it |
| 7 | `tr_13f8d5cfec57` | P007 | email | I am planning to resign next month. What is the correct resignation process and who do I submit the letter to? |
| 8 | `tr_140c09ac3efc` | P030 | slack | how much is the referral bonus |
| 9 | `tr_ee49a8e02089` | P005 | slack | Do I need a doctors note for 2 days of sick leave? |
| 10 | `tr_b1163888dad8` | P025 | portal | Which date of the month is salary credited? |
