# quest.py
import os
import json
import random
from typing import List, Dict, Any, Optional
from db.db import connect_db  # ← 기존에 쓰던 헬퍼 (컬렉션 핸들 반환)

# 기본 경로
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_MAP_PATH = os.path.join(DATA_DIR, "survey_topic_map.json")

# =========================
# 유틸
# =========================
def _load_json_safe(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _normalize_key(s: str) -> str:
    return s.strip().lower()

def _pick_distinct(items: List[str], n: int, rng: random.Random) -> List[str]:
    """중복 제거 후 섞어서 n개 추출"""
    items = list(dict.fromkeys(items))
    rng.shuffle(items)
    return items[: min(n, len(items))]

def _cycle_pick(items: List[str], n: int) -> List[str]:
    """items 길이가 n보다 작아도 순환하면서 n개 채움 (설문 토픽이 1~2개만 있을 때 대응)"""
    if not items:
        return []
    out = []
    i = 0
    while len(out) < n:
        out.append(items[i % len(items)])
        i += 1
    return out

# =========================
# 데이터 로더
# =========================
def _load_survey_map(map_path: str = DEFAULT_MAP_PATH) -> Dict[str, str]:
    """원문(한글 등) → 영문 토픽 문자열 매핑"""
    obj = _load_json_safe(map_path) or {}
    # 문자열 안전 변환
    return {str(k): str(v) for k, v in obj.items()}

# =========================
# DB 질의
# =========================
def _fetch_survey_pool(col, topic: str) -> List[str]:
    """
    category='survey' & topic='<topic>' 문서들의 content를 합쳐 질문 풀을 만든다.
    """
    cursor = col.find({"category": "survey", "topic": topic}, {"content": 1})
    pool: List[str] = []
    for doc in cursor:
        if isinstance(doc.get("content"), list):
            pool.extend([str(x) for x in doc["content"] if isinstance(x, str)])
    if not pool:
        raise RuntimeError(f"[DB] survey pool empty for topic='{topic}'")
    # 중복 제거(원문 순서 유지)
    pool = list(dict.fromkeys(pool))
    return pool

def _fetch_category_pool(col, category: str) -> List[str]:
    """
    category='role-play' 또는 'random_question' 풀을 전부 합친다.
    topic 필드는 없을 수도/있을 수도 있다고 가정.
    """
    cursor = col.find({"category": category}, {"content": 1})
    pool: List[str] = []
    for doc in cursor:
        if isinstance(doc.get("content"), list):
            pool.extend([str(x) for x in doc["content"] if isinstance(x, str)])
    if not pool:
        raise RuntimeError(f"[DB] pool empty for category='{category}'")
    pool = list(dict.fromkeys(pool))
    return pool

def _sample_n(pool: List[str], n: int, rng: random.Random) -> List[str]:
    """풀에서 중복 없이 n개 샘플링. 개수가 부족하면 섞은 뒤 앞에서 n개 자름(중복 없이 최대치까지)."""
    if not pool:
        return []
    if len(pool) <= n:
        pool_copy = pool[:]
        rng.shuffle(pool_copy)
        return pool_copy
    # len(pool) > n
    return rng.sample(pool, n)

# =========================
# 공개 API
# =========================
def build_opic_exam(
    survey_answers: List[str],
    seed: Optional[int] = None,
    map_path: str = DEFAULT_MAP_PATH,
    mongo_collection: str = "opic_samples",
) -> List[str]:
    """
    설문 응답(한글 선택지 등)을 받아 OPIc 15문항을 생성 (DB 전용).

    시퀀스:
      1) 자기소개 1문항
      2~4) 설문 토픽 A에 대한 3문항
      5~7) 설문 토픽 B에 대한 3문항
      8~10) 설문 토픽 C에 대한 3문항
      11~13) role-play 3문항
      14~15) random_question 2문항

    가정:
      - opic_samples 스키마: {category, topic?, content: [str, ...]}
      - category in {"survey","role-play","random_question"}
      - survey_topic_map.json으로 설문 응답 문자열 → 영문 topic 매핑이 항상 가능
      - 각 풀에 충분한 질문이 존재 (백업/하드코딩 없음)
    """
    rng = random.Random(seed)

    # 1) 설문 -> 토픽 매핑
    keymap = _load_survey_map(map_path)  # 원문 -> 영문 토픽
    mapped_topics: List[str] = []
    for ans in survey_answers:
        # 설문 원문 그대로 매칭(대소문자/공백 차이 최소화)
        if ans in keymap:
            mapped_topics.append(keymap[ans])
        else:
            # 혹시나 소문자 normalize 필요 시(키맵이 원문 그대로라면 통상 필요 없음)
            # 역매핑 시도: normalize로 비교
            for k, v in keymap.items():
                if _normalize_key(k) == _normalize_key(ans):
                    mapped_topics.append(v)
                    break

    mapped_topics = list(dict.fromkeys([t for t in mapped_topics if t]))  # 중복 제거

    if not mapped_topics:
        raise RuntimeError("설문 응답에서 매핑된 토픽이 없습니다. survey_topic_map.json을 확인하세요.")

    # 설문 토픽 3개 선택(설문이 1~2개여도 순환해서 3개 채움)
    chosen_topics = _pick_distinct(mapped_topics, 3, rng)
    if len(chosen_topics) < 3:
        chosen_topics = _cycle_pick(chosen_topics or mapped_topics, 3)

    # 2) DB 연결
    col = connect_db(mongo_collection)

    # 3) 질문 구성
    questions: List[str] = []

    # (1) 자기소개
    questions.append(
        "Please introduce yourself. Include your name, where you live, what you do, and a few hobbies or interests."
    )

    # (2~10) 설문 토픽 3개 × 각 3문항
    for topic in chosen_topics:
        pool = _fetch_survey_pool(col, topic)
        questions.extend(_sample_n(pool, 3, rng))

    # (11~13) role-play 3문항 (토픽 무관, 카테고리 풀에서 랜덤)
    rp_pool = _fetch_category_pool(col, "role_play")
    questions.extend(_sample_n(rp_pool, 3, rng))

    # (14~15) random_question 2문항
    rq_pool = _fetch_category_pool(col, "random_question")
    questions.extend(_sample_n(rq_pool, 2, rng))

    # 최종 길이 보장(정확히 15)
    if len(questions) != 15:
        # DB 상태나 샘플 수가 과/부족일 경우를 대비해 정확히 자르거나(>15) 보완(<15)
        questions = questions[:15]
        if len(questions) < 15:
            raise RuntimeError(f"최종 문항이 15개가 아닙니다. 현재={len(questions)}. DB 질문 수를 확인하세요.")

    return questions
