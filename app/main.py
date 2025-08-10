# app/main.py
import streamlit as st
from components.intro import show_intro
from components.survey import show_survey
from components.chat import show_chat
from components.exam import show_exam   # ★ 추가

def main():
    st.set_page_config(page_title="🤖 OPIc Buddy", page_icon="🤖", layout="centered")
    initialize_session_state()

    if st.session_state.stage == "intro":
        show_intro()
    elif st.session_state.stage == "survey":
        show_survey()
    elif st.session_state.stage == "exam":      # ★ 추가
        show_exam()
    elif st.session_state.stage == "chat":
        show_chat(None)  # 모델 파이프라인 없으면 None 전달(components/chat.py 내부에서 처리)
    else:
        st.error("알 수 없는 스테이지입니다.")

def initialize_session_state():
    if "stage" not in st.session_state:
        st.session_state.stage = "intro"
    if "survey_data" not in st.session_state:
        st.session_state.survey_data = {"work": {}, "education": {}, "living": "", "activities": {}}
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "survey_step" not in st.session_state:
        st.session_state.survey_step = 0

if __name__ == "__main__":
    main()
