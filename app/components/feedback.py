# app/components/feedback.py
import time
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1].parent

# ===== [3] OPICFeedbackService (ComprehensiveOPIcTutor 래퍼) =====
class OPICFeedbackService:
    def __init__(self):
        from app.utils.openai_api.comprehensive_tutor import ComprehensiveOPIcTutor
        self.tutor = ComprehensiveOPIcTutor()

    def run(self, questions, answers, survey_data):
        return self.tutor.get_comprehensive_feedback(questions, answers, survey_data)

# ===== [4] 텍스트 하이라이트 유틸 =====
import difflib, re
def _classify_change_type(original_part, improved_part):
    grammar_indicators = ['is','are','was','were','have','has','had','a','an','the',
                          'in','on','at','with','by','for','and','but','or','so','because',
                          'ed','ing','s']
    content_indicators = ['really','very','extremely','especially','particularly',
                          'for example','such as','including','like',
                          'beautiful','amazing','wonderful','fantastic',
                          'years','months','since','always','often','usually',
                          'because','therefore','moreover','furthermore']
    if len(improved_part) > len(original_part) * 1.5:
        return 'content'
    ol, il = original_part.lower(), improved_part.lower()
    for c in content_indicators:
        if c in il and c not in ol:
            return 'content'
    for g in grammar_indicators:
        if g in il or g in ol:
            return 'grammar'
    return 'grammar'

def highlight_text_differences(original_text, improved_text):
    if not original_text or not original_text.strip():
        return improved_text
    original_words = re.findall(r'\S+|\s+', original_text.lower())
    improved_words = re.findall(r'\S+|\s+', improved_text)
    improved_words_lower = re.findall(r'\S+|\s+', improved_text.lower())
    differ = difflib.SequenceMatcher(None, original_words, improved_words_lower)
    result_html = ""
    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'equal':
            result_html += ''.join(improved_words[j1:j2])
        elif tag == 'replace':
            replaced = ''.join(improved_words[j1:j2])
            original_part = ''.join(original_words[i1:i2])
            if len(replaced.strip()) >= 3 and original_part.strip().lower() != replaced.strip().lower():
                t = _classify_change_type(original_part, replaced)
                color = "#1976d2" if t == 'content' else "#d32f2f"
                result_html += f'<strong style="color:{color};">{replaced}</strong>'
            else:
                result_html += replaced
        elif tag == 'insert':
            inserted = ''.join(improved_words[j1:j2])
            if len(inserted.strip()) >= 3:
                t = _classify_change_type('', inserted)
                color = "#1976d2" if t == 'content' else "#d32f2f"
                result_html += f'<strong style="color:{color};">{inserted}</strong>'
            else:
                result_html += inserted
        # delete는 표시하지 않음
    return result_html

# ===== [2] 피드백 UI 패널 =====
try:
    from app.utils.voice_utils import VoiceManager
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

def show_feedback_page():
    st.title("OPIc Buddy — 종합 피드백")

    questions = st.session_state.get("exam_questions", [])
    answers   = st.session_state.get("exam_answers", [])
    if not questions or not answers:
        st.warning("먼저 시험을 완료해 주세요.")
        if st.button("← 시험으로 가기"):
            st.session_state.stage = "exam"
            st.rerun()
        return

    # ===== 전체 질문/답변 카드 형태로 항상 표시 =====
    st.markdown("---")
    questions = st.session_state.get("exam_questions", [])
    answers = st.session_state.get("exam_answers", [])
    with st.expander("📋 내가 답변한 전체 질문/답변", expanded=True):
        for i, (q, a) in enumerate(zip(questions, answers), 1):
            st.markdown(f"<div style='background:#f8f9fa;border-radius:8px;padding:14px 18px;margin-bottom:10px;box-shadow:0 1px 4px #0001;'>"
                        f"<b style='color:#1976d2;'>Q{i}.</b> <span style='font-size:1.08em;font-weight:500'>{q}</span><br>"
                        f"<span style='color:#222;font-size:1.04em;'><b>내 답변:</b> {a if a else '<i>(답변 없음)</i>'}</span>"
                        "</div>", unsafe_allow_html=True)
 
    if st.button("📊 OPIc 레벨 분석 & 피드백 받기", type="primary"):
        _generate_feedback()

    if "comprehensive_feedback" in st.session_state:
        _display_feedback()

    # 하단에 다시하기 버튼 추가
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Survey 다시하기"):
            st.session_state.stage = "survey"
            st.rerun()
    with col2:
        if st.button("🧐 Test 다시하기"):
            st.session_state.stage = "exam"
            # 시험 상태 초기화
            st.session_state.exam_idx = 0
            st.session_state.exam_answers = []
            st.session_state.exam_questions = []
            st.rerun()

