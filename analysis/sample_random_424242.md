# Seeded random sample of 20 traces

- Population: 90 traces in `traces/traces.jsonl`
- Command: `python -m scripts.sample_traces --seed 424242 --n 20`
- Seed: **424242** (Python `random.Random(seed).sample(sorted(trace_ids), 20)`)

| # | trace_id | source_qid | channel | question |
|---|---|---|---|---|
| 1 | `tr_b1163888dad8` | P025 | portal | Which date of the month is salary credited? |
| 2 | `tr_5bedf7521bc9` | P003 | email | Hi team, I hope you are doing well. I wanted to understand the process for applying for maternity leave, including how much advance notice I should give and what documents are required. I am based in London. Thank you so much for your help. |
| 3 | `tr_70e480dfca88` | P046 | email | Is there any provision for bereavement leave? My grandfather passed away and I need a few days. |
| 4 | `tr_ff64ec880989` | P072 | slack | carry forward limit as per the leave policy 2023? |
| 5 | `tr_bda9238e2c99` | P076 | portal | What is the relocation allowance if I move from Chennai to Austin? |
| 6 | `tr_68e7240fd2bc` | P039 | email | I am relocating my working hours slightly to overlap with the US team. Does that need a formal flexible working request? |
| 7 | `tr_0f87b193b804` | P059 | portal | Kindly confirm the notice period applicable during the probation period. |
| 8 | `tr_7bae0296d4ee` | P029 | email | I got married last month. How do I add my spouse to the medical policy and is there a window for that? |
| 9 | `tr_4ad877f7c45f` | P053 | portal | Is my probation period counted towards gratuity or any service based benefit? |
| 10 | `tr_2d598db33366` | P027 | portal | Does the health insurance cover my parents or only spouse and kids? |
| 11 | `tr_c8c4d8bc166a` | P047 | portal | can i extend maternity leave unpaid after the paid part ends |
| 12 | `tr_872f7b3c3240` | P016 | portal | What are the rating levels used in the performance review and what does a mid rating mean for my increment? |
| 13 | `tr_7e639afc6da6` | P080 | email | I have an offer from another company. How should I approach negotiating a counter offer with my manager? |
| 14 | `tr_8ef8234736af` | P071 | portal | Under the 2023 leave policy my entitlement was different. Which one applies to me now? |
| 15 | `tr_c33486812828` | P045 | portal | Kindly advise the procedure for availing adoption leave. |
| 16 | `tr_abf70e663942` | P087 | portal | Kindly reach me on [PHONE] regarding my notice period query, as I am travelling and may not see email. |
| 17 | `tr_30b5aa50d18e` | P014 | email | Kindly let me know the maximum hotel tariff permissible for a two night client visit to London. |
| 18 | `tr_ac52dcbada67` | P011 | portal | Can I work from home full time if my manager approves it? |
| 19 | `tr_ee4802d0dcde` | P083 | portal | Can HR help with a rental agreement or broker for accommodation near the Chennai office? |
| 20 | `tr_6eb9c787ea49` | P042 | portal | Reimbursement for internet and home office setup, is there a monthly allowance? |
