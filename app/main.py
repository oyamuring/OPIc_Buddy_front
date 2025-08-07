"""
OPIc Buddy - AI 기반 영어 말하기 연습 앱
"""
import streamlit as st
from pathlib import Path

# 모듈 임포트
from utils.model_loader import load_model
from components.intro import show_intro
from components.survey import show_survey
from components.chat import show_chat

# 페이지 설정
st.set_page_config(
    page_title="🤖 OPIc Buddy", 
    page_icon="🤖",
    layout="wide"
)

def initialize_session_state():
    """세션 상태 초기화"""
    if "stage" not in st.session_state:
        st.session_state.stage = "intro"  # intro → survey → chat
    
    if "survey_step" not in st.session_state:
        st.session_state.survey_step = 0
    
    if "survey_data" not in st.session_state:
        st.session_state.survey_data = {}
    
    if "survey_value_pool" not in st.session_state:
        st.session_state.survey_value_pool = []
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Survey Value Pool 업데이트 함수
    def update_survey_value_pool():
        """설문조사 데이터에서 Survey Value Pool 생성"""
        if not st.session_state.survey_data:
            return
        
        value_pool = []
        survey_data = st.session_state.survey_data
        
        # work 섹션에서 값 추출
        if survey_data.get("work"):
            for value in survey_data["work"].values():
                if value and value not in value_pool:
                    value_pool.append(value)
        
        # education 섹션에서 값 추출
        if survey_data.get("education"):
            for value in survey_data["education"].values():
                if value and value not in value_pool:
                    value_pool.append(value)
        
        # living 값 추가
        if survey_data.get("living") and survey_data["living"] not in value_pool:
            value_pool.append(survey_data["living"])
        
        # activities 섹션에서 값 추출
        if survey_data.get("activities"):
            for category, items in survey_data["activities"].items():
                if items:
                    for item in items:
                        if item and item not in value_pool:
                            value_pool.append(item)
        
        # self_assessment 값 추가
        if survey_data.get("self_assessment") and survey_data["self_assessment"] not in value_pool:
            value_pool.append(survey_data["self_assessment"])
        
        st.session_state.survey_value_pool = value_pool
    
    # 세션 상태에 업데이트 함수 저장
    st.session_state.update_survey_value_pool = update_survey_value_pool

def main():
    """메인 애플리케이션"""
    initialize_session_state()
    
    # 모델 로드
    gen_pipeline = load_model()
    
    # 스테이지별 화면 표시
    if st.session_state.stage == "intro":
        show_intro()
    elif st.session_state.stage == "survey":
        show_survey()
    elif st.session_state.stage == "chat":
        show_chat(gen_pipeline)

if __name__ == "__main__":
    main()
