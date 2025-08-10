import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from db.db import connect_db
from embedding import embedding_user_input

def retrieve_top_k(
    query: str,
    model_path: str,
    collection_name: str = "embedded_opic_samples",
    k: int = 1,
    text_field: str = "content",
    emb_field: str = "embedding",
    category: str | None = None,          # 선택 필터
    topic: str | None = None              # 선택 필터
) -> list[str]:
    col = connect_db(collection_name)

    q = {}
    if category: q["category"] = category
    if topic:    q["topic"]    = topic

    raw = list(col.find(q, {text_field: 1, emb_field: 1, "_id": 0}))
    docs = [d for d in raw if text_field in d and emb_field in d and d[emb_field]]
    if not docs:
        return []

    lines = [d[text_field] for d in docs]
    embeddings = np.asarray([d[emb_field] for d in docs], dtype=np.float32)

    q_emb = np.asarray(embedding_user_input(query, model_path), dtype=np.float32).reshape(1, -1)
    if embeddings.shape[1] != q_emb.shape[1]:
        raise ValueError(f"Dim mismatch: DB {embeddings.shape[1]} vs query {q_emb.shape[1]}")

    sims = cosine_similarity(q_emb, embeddings)[0]
    k = min(k, len(lines))
    idx = np.argpartition(sims, -k)[-k:]
    idx = idx[np.argsort(sims[idx])[::-1]]
    return [lines[i] for i in idx]
