# ===== OpenAI + quest.py를 이용한 최종 오픽 15문항 생성 (exam 전용) =====
import json, random
import streamlit as st
from openai import OpenAI

import os, sys

HERE = os.path.dirname(__file__)
PARENT = os.path.abspath(os.path.join(HERE, ".."))        # components의 부모
GRANDP = os.path.abspath(os.path.join(HERE, "..", ".."))  # app/components 구조 대비

for p in (PARENT, GRANDP):
    if p not in sys.path:
        sys.path.insert(0, p)

from quest import build_opic_exam  # quest.py는 그대로 사용

from components.survey import (
    LEISURE_MAPPING, HOBBY_MAPPING, SPORT_MAPPING, TRAVEL_MAPPING,
    get_user_profile,  # 선택
)

def _to_korean_originals(items_en: list[str]) -> list[str]:
    rev = {}
    rev.update({v: k for k, v in LEISURE_MAPPING.items()})
    rev.update({v: k for k, v in HOBBY_MAPPING.items()})
    rev.update({v: k for k, v in SPORT_MAPPING.items()})
    rev.update({v: k for k, v in TRAVEL_MAPPING.items()})
    return [rev.get(x, x) for x in items_en]


def _parse_level(level_any) -> int:
    """'level_4' / '레벨 4' / 4 모두 허용 → 1~6 정수로 변환"""
    if isinstance(level_any, int):
        k = level_any
    else:
        s = str(level_any).lower()
        for token in ["레벨", "level", "lvl", "_"]:
            s = s.replace(token, " ")
        s = s.strip()
        digits = [ch for ch in s if ch.isdigit()]
        k = int(digits[-1]) if digits else 4
    return max(1, min(6, k))

def _level_hint(k: int) -> str:
    table = {
        1: ("Use very simple, short prompts on concrete daily topics. "
            "No multi-part instructions or uncommon vocabulary."),
        2: ("Simple familiar scenarios. One-step prompts. Short sentences."),
        3: ("Basic narratives about routines, preferences, and near past/future."),
        4: ("Everyday scenarios with brief reasons/comparisons; 1–2 parts okay."),
        5: ("Richer, multi-part prompts with opinions, causes/effects, examples."),
        6: ("Advanced, multi-part prompts with analysis and hypotheticals."),
    }
    return table[k]

def _openai_json(messages, model="gpt-4o-mini", temperature=0.6, client: OpenAI | None = None) -> dict:
    cli = client or OpenAI()  # OPENAI_API_KEY 필요
    resp = cli.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=temperature,
        top_p=0.9,
    )
    text = resp.choices[0].message.content
    try:
        return json.loads(text)
    except Exception:
        cleaned = text.strip().strip("`")
        b, e = cleaned.find("{"), cleaned.rfind("}")
        if b >= 0 and e > b:
            return json.loads(cleaned[b:e+1])
        raise RuntimeError(f"OpenAI 응답 JSON 파싱 실패: {text[:200]}...")

