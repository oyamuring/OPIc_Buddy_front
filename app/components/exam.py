# -*- coding: utf-8 -*-
"""
OPIc Exam Page (feature/opic-questions 우선)
- 설문 기반 15문항 생성(create_opic_exam)
- Streamlit 화면(show_exam)
- GIF 재생: base64/HTML로 확실히 움직이게 처리
"""

import os
import sys
import random
import asyncio
import base64
from typing import List, Dict

# --- 프로젝트 루트 경로 추가 (필요 시) ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st

# 내부 모듈
from quest import make_questions
from .survey import get_survey_data, get_user_profile, KO_EN_MAPPING  # ← 오타/중복 주석 제거
from app.utils.voice_utils import VoiceManager, unified_answer_input  # 음성 유틸

# ========================
# Helper Functions
# ========================
def get_survey_topics_from_data() -> Dict[str, List[str]]:
    """
    Extracts all possible survey topics to be used for the exam.
    (feature/opic-questions 분기에서 쓰던 기본 구조 유지)
    """
    topic_structure = {
        "survey": [
            "have work experience", "living alone in a house/apartment", "living with friends in a house/apartment",
            "living with family in a house/apartment", "dormitory", "military barracks", "student",
            "museum", "watching sports", "TV", "watching cooking programs", "driving", "club", "park",
            "Improving living space", "texting friends", "watching reality shows", "spa/massage shop",
            "camping", "performance", "bar/pub", "billiard", "test preparation", "news", "shopping",
            "beach", "volunteering", "chess", "cafe", "SNS", "movies", "game", "concert", "health",
            "searching job", "reading books to children", "music", "musical instruments", "dancing",
            "writing", "drawing", "cooking", "pets", "reading", "investing", "travel magazine", "singing",
            "basketball", "baseball/softball", "soccer", "american football", "hockey", "cricket",
            "golf", "volleyball", "tennis", "badminton", "table tennis", "swimming", "bicycling",
            "skiing/snowboarding", "ice skating", "jogging", "walking", "yoga", "hiking/trekking",
            "fishing", "taekwondo", "taking fitness classes", "do not exercise",
            "domestic business trip", "overseas business trip", "staycation", "domestic travel",
            "international travel", "newspaper", "taking photos"
        ],
        "role_play": [
            "Getting Ready for Traveling", "Cancelling Appointment", "Item Purchase"
        ],
        "random_question": [
            "technology", "industry", "recycling", "weather"
        ]
    }
    return topic_structure


def get_mapped_survey_topics() -> List[str]:
    """
    Gets the user's selected survey topics from survey.py's session state
    and maps them to their English equivalents.
    """
    survey_data = get_survey_data()
    selected_topics = []

    if "work" in survey_data and survey_data["work"].get("field"):
        selected_topics.append(survey_data["work"]["field"])
    if "living" in survey_data:
        selected_topics.append(survey_data["living"])
    if "education" in survey_data and survey_data["education"].get("is_student"):
        selected_topics.append(survey_data["education"]["is_student"])

    activities = survey_data.get("activities", {})
    for category in ["leisure", "hobbies", "sports", "travel"]:
        selected_topics.extend(activities.get(category, []))

    return [topic for topic in selected_topics if topic]


