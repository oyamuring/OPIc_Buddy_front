import streamlit as st
from components.intro import show_intro
from components.survey import show_survey
from components.exam import show_exam   # ★ 추가

def initialize_session_state():
    # 한 곳에서 전부 초기화
    defaults = {
        "stage": "intro",
        "survey_data": {"work": {}, "education": {}, "living": "", "activities": {}},
        "survey_step": 0,
        "survey_value_pool": [],   # ★ 여기 추가
        "user_input": ""           # (옵션) 음성 입력 버퍼
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def main():
    # set_page_config는 가능한 한 가장 먼저 호출
    st.set_page_config(
        page_title="🤖 OPIc Buddy", 
        page_icon="opic buddy.png", 
        layout="centered"
    )
    initialize_session_state()

    if st.session_state.stage == "intro":
        show_intro()
    elif st.session_state.stage == "survey":
        show_survey()
    elif st.session_state.stage == "exam":
        show_exam()
    else:
        st.error("알 수 없는 스테이지입니다.")

if __name__ == "__main__":
    main()

