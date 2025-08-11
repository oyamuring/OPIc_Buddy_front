import sys, json, time
from pathlib import Path
import streamlit as st

# 프로젝트 루트(quest.py, retriever.py 등)에 접근 가능하도록 경로 추가
ROOT = Path(__file__).resolve().parents[1].parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from quest import build_opic_mock_exam  # ✅ 새 빌더만 사용

# AI Tutor 모듈 추가
try:
    from app.utils.openai_api.comprehensive_tutor import ComprehensiveOPIcTutor

    AI_TUTOR_AVAILABLE = True
except ImportError:
    AI_TUTOR_AVAILABLE = False
    print("⚠️ OpenAI API를 사용할 수 없습니다. 기본 피드백을 사용합니다.")

DATA_DIR = ROOT / "data"
DEFAULT_SURVEY_KEYS = [
    "dormitory", "student", "driving", "travel", "hobby",
    "food", "family", "friend", "neighborhood", "shopping",
    "sports", "health", "movie", "music", "part-time job"
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
    """(선택) 예전 RAG용 힌트 텍스트 — 지금은 미사용이지만 보관."""
    sd = st.session_state.get("survey_answers") or st.session_state.get("survey_data")
    if not sd:
        return "general background travel hobbies"
    parts = []
    try:
        if isinstance(sd, dict):
            for v in sd.values():
                if isinstance(v, (list, tuple)):
                    parts.extend([str(x) for x in v])
                else:
                    parts.append(str(v))
        elif isinstance(sd, (list, tuple)):
            parts.extend([str(x) for x in sd])
        else:
            parts.append(str(sd))
    except Exception:
        pass
    text = " ".join([p for p in parts if p])
    return text if text.strip() else "general background travel hobbies"


def _extract_survey_answers_list():
    """
    build_opic_mock_exam에 넘길 설문 답변 리스트 생성.
    - survey_data / survey_answers가 dict이면 모든 값을 평탄화
    - list/tuple이면 그대로 사용
    - 없으면 빈 리스트
    """
    sd = st.session_state.get("survey_answers") or st.session_state.get("survey_data")
    answers = []
    if not sd:
        return answers

    if isinstance(sd, dict):
        for v in sd.values():
            if isinstance(v, (list, tuple)):
                answers.extend([str(x) for x in v])
            else:
                answers.append(str(v))
    elif isinstance(sd, (list, tuple)):
        answers.extend([str(x) for x in sd])
    else:
        answers.append(str(sd))

    # 공백 제거 + 중복 제거(순서 유지)
    answers = [a.strip() for a in answers if str(a).strip()]
    answers = list(dict.fromkeys(answers))
    return answers


def _ensure_exam_questions():
    """처음 exam 진입 시 15문항 생성 (API 미사용, 로컬 생성)."""
    if st.session_state.get("exam_questions"):
        return

    # 설문 기반 답변 리스트 준비
    survey_answers = _extract_survey_answers_list()

    # 경로 명시 (data/ 하위 파일을 사용)
    map_path = str(DATA_DIR / "survey_topic_map.json")
    qbank_path = str(DATA_DIR / "opic_question.json")

    # ✅ build_opic_mock_exam 호출
    qs = build_opic_mock_exam(
        survey_answers=survey_answers,
        seed=123,
        map_path=map_path,
        qbank_path=qbank_path,
    )

    st.session_state.exam_questions = qs
    st.session_state.exam_index = 0
    st.session_state.exam_answers = []


def show_exam():
    st.title("OPIc Test")
    _ensure_exam_questions()

    qs = st.session_state.exam_questions
    idx = st.session_state.exam_index

    if idx >= len(qs):
        st.success("🎉 시험이 종료되었습니다!")

        with st.expander("📝 내 답변 확인", expanded=True):
            for i, (q, a) in enumerate(zip(qs, st.session_state.exam_answers), start=1):
                st.markdown(f"**Q{i}. {q}**")
                if a and a.strip():
                    st.write(f"'{a}'")
                else:
                    st.write("_(no answer)_")
                st.markdown("---")

        # 통합 AI 피드백 섹션
        if AI_TUTOR_AVAILABLE and st.session_state.get("survey_data"):
            st.markdown("## 🤖 AI 튜터 종합 피드백")

            if st.button("📊 OPIc 레벨 분석 & 피드백 받기",
                         help="7단계 OPIc 레벨 시스템으로 정확한 평가와 모범답안을 제공합니다",
                         type="primary"):
                _generate_comprehensive_feedback()

            if "comprehensive_feedback" in st.session_state:
                _display_comprehensive_feedback()

        else:
            st.info("💡 OpenAI API가 설정되면 AI 튜터의 7단계 레벨 분석을 받을 수 있습니다!")

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 다시 시험 보기"):
                for i in range(len(qs)):
                    if f"ans_{i}" in st.session_state:
                        del st.session_state[f"ans_{i}"]
                st.session_state.exam_index = 0
                st.session_state.exam_completed = False
                st.session_state.pop("comprehensive_feedback", None)
                st.rerun()
        with col2:
            if st.button("📋 설문 다시 하기"):
                st.session_state.stage = "survey"
                st.rerun()
        return

    # 진행도/문항
    st.progress((idx + 1) / len(qs))
    st.caption(f"Question {idx + 1} / {len(qs)}")
    st.subheader(qs[idx])

    answer = st.text_area("Your answer (English)", key=f"ans_{idx}", height=160)

    col1, col2 = st.columns([1, 4])
    with col1:
        st.button("← Back", disabled=(idx == 0), on_click=_go_back)
    with col2:
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


def _generate_comprehensive_feedback():
    """OPIc 7단계 레벨 시스템에 기반한 종합 피드백 생성"""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        with st.spinner("🔍 OPIc 7단계 레벨 시스템으로 분석 중..."):
            status_text.text("AI가 답변을 분석하고 있습니다...")
            progress_bar.progress(20)

            survey_data = st.session_state.get("survey_data", {})
            questions = st.session_state.exam_questions
            answers = st.session_state.exam_answers

            progress_bar.progress(40)
            status_text.text("OPIc 레벨 평가 중...")

            tutor = ComprehensiveOPIcTutor()
            feedback = tutor.get_comprehensive_feedback(questions, answers, survey_data)

            progress_bar.progress(80)
            status_text.text("피드백을 정리하고 있습니다...")

            st.session_state.comprehensive_feedback = feedback

            progress_bar.progress(100)
            status_text.text("✅ 분석 완료!")
            time.sleep(0.5)

            progress_bar.empty()
            status_text.empty()

            st.success("🎊 OPIc 레벨 분석이 완료되었습니다!")

    except Exception as e:
        st.error(f"❌ 피드백 생성 중 오류가 발생했습니다: {str(e)}")
        print(f"Error details: {e}")


def _display_comprehensive_feedback():
    """생성된 종합 피드백을 표시"""
    feedback = st.session_state.get("comprehensive_feedback", {})

    if not feedback:
        st.warning("피드백이 아직 생성되지 않았습니다.")
        return

    st.markdown("---")
    st.markdown("## 🏆 총점 및 OPIc 레벨")

    col1, col2 = st.columns(2)
    with col1:
        score = feedback.get("overall_score", 0)
        st.metric("📊 총점", f"{score}/100", help="전체 답변의 종합 평가 점수")

    with col2:
        level = feedback.get("opic_level", "평가 불가")
        st.metric("🎯 OPIc 레벨", level, help="국제 공인 OPIc 7단계 기준")

    level_desc = feedback.get("level_description", "")
    if level_desc:
        st.info(f"💡 **레벨 설명**: {level_desc}")

    st.markdown("---")
    st.markdown("## 📝 문항별 상세 피드백")

    individual_feedback = feedback.get("individual_feedback", [])
    questions = st.session_state.exam_questions
    answers = st.session_state.exam_answers

    for item in individual_feedback:
        q_num = item.get("question_num", 0)
        q_idx = q_num - 1

        if q_idx < len(questions) and q_idx < len(answers):
            question = questions[q_idx]
            answer = answers[q_idx]

            with st.expander(f"Q{q_num} - 점수: {item.get('score', 0)}/100"):
                st.markdown("### 📋 질문")
                st.info(question)

                st.markdown("### 📝 내 답변")
                if answer and answer.strip():
                    st.write(f'"{answer}"')
                else:
                    st.write("_(답변 없음)_")

                st.markdown("### 💭 피드백")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**💪 잘한 점**")
                    for strength in item.get("strengths", []):
                        st.write(f"• {strength}")

                with col2:
                    st.markdown("**🎯 개선점**")
                    for improvement in item.get("improvements", []):
                        st.write(f"• {improvement}")

                sample_answer = item.get("sample_answer", "")
                if sample_answer:
                    st.markdown("### ✨ 개선된 모범답안")
                    st.success(f'"{sample_answer}"')

                st.markdown("---")

    st.markdown("## 🎯 종합 평가")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🌟 전체 강점")
        overall_strengths = feedback.get("overall_strengths", [])
        for strength in overall_strengths:
            st.write(f"✓ {strength}")

    with col2:
        st.markdown("### 📈 우선 개선사항")
        priority_improvements = feedback.get("priority_improvements", [])
        for improvement in priority_improvements:
            st.write(f"→ {improvement}")

    study_recommendations = feedback.get("study_recommendations", "")
    if study_recommendations:
        st.markdown("### 💡 학습 추천사항")
        st.info(study_recommendations)
