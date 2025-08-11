import sys, json, time, difflib, re
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

# 음성 기능 모듈 추가
try:
    from app.utils.voice_utils import VoiceManager, unified_answer_input
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️ 음성 기능을 사용할 수 없습니다.")

DATA_DIR = ROOT / "data"
DEFAULT_SURVEY_KEYS = [
    "dormitory", "student", "driving", "travel", "hobby",
    "food", "family", "friend", "neighborhood", "shopping",
    "sports", "health", "movie", "music", "part-time job"
]


def _classify_change_type(original_part, improved_part):
    """
    변화의 유형을 분류: 문법 수정 vs 내용 추가
    """
    # 문법 수정 키워드들
    grammar_indicators = [
        'is', 'are', 'was', 'were', 'have', 'has', 'had',  # 동사 변화
        'a', 'an', 'the',  # 관사
        'in', 'on', 'at', 'with', 'by', 'for',  # 전치사
        'and', 'but', 'or', 'so', 'because',  # 접속사
        'ed', 'ing', 's'  # 어미 변화
    ]
    
    # 내용 추가 키워드들 (더 구체적이고 설명적인 단어들)
    content_indicators = [
        'really', 'very', 'extremely', 'especially', 'particularly',
        'for example', 'such as', 'including', 'like',
        'beautiful', 'amazing', 'wonderful', 'fantastic',
        'years', 'months', 'since', 'always', 'often', 'usually',
        'because', 'therefore', 'moreover', 'furthermore'
    ]
    
    original_lower = original_part.lower()
    improved_lower = improved_part.lower()
    
    # 길이가 많이 늘어났으면 내용 추가로 간주
    if len(improved_part) > len(original_part) * 1.5:
        return 'content'
    
    # 내용 추가 키워드가 있으면 내용 추가
    for indicator in content_indicators:
        if indicator in improved_lower and indicator not in original_lower:
            return 'content'
    
    # 문법 키워드만 바뀌었으면 문법 수정
    for indicator in grammar_indicators:
        if indicator in improved_lower or indicator in original_lower:
            return 'grammar'
    
    # 기본적으로는 문법 수정으로 간주
    return 'grammar'