def _generate_feedback():
    try:
        progress_bar = st.progress(0)
        status = st.empty()
        with st.spinner("🔍 분석 중..."):
            status.text("답변 로딩...")
            progress_bar.progress(25)

            questions = st.session_state.exam_questions
            answers   = st.session_state.exam_answers
            survey    = st.session_state.get("survey_data", {})

            svc = OPICFeedbackService()
            status.text("OPIc 레벨 평가 중...")
            progress_bar.progress(60)
            fb = svc.run(questions, answers, survey)

            status.text("피드백 정리 중...")
            progress_bar.progress(90)
            st.session_state.comprehensive_feedback = fb

            progress_bar.progress(100)
            time.sleep(0.3)
        status.empty()
        progress_bar.empty()
        st.success("🎊 분석 완료!")
    except Exception as e:
        st.error(f"❌ 피드백 생성 오류: {e}")

def _display_feedback():
    fb = st.session_state.get("comprehensive_feedback", {})
    if not fb:
        st.warning("피드백 데이터가 없습니다.")
        return

    st.markdown("---")
    col1, col2 = st.columns(2)
    col1.metric(
        "📊 총점",
        f"{fb.get('overall_score',0)}/100",
        help="OPIc Buddy의 0~100점 환산 기준에 따라 산출된 전체 평균 점수입니다. 각 문항별 점수를 평균내어 계산합니다."
    )
    col2.metric(
        "🎯 OPIc 레벨",
        fb.get("opic_level","-"),
        help="OPIc Buddy의 9단계 등급 체계(AL, IH, IM3, IM2, IM1, IL, NH, NM, NL) 중 본인의 답변 평균 점수에 따라 자동 산정된 레벨입니다."
    )
    if fb.get("level_description"):
        st.info(f"💡 {fb['level_description']}")

    # (상단 질문/답변 요약은 show_feedback_page에서 항상 카드로 보여주므로 여기선 제거)
    st.markdown("## 📝 문항별 상세 피드백")
    indiv = fb.get("individual_feedback", [])
    qs = st.session_state.exam_questions
    ans = st.session_state.exam_answers

    answer_audio_files = st.session_state.get("answer_audio_files", [None]*len(ans))
    for item in indiv:
        qn = item.get("question_num", 0)
        i = qn - 1
        if i < 0 or i >= len(qs):
            continue
        with st.expander(f"Q{qn} - 점수: {item.get('score',0)}/100", expanded=False):
            st.markdown("### 📋 질문")
            st.info(qs[i])

            st.markdown("### 📝 내 답변")
            user_answer = ans[i] if i < len(ans) else ""
            st.write(f'"{user_answer}"' if user_answer else "_(답변 없음)_")
            # 내 답변 오디오 듣기 버튼 (항상 표시, 파일이 있으면 재생)
            audio_file = answer_audio_files[i] if i < len(answer_audio_files) else None
            if st.button("🎤 내 답변 듣기", key=f"play_my_{qn}"):
                if audio_file:
                    st.audio(audio_file, format="audio/mp3")
                else:
                    st.warning("녹음된 음성 파일이 없습니다.")

            st.markdown("### 💭 피드백")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("💪 잘한 점")
                for s in item.get("strengths", []):
                    st.write(f"• {s}")
            with c2:
                st.subheader("🎯 개선점")
                for g in item.get("improvements", []):
                    st.write(f"→ {g}")

            sample = item.get("sample_answer","")
            if sample:
                st.markdown("### ✨ 개선된 모범답안")
                st.markdown(
                    '<span style="font-size:0.98em;">'
                    ' <span style="color:#d32f2f;font-weight:600;">빨간색</span>: 문법 수정 '
                    ' <span style="color:#1976d2;font-weight:600;">파란색</span>: 내용 추가/개선'
                    '</span>', unsafe_allow_html=True)
                html = highlight_text_differences(user_answer, sample)
                st.markdown(
                    '<div style="background-color:#f8f9fa;padding:16px;border-radius:8px;'
                    'border-left:4px solid #0d6efd;margin:10px 0;">'
                    f'<div style="font-style:italic;line-height:1.8;color:#495057;font-size:1.05em;">"{html}"</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
                if VOICE_AVAILABLE and st.button("🎧 모범답안 듣기", key=f"play_sample_{qn}"):
                    try:
                        audio_bytes = VoiceManager().text_to_speech(sample.strip())
                        if audio_bytes:
                            st.audio(audio_bytes)
                    except Exception as e:
                        st.error(f"TTS 오류: {e}")

    st.markdown("## 🎯 종합 평가")
    for title, key in [("🌟 전체 강점","overall_strengths"), ("📈 우선 개선사항","priority_improvements")]:
        items = fb.get(key, [])
        if items:
            st.subheader(title)
            for it in items:
                st.write(f"• {it}")
    rec = fb.get("study_recommendations","")
    if rec:
        st.subheader("💡 학습 추천사항")
        st.write(rec)
