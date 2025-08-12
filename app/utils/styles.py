"""
CSS 스타일 관리 유틸리티
"""
import streamlit as st
from pathlib import Path

def load_css():
    """CSS 파일을 로드하여 Streamlit에 적용"""
    css_file = Path(__file__).parent.parent / "styles" / "app.css"
    
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            css_content = f.read()
        
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        st.warning("CSS 파일을 찾을 수 없습니다.")

def apply_intro_styles():
    """인트로 페이지 스타일 적용"""
    st.markdown("""
    <style>
        .block-welcome {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .block-welcome h2.opic-header {
            color: #36f;
            font-size: 2.1rem;
            font-weight: bold;
            white-space: nowrap;
            overflow-wrap: break-word;
            text-align: center;
        }
        .ava-desc {
            text-align: center;
            margin-top: 10px;
        }
        
        /* 인트로 페이지 전용 버튼 스타일 */
        div[data-testid="stButton"] button[key="start_button"] {
            background: #f4621f !important;
            color: #fff !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            border-radius: 6px !important;
            border: none !important;
            padding: 0.4em 1.5em !important;
            box-shadow: 0 1px 4px 0 rgba(244,98,31,0.08) !important;
            transition: background 0.18s !important;
            height: 36px !important;
            min-width: 90px !important;
            max-width: 160px !important;
            width: auto !important;
            white-space: nowrap !important;
        }
        
        div[data-testid="stButton"] button[key="start_button"]:hover {
            background: #d94e0b !important;
            color: #fff !important;
        }
    </style>
    """, unsafe_allow_html=True)

def apply_survey_styles():
    """설문조사 페이지 스타일 적용"""
    st.markdown("""
    <style>
        /* --- Progress Status Stick (fixed) --- */
        .progress-status {
            position: fixed;
            top: 120px;
            right: 32px;
            width: 12px;
            height: 260px;
            background: #f3f4f6;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            z-index: 9999;
            display: flex;
            align-items: flex-end;
            justify-content: center;
        }
        .progress-status-bar {
            width: 100%;
            border-radius: 6px;
            background: linear-gradient(180deg, #f4621f 0%, #ffb37b 100%);
            transition: height 0.5s cubic-bezier(.4,1.3,.6,1);
            box-shadow: 0 1px 4px 0 rgba(244,98,31,0.08);
        }
        .progress-status-label {
            position: fixed;
            right: 52px;
            top: 120px;
            font-size: 1.05rem;
            font-weight: 700;
            color: #f4621f;
            background: #fff;
            border-radius: 6px;
            padding: 6px 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
            z-index: 10000;
            text-align: right;
        }
        @media (max-width: 1200px) {
            .progress-status, .progress-status-label { display:none; }
        }
.thin-progress-container {
    width: 100%;
    margin-bottom: 28px;
    margin-top: 2px;
}
.thin-progress-bar-bg {
    width: 100%;
    height: 7px;
    background: #f3f4f6;
    border-radius: 5px;
    position: relative;
    overflow: hidden;
}
.thin-progress-bar-fg {
    height: 100%;
    background: linear-gradient(90deg, #f4621f 60%, #ffb37b 100%);
    border-radius: 5px;
    transition: width 0.4s cubic-bezier(.4,1.3,.6,1);
}
.thin-progress-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 7px;
    font-size: 1.07rem;
    font-weight: 600;
    color: #b0b3b8;
    letter-spacing: -0.5px;
}
.thin-progress-labels .active {
    color: #f4621f;
    font-weight: 800;
    text-shadow: 0 1px 0 #fff2e6;
}

/* 라디오 버튼 스타일링 */
.stRadio > div > div:first-child p {
    font-size: 1.18rem !important;
    font-weight: 600 !important;
    color: rgb(34, 34, 34) !important;
    margin-bottom: 12px !important;
}
.stRadio > div > div:nth-child(2) > div > label {
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    color: rgb(51, 51, 51) !important;
    line-height: 1.4 !important;
    padding: 8px 0 !important;
}
.stRadio > div > div:nth-child(2) > div > label:hover {
    color: #f4621f !important;
}
</style>
""", unsafe_allow_html=True)

def apply_button_styles():
    """버튼 스타일 적용"""
    st.markdown("""
    <style>
    .stButton>button {
        background: #f4621f;
        color: #fff;
        font-weight: 600;
        font-size: 0.9rem;
        border-radius: 6px;
        border: none;
        padding: 0.4em 1.5em;
        box-shadow: 0 1px 4px 0 rgba(244,98,31,0.08);
        transition: background 0.18s;
        height: 36px;
        min-width: 90px;
        max-width: 160px;
        width: auto !important;
        white-space: nowrap;
    }
    .stButton>button:hover {
        background: #d94e0b;
        color: #fff;
    }
    .stButton>button:disabled {
        background: #cccccc;
        color: #666666;
    }
    .stButton>button:disabled:hover {
        background: #cccccc;
        color: #666666;
    }
    </style>
    """, unsafe_allow_html=True)
