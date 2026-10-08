"""Prompt templates. PROMPT_VERSION is written into every trace so a trace can be
replayed against the template that produced it.

v1 is deliberately plain: it says nothing about effective dates, superseded policies or
regions. Week 5 reads traces to find out what that costs; it is not fixed this week.
"""

import os

from app.retrieval.policy_index import by_page_id, sections_for_chunk

# v2 (Week 6) adds citations and the out-of-jurisdiction refusal path, which the eval checks with
# deterministic assertions. It still says nothing about superseded versions or ambiguous offices:
# those failure modes are left in so the eval and the judge have something real to catch.
PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "hr-rag-v2")

REFUSAL_SENTENCE = "I cannot answer this based on the provided documents."

HR_RAG_PROMPT_TEMPLATE = """You are the Northwind Systems HR assistant. Answer the employee's question using only the policy extracts provided below.
If the answer is not contained in the extracts, say "I cannot answer this based on the provided documents."

Policy extracts:
{context}

Question:
{question}

Answer:
"""

HR_RAG_PROMPT_TEMPLATE_V2 = """You are the Northwind Systems HR assistant. Answer the employee's question using only the policy extracts provided below.

Northwind policies cover employees on three payrolls only: India (Chennai office), United Kingdom (London office) and United States (Austin office). If the employee says they are on any other payroll or based in any other country's office, do not answer from these policies; reply with exactly: "I cannot answer this based on the provided documents."

Cite every policy statement you make in this exact form: [POLICY_ID §SECTION, effective YYYY-MM-DD], using the policy ID, a section listed in that extract's header, and the effective date in that header. For example: [HR-LEAVE-002 §3, effective 2025-04-01].

If the answer is not contained in the extracts, say "I cannot answer this based on the provided documents."

Policy extracts:
{context}

Question:
{question}

Answer:
"""

# Kept under its old name so existing callers and the API keep working.
RAG_PROMPT_TEMPLATE = HR_RAG_PROMPT_TEMPLATE

PROMPT_TEMPLATES = {"hr-rag-v1": HR_RAG_PROMPT_TEMPLATE, "hr-rag-v2": HR_RAG_PROMPT_TEMPLATE_V2}


def render_context(version: str, chunks: list) -> str:
    """chunks: chunk-store records (payloads). v1 joins raw text; v2 heads each extract with the
    policy ID, effective date, region and sections it spans, so it can be cited."""
    if version == "hr-rag-v1":
        return "\n\n---\n\n".join(c.get("text", "") for c in chunks)
    parts = []
    for i, c in enumerate(chunks, 1):
        policy = by_page_id(c.get("page_id", ""))
        secs = "; ".join(f"§{s.ref}" + (f" {s.title}" if s.number else "")
                         for s in sections_for_chunk(c.get("page_id", ""), c.get("text", "")))
        head = (f"[Extract {i}] {c.get('policy_id')} | {policy.title if policy else c.get('title')} | "
                f"effective {c.get('effective_date')} | region {c.get('region')} | sections: {secs or 'unknown'}")
        parts.append(f"{head}\n{c.get('text', '')}")
    return "\n\n---\n\n".join(parts)

QUESTION_GENERATION_PROMPT = """
You are a helpful assistant. Based on the following retrieved document chunks, generate 4 to 5 highly relevant questions that can be answered using *only* this context.
Output the questions as a list, one per line. Do not include answers, numbering is fine, but no extra conversational text.

Context:
{context}

Questions:
"""
