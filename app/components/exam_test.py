# streamlit run app/components/exam_test.py
"""
Exam Test Page
- Bypasses the survey and uses fixed activities to generate OPIc-style questions.
- Lets you quickly verify that question generation (RAG/LLM) works end-to-end.

Usage:
  In Streamlit sidebar (or pages), open this file as a page to test.

It will:
  1) Seed st.session_state with a fixed survey_data payload using the provided default_activities.
  2) Call quest.build_opic_mock_exam (or a compatible generator) with the chosen level.
  3) Show the generated questions and allow copying them to the main exam session keys.
"""

from __future__ import annotations
import sys
from pathlib import Path
import json
import traceback
import streamlit as st

# ----------------------
# Path setup (import from project root)
# ----------------------
ROOT = Path(__file__).resolve().parents[1].parent  # <repo>/app -> <repo>
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Prefer the canonical entry point used in the rest of the app
try:
    # quest.py at repo root (as used elsewhere)
    from quest import build_opic_mock_exam  # type: ignore
    HAS_BUILDER = True
except Exception:
    HAS_BUILDER = False

st.set_page_config(page_title="Dev • Exam Test", page_icon="🧪", layout="wide")
st.title("🧪 Exam Test — 설문 스킵 모드")

# ----------------------
# Fixed activities from user request (EN keys)
# ----------------------
DEFAULT_ACTIVITIES = {
    "leisure": ["movies", "cafe", "park", "museum", "concert", "beach", "chess"],
    "hobbies": ["music", "musical instruments", "drawing", "investing"],
    "sports": ["walking"],
    "travel": ["domestic travel", "international travel"],
}

# ----------------------
# Helpers
# ----------------------

