# main.py
import streamlit as st
import os
from components.intro import show_intro
from components.survey import show_survey


def initialize_session_state():
    defaults = {
        "stage": "intro",
        "survey_data": {"work": {}, "education": {}, "living": "", "activities": {}, "self_assessment": ""},
        "survey_step": 0,
        "survey_value_pool": [],
        "user_input": "",
        # exam 화면에서 저장할 값들
        "exam_questions": [],
        "exam_answers": [],
        "exam_idx": 0,
        "feedback_payload": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def main():
    favicon_path = os.path.join(os.path.dirname(__file__), "opic buddy.png")
    st.set_page_config(page_title="OPIc Buddy", page_icon=favicon_path, layout="centered")
    initialize_session_state()

    stage = st.session_state.get("stage", "intro")

    if stage == "intro":
        show_intro()

    elif stage == "survey":
        show_survey()

    elif stage == "exam":
        # exam 모듈은 지연 임포트 (안전)
        from components import exam as exam_mod
        # 아직 문제 없으면 한 번만 생성
        if not st.session_state.get("exam_questions"):
            with st.spinner("Generating OPIc questions..."):
                exam_mod.ensure_exam_questions_openai(seed=42, model="gpt-4o-mini")
        exam_mod.show_exam()


    elif stage == "feedback":
        from components.feedback import show_feedback_page# ★ 새 라우트
        show_feedback_page()

    else:
        st.session_state.stage = "intro"
        show_intro()

if __name__ == "__main__":
    main()