# ========================
# Exam Generation (feature branch)
# ========================
async def create_opic_exam() -> List[str]:
    """
    Generates a full 15-question OPIc-style exam based on the survey results.
    1: 자기소개 1문항
    2-10: 설문 기반 3세트 x 각 3문항
    11-13: 롤플레이 3문항
    14-15: 랜덤 2문항
    """
    exam_questions: List[str] = []

    survey_data = get_survey_data()
    user_level = survey_data.get("self_assessment", "level_5")

    # 1. Self-introduction
    exam_questions.append("Tell me about yourself.")

    # 2-10. Survey topics (3 topics x 3 questions)
    user_survey_topics = get_mapped_survey_topics()
    unique_topics = list({t for t in user_survey_topics if t})

    if len(unique_topics) >= 3:
        topics_for_exam = random.sample(unique_topics, 3)
    else:
        all_survey_topics = get_survey_topics_from_data()["survey"]
        topics_for_exam = random.sample(all_survey_topics, 3)

    for topic in topics_for_exam:
        questions = make_questions(topic, 'survey', user_level, 3)
        exam_questions.extend(questions)

    # 11-13. Role-play (3 questions)
    role_play_topics = get_survey_topics_from_data()["role_play"]
    role_play_topic = random.choice(role_play_topics)
    role_play_questions = make_questions(role_play_topic, 'role_play', user_level, 3)
    exam_questions.extend(role_play_questions)

    # 14-15. Random (2 questions)
    random_question_topics = get_survey_topics_from_data()["random_question"]
    random_topic = random.choice(random_question_topics)
    random_questions = make_questions(random_topic, 'random_question', user_level, 2)
    exam_questions.extend(random_questions)

    return exam_questions


async def get_final_questions_for_streamlit() -> List[str]:
    """Streamlit에서 최종 15문항 불러올 엔트리 포인트."""
    return await create_opic_exam()


