import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from db.db import connect_db
from embedding import embedding_user_input  # 기존에 만든 함수 재사용

def retrieve_top_k(query: str,
                   model_path: str,
                   collection_name: str = "embedded_scripts",
                   k: int = 3) -> list[str]:
    """
    1) embedding_user_input으로 query 임베딩
    2) embedded_scripts 컬렉션에서 저장된 embedding들과
       코사인 유사도를 계산해
    3) 상위 k개 line을 반환합니다.
    """

    # 1) DB에서 미리 임베딩된 문서 로드
    col = connect_db(collection_name)
    docs = list(col.find({}, {"line": 1, "embedding": 1}))
    if not docs:
        return []

    lines = [d["line"] for d in docs]
    embeddings = np.array([d["embedding"] for d in docs])  # (N, D)

    # 2) query 임베딩 (기존 embedding_user_input 재사용)
    query_emb = embedding_user_input(query, model_path)     # list of floats
    query_emb = np.array(query_emb).reshape(1, -1)          # (1, D)

    # 3) 코사인 유사도 및 top-k 추출
    sims = cosine_similarity(query_emb, embeddings)[0]      # (N, )
    idx_topk = np.argsort(sims)[::-1][:k]
    return [lines[i] for i in idx_topk]
