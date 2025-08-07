"""
OPIc Buddy - 메인 애플리케이션
영어 말하기 평가를 위한 Streamlit 애플리케이션
"""
import streamlit as st
from pathlib import Path

# 모듈 임포트
from utils.model_loader import load_model
from components.intro import show_intro
from components.survey import show_survey
from components.chat import show_chat

def main():
    """메인 애플리케이션 함수"""
    # 페이지 설정
    st.set_page_config(
        page_title="🤖 OPIc Buddy", 
        page_icon="🤖",
        layout="centered"
    )
    
    # 세션 상태 초기화
    initialize_session_state()
    
    # AI 모델 로드
    gen_pipeline = load_model()
    
    # 현재 스테이지에 따라 화면 표시
    if st.session_state.stage == "intro":
        show_intro()
    elif st.session_state.stage == "survey":
        show_survey()
    elif st.session_state.stage == "chat":
        show_chat(gen_pipeline)
    else:
        st.error("알 수 없는 스테이지입니다.")

def initialize_session_state():
    """세션 상태를 초기화합니다."""
    # 스테이지 초기화
    if "stage" not in st.session_state:
        st.session_state.stage = "intro"  # intro → survey → chat
    
    # 설문 데이터 저장소 (새로운 구조)
    if "survey_data" not in st.session_state:
        st.session_state.survey_data = {
            "work": {},
            "education": {},
            "living": "",
            "activities": {}
        }
    
    # 채팅 기록 저장소
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # 설문 진행 단계
    if "survey_step" not in st.session_state:
        st.session_state.survey_step = 0

if __name__ == "__main__":
    main()
