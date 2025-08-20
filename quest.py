import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import OpenAI
from db.db import connect_db

# 기본 경로 설정
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_MAP_PATH = os.path.join(DATA_DIR, "survey_topic_map.json")

# opic_question.json 파일의 경로를 설정합니다.
OPIC_DATA_PATH = os.path.join(os.path.dirname(__file__), "opic_question.json")

# 안전하게 JSON 파일 로드
def load_json_safe(path: str) -> Optional[Dict[str, Any]]:
    """
    Loads a JSON file safely from the given path.
    Returns the loaded dictionary or None if an error occurs.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# opic_data 변수를 opic_question.json 파일에서 로드하여 선언합니다.
# 파일이 없거나 오류가 발생하면 빈 딕셔너리를 사용합니다.
opic_data = load_json_safe(OPIC_DATA_PATH) or {}

# 키 정규화 유틸리티 함수
def _normalize_key(s: str) -> str:
    """
    Normalizes a string key by stripping whitespace and converting to lowercase.
    """
    return s.strip().lower()


# 설문조사 항목과 DB 토픽 매핑 로드
def load_survey_map(map_path: str = DEFAULT_MAP_PATH) -> Dict[str, str]:
    """
    Loads the survey topic mapping from a JSON file.
    Returns a dictionary mapping survey topics to database topics.
    """
    obj = load_json_safe(map_path)
    if obj is None:
        return {}
    # Ensures keys and values are strings
    return {str(k): str(v) for k, v in obj.items()}


# MongoDB에서 서베이 질문 가져오기
async def get_questions_from_db(survey_topic: str) -> List[str]:
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
async def get_role_play_questions_from_db(role_play_topic: str) -> List[str]:
    db = connect_db('opic_samples')

    normalized_topic = _normalize_key(role_play_topic)

    if normalized_topic in opic_data.get('role_play', {}):
        return opic_data['role_play'][normalized_topic]

    return []

# MongoDB에서 돌발질문 가져오기
async def get_random_questions_from_db(random_topic: str) -> List[str]:
    db = connect_db("opic_samples")

    normalized_topic = _normalize_key(random_topic)

    if normalized_topic in opic_data.get('random_question', {}):
        return opic_data['random_question'][normalized_topic]

    return []

# OpenAI API를 이용해 추가 질문 생성
def generate_openai_questions(prompt: str, questions_needed: int = 3) -> List[str]:
    # ... 기존 코드와 동일 ...
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


# 메인 함수: 질문 목록 생성
async def make_questions(topic: str, category: str, level: str, count: int) -> List[str]:
    """
    Combines questions from the database with AI-generated questions to a specified total count.

    Args:
        topic: The topic chosen for the questions.
        category: The category of the questions ('survey', 'role_play', 'random_question').
        level: (ignored, kept for compatibility)
        count: The total number of questions to generate.

    Returns:
        A final list of questions for the user.
    """
    db_questions = []

    # 1. Get questions from the database based on the category and topic
    if category == 'survey':
        db_questions = await get_questions_from_db(topic)
    elif category == 'role_play':
        db_questions = await get_role_play_questions_from_db(topic)
    elif category == 'random_question':
        db_questions = await get_random_questions_from_db(topic)

    # 2. Determine how many more questions are needed
    questions_needed = max(0, count - len(db_questions))

    # 3. Generate additional questions if needed (level은 프롬프트에 반영하지 않음)
    openai_questions = []
    if questions_needed > 0:
        prompt = (
            f"Generate {questions_needed} additional OPIC-style questions about the topic '{topic}' "
            f"in the category '{category}'. "
            f"Make sure they are open-ended and require detailed answers."
        )
        openai_questions = generate_openai_questions(prompt, questions_needed)

    # 4. Combine and return the questions, ensuring the total count is respected
    final_questions = db_questions + openai_questions

    return final_questions[:count]