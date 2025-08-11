import os
import json
import random
from typing import List, Dict, Any, Optional

# 기본 경로
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DEFAULT_MAP_PATH = os.path.join(DATA_DIR, "survey_topic_map.json")
DEFAULT_QBANK_PATH = os.path.join(DATA_DIR, "opic_question.json")

# =========================
# 유틸
# =========================
def _load_json_safe(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _pick(items: List[str], n: int, rng: random.Random) -> List[str]:
    items = list(dict.fromkeys(items))  # 중복 제거, 순서 유지
    rng.shuffle(items)
    return items[: min(n, len(items))]

def _normalize_key(s: str) -> str:
    return s.strip().lower()

# =========================
# 데이터 로더
# =========================
def _load_survey_map(map_path: str = DEFAULT_MAP_PATH) -> Dict[str, str]:
    obj = _load_json_safe(map_path)
    if not obj:
        return {}
    # 원문(한글 키 등) -> 영어 토픽 문자열
    return {str(k): str(v) for k, v in obj.items()}

def _load_qbank(qbank_path: str = DEFAULT_QBANK_PATH) -> Dict[str, List[str]]:
    """
    예상 형태(권장):
    {
      "survey": {
        "<topic>": ["Q1", "Q2", ...],
        ...
      }
    }
    혹은 그냥:
    {
        "<topic>": ["Q1","Q2",...]
    }
    둘 다 지원.
    """
    obj = _load_json_safe(qbank_path) or {}
    # 1) "survey" 섹션 우선
    if isinstance(obj, dict) and "survey" in obj and isinstance(obj["survey"], dict):
        raw = obj["survey"]
    else:
        raw = obj

    qbank: Dict[str, List[str]] = {}
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, list):
                qbank[_normalize_key(k)] = [str(q) for q in v if isinstance(q, str)]
    return qbank

# =========================
# 질문 템플릿 (백업용)
# =========================
def _generic_triplet_for(topic: str) -> List[str]:
    """토픽 전용 3문항 기본 템플릿 (qbank에 없을 때 사용)"""
    t = topic
    return [
        f"Tell me about your experience with {t}. What do you usually do, and why do you like or dislike it?",
        f"When was the last time you dealt with {t}? Describe what happened in detail.",
        f"Compare your past and present habits related to {t}. What has changed, and why?",
    ]

def _roleplay_for(topic: str) -> List[str]:
    """역할극 2문항 (간단 템플릿)"""
    t = topic
    return [
        f"Role-play: You call a friend to make plans related to {t}. Explain your plan, ask questions, and handle any scheduling issues.",
        f"Role-play: You speak to a staff member to get help about {t}. Ask follow-up questions and respond naturally.",
    ]

def _advanced_wrapup_for(chosen_topics: List[str]) -> List[str]:
    """마무리 2문항"""
    a = chosen_topics[0] if chosen_topics else "your daily life"
    b = chosen_topics[1] if len(chosen_topics) > 1 else "your hobbies"
    return [
        f"Among {a} and {b}, which is more important to you now and why? Give detailed reasons and examples.",
        "What are your goals for improving your English speaking over the next 3 months? Be specific about time, materials, and routines.",
    ]

# =========================
# 메인 빌더
# =========================
def build_opic_mock_exam(
    survey_answers: List[str],
    seed: Optional[int] = None,
    map_path: str = DEFAULT_MAP_PATH,
    qbank_path: str = DEFAULT_QBANK_PATH,
) -> List[str]:
    """
    설문 응답(한글 선택지 등)을 받아 OPIc 15문항을 생성(API 미사용, 로컬만).

    Args:
        survey_answers: 설문에서 사용자가 선택한 문자열 리스트(예: ["학교 기숙사","요가","국내 여행"])
        seed: 무작위 시드(재현용)
        map_path: survey_topic_map.json 경로
        qbank_path: opic_question.json 경로(있으면 사용, 없으면 템플릿)

    Returns:
        15개 문자열(문항)의 리스트
    """
    rng = random.Random(seed)

    # 1) 설문 -> 토픽 매핑
    keymap = _load_survey_map(map_path)  # 원문 -> 영문 토픽
    mapped_topics: List[str] = []
    for ans in survey_answers:
        if ans in keymap:
            mapped_topics.append(keymap[ans])
    # 중복 제거 & 정규화 키
    mapped_topics = list(dict.fromkeys(mapped_topics))

    # 2) 질문은행 로드
    qbank = _load_qbank(qbank_path)

    def pick_qs_for(topic: str, n: int) -> List[str]:
        # qbank에서 먼저 시도 (대소문자/공백 무시 매칭)
        key = _normalize_key(topic)
        bank = qbank.get(key, [])
        if bank:
            # 은행에 충분치 않으면 템플릿으로 보충
            picked = _pick(bank, n, rng)
            if len(picked) < n:
                picked += _generic_triplet_for(topic)[: max(0, n - len(picked))]
            return picked[:n]
        # 없으면 템플릿
        base = _generic_triplet_for(topic)
        if len(base) >= n:
            return base[:n]
        # 혹시 부족하면 약간 변형해서 채움
        extra = [
            f"Describe a problem you faced about {topic} and how you solved it.",
            f"Give advice to a friend who wants to start {topic}. What should they know first?",
        ]
        return (base + extra)[:n]

    # 3) 토픽 그룹(3개) 선택: 설문 기반에서 우선, 부족하면 보충
    # 설문 기반 후보
    topic_pool = mapped_topics[:]
    # 혹시 설문이 너무 적을 때 대비해서 보충 후보(빈번한 일반 토픽)
    fallback_pool = [
        "daily routine", "school life", "hobbies", "travel", "shopping",
        "movies", "music", "sports", "technology", "food/cooking"
    ]
    # 그룹에 뽑을 토픽 3개
    chosen_topics = []
    chosen_topics += _pick(topic_pool, 3, rng)
    if len(chosen_topics) < 3:
        # 이미 뽑은 것 제외 후 보충
        remain = [t for t in fallback_pool if _normalize_key(t) not in {_normalize_key(x) for x in chosen_topics}]
        chosen_topics += _pick(remain, 3 - len(chosen_topics), rng)
    chosen_topics = chosen_topics[:3]

    # 4) 문항 구성 (총 15)
    questions: List[str] = []

    # (1) 자기소개 1문항
    questions.append(
        "Please introduce yourself. Include your name, where you live, what you do, and a few hobbies or interests."
    )

    # (2~4), (5~7), (8~10): 각 토픽별 3문항씩
    for topic in chosen_topics:
        questions += pick_qs_for(topic, 3)

    # (11~12): 역할극 2문항 — 첫 두 토픽 기준
    for t in chosen_topics[:2]:
        rp = _roleplay_for(t)
        # 안전하게 2개만
        questions += rp[:2]

    # (13~14): 종합/비교 2문항
    questions += _advanced_wrapup_for(chosen_topics)[:2]

    # (15): 마무리 1문항
    questions.append(
        "Is there anything else you want to share about yourself that didn’t come up in this interview? Add any final thoughts."
    )

    # 혹시 15개보다 많아지면 자르고, 모자라면 보충
    if len(questions) > 15:
        questions = questions[:15]
    elif len(questions) < 15:
        # 안전 보충(드물겠지만)
        fill_topic = chosen_topics[0] if chosen_topics else "your daily life"
        questions += pick_qs_for(fill_topic, 15 - len(questions))

    return questions