# ========================
# GIF Utilities (확실히 움직이게)
# ========================
def _gif_to_base64_html(gif_path: str, width: int | None = None) -> str:
    """GIF 파일을 base64 data-URI로 변환해 <img> HTML 반환."""
    if not os.path.exists(gif_path):
        # 경로가 상대라면 Streamlit 실행 위치 기준이라 종종 꼬임 → 프로젝트 루트도 시도
        alt = os.path.join(project_root, gif_path)
        gif_path = alt if os.path.exists(alt) else gif_path

    with open(gif_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    size_attr = f" width='{width}'" if width else ""
    return f"<img src='data:image/gif;base64,{b64}'{size_attr} style='display:block;margin:auto;' />"


# ========================
# Streamlit Page
# ========================
def show_exam():
    if "stage" not in st.session_state:
        st.session_state.stage = "intro"
    # 세션 준비
    if "exam_questions" not in st.session_state or not st.session_state["exam_questions"]:
        # 최초 진입 시 비동기 생성
        with st.spinner("문제를 생성하는 중..."):
            qs = asyncio.run(get_final_questions_for_streamlit())
        st.session_state["exam_questions"] = qs

    if "exam_answers" not in st.session_state or not isinstance(st.session_state["exam_answers"], list):
        st.session_state["exam_answers"] = []
    if "exam_idx" not in st.session_state:
        st.session_state["exam_idx"] = 0

    questions = st.session_state["exam_questions"]
    exam_idx = st.session_state["exam_idx"]

    if exam_idx >= len(questions):
        # 바로 feedback 페이지로 이동 (버튼/메시지 없이)
        st.session_state.stage = "feedback"
        st.rerun()
        return

    current_question = questions[exam_idx]

    # 상단 진행 상태
    st.title("🗣️ OPIc Buddy TEST")
    # 진행도 텍스트
    st.markdown(f"<div style='font-size:1.1rem; color:#666; margin-bottom:4px;'>진행도: {exam_idx + 1} / {len(questions)}</div>", unsafe_allow_html=True)
    st.progress((exam_idx + 1) / len(questions))

    # 차차(GIF) 왼쪽, 문제 텍스트 토글+오디오 안내 오른쪽 (세로 배치)
    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)
    chacha_gif_html = _gif_to_base64_html("app/chacha.gif", width=140)
    col_left, col_right = st.columns([1, 3])
    with col_left:
        st.markdown(chacha_gif_html, unsafe_allow_html=True)

    # 오디오 데이터 생성/캐싱은 col_right 밖에서 항상 exam_idx, current_question 기준으로 실행
    if 'tts_audio_cache' not in st.session_state:
        st.session_state['tts_audio_cache'] = {}
    tts_key = f"q{exam_idx}_tts"
    audio_data = st.session_state['tts_audio_cache'].get(tts_key)
    if audio_data is None:
        import uuid
        with st.spinner("문제 음성 변환 중..."):
            voice_manager = VoiceManager()
            audio_data = voice_manager.text_to_speech(current_question)
            st.session_state['tts_audio_cache'][tts_key] = audio_data

    # 오디오 플레이어는 col_right 밖(상단)에 항상 위치
    if audio_data:
        try:
            import base64, uuid
            b64 = base64.b64encode(audio_data).decode()
            audio_id = f"question-audio-{exam_idx}-{uuid.uuid4()}"
            audio_html = f'''
                <div style="text-align:left; margin: 12px 0 0 0; padding: 12px 18px; background: #f8f9fa; border-radius: 10px; box-shadow: 0 1px 4px #0001; border: 1px solid #e3e6ea;">
                    <b style="color:#1976d2;">문제 오디오</b><br>
                    <audio id="{audio_id}" controls style="width:100%; margin-top:4px;">
                        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                        <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                </div>
            '''
            st.markdown(audio_html, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"audio 태그 예외: {e}")

    # col_right 안에는 안내 메시지만 배치
    with col_right:
        show_text = st.toggle("📝 문제 텍스트 보기", value=False, key=f"show_text_{exam_idx}")
        if show_text:
            st.markdown(
                f"<div style='font-size:1.1rem; font-weight:600; color:#222; margin-bottom:6px;'>{current_question}</div>",
                unsafe_allow_html=True
            )
        st.markdown("<div style='margin-top:10px; color:#888; font-size:0.97em;'>🔊 하단의 오디오 플레이어에서 문제 음성을 들을 수 있습니다.</div>", unsafe_allow_html=True)



















    # 답변 입력(음성+텍스트 통합)
    answer = unified_answer_input(exam_idx, current_question)

    # 네비게이션: Back, Next, Clear
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        back_label = "← Survey" if exam_idx == 0 else "← Back"
        if st.button(back_label, key=f"back_btn_{exam_idx}"):
            # 문제 이동 시 현재 문제의 오디오 캐시만 삭제
            tts_key = f"q{exam_idx}_tts"
            if 'tts_audio_cache' in st.session_state and tts_key in st.session_state['tts_audio_cache']:
                del st.session_state['tts_audio_cache'][tts_key]
            if exam_idx == 0:
                st.session_state.stage = "survey"
            else:
                st.session_state.exam_idx -= 1
            st.rerun()
            return
    with col2:
        if st.button("🧹 Clear Answer", key=f"clear_btn_{exam_idx}"):
            st.session_state[f"ans_{exam_idx}"] = ""
            # text_input_x의 키를 변경하여 위젯을 새로 렌더링 (세션 상태 직접 할당 X)
            st.session_state[f"text_input_key_{exam_idx}"] = str(uuid.uuid4())
            st.session_state[f"audio_data_{exam_idx}"] = None
            st.session_state.user_input = ""
            st.session_state[f"play_gif_{exam_idx}"] = False
            st.rerun()
    with col3:
        if st.button("→ Next", key=f"next_btn_{exam_idx}"):
            # 문제 이동 시 현재 문제의 오디오 캐시만 삭제
            tts_key = f"q{exam_idx}_tts"
            if 'tts_audio_cache' in st.session_state and tts_key in st.session_state['tts_audio_cache']:
                del st.session_state['tts_audio_cache'][tts_key]
            recorded_answer = answer.strip() if answer and answer.strip() else "무응답"
            st.session_state.exam_answers.append(recorded_answer)
            audio_key = f"audio_data_{exam_idx}"
            answer_audio_data = st.session_state.get(audio_key)
            if "answer_audio_files" not in st.session_state:
                st.session_state["answer_audio_files"] = []
            st.session_state["answer_audio_files"].append(answer_audio_data)
            st.session_state.user_input = ""
            st.session_state.exam_idx += 1
            st.rerun()
            return


# ---- 이 모듈을 직접 실행했을 때의 가벼운 테스트 진입점 ----
if __name__ == "__main__":
    # streamlit run app/pages/exam.py 로 실행하는 것을 권장
    # 여기서는 함수만 호출
    print("직접 실행 시: 별도 동작 없음 (Streamlit에서 실행하세요)")