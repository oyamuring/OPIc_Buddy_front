"""
인트로 화면 컴포넌트
"""
import streamlit as st
import base64
from pathlib import Path
from utils.styles import apply_intro_styles

def show_intro():
    if "stage" not in st.session_state:
        st.session_state.stage = "intro"
    """인트로 화면을 표시합니다."""
    # 스타일 적용
    apply_intro_styles()

    # 타이틀 + 설명
    st.markdown("""
    <div class="block-welcome" style='text-align: center;'>
        <h2 class="opic-header">
            <span class="opic-header-en" style='color:#36f; font-weight:bold;'>
                🔊 <span class="opic-header-en-desktop">Oral Proficiency Interview - computer (OPIc)</span>
                <span class="opic-header-en-mobile">Oral Proficiency Interview<br>- computer (OPIc)</span>
            </span>
        </h2>
        <p style="font-size:1.25rem; font-weight:bold;">지금부터 <span style='color:#f4621f; font-weight:bold;'>English 말하기 평가</span>를 시작하겠습니다.</p>
    </div>
    """, unsafe_allow_html=True)

    # chacha 이미지 + 설명
    _display_chacha_image()
    
    # 시작 버튼
    _display_start_button()

def _display_chacha_image():
    """chacha 이미지를 표시합니다."""
    chacha_path = Path(__file__).parent.parent / "chacha.png"
    if chacha_path.exists():
        with open(chacha_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        st.markdown(
            f"""
            <div style='display: flex; flex-direction: column; align-items: center; justify-content: center;'>
                <img src="data:image/png;base64,{img_base64}" alt="chacha" style="width: 228px;"/>
            </div>
            <div style='font-size: 1.35rem; font-weight: 600; color: #222; text-align: center; margin-top: 18px; margin-bottom: 40px;'>
            본 인터뷰 평가의 진행자는 chacha입니다.
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("chacha 이미지를 찾을 수 없습니다.")

def _display_start_button():
    """시작 버튼을 표시합니다."""
    # 인트로 전용 버튼 스타일
    st.markdown("""
    <style>
        .intro-button-container .stButton > button {
            background: #f4621f !important;
            color: #fff !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            border-radius: 6px !important;
            border: none !important;
            padding: 0.35em 0.8em !important;
            box-shadow: 0 1px 4px 0 rgba(244,98,31,0.08) !important;
            transition: background 0.18s !important;
            height: 34px !important;
            min-width: 60px !important;
            max-width: 90px !important;
            width: auto !important;
            white-space: nowrap !important;
        }
        .intro-button-container .stButton > button:hover {
            background: #d94e0b !important;
            color: #fff !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([4, 1.5, 4])
    
    with col2:
        st.markdown('<div class="intro-button-container">', unsafe_allow_html=True)
        if st.button("next", key="start_button", help="opic 모의고사 시작", use_container_width=True):
            if "stage" not in st.session_state:
                st.session_state.stage = "intro"
            st.session_state.stage = "survey"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
