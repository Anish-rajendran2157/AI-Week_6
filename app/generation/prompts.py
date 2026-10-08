"""Prompt templates. PROMPT_VERSION is written into every trace so a trace can be
replayed against the template that produced it.

v1 is deliberately plain: it says nothing about effective dates, superseded policies or
regions. Week 5 reads traces to find out what that costs; it is not fixed this week.
"""

PROMPT_VERSION = "hr-rag-v1"

HR_RAG_PROMPT_TEMPLATE = """You are the Northwind Systems HR assistant. Answer the employee's question using only the policy extracts provided below.
If the answer is not contained in the extracts, say "I cannot answer this based on the provided documents."

Policy extracts:
{context}

Question:
{question}

Answer:
"""

# Kept under its old name so existing callers and the API keep working.
RAG_PROMPT_TEMPLATE = HR_RAG_PROMPT_TEMPLATE

PROMPT_TEMPLATES = {"hr-rag-v1": HR_RAG_PROMPT_TEMPLATE}

QUESTION_GENERATION_PROMPT = """
You are a helpful assistant. Based on the following retrieved document chunks, generate 4 to 5 highly relevant questions that can be answered using *only* this context.
Output the questions as a list, one per line. Do not include answers, numbering is fine, but no extra conversational text.

Context:
{context}

Questions:
"""
