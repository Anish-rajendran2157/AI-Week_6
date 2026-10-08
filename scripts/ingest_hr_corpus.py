"""Chunk data/corpus/*.md (HR policies) into data/chunks.json, carrying the policy
front-matter (policy_id, effective_date, supersedes, status, region) onto every chunk
so traces record which policy version was served.

    python -m scripts.ingest_hr_corpus
"""
import glob
import os
import re

from dotenv import load_dotenv
load_dotenv(override=True)

from app import config
from app.embeddings.model import embedding_model
from app.ingestion.chunker import recursive_chunk
from app.ingestion.cleaner import clean_text
from app.retrieval.chunk_store import chunk_store

CORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "corpus")
CHUNK_SIZE = 600
CHUNK_OVERLAP = 120
FRONT_MATTER_FIELDS = ("page_id", "policy_id", "effective_date", "supersedes", "status", "region", "page_type")


def parse_front_matter(raw: str) -> dict:
    meta = {}
    for field in FRONT_MATTER_FIELDS:
        m = re.search(rf"^{field}:\s*(.+)$", raw, re.M)
        if m:
            meta[field] = m.group(1).strip()
    return meta


def main():
    all_meta = []
    for path in sorted(glob.glob(os.path.join(CORPUS_DIR, "*.md"))):
        raw = open(path, encoding="utf-8").read()
        front = parse_front_matter(raw)
        if "page_id" not in front:
            print(f"SKIP {os.path.basename(path)}: no page_id in front matter")
            continue
        title = raw.splitlines()[0].lstrip("# ").strip()
        chunks = recursive_chunk(clean_text(raw), chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        for i, text in enumerate(chunks):
            all_meta.append({
                "document_id": front["page_id"],
                "chunk_id": f"{front['page_id']}_chunk_{i}",
                "source": os.path.basename(path),
                "source_type": "file",
                "title": title,
                "text": text,
                **front,
            })
        print(f"{front['page_id']:28s} {front.get('status','?'):11s} {front.get('region','?'):4s} {len(chunks)} chunks")

    chunk_store.replace_all(all_meta)
    print(f"\nWrote {len(all_meta)} chunks to {chunk_store.path}")
    print(f"Chunk store fingerprint: {chunk_store.fingerprint()}")

    if os.environ.get("PINECONE_API_KEY"):
        from app.vectorstore.pinecone_store import pinecone_store
        embeddings = embedding_model.encode([m["text"] for m in all_meta])
        pinecone_store.upsert_chunks(all_meta, embeddings, namespace=config.PINECONE_NAMESPACE)
        print(f"Upserted {len(all_meta)} vectors to Pinecone namespace '{config.PINECONE_NAMESPACE}'")
    else:
        print("PINECONE_API_KEY not set - dense search will use the local index.")


if __name__ == "__main__":
    main()
