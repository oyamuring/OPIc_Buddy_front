import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON_PATH = os.path.join(BASE_DIR, "data", "seed_contexts.json")

# .env 로드 (없으면 무시)
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "OPIcBuddy"

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI 환경변수가 비어 있습니다. 루트의 .env 파일 또는 OS 환경변수를 설정하세요."
    )

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
    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    docs = []
    for category, topics in raw.items():
        for topic, prompts in topics.items():
            docs.append({
                "category": category,
                "topic": topic,
                "content": prompts
            })

    if overwrite:
        col.delete_many({})

    result = col.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids)} documents into {DB_NAME}.{collection_name}")
