# Replay evidence - `tr_5bedf7521bc9`

- Question (as stored, post-redaction): Hi team, I hope you are doing well. I wanted to understand the process for applying for maternity leave, including how much advance notice I should give and what documents are required. I am based in London. Thank you so much for your help.
- Prompt version: `hr-rag-v1`
- Model: `openai/gpt-oss-20b` params `{'temperature': 0.0, 'max_tokens': 700, 'top_p': 1.0, 'seed': 7}`
- Retrieved chunk_ids + scores: `parental-leave-in-2023_chunk_0`(0.03125), `parental-leave-uk-2025_chunk_0`(0.030415), `parental-leave-in-2023_chunk_1`(0.016393)
- Chunk store fingerprint: trace `80-780c5a69d018` vs now `80-780c5a69d018` -> SAME index
- Prompt sha256: stored `f4bcffe464c24040` vs rebuilt `f4bcffe464c24040` -> byte-identical
- Redactions at write time: none
- Could not reconstruct: nothing
- Replays identical to the original: **2 of 3**

## Original output

- finish_reason `stop`, tokens {'prompt_tokens': 632, 'completion_tokens': 252}, system_fingerprint `fp_75c733514d`

```
You should give **10 weeks’ notice** to your manager before the expected start of your maternity leave.  
To be eligible, you must have worked **80 days in the 12 months preceding the expected date of birth**.

I cannot answer this based on the provided documents.
```

## Replay 1 (identical)

- finish_reason `stop`, tokens {'prompt_tokens': 632, 'completion_tokens': 252}, system_fingerprint `fp_f8aab374e8`

```
You should give **10 weeks’ notice** to your manager before the expected start of your maternity leave.  
To be eligible, you must have worked **80 days in the 12 months preceding the expected date of birth**.

I cannot answer this based on the provided documents.
```

## Replay 2 (identical)

- finish_reason `stop`, tokens {'prompt_tokens': 632, 'completion_tokens': 252}, system_fingerprint `fp_63473661d7`

```
You should give **10 weeks’ notice** to your manager before the expected start of your maternity leave.  
To be eligible, you must have worked **80 days in the 12 months preceding the expected date of birth**.

I cannot answer this based on the provided documents.
```

## Replay 3 (differs)

- finish_reason `length`, tokens {'prompt_tokens': 632, 'completion_tokens': 700}, system_fingerprint `fp_4f7e7dc26e`

```
<empty>
```

