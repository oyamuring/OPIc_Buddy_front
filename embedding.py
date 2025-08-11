import os
import torch
from pymongo import MongoClient
from transformers import AutoModel, AutoTokenizer
from tqdm import tqdm
from db.db import connect_db  # 기존에 작성된 DB 연결 함수 재사용

# 임베딩 하는 클래스
class E5Embedder:
    def __init__(self, model_path, pooling="mean"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path)
        self.pooling = pooling

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
        if self.pooling == "mean":
            emb = outputs.last_hidden_state.mean(dim=1)
        else:  # cls pooling
            emb = outputs.last_hidden_state[:, 0, :]
        return emb.numpy().tolist()

# 임베딩 클래스를 이용한 임베딩 함수
def embedding_collection(
    input_collection: str,
    output_collection: str,
    model_path: str,
    batch_size: int = 100
):
    src_col = connect_db(input_collection)
    tgt_col = connect_db(output_collection)
    embedder = E5Embedder(model_path)

    # 이미 임베딩된 content 중복 방지
    existing = set(
        doc['content'] for doc in tgt_col.find({}, {'content':1})
    )

    batch = []
    # src 컬렉션의 모든 문서 탐색
    for doc in tqdm(src_col.find(), desc="Embedding docs"):
        category = doc['category']
        topic    = doc['topic']
        for text in doc.get('content', []):
            text = text.strip()
            if not text or text in existing:
                continue
            vec = embedder.encode(text)[0]
            batch.append({
                "category":  category,
                "topic":     topic,
                "content":   text,
                "embedding": vec
            })
            existing.add(text)

            if len(batch) >= batch_size:
                tgt_col.insert_many(batch)
                batch.clear()

    if batch:
        tgt_col.insert_many(batch)

# 임베딩 클래스를 이용한사용자 입력 임베딩 함수
def embedding_user_input(text, model_path):
    embedder = E5Embedder(model_path)
    return embedder.encode(text)[0]