def ensure_session_defaults():
    """Initialize the minimal session state expected by exam screens."""
    defaults = {
        "stage": "exam",  # jump straight to exam-like state
        "survey_data": {
            "work": {},
            "education": {},
            "living": "",
            "activities": DEFAULT_ACTIVITIES.copy(),
            "self_assessment": "level_4",
        },
        "exam_questions": [],
        "exam_answers": [],
        "exam_idx": 0,
        "feedback_payload": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def call_builder_safely(activities: dict, level: str, seed: int | None = None):
    """Call build_opic_mock_exam with best-effort signature matching.

    Many versions of `build_opic_mock_exam` exist in this project history.
    We try a few common signatures so you don't have to edit this page every time.
    Returns list[dict] where each dict has at least keys like {"id", "topic", "question"}.
    """
    if not HAS_BUILDER:
        raise RuntimeError("quest.build_opic_mock_exam 를 찾을 수 없습니다. quest.py를 확인하세요.")

    # Try the most likely signatures in order.
    last_err = None
    try:
        # v1: explicit activities & level, JSON mode (Gemini/OpenAI path inside)
        return build_opic_mock_exam(activities=activities, level=level, rng_seed=seed, json_mode=True)  # type: ignore
    except Exception as e:
        last_err = e

    try:
        # v2: activities & level only
        return build_opic_mock_exam(activities=activities, level=level)  # type: ignore
    except Exception as e:
        last_err = e

    try:
        # v3: provide a simplified user_profile
        user_profile = {"activities": activities, "self_assessment": level}
        return build_opic_mock_exam(user_profile=user_profile, level=level, rng_seed=seed)  # type: ignore
    except Exception as e:
        last_err = e

    try:
        # v4: builder expects survey_keys instead of activities
        # Flatten activities to a unique list of keys
        survey_keys = []
        for v in activities.values():
            survey_keys.extend(v)
        survey_keys = list(dict.fromkeys(survey_keys))
        return build_opic_mock_exam(survey_keys=survey_keys, level=level, rng_seed=seed)  # type: ignore
    except Exception as e:
        last_err = e

    # If all attempts failed, raise a helpful error
    raise RuntimeError(
        "build_opic_mock_exam 호출에 모두 실패했습니다.\n" +
        f"마지막 오류: {type(last_err).__name__}: {last_err}\n\n" +
        "exam_test.py의 call_builder_safely()에서 시그니처 분기를 추가하세요."
    )


# ----------------------
# UI
# ----------------------
ensure_session_defaults()

with st.sidebar:
    st.header("⚙️ Generator Options")

    # Level picker (string like "level_1" ... "level_6" to match the rest of the app)
    level = st.selectbox(
        "Self Assessment (Level)",
        options=[f"level_{i}" for i in range(1, 7)],
        index=3,  # default level_4
        help="난이도 가이드: 1=아주 쉬움 ~ 6=아주 어려움",
    )

    # Optional RNG seed for deterministic tests
    seed = st.number_input("RNG Seed (선택)", min_value=0, value=42, step=1)

    # Allow quick edits to activities (comma-separated per field)
    st.divider()
    st.caption("Activities (쉼표로 구분해 편집 가능)")

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

    st.session_state.survey_data["activities"] = edited_activities
    st.session_state.survey_data["self_assessment"] = level

    st.divider()
    run_btn = st.button("🚀 Generate Questions", use_container_width=True)
    clear_btn = st.button("🧹 Clear (세션 초기화)", use_container_width=True)

colL, colR = st.columns([2, 3])

with colL:
    st.subheader("Survey Payload (preview)")
    st.json(st.session_state.survey_data, expanded=False)

with colR:
    st.subheader("Generated Questions")

    if clear_btn:
        # Soft clear: reset only exam-related keys
        for k in ["exam_questions", "exam_answers", "exam_idx", "feedback_payload"]:
            st.session_state[k] = [] if "questions" in k or "answers" in k else 0
        st.success("Cleared exam-related session keys.")

    if run_btn:
        try:
            qs = call_builder_safely(
                activities=st.session_state.survey_data.get("activities", {}),
                level=st.session_state.survey_data.get("self_assessment", "level_4"),
                seed=int(seed) if seed is not None else None,
            )
            # Normalize to list of dicts with minimal expected fields
            norm = []
            for i, q in enumerate(qs, start=1):
                if isinstance(q, dict):
                    item = {
                        "idx": i,
                        "id": q.get("id", f"q{i:02d}"),
                        "topic": q.get("topic") or q.get("key") or q.get("category"),
                        "question": q.get("question") or q.get("text") or q.get("q"),
                        "difficulty": q.get("difficulty") or q.get("level"),
                    }
                else:
                    item = {"idx": i, "id": f"q{i:02d}", "topic": None, "question": str(q), "difficulty": None}
                norm.append(item)

            st.session_state.exam_questions = norm
            st.session_state.exam_answers = [""] * len(norm)
            st.session_state.exam_idx = 0

            st.success(f"총 {len(norm)}개의 문제가 생성되었습니다.")
        except Exception as e:
            st.error("질문 생성 중 오류가 발생했습니다. 아래 스택트레이스를 확인하세요.")
            st.exception(e)
            with st.expander("Traceback"):
                st.code(traceback.format_exc())

    # Render existing questions if any
    qs = st.session_state.get("exam_questions", [])
    if qs:
        # Quick actions
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📋 Copy to clipboard (JSON)"):
                st.toast("브라우저 보안 정책상 자동 복사는 제한될 수 있습니다. 아래 JSON을 직접 복사하세요.")
        with c2:
            if st.button("💾 Download JSON"):
                st.download_button(
                    label="Download questions.json",
                    data=json.dumps(qs, ensure_ascii=False, indent=2),
                    file_name="questions.json",
                    mime="application/json",
                    use_container_width=True,
                )

        # Show as an accordion list
        for row in qs:
            header = f"{row.get('idx', '?'):>02} • {row.get('topic') or 'topic?'}"
            with st.expander(header, expanded=False):
                st.markdown(f"**Q:** {row.get('question')}")
                meta = {k: v for k, v in row.items() if k not in {"idx", "question"}}
                st.caption(json.dumps(meta, ensure_ascii=False))

        st.info(
            "이 리스트는 `st.session_state.exam_questions`에 저장되어 있습니다. "
            "원하면 메인 exam 화면에서 그대로 사용할 수 있습니다.")
    else:
        st.caption("아직 생성된 문제가 없습니다. 왼쪽에서 **Generate Questions** 를 누르세요.")
