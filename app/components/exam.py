import sys, json
from pathlib import Path
import streamlit as st

# 프로젝트 루트(quest.py, retriever.py 등)에 접근 가능하도록 경로 추가
ROOT = Path(__file__).resolve().parents[1].parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from quest import sample_opic_test

DATA_DIR = ROOT / "data"
DEFAULT_SURVEY_KEYS = [
    "dormitory","student","driving","travel","hobby",
    "food","family","friend","neighborhood","shopping",
    "sports","health","movie","music","part-time job"
]

def _load_survey_keys():
    """사용자가 별도로 세션에 넣어준 키가 있으면 그걸 쓰고,
    아니면 data/opic_question.json에서 추출, 그래도 없으면 기본값."""
    # 1) 세션 제공
    keys = st.session_state.get("survey_keys")
    if keys:
        return keys

    # 2) JSON에서 추출
    json_path = DATA_DIR / "opic_question.json"
    if json_path.exists():
        try:
            obj = json.loads(json_path.read_text(encoding="utf-8"))
            # 최상위 키들 중에서 15개 뽑기 (필요에 맞게 조정)
            jkeys = list(obj.keys())
            if jkeys:
                return jkeys[:15]
        except Exception:
            pass

    # 3) 기본값
    return DEFAULT_SURVEY_KEYS

def _build_user_input_from_survey():
    """설문 답변(세션)을 간단히 텍스트로 묶어 retrieval 힌트로 사용."""
    sd = st.session_state.get("survey_answers") or st.session_state.get("survey_data")
    if not sd:
        return "general background travel hobbies"
    parts = []
    try:
        # app.py의 survey_answers 형태 or main.py의 survey_data 형태 둘 다 지원
        if isinstance(sd, dict):
            for v in sd.values():
                if isinstance(v, (list, tuple)):
                    parts.extend([str(x) for x in v])
                else:
                    parts.append(str(v))
    except Exception:
        pass
    text = " ".join([p for p in parts if p])
    return text if text.strip() else "general background travel hobbies"

def _ensure_exam_questions():
    """처음 exam 진입 시 15문항 생성."""
    if st.session_state.get("exam_questions"):
        return
    user_input = _build_user_input_from_survey()
    survey_keys = _load_survey_keys()
    qs = sample_opic_test(
        user_input=user_input,
        survey_keys=survey_keys,
        k_retrieve=400,
        seed=123,
        collection_name="embedded_opic_samples",  # 실제 컬렉션명 사용
    )
    st.session_state.exam_questions = qs
    st.session_state.exam_index = 0
    st.session_state.exam_answers = []

def show_exam():
    st.title("📝 OPIc Mock Test")
    _ensure_exam_questions()

    qs = st.session_state.exam_questions
    idx = st.session_state.exam_index

    if idx >= len(qs):
        st.success("시험이 종료되었습니다! 👏")
        with st.expander("내 답변 확인"):
            for i, (q, a) in enumerate(zip(qs, st.session_state.exam_answers), start=1):
                st.markdown(f"**Q{i}. {q}**")
                st.write(a or "_(no answer)_")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("시험 다시 보기"):
                st.session_state.pop("exam_questions", None)
                st.session_state.pop("exam_answers", None)
                st.session_state.pop("exam_index", None)
                st.rerun()
        with col2:
            if st.button("채팅으로 이동 →"):
                st.session_state.stage = "chat"
                st.rerun()
        return

    # 진행도/문항
    st.progress((idx + 1) / len(qs))
    st.caption(f"Question {idx+1} / {len(qs)}")
    st.subheader(qs[idx])

    answer = st.text_area("Your answer (English)", key=f"ans_{idx}", height=160)

    c1, c2 = st.columns(2)
    with c1:
        st.button("← Back", disabled=(idx == 0), on_click=_go_back)
    with c2:
        st.button("Next →", on_click=_go_next, args=(answer,))

def _go_back():
    st.session_state.exam_index -= 1

def _go_next(answer: str):
    idx = st.session_state.exam_index
    answers = st.session_state.exam_answers
    if len(answers) <= idx:
        answers.append(answer)
    else:
        answers[idx] = answer
    st.session_state.exam_answers = answers
    st.session_state.exam_index = idx + 1
