from pymongo import MongoClient
import os
import json


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON_PATH = os.path.join(BASE_DIR, "data", "seed_contexts.json")
API_KEY = "mongodb+srv://hakliml22:Lifegoeson%211@cluster0.1ryjiuy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

MONGO_URI = os.getenv(
    "MONGO_URI",
    API_KEY
)

DB_NAME = "OPIcBuddy"

def connect_db(collection_name):
    try:
        client = MongoClient(MONGO_URI)
        client.server_info()  # 연결 확인
        db = client[DB_NAME]
        collection = db[collection_name]
        print(f"MongoDB 연결 성공 (컬렉션: {collection_name})")
        return collection
    except Exception as e:
        print(f"MongoDB 연결 실패: {e.__class__.__name__} - {e}")
        return None

def upload_contents(json_path, collection_name, overwrite=True, uri=None):
    col = connect_db(collection_name)
    if col is None:
        return

    # 1. JSON 로드
    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    # 2. 리스트 형태로 변환
    docs = []
    for category, topics in raw.items():           # survey / role_play
        for topic, prompts in topics.items():      # e.g. "Housing", ["Tell me ..."]
            docs.append({
                "category": category,              # "survey" 또는 "role_play"
                "topic": topic,                    # "Housing", "School" 등
                "content": prompts                 # 질문 리스트
            })

    # 3. 덮어쓰기 옵션
    if overwrite:
        col.delete_many({})

    # 4. 삽입
    result = col.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} documents into {DB_NAME}.{collection_name}")