def _highlight_text_differences(original_text, improved_text):
    """
    원본 텍스트와 개선된 텍스트를 비교해서 엄청 다른 부분만 색깔별로 강조
    """
    if not original_text or not original_text.strip():
        # 원본이 없으면 개선된 텍스트 그대로 반환
        return improved_text
    
    # 문장을 단어 단위로 분리 (공백과 구두점 포함)
    original_words = re.findall(r'\S+|\s+', original_text.lower())
    improved_words = re.findall(r'\S+|\s+', improved_text)
    improved_words_lower = re.findall(r'\S+|\s+', improved_text.lower())
    
    # difflib으로 차이점 찾기
    differ = difflib.SequenceMatcher(None, original_words, improved_words_lower)
    
    result_html = ""
    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'equal':
            # 같은 부분은 그대로 표시
            result_html += ''.join(improved_words[j1:j2])
        elif tag == 'replace':
            # 바뀐 부분의 유형을 분류
            replaced_text = ''.join(improved_words[j1:j2])
            original_part = ''.join(original_words[i1:i2])
            
            # 단순한 대소문자 변화나 아주 짧은 변화는 무시
            if len(replaced_text.strip()) >= 3 and original_part.strip().lower() != replaced_text.strip().lower():
                change_type = _classify_change_type(original_part, replaced_text)
                if change_type == 'grammar':
                    result_html += f'<strong style="color: #d32f2f;">{replaced_text}</strong>'  # 빨간색
                else:
                    result_html += f'<strong style="color: #1976d2;">{replaced_text}</strong>'  # 파란색
            else:
                result_html += replaced_text
        elif tag == 'insert':
            # 새로 추가된 부분의 유형을 분류 (3글자 이상)
            inserted_text = ''.join(improved_words[j1:j2])
            if len(inserted_text.strip()) >= 3:
                change_type = _classify_change_type('', inserted_text)
                if change_type == 'grammar':
                    result_html += f'<strong style="color: #d32f2f;">{inserted_text}</strong>'  # 빨간색
                else:
                    result_html += f'<strong style="color: #1976d2;">{inserted_text}</strong>'  # 파란색
            else:
                result_html += inserted_text
        elif tag == 'delete':
            # 삭제된 부분은 표시하지 않음
            pass
    
    return result_html


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
    st.title("OPIc Buddy")
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

        # 통합 OPIc Buddy 피드백 섹션
        if AI_TUTOR_AVAILABLE and st.session_state.get("survey_data"):
            st.markdown("## 🤖 OPIc Buddy 종합 피드백")

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
    st.caption(f"Question {idx+1} / {len(qs)}")
    
    # 현재 문제를 세션에 저장 (TTS용)
    st.session_state.current_question = qs[idx]
    
    # 음성 기능 섹션
    if VOICE_AVAILABLE:
        # 문제가 바뀌었을 때 자동으로 음성 재생
        auto_play_key = f"auto_played_{idx}"
        if auto_play_key not in st.session_state:
            voice_manager = VoiceManager()
            voice_manager.play_question_audio(qs[idx])
            st.session_state[auto_play_key] = True
        
        # 토글로 텍스트 문제 보기/숨기기
        show_text = st.toggle("📝 문제 텍스트 보기", key=f"show_text_{idx}")
        
        if show_text:
            st.info(f"**문제:** {qs[idx]}")
            
            # 수동 재생 버튼 (다시 듣기용) - 텍스트 보기할 때만 표시
            if st.button("다시 듣기", help="질문을 다시 음성으로 읽어드립니다", key=f"replay_{idx}"):
                voice_manager = VoiceManager()
                voice_manager.play_question_audio(qs[idx])
    else:
        # 음성 기능이 없을 때는 일반적으로 문제 표시
        st.subheader(qs[idx])
    
    st.markdown("### 답변 입력")
    
    # 통합된 답변 입력 인터페이스 사용
    if VOICE_AVAILABLE:
        answer = unified_answer_input(idx, qs[idx])
    else:
        # 음성 기능이 없을 때는 기본 텍스트 입력만
        answer = st.text_area("Your answer (English)", key=f"ans_{idx}", height=160)
    
    st.markdown("---")

    col1, col2 = st.columns([1, 4])
    with col1:
        if idx == 0:
            st.button("← Survey", on_click=_go_to_survey)
        else:
            st.button("← Back", on_click=_go_back)
    with col2:
        st.button("Next →", on_click=_go_next, args=(answer,))


def _go_back():
    current_idx = st.session_state.exam_index
    prev_idx = current_idx - 1
    
    # 이전 문제의 자동 재생 플래그를 초기화 (다시 들을 수 있도록)
    if f"auto_played_{prev_idx}" in st.session_state:
        del st.session_state[f"auto_played_{prev_idx}"]
    
    st.session_state.exam_index = prev_idx


def _go_to_survey():
    """첫 번째 문제에서 Survey 버튼을 누르면 설문조사로 돌아가기"""
    st.session_state.stage = "survey"


