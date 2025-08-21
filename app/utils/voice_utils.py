"""
OPIc 시험용 통합 음성 기능 유틸리티
- TTS: 문제 읽어주기 (gTTS)
- STT: OpenAI Whisper API 사용
- 음성 인식 인터페이스
- 타이머: 1분 제한
"""

import io
import os
import time
import tempfile
import streamlit as st
## import speech_recognition as sr  # 제거
## from gtts import gTTS  # 제거
from openai import OpenAI


import re

def clean_text_for_tts(text: str) -> str:
    """
    TTS 전달 전 모든 dash 계열, smart quote, 기타 비ASCII 문자 제거/치환
    영어, 숫자, 기본 기호(.,!?\'"-:;()[] 등)만 남김
    """
    # dash 계열 모두 일반 하이픈(-)으로 치환
    dash_pattern = r"[\u2012\u2013\u2014\u2015\u2212\u2010\u2011]"
    text = re.sub(dash_pattern, "-", text)
    # smart quote 계열 치환
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    # 기타 비ASCII 문자 제거 (영어, 숫자, 기본 기호만 허용)
    text = re.sub(r"[^A-Za-z0-9 .,!?'\"\-:;()\[\]{}@#$%^&*_+=/\\|<>~`]+", " ", text)
    # 연속 공백 정리
    text = re.sub(r"\s+", " ", text).strip()
    return text


class VoiceManager:
    def text_to_speech(self, text: str, lang: str = 'en') -> bytes:
        """OpenAI TTS API를 사용해 텍스트를 mp3 음성으로 변환 (안전 정제 적용)"""
        if not self.openai_client:
            st.warning("OpenAI API 키가 설정되지 않아 TTS를 사용할 수 없습니다.")
            return None
        safe_text = clean_text_for_tts(text)
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",  # 또는 "tts-1-hd"
                input=safe_text,
                voice="alloy",  # "alloy", "echo", "fable", "onyx", "nova", "shimmer" 중 선택 가능
                response_format="mp3"
            )
            return response.content  # mp3 바이너리
        except Exception as e:
            st.error(f"TTS 오류: {e}")
            return None
    def __init__(self):
        # OpenAI API 키 확인
        self.openai_client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        
    # def text_to_speech(self, text: str, lang: str = 'en') -> bytes:
    #     """텍스트를 음성으로 변환"""
    #     try:
    #         tts = gTTS(text=text, lang=lang, slow=False)
    #         fp = io.BytesIO()
    #         tts.write_to_fp(fp)
    #         fp.seek(0)
    #         return fp.getvalue()
    #     except Exception as e:
    #         st.error(f"TTS 오류: {str(e)}")
    #         return None

    # def play_question_audio(self, question_text: str):
    #     """질문을 음성으로 재생"""
    #     audio_data = self.text_to_speech(question_text)
    #     if audio_data:
    #         st.audio(audio_data, format='audio/mp3')
    #         st.success("🔊 문제를 재생합니다!")

    def speech_to_text(self, audio_bytes: bytes) -> str:
        """음성을 텍스트로 변환 (OpenAI Whisper API 사용)"""
        if not self.openai_client:
            st.warning("⚠️ OpenAI API 키가 설정되지 않아 STT 기능을 사용할 수 없습니다.")
            return "[Voice recording - STT unavailable]"
        
        try:
            # 임시 파일로 오디오 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file.flush()
                
                # OpenAI Whisper API로 STT 수행
                with open(tmp_file.name, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en"  # 영어로 고정
                    )
                
                # 임시 파일 삭제
                os.unlink(tmp_file.name)
                
                return transcript.text.strip()
                
        except Exception as e:
            st.error(f"STT 오류: {str(e)}")
            return f"[Voice recording - STT error: {str(e)}]"

