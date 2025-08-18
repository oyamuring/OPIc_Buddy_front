import streamlit as st
import os
import asyncio
from components.intro import show_intro
from components.survey import show_survey
from components import exam as exam_mod # <--- Corrected import statement

def initialize_session_state():
    """Initializes session state variables with default values."""
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
    """Main function to run the Streamlit application."""
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
        # Note: The import is moved outside of the main() function for better practice,
        # but the original code worked by calling the module, not the function.
        # It's better to import at the top of the file for clarity.

        # 비동기 함수를 사용하여 문제 생성
        # `exam_questions`가 비어있을 때만 문제를 생성합니다.
        if not st.session_state.get("exam_questions"):
            with st.spinner("Generating OPIc questions..."):
                st.session_state["exam_questions"] = asyncio.run(exam_mod.create_opic_exam())

        exam_mod.show_exam()

    elif stage == "feedback":
        from components.feedback import show_feedback_page
        show_feedback_page()

    else:
        st.session_state.stage = "intro"
        show_intro()

if __name__ == "__main__":
    main()