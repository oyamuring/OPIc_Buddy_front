import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import OpenAI
from db.db import connect_db

# 서베이랑 질문 topic 매칭위한 파일 경로
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_MAP_PATH = os.path.join(DATA_DIR, "survey_topic_map.json")

# 오픽 질문 샘플 파일 경로
OPIC_DATA_PATH = os.path.join(os.path.dirname(__file__), "opic_question.json")

# JSON 파일 로드
def load_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# opic_data 변수를 opic_question.json 파일에서 로드하여 선언합니다.
# 파일이 없거나 오류가 발생하면 빈 딕셔너리를 사용합니다.
opic_data = load_json(OPIC_DATA_PATH) or {}

# 서베이 내용(키)을 표준화 함수
def _normalize_key(s: str) -> str:
    return s.strip().lower()


# 설문조사 항목과 DB 토픽 매핑 로드
def load_survey_map(map_path: str = DEFAULT_MAP_PATH) -> Dict[str, str]:
    """
    Loads the survey topic mapping from a JSON file.
    Returns a dictionary mapping survey topics to database topics.
    """
    obj = load_json(map_path)
    if obj is None:
        return {}
    return {str(k): str(v) for k, v in obj.items()}


# MongoDB에서 서베이 질문 가져오기
def get_questions_from_db(survey_topic: str) -> List[str]:
    # connect_db is a synchronous function, so await is not needed.
    db_collection = connect_db('opic_samples')

    if db_collection is None:
        return []

    normalized_topic = _normalize_key(survey_topic)

    # Use find_one to query the database for the topic.
    # We are assuming the documents are structured with 'topic' as a field.
    document = db_collection.find_one({"topic": normalized_topic, "category": "survey"})

    if document:
        # The questions are stored in a key called 'content' within the document.
        return document.get("content", [])

    return []

# MongoDB에서 롤플레이 질문 가져오기
def get_role_play_questions_from_db(role_play_topic: str) -> List[str]:
    db_collection = connect_db('opic_samples')
    if db_collection is None:
        return []

    # 대소문자 구분 없이 검색
    document = db_collection.find_one({
        "topic": {"$regex": f"^{role_play_topic}$", "$options": "i"},
        "category": "role_play"
    })

    if document:
        return document.get("content", [])

    return []


# MongoDB에서 돌발질문 가져오기
def get_random_questions_from_db(random_topic: str) -> List[str]:
    db_collection = connect_db("opic_samples")

    if db_collection is None:
        return []

    normalized_topic = _normalize_key(random_topic)

    # DB에서 topic과 category를 기준으로 문서 조회
    document = db_collection.find_one({"topic": normalized_topic, "category": "random_question"})

    if document:
        return document.get("content", [])

    return []

# OpenAI API를 이용해 오픽 질문 생성 전작업
def generate_openai_questions(prompt: str, questions_needed: int = 3) -> List[str]:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use an appropriate model
            messages=[
                {"role": "system", "content": "You are a helpful assistant for generating language test questions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        questions_text = response.choices[0].message.content.strip()
        questions_list = [q.strip() for q in questions_text.split('\n') if q.strip()]
        return questions_list[:questions_needed]
    except Exception as e:
        print(f"An error occurred with the OpenAI API: {e}")
        return []


# 질문 생성
def make_questions(topic: str, category: str, level: str, count: int) -> List[str]:
    """
    Generates OPIC questions:
    - Fetches questions from the DB
    - Uses them as context to generate 3 similar additional questions
    """

    db_questions = []

    # 1. Get questions from the database based on the category and topic
    if category == 'survey':
        db_questions = get_questions_from_db(topic)
    elif category == 'role_play':
        db_questions = get_role_play_questions_from_db(topic)
    elif category == 'random_question':
        db_questions = get_random_questions_from_db(topic)

    # 2. Always generate 3 additional similar questions using OpenAI
    # f"appropriate for a speaker at an {level} level. "
    openai_questions = []
    if db_questions:  # context가 있어야만 실행
        context_str = "\n".join(f"- {q}" for q in db_questions)
        prompt = (
            f"You are an OPIC question generator.\n\n"
            f"Here are some sample questions about the topic '{topic}' in category '{category}':\n"
            f"{context_str}\n\n"
            f"Now, generate 3 new OPIC-style questions that are similar in style and difficulty, "
            f"Make sure they are open-ended and not duplicates of the examples."
        )
        openai_questions = generate_openai_questions(prompt, 3)

    # 3. Combine DB + AI questions
    final_questions = db_questions + openai_questions

    # 4. Return, but still respect 'count'
    return final_questions[:count]
