# streamlit run app/components/exam_test.py
"""
Exam Test Page — 고정 설문으로 질문 생성 체크 전용 (레벨 5 고정)
- 음성/피드백 없이, 질문 생성만 검증합니다.
- quest.py의 make_questions(topic, category, level, count) 시그니처에 맞춰 호출합니다.
"""
from __future__ import annotations
import sys
from pathlib import Path
import asyncio
import streamlit as st

ROOT = Path(__file__).resolve().parents[1].parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from quest import load_survey_map, make_questions  # type: ignore
    QUEST_OK = True
except Exception as e:
    QUEST_OK = False
    IMPORT_ERR = e

st.set_page_config(page_title="Dev • Exam Test (Questions Only)", page_icon="🧪", layout="wide")
st.title("🧪 Exam Test — 질문 생성 확인 (설문 고정, 레벨5)")

DEFAULT_ACTIVITIES = {
    "leisure": ["movies", "cafe", "park", "museum", "concert", "beach", "chess"],
    "hobbies": ["music", "musical instruments", "drawing", "investing"],
    "sports": ["walking"],
    "travel": ["domestic travel", "international travel"],
}

LEVEL_FIXED = "advanced"  # level 5 → advanced 매핑

CATEGORY_DEFAULT = "survey"
PER_TOPIC_DEFAULT = 3

def flatten_activities(acts: dict) -> list[str]:
    keys: list[str] = []
    for v in acts.values():
        if isinstance(v, (list, tuple)):
            keys.extend([str(x) for x in v])
    return list(dict.fromkeys(keys))

async def _gen_for_topics(topics: list[str], category: str, level: str, count: int) -> dict[str, list[str]]:
    tasks = [make_questions(t, category, level, count) for t in topics]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out: dict[str, list[str]] = {}
    for t, r in zip(topics, results):
        if isinstance(r, Exception):
            out[t] = [f"[ERROR] {type(r).__name__}: {r}"]
        else:
            out[t] = list(map(str, r))
    return out

def run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

with st.sidebar:
    st.header("⚙️ 옵션")
    st.caption("레벨은 advanced(5)로 고정")
    category = st.selectbox("카테고리", options=["survey", "role_play", "random_question"], index=0)
    per_topic = st.number_input("토픽당 문항 수", min_value=1, max_value=10, value=PER_TOPIC_DEFAULT, step=1)
    st.divider()
    st.caption("Activities (쉼표 편집 가능)")
    def _csv(text: str) -> list[str]:
        return [t.strip() for t in text.split(",") if t.strip()]
    leisure = st.text_input("leisure", ", ".join(DEFAULT_ACTIVITIES["leisure"]))
    hobbies = st.text_input("hobbies", ", ".join(DEFAULT_ACTIVITIES["hobbies"]))
    sports = st.text_input("sports", ", ".join(DEFAULT_ACTIVITIES["sports"]))
    travel = st.text_input("travel", ", ".join(DEFAULT_ACTIVITIES["travel"]))
    edited_activities = {
        "leisure": _csv(leisure),
        "hobbies": _csv(hobbies),
        "sports": _csv(sports),
        "travel": _csv(travel),
    }
    run_btn = st.button("🚀 Generate", use_container_width=True)
    clear_btn = st.button("🧹 Clear", use_container_width=True)

colL, colR = st.columns([2, 3])

with colL:
    st.subheader("설문 프리뷰")
    st.json({"activities": edited_activities}, expanded=False)
    if not QUEST_OK:
        st.error("quest 모듈 임포트 실패. 아래 에러를 확인하세요.")
        st.exception(IMPORT_ERR)

with colR:
    st.subheader("토픽 매핑 & 질문 생성")
    topics = []
    survey_map = {}
    if QUEST_OK:
        try:
            survey_map = load_survey_map()
        except Exception as e:
            st.warning(f"survey_topic_map.json 로드 실패: {e}")
    flat = flatten_activities(edited_activities)
    for k in flat:
        mapped = survey_map.get(k, k)
        topics.append(mapped)
    topics = list(dict.fromkeys(topics))
    st.write("**토픽 후보:**", ", ".join(topics) if topics else "(없음)")
    if clear_btn:
        st.session_state.pop("_last_results", None)
        st.success("초기화 완료")
    if run_btn:
        if not QUEST_OK:
            st.stop()
        with st.spinner("질문 생성 중..."):
            results = run_async(_gen_for_topics(topics, category, LEVEL_FIXED, int(per_topic)))
        st.session_state["_last_results"] = {"category": category, "level": LEVEL_FIXED, "per_topic": int(per_topic), "results": results}
        st.success("생성 완료!")
    saved = st.session_state.get("_last_results")
    if saved:
        meta = {k: v for k, v in saved.items() if k != "results"}
        st.caption(str(meta))
        for t, qs in saved["results"].items():
            with st.expander(f"{t} ({len(qs)}개)", expanded=False):
                for i, q in enumerate(qs, start=1):
                    st.markdown(f"**Q{i}.** {q}")
        st.divider()
        st.subheader("모든 질문 합치기 (복사용)")
        flat_all = []
        for t, qs in saved["results"].items():
            for q in qs:
                flat_all.append({"topic": t, "question": q})
        import json
        st.json(flat_all, expanded=False)
        st.download_button(
            label="Download questions.json",
            data=json.dumps(flat_all, ensure_ascii=False, indent=2),
            file_name="questions.json",
            mime="application/json",
            use_container_width=True,
        )
