"""最小可运行 RAG 检索器。

为了零外部依赖，Demo 使用关键词打分；接口刻意设计成可替换，
后续可换 pgvector + embedding + rerank。
"""
from pathlib import Path

POLICY_FILE = Path(__file__).parents[2] / "data" / "hr_policies.md"

def search_policy(query: str, top_k: int = 2) -> list[dict]:
    text = POLICY_FILE.read_text(encoding="utf-8")
    chunks = [x.strip() for x in text.split("## ") if x.strip()]
    terms = [t for t in ["年假", "病假", "婚假", "请假", "审批", "余额"] if t in query]
    scored = []
    for chunk in chunks:
        score = sum(chunk.count(t) for t in terms)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"content": c, "score": s, "source": "data/hr_policies.md"} for s, c in scored[:top_k]]
