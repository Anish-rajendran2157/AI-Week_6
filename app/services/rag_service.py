from typing import Any, Dict, List, Optional

from app import config
from app.generation.llm import generate_with_metadata
from app.generation.prompts import PROMPT_TEMPLATES, PROMPT_VERSION, render_context
from app.retrieval.chunk_store import chunk_store
from app.services.retrieval_service import retrieval_service
from app.tracing.trace_store import new_trace_id, write_trace


class RAGService:
    async def answer_query(self, query: str, mode: Optional[str] = None, **trace_meta) -> Dict[str, Any]:
        initial_k, final_k = 10, 3
        retrieved = retrieval_service.retrieve(query, initial_k=initial_k, final_k=final_k, mode=mode)
        return self.answer_traced(query, retrieved, mode or config.RETRIEVAL_MODE, initial_k, final_k, trace_meta)

    def answer_traced(self, query: str, retrieved: List[Dict[str, Any]], mode: str,
                      initial_k: int, final_k: int, trace_meta: Dict[str, Any]) -> Dict[str, Any]:
        version = trace_meta.get("prompt_version") or PROMPT_VERSION
        context = render_context(version, [r["payload"] for r in retrieved])
        prompt = PROMPT_TEMPLATES[version].format(context=context, question=query)

        gen = generate_with_metadata(prompt)

        sources = []
        for r in retrieved:
            p = r["payload"]
            info = {"policy_id": p.get("policy_id"), "page_id": p.get("page_id"),
                    "title": p.get("title"), "chunk_id": p.get("chunk_id"),
                    "effective_date": p.get("effective_date"), "status": p.get("status"),
                    "region": p.get("region")}
            if info not in sources:
                sources.append(info)

        trace = write_trace({
            "trace_id": new_trace_id(),
            "channel": trace_meta.get("channel", "api"),
            "source_qid": trace_meta.get("qid"),
            "query": query,
            "retrieval": {
                "mode": mode, "initial_k": initial_k, "final_k": final_k, "rrf_k": config.RRF_K,
                "embedding_model": "all-MiniLM-L6-v2",
                "dense_backend": config.DENSE_BACKEND,
                "pinecone_namespace": config.PINECONE_NAMESPACE,
                "chunk_store_fingerprint": chunk_store.fingerprint(),
                "chunks": [{
                    "chunk_id": r["payload"]["chunk_id"],
                    "page_id": r["payload"].get("page_id"),
                    "policy_id": r["payload"].get("policy_id"),
                    "effective_date": r["payload"].get("effective_date"),
                    "status": r["payload"].get("status"),
                    "region": r["payload"].get("region"),
                    "score": round(r["score"], 6),
                    "ranks": r.get("ranks", {}),
                    "retriever_scores": {k: round(float(v), 6) for k, v in r.get("scores", {}).items()},
                } for r in retrieved],
            },
            "prompt": {"version": version, "rendered_prompt": prompt},
            "model": {"provider": "groq", "name": gen["model"], "params": gen["params"],
                      "system_fingerprint": gen.get("system_fingerprint")},
            "output": {"raw": gen["raw"], "reasoning": gen.get("reasoning"),
                       "response_id": gen.get("response_id"), "latency_ms": gen["latency_ms"],
                       "finish_reason": gen["finish_reason"], "usage": gen["usage"]},
        })

        return {"answer": trace["output"]["raw"], "sources": sources, "trace_id": trace["trace_id"],
                "finish_reason": gen["finish_reason"]}
