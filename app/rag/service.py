"""Stable RAG service boundary used by the Tool layer."""
from pathlib import Path
from app import config
from app.rag.chunking import chunk_markdown
from app.rag.postgres import PgVectorPolicyStore

POLICY = Path(__file__).parents[2] / "data" / "hr_policies.md"

def keyword_search(query, top_k=5):
    text = POLICY.read_text(encoding="utf-8")
    chunks = chunk_markdown("hr_policies", text)
    terms = [x for x in query if x.strip()]
    scored = []
    for chunk in chunks:
        score = sum(chunk.content.count(t) + chunk.title.count(t) for t in terms)
        if score:
            scored.append({
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "title": chunk.title,
                "content": chunk.content,
                "score": score,
                "source": "data/hr_policies.md",
                "sources": ["keyword_local"],
            })
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]

def search_policy(query, top_k=None):
    # Agent/Tool code does not change when retrieval backend changes.
    k = top_k or config.RAG_TOP_K
    if config.RAG_BACKEND == "keyword":
        return keyword_search(query, k)
    if config.RAG_BACKEND == "pgvector":
        return PgVectorPolicyStore().search(query, k)
    raise ValueError(f"Unsupported RAG_BACKEND={config.RAG_BACKEND}")