def _go_next(answer: str):
    idx = st.session_state.exam_index
    
    # 음성 기능이 사용 가능한 경우 자동 변환 시도
    if VOICE_AVAILABLE:
        from app.utils.voice_utils import auto_convert_audio_if_needed
        
        # 자동 변환된 답변이 있다면 사용
        auto_converted_answer = auto_convert_audio_if_needed(idx)
        if auto_converted_answer:
            answer = auto_converted_answer
    
    answers = st.session_state.exam_answers
    if len(answers) <= idx:
        answers.append(answer)
    else:
        answers[idx] = answer
    st.session_state.exam_answers = answers
    
    # 다음 문제로 넘어가기 전에 현재 답변 표시 관련 세션 상태 정리
    next_idx = idx + 1
    if f"ans_{next_idx}" in st.session_state:
        # 다음 문제에 이미 답변이 있으면 표시하지 않도록 임시 플래그 설정
        st.session_state[f"hide_current_answer_{next_idx}"] = True
    
    # 다음 문제의 자동 재생 플래그 초기화 (음성이 확실히 재생되도록)
    if f"auto_played_{next_idx}" in st.session_state:
        del st.session_state[f"auto_played_{next_idx}"]
    
    st.session_state.exam_index = next_idx


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
                    # 답변을 읽기 쉽게 표시
                    st.markdown(
                        f'<div style="background-color: #f8f9fa; padding: 12px; border-radius: 8px; '
                        f'border-left: 3px solid #007bff; margin: 8px 0;">'
                        f'<div style="font-style: italic; color: #495057; word-wrap: break-word; word-break: break-word;">"{answer}"</div>'
                        f'</div>', 
                        unsafe_allow_html=True
                    )
                    
                    # 재생 버튼 (너비를 늘려서 텍스트 안 짤리게)
                    if VOICE_AVAILABLE:
                        col1, col2 = st.columns([2, 5])  # 너비 비율 조정 (1,6 → 2,5)
                        with col1:
                            if st.button("🔊 내 답변 다시 듣기", key=f"play_my_answer_{q_num}", help="내 답변 다시 듣기"):
                                # 여러 가능한 오디오 키를 시도
                                audio_keys_to_try = [
                                    f"audio_data_{q_idx}",  # unified_answer_input에서 사용하는 키
                                    f"audio_{q_idx}",       # 이전 버전 호환성
                                    f"audio_data_{q_num-1}", # 인덱스 차이 고려
                                    f"audio_{q_num-1}"      # 이전 버전 호환성 2
                                ]
                                audio_found = False
                                
                                for audio_key in audio_keys_to_try:
                                    if audio_key in st.session_state and st.session_state[audio_key] is not None:
                                        # 원본 녹음 재생
                                        audio_data = st.session_state[audio_key]
                                        if isinstance(audio_data, bytes) and len(audio_data) > 0:
                                            st.session_state[f"play_original_{q_num}"] = audio_data
                                            audio_found = True
                                            st.success("원본 녹음을 재생합니다.")
                                            break
                                
                                if not audio_found:
                                    # 녹음된 음성이 없으면 TTS로 변환해서 재생
                                    try:
                                        from app.utils.voice_utils import VoiceManager
                                        vm = VoiceManager()
                                        audio_bytes = vm.text_to_speech(answer)
                                        if audio_bytes:
                                            st.session_state[f"play_original_{q_num}"] = audio_bytes
                                            st.info("답변을 음성으로 변환하여 재생합니다.")
                                        else:
                                            st.error("음성 변환에 실패했습니다.")
                                    except Exception as e:
                                        st.error(f"음성 재생 중 오류: {e}")
                        
                        # 재생할 음성이 있으면 표시 (오류 방지: 키 존재 여부 먼저 확인)
                        play_key = f"play_original_{q_num}"
                        if play_key in st.session_state:
                            audio_data = st.session_state[play_key]
                            # 오디오 데이터가 유효한지 확인
                            if audio_data is not None and isinstance(audio_data, bytes) and len(audio_data) > 0:
                                try:
                                    st.audio(audio_data)
                                except Exception as e:
                                    st.error(f"오디오 재생 오류: {str(e)}")
                            # 재생 후 세션에서 제거 (다음 번에 다시 클릭해야 재생)
                            try:
                                del st.session_state[play_key]
                            except:
                                pass  # 이미 삭제되었을 경우 무시
                else:
                    st.write("_(답변 없음)_")

                st.markdown("### 💭 피드백")

                col1, col2 = st.columns(2, gap="medium")
                with col1:
                    st.markdown(
                        '<div style="background: linear-gradient(135deg, #e8f5e8, #f1f8e9); '
                        'padding: 12px; border-radius: 10px; border-left: 4px solid #4caf50; margin-bottom: 10px;">'
                        '<h4 style="color: #2e7d32; margin: 0; font-size: 1.1em;">💪 잘한 점</h4></div>',
                        unsafe_allow_html=True
                    )
                    for strength in item.get("strengths", []):
                        st.markdown(
                            f'<div style="background-color: #f9f9f9; padding: 8px 12px; margin: 4px 0; '
                            f'border-radius: 6px; border-left: 3px solid #4caf50;">'
                            f'<span style="color: #2e7d32;">✓ {strength}</span></div>',
                            unsafe_allow_html=True
                        )

                with col2:
                    st.markdown(
                        '<div style="background: linear-gradient(135deg, #fff3e0, #fef7e0); '
                        'padding: 12px; border-radius: 10px; border-left: 4px solid #ff9800; margin-bottom: 10px;">'
                        '<h4 style="color: #e65100; margin: 0; font-size: 1.1em;">🎯 개선점</h4></div>',
                        unsafe_allow_html=True
                    )
                    for improvement in item.get("improvements", []):
                        st.markdown(
                            f'<div style="background-color: #f9f9f9; padding: 8px 12px; margin: 4px 0; '
                            f'border-radius: 6px; border-left: 3px solid #ff9800;">'
                            f'<span style="color: #e65100;">→ {improvement}</span></div>',
                            unsafe_allow_html=True
                        )

                sample_answer = item.get("sample_answer", "")
                if sample_answer:
                    st.markdown("### ✨ 개선된 모범답안")
                    
                    # 예쁜 색상 구분 설명
                    st.markdown(
                        '<div style="background: linear-gradient(90deg, #fff3e0, #e3f2fd); padding: 8px 12px; '
                        'border-radius: 20px; margin: 8px 0; text-align: center; border: 1px solid #e0e0e0;">'
                        '<span style="font-size: 0.85em; color: #666;">'
                        '🔴 <span style="color: #d32f2f; font-weight: 600;">문법 수정</span> | '
                        '🔵 <span style="color: #1976d2; font-weight: 600;">내용 추가</span>'
                        '</span></div>',
                        unsafe_allow_html=True
                    )
                    
                    # 사용자 답변과 모범답안을 비교해서 다른 부분만 색깔별로 강조
                    highlighted_answer = _highlight_text_differences(answer, sample_answer)
                    
                    # 모범답안을 읽기 쉽게 표시
                    st.markdown(
                        f'<div style="background: linear-gradient(135deg, #f8f9fa, #e8f5e8); '
                        f'padding: 16px; border-radius: 12px; margin: 10px 0; '
                        f'border-left: 4px solid #28a745; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">'
                        f'<div style="font-style: italic; line-height: 1.8; color: #495057; font-size: 1.05em; word-wrap: break-word; word-break: break-word;">"{highlighted_answer}"</div>'
                        f'</div>', 
                        unsafe_allow_html=True
                    )

                st.markdown("---")

    st.markdown("## 🎯 종합 평가")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            '<div style="background: linear-gradient(135deg, #e3f2fd, #e8eaf6); '
            'padding: 16px; border-radius: 12px; border-left: 4px solid #2196f3; margin-bottom: 15px;">'
            '<h3 style="color: #0d47a1; margin: 0 0 12px 0; font-size: 1.2em;">🌟 전체 강점</h3></div>',
            unsafe_allow_html=True
        )
        overall_strengths = feedback.get("overall_strengths", [])
        for strength in overall_strengths:
            st.markdown(
                f'<div style="background: linear-gradient(90deg, #f8f9fa, #e3f2fd); '
                f'padding: 10px 14px; margin: 6px 0; border-radius: 8px; '
                f'border-left: 3px solid #2196f3; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">'
                f'<span style="color: #0d47a1; font-weight: 500;">✨ {strength}</span></div>',
                unsafe_allow_html=True
            )

    with col2:
        st.markdown(
            '<div style="background: linear-gradient(135deg, #ffe0b2, #ffecb3); '
            'padding: 16px; border-radius: 12px; border-left: 4px solid #ff9800; margin-bottom: 15px;">'
            '<h3 style="color: #e65100; margin: 0 0 12px 0; font-size: 1.2em;">📈 우선 개선사항</h3></div>',
            unsafe_allow_html=True
        )
        priority_improvements = feedback.get("priority_improvements", [])
        for improvement in priority_improvements:
            st.markdown(
                f'<div style="background: linear-gradient(90deg, #fff8e1, #ffe0b2); '
                f'padding: 10px 14px; margin: 6px 0; border-radius: 8px; '
                f'border-left: 3px solid #ff9800; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">'
                f'<span style="color: #e65100; font-weight: 500;">🎯 {improvement}</span></div>',
                unsafe_allow_html=True
            )

    study_recommendations = feedback.get("study_recommendations", "")
    if study_recommendations:
        st.markdown(
            '<div style="background: linear-gradient(135deg, #f3e5f5, #e1bee7); '
            'padding: 20px; border-radius: 15px; margin: 20px 0; '
            'border-left: 5px solid #9c27b0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">'
            '<h3 style="color: #4a148c; margin: 0 0 12px 0; font-size: 1.3em;">💡 학습 추천사항</h3>'
            f'<p style="color: #6a1b9a; line-height: 1.6; margin: 0; font-size: 1.05em;">{study_recommendations}</p>'
            '</div>',
            unsafe_allow_html=True
        )