def unified_answer_input(question_idx: int, question_text: str) -> str:
    """통합된 답변 입력 인터페이스 (음성 + 텍스트)"""
    
    voice_manager = VoiceManager()
    
    # 현재 저장된 답변 확인
    answer_key = f"ans_{question_idx}"
    current_answer = st.session_state.get(answer_key, "")
    
    # 탭으로 입력 방식 구분
    tab1, tab2 = st.tabs(["🎤 음성 답변", "💬 텍스트 답변"])
    
    final_answer = ""
    
    with tab1:
        st.markdown("#### 🎤 음성으로 답변하기 (최대 60초)")
        
        # 마이크 사용 안내 (한 번만 표시)
        if not st.session_state.get("voice_instructions_shown", False):
            st.info("""
            🔍 **마이크 사용 방법:**
            1. 아래 마이크 버튼을 클릭하세요
            2. 브라우저에서 마이크 권한을 허용해주세요
            3. 녹음 버튼을 누르고 영어로 답변하세요
            4. 다시 버튼을 눌러서 녹음을 종료하세요
            
            ⚠️ Chrome, Safari, Firefox 등 최신 브라우저를 사용하세요
            """)
            st.session_state.voice_instructions_shown = True
        
        # 기존 답변이 있다면 표시 (단, 다음 페이지로 넘어온 경우는 숨김)
        hide_flag = st.session_state.get(f"hide_current_answer_{question_idx}", False)
        if hide_flag:
            del st.session_state[f"hide_current_answer_{question_idx}"]
        elif current_answer and not current_answer.startswith("[Voice"):
            st.success(f"💭 현재 텍스트 답변:")
            st.info(current_answer)
        elif current_answer:
            st.success(f"✅ 음성 답변이 저장되어 있습니다")

        # 내 답변 오디오 항상 재생
        audio_data_key = f"audio_data_{question_idx}"
        audio_data = st.session_state.get(audio_data_key)
        if audio_data:
            st.audio(audio_data, format='audio/wav')

        # 오디오 입력 (streamlit 1.32+)
        audio_value = st.audio_input(
            "마이크 버튼을 눌러서 녹음을 시작/종료하세요",
            key=f"audio_input_{question_idx}",
            help="마이크 버튼을 클릭하여 녹음을 시작하고, 다시 클릭하여 종료하세요. 최대 60초까지 녹음 가능합니다."
        )
        stt_flag_key = f"stt_done_{question_idx}"
        # 새로운 녹음이 들어오면 플래그 초기화
        if audio_value is not None and not st.session_state.get(stt_flag_key):
            st.success("🎵 음성이 성공적으로 녹음되었습니다!")
            st.session_state[audio_data_key] = audio_value.getvalue()
            st.audio(audio_value, format='audio/wav')
            with st.spinner("🔄 음성을 텍스트로 변환 중..."):
                transcript = voice_manager.speech_to_text(audio_value.getvalue())
            if transcript and not transcript.startswith("[Voice recording"):
                final_answer = transcript
                st.session_state[answer_key] = final_answer
                st.session_state[stt_flag_key] = True
                st.rerun()
            else:
                st.error("⚠️ 음성 변환에 실패했습니다. 다시 녹음해보세요.")
        elif audio_value is None and st.session_state.get(stt_flag_key):
            st.session_state[stt_flag_key] = False
    with tab2:
        st.markdown("#### 💬 텍스트로 답변하기")
        # 동적 키 적용: exam.py에서 text_input_key_{question_idx}가 있으면 그 값을, 없으면 기본값
        text_input_key = st.session_state.get(f"text_input_key_{question_idx}", f"text_input_{question_idx}")
        text_answer = st.text_area(
            "Your answer (English):",
            value=current_answer if not current_answer.startswith("[Voice") else "",
            key=text_input_key,
            height=150,
            help="영어로 답변을 입력해주세요. 음성 답변 대신 직접 텍스트로 입력할 수 있습니다."
        )
        if text_answer.strip():
            final_answer = text_answer.strip()
            st.session_state[answer_key] = final_answer
    
    return st.session_state.get(answer_key, "")

def auto_convert_audio_if_needed(question_idx: int) -> str:
    """Next 버튼 클릭 시 녹음된 음성을 자동으로 텍스트로 변환"""
    answer_key = f"ans_{question_idx}"
    audio_key = f"audio_data_{question_idx}"
    
    # 이미 답변이 있으면 그대로 반환
    existing_answer = st.session_state.get(answer_key, "")
    if existing_answer and not existing_answer.startswith("[Voice recording"):
        return existing_answer
    
    # 녹음된 오디오가 있고 아직 변환되지 않았다면 자동 변환
    audio_data = st.session_state.get(audio_key)
    if audio_data:
        try:
            voice_manager = VoiceManager()
            
            # STT 변환 수행
            transcript = voice_manager.speech_to_text(audio_data)
            
            if transcript and not transcript.startswith("[Voice recording"):
                # 변환된 텍스트를 답변으로 저장
                st.session_state[answer_key] = transcript
                # 오디오 데이터는 피드백에서 재생하기 위해 유지 (삭제하지 않음)
                # 피드백 페이지에서 접근할 수 있도록 추가 키로도 저장
                st.session_state[f"audio_{question_idx}"] = audio_data
                return transcript
            else:
                return "[Voice recording - conversion failed]"
        except Exception as e:
            return f"[Voice recording - STT error: {str(e)}]"
    
    return existing_answer

# ========== 추가 유틸리티 함수들 ==========

def display_tts_button(text, message_index=0):
    """텍스트를 음성으로 변환하는 버튼을 표시합니다."""
    # 우측 정렬을 위한 컬럼 사용
    col1, col2 = st.columns([2.5, 1.5])
    
    with col2:
        # 메시지 인덱스를 포함한 유니크한 키 생성
        unique_key = f"tts_{message_index}_{hash(text)}"
        if st.button("🔊 음성으로 듣기", key=unique_key, 
                     help="음성으로 재생하기",
                     use_container_width=True):
            pass  # gTTS 제거로 비활성화

## def _generate_google_tts(text, lang="en"):
##     """Google TTS로 빠른 음성 생성"""
##     ... (gTTS 관련 코드 전체 주석 처리)

## def recognize_speech():
##     ... (speech_recognition 관련 코드 전체 주석 처리)

## def display_speech_interface():
##     pass  # (speech_recognition 관련 코드 전체 주석 처리)