def _mk_exam_prompt(level_k: int, db_examples: list[str], user_profile: str | None) -> list[dict[str, str]]:
    system = (
        "You are an expert OPIc (Oral Proficiency Interview - computer) item writer. "
        "You must respond ONLY with a valid JSON object. "                 # ★ JSON 명시
        "Schema: {\"questions\": [string, ...]}. No extra text, no markdown."
    )
    payload = {
        "task": "Create exactly 15 OPIc-style questions following the sequence.",
        "sequence_outline": [
            "1: self-introduction (1 question)",
            "2-10: survey-related topics (3 blocks × 3 Q each = 9 questions)",
            "11-13: role-play (3 questions)",
            "14-15: random/general OPIc (2 questions)"
        ],
        "difficulty_hint": _level_hint(level_k),
        "constraints": [
            "One question per line. No numbering, no quotes.",
            "Avoid yes/no-only prompts; elicit responses appropriate to the level.",
            "No duplicates. No references to the prompt/context/system.",
            "Keep questions realistic for OPIc.",
            "Return JSON only with the key 'questions' (array of strings)."  # ★ JSON 명시
        ],
        "context_examples_from_db": db_examples[:30],
        "user_profile_hint": user_profile or "",
        "output_format_note": "Respond in JSON like: {\"questions\":[\"...\", \"...\"]}"  # ★ JSON 명시
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def build_opic_questions_with_openai_from_exam(
    seed: int | None = None,
    model: str = "gpt-4o-mini",
    client: OpenAI | None = None
) -> list[str]:
 
    """
    - OpenAI로 레벨에 맞춘 최종 15문항 생성 (백업/하드코딩 없음; 실패 시 예외)
    """
    if "survey_data" not in st.session_state or not st.session_state.survey_data:
        raise RuntimeError("설문 데이터가 없습니다. survey를 완료하세요.")

    data = st.session_state.survey_data
    level_any = data.get("self_assessment")  # 예: "level_4" 또는 "레벨 4"
    level_k = _parse_level(level_any)

    # 설문 응답에서 사용할 키들(activities의 영어 리스트)
    acts = st.session_state.survey_data.get("activities", {})
    survey_answers_en = []
    for key in ("leisure", "hobbies", "sports", "travel"):
        vals = acts.get(key, [])
        if isinstance(vals, list):
            survey_answers_en.extend([str(v) for v in vals])

    if not survey_answers_en:
        raise RuntimeError("설문 활동 선택이 비어 있습니다. Step 4에서 항목을 선택하세요.")

    survey_answers_ko = _to_korean_originals(survey_answers_en)  # ★ 변환
    db_examples = build_opic_exam(survey_answers=survey_answers_ko, seed=seed)

    # 사용자 요약(선택): survey.py의 get_user_profile()이 있다면 활용
    try:
        from app.components.survey import get_user_profile  # 경로 프로젝트에 맞게
        user_profile = get_user_profile()
    except Exception:
        user_profile = ""

    # OpenAI에 레벨/컨텍스트/프로필 반영해 최종 15문항 생성
    messages = _mk_exam_prompt(level_k, db_examples, user_profile)
    out = _openai_json(messages, model=model, client=client, temperature=0.6)

    # 빈 문자열 제거, 중복 제거, 15개만 사용 (항상 15개로 맞춤)
    cleaned = []
    seen = set()
    for q in out.get("questions", []):
        if not isinstance(q, str):
            continue
        q = q.strip()
        if not q or q in seen:
            continue
        seen.add(q)
        cleaned.append(q)
        if len(cleaned) == 15:
            break
    # 혹시라도 남아있을 수 있는 15개 체크 및 예외 발생 코드 완전 제거
    while len(cleaned) < 15:
        cleaned.append("")
    if len(cleaned) > 15:
        cleaned = cleaned[:15]
    return cleaned

def ensure_exam_questions_openai(seed: int | None = None, model: str = "gpt-4o-mini"):
    """세션에 exam_questions가 없으면 생성해서 넣는다."""
    if st.session_state.get("exam_questions"):
        return
    client = OpenAI()
    qs = build_opic_questions_with_openai_from_exam(seed=seed, model=model, client=client)
    st.session_state.exam_questions = qs

    # ★ 길이 맞춰 답안/인덱스 초기화
    st.session_state.exam_answers = [""] * len(qs)
    st.session_state.exam_idx = 0

def show_exam():

    qs = st.session_state.get("exam_questions", [])
    if not qs:
        st.error("시험 문항이 없습니다. 다시 시도해 주세요.")
        return

    # ===== 개발자 모드 (메인 화면) =====
    dev_mode = st.toggle("개발자 모드", value=False, key="dev_mode_main")
    if dev_mode:
        st.markdown("---")
        st.subheader("[개발자모드] 사용자가 선택한 Survey 데이터")
        st.json(st.session_state.get("survey_data", {}))
        st.subheader("[개발자모드] OpenAI가 생성한 질문 리스트")
        st.write(qs)
        st.markdown("---")

    if ("exam_answers" not in st.session_state
            or not isinstance(st.session_state.exam_answers, list)
            or len(st.session_state.exam_answers) != len(qs)):
        st.session_state.exam_answers = [""] * len(qs)

    if "exam_idx" not in st.session_state:
        st.session_state.exam_idx = 0

    idx = st.session_state.exam_idx
    if idx < 0 or idx >= len(qs):
        idx = 0
        st.session_state.exam_idx = 0

    # ===== 상단 진행 바 =====
    progress = (idx + 1) / len(qs)
    st.markdown(
        f"""
        <div style='margin-bottom: 8px; margin-top: 2px;'>
            <div style='width: 100%; height: 7px; background: #f3f4f6; border-radius: 5px; position: relative; overflow: hidden;'>
                <div style='height: 100%; width: {progress*100:.1f}%; background: linear-gradient(90deg, #3b82f6 60%, #60a5fa 100%); border-radius: 5px; transition: width 0.4s;'></div>
            </div>
        </div>
        <div style='font-size: 1.08rem; font-weight: 600; color: #222; margin-bottom: 8px;'>
            Question {idx + 1} / {len(qs)}
        </div>
        """,
        unsafe_allow_html=True
    )



    from app.utils.voice_utils import VoiceManager, unified_answer_input
    voice_manager = VoiceManager()

    # 문제 오디오를 항상 새로 생성하여 즉시 재생
    audio_bytes = voice_manager.text_to_speech(qs[idx])
    st.session_state[f"audio_bytes_{idx}"] = audio_bytes

    st.audio(audio_bytes, format='audio/mp3', start_time=0)
    st.success("문제를 재생합니다!")

    # ===== 문제 텍스트 보기 토글 =====
    show_text = st.toggle("📝 문제 텍스트 보기", value=False, key=f"show_text_{idx}")
    if show_text:
        st.markdown(f"<div style='font-size:1.18rem; font-weight:600; color:#222;'>{qs[idx]}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    # ===== 답변 입력 (음성+텍스트 통합) =====
    from app.utils.voice_utils import auto_convert_audio_if_needed
    answer = unified_answer_input(idx, qs[idx])
    # 항상 최신 답변을 exam_answers에 저장
    st.session_state.exam_answers[idx] = answer
    # 음성 파일도 별도 리스트로 관리 (피드백에서 재생용)
    if 'answer_audio_files' not in st.session_state:
        st.session_state['answer_audio_files'] = [None] * len(qs)
    audio_key = f"audio_data_{idx}"
    if audio_key in st.session_state:
        st.session_state['answer_audio_files'][idx] = st.session_state[audio_key]

    # ===== 네비게이션 버튼 =====
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("← Back", disabled=(idx == 0)):
            st.session_state.exam_idx -= 1
            st.rerun()
    with col2:
        if idx == len(qs) - 1:
            # 마지막 문제: Finish
            if st.button("Finish"):
                # 마지막 답변도 자동 변환 시도 (음성만 있고 텍스트 없을 때)
                final_answer = auto_convert_audio_if_needed(idx)
                st.session_state.exam_answers[idx] = final_answer
                # 음성 파일도 저장
                if audio_key in st.session_state:
                    st.session_state['answer_audio_files'][idx] = st.session_state[audio_key]
                st.session_state.stage = "feedback"
                st.rerun()
        else:
            if st.button("Next →"):
                # 다음 문제로 넘어갈 때도 자동 변환 시도
                final_answer = auto_convert_audio_if_needed(idx)
                st.session_state.exam_answers[idx] = final_answer
                # 음성 파일도 저장
                if audio_key in st.session_state:
                    st.session_state['answer_audio_files'][idx] = st.session_state[audio_key]
                st.session_state.exam_idx += 1
                st.rerun()

