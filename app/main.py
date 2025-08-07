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
    
    # 개발자 모드 토글 (사이드바에 숨겨진 체크박스)
    st.sidebar.markdown("---")
    st.session_state.dev_mode = st.sidebar.checkbox("🛠️ 개발자 모드", value=st.session_state.get("dev_mode", False))
    
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
        
    # 설문 데이터가 업데이트될 때마다 value pool 갱신
    def update_survey_value_pool():
        """설문 데이터에서 값들을 추출해 survey_value_pool에 저장"""
        survey_data = st.session_state.get("survey_data", {})
        value_pool = []

        # work, education, living에서 값 추출
        if isinstance(survey_data.get("work"), dict):
            value_pool.extend([v for v in survey_data["work"].values() if v])
        if isinstance(survey_data.get("education"), dict):
            value_pool.extend([v for v in survey_data["education"].values() if v])
        if survey_data.get("living"):
            value_pool.append(survey_data["living"])
            
        # activities는 중첩 구조이므로 별도 처리
        if isinstance(survey_data.get("activities"), dict):
            for category_items in survey_data["activities"].values():
                if isinstance(category_items, list):
                    value_pool.extend(category_items)

        # None, 빈 문자열, 빈 리스트 등은 제외
        st.session_state.survey_value_pool = [v for v in value_pool if v and v != ""]

    # survey_value_pool 초기화 및 업데이트
    if "survey_value_pool" not in st.session_state:
        st.session_state.survey_value_pool = []
    
    # 설문 데이터가 있으면 value pool 업데이트
    update_survey_value_pool()

    # 개발자 모드에서만 출력
    if st.session_state.get("dev_mode", False):
        st.sidebar.subheader("🛠️ Survey Value Pool (Dev)")
        st.sidebar.write(st.session_state.survey_value_pool)
    # 채팅 기록 저장소
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # 설문 진행 단계
    if "survey_step" not in st.session_state:
        st.session_state.survey_step = 1

if __name__ == "__main__":
    main()
