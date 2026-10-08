# Prediction for Week 6 (written and committed 2026-10-08, before any fix)

**Mode attacked:** rank 1, *Quotes a figure from the superseded 2023 policy as current, or puts the 2023 label on
a current figure*. It is currently **3 of 20 (15%)**: traces `tr_5bedf7521bc9`, `tr_ff64ec880989` and
`tr_6eb9c787ea49`.

**The one change:** restrict both retrievers to chunks whose `status` is `active`.
- Dense side: a Pinecone metadata filter `{"status": {"$eq": "active"}}`.
- BM25 side: score active chunks only.
- Effect: the three superseded files (`annual-leave-2023`, `parental-leave-in-2023`, `remote-working-2023`) can
  never reach the prompt.
- Everything else stays the same: prompt `hr-rag-v1`, `openai/gpt-oss-20b` with the same params, initial_k 10,
  final_k 3, RRF k 60, chunk store `80-780c5a69d018`.

**How it will be measured:** re-run the same 20 sampled questions (P025 P003 P046 P072 P076 P039 P059 P029 P053
P027 P047 P016 P080 P071 P045 P087 P014 P011 P083 P042). Then open-code the new traces with the same rules and
count by the same mode definitions.

**Predicted numbers:**

1. **Mode 1 drops from 3/20 (15%) to at most 1/20 (5%).** The one I expect to survive is P072, which names "the
   leave policy 2023" itself. With the 2023 table filtered out, the FAQ's "10 days" is still in context, and I
   expect the model may again call it the 2023 limit.
2. **Superseded chunks in the top 3 drop from 33/90 (37%) to 0/90** when the full pool of 90 is re-run.
3. **Side effects:**
   - Mode 2 (answers for an office the employee never named) ends at **3 or 4 of 20, not lower**. P003 (London
     maternity) may move from mode 1 into mode 2 if India 2025 chunks take the place of the India 2023 ones.
   - Mode 5 (refuses although the answer was retrieved) ends at **2 or 3 of 20**.

**I will count this prediction as wrong if:**
- mode 1 is 2 or more of the 20, or
- any re-run answer contains a figure that exists only in a 2023 file, or
- mode 2 or mode 5 moves outside the ranges above.
