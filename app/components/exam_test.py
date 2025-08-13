# exam.py 테스트 페이지
# 터미널에 streamlit run C:\PythonEnvs\huggingface\OPIc_Buddy\app\components\exam_test.py
# ctrl+c하면 터미널에서 멈춤
import streamlit as st
import os, sys
from pathlib import Path
import random

# 경로 보정 (필요시)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Dev • Exam Sandbox", page_icon="🤖", layout="centered")

st.title("Exam Sandbox (설문 스킵)")

# 기본 샘플(EN) — survey.py가 저장하는 포맷과 동일
default_activities = {
    "leisure": ["movies", "cafe", "park", "museum", "concert", "beach", "chess"],
    "hobbies": ["music", "musical instruments", "drawing", "investing"],
    "sports": ["walking"],
    "travel": ["domestic travel", "international travel"],
}
default_level = "level_4"  # "level_3" 등으로 바꿔 테스트 가능

with st.form("sandbox"):
    st.subheader("Survey 키 고정값")
    leisure = st.text_input("leisure (쉼표 구분, EN)", ", ".join(default_activities["leisure"]))
    hobbies = st.text_input("hobbies (쉼표 구분, EN)", ", ".join(default_activities["hobbies"]))
    sports  = st.text_input("sports (쉼표 구분, EN)", ", ".join(default_activities["sports"]))
    travel  = st.text_input("travel (쉼표 구분, EN)", ", ".join(default_activities["travel"]))
    level   = st.text_input("self_assessment (예: level_4 / 레벨 4 / 4)", default_level)
    if "seed" not in st.session_state:
        st.session_state.seed = 42  # 초기 시드값 설정
    seed = st.number_input("seed", value=st.session_state.seed, step=1)
    run = st.form_submit_button("Generate 15 Questions")

if run:
    # 1) 세션에 설문 데이터 주입
    st.session_state.survey_data = {
        "work": {}, "education": {}, "living": "",
        "activities": {
            "leisure": [s.strip() for s in leisure.split(",") if s.strip()],
            "hobbies": [s.strip() for s in hobbies.split(",") if s.strip()],
            "sports":  [s.strip() for s in sports.split(",")  if s.strip()],
            "travel":  [s.strip() for s in travel.split(",")  if s.strip()],
        },
        "self_assessment": level.strip(),
    }

    # 2) 생성 호출
    from components.exam import ensure_exam_questions_openai
    with st.spinner("Generating..."):
        try:
            st.session_state.seed = random.randint(1, 10000)
            ensure_exam_questions_openai(seed=int(seed), model="gpt-4o-mini")
            qs = st.session_state.get("exam_questions", [])
            st.success(f"완료: {len(qs)}문항 생성")
        except Exception as e:
            st.error(f"실패: {e}")
            qs = []

    # 3) 생성 결과 확인
    if qs:
        st.markdown("### ▶ Generated Questions")
        for i, q in enumerate(qs, 1):
            st.write(f"**Q{i}.** {q}")

        # '다시 질문 만들기' 버튼을 추가하여 페이지를 새로고침
        if st.button("Regenerate Questions"):
            st.session_state.clear()
            st.rerun()