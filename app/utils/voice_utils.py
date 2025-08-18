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

class VoiceManager:
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
            # 플래그를 한 번 사용하면 삭제
            del st.session_state[f"hide_current_answer_{question_idx}"]
        elif current_answer and not current_answer.startswith("[Voice"):
            st.success(f"💭 현재 텍스트 답변:")
            st.info(current_answer)
        elif current_answer:
            st.success(f"✅ 음성 답변이 저장되어 있습니다")
        
        # 오디오 입력 (개선된 버전)
    # audio_value = st.audio_input(
    #     "마이크 버튼을 눌러서 녹음을 시작/종료하세요",
    #     key=f"audio_input_{question_idx}",
    #     help="마이크 버튼을 클릭하여 녹음을 시작하고, 다시 클릭하여 종료하세요. 최대 60초까지 녹음 가능합니다."
    # )
        
    # audio_value 관련 코드는 speech_recognition/gTTS 제거로 인해 비활성화
    # 음성 변환 실패/성공 분기 및 audio_value 관련 코드 전체 제거
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
            # _generate_google_tts(text)  # gTTS 제거로 비활성화

## def _generate_google_tts(text, lang="en"):
##     """Google TTS로 빠른 음성 생성"""
##     ... (gTTS 관련 코드 전체 주석 처리)

## def recognize_speech():
##     ... (speech_recognition 관련 코드 전체 주석 처리)

## def display_speech_interface():
##     pass  # (speech_recognition 관련 코드 전체 주석 처리)