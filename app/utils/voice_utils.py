"""
OPIc 시험용 통합 음성 기능 유틸리티
- TTS: OpenAI TTS (mp3)
- STT: OpenAI Whisper API (BytesIO 기반)
- 통합 답변 입력 (음성 + 텍스트)
"""

import io
import os
import streamlit as st
from openai import OpenAI


class VoiceManager:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = OpenAI(api_key=api_key) if api_key else None

    def text_to_speech(self, text: str, lang: str = 'en') -> bytes:
        """텍스트를 음성(mp3)으로 변환 (OpenAI TTS API)"""
        if not self.openai_client:
            st.warning("⚠️ OpenAI API 키가 없어 TTS 사용 불가")
            return None
        try:
            resp = self.openai_client.audio.speech.create(
                model="tts-1",
                input=text,
                voice="alloy",  # 선택: alloy, echo, fable, onyx, nova, shimmer
                response_format="mp3"
            )
            return resp.content
        except Exception as e:
            st.error(f"TTS 오류: {e}")
            return None

    def speech_to_text(self, audio_bytes: bytes) -> str:
        """음성을 텍스트로 변환 (OpenAI Whisper API, BytesIO 기반)"""
        if not self.openai_client:
            st.warning("⚠️ OpenAI API 키가 없어 STT 사용 불가")
            return "[Voice recording - STT unavailable]"
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "input.wav"  # 확장자 필수
            transcript = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
            return transcript.text.strip()
        except Exception as e:
            st.error(f"STT 오류: {e}")
            return f"[Voice recording - STT error: {e}]"


def unified_answer_input(question_idx: int, question_text: str) -> str:
    """통합된 답변 입력 UI (음성 + 텍스트)"""
    voice_manager = VoiceManager()
    answer_key = f"ans_{question_idx}"
    current_answer = st.session_state.get(answer_key, "")

    tab1, tab2 = st.tabs(["🎤 음성 답변", "💬 텍스트 답변"])
    final_answer = ""

    # 🎤 음성 입력 탭
    with tab1:
        st.markdown("#### 🎤 음성으로 답변하기 (최대 60초)")

        audio_data_key = f"audio_data_{question_idx}"
        stt_flag_key = f"stt_done_{question_idx}"

        audio_data = st.session_state.get(audio_data_key)
        if audio_data:
            st.audio(audio_data, format="audio/wav")

        audio_value = st.audio_input(
            "마이크 버튼을 눌러 녹음하세요",
            key=f"audio_input_{question_idx}"
        )

        if audio_value is not None and not st.session_state.get(stt_flag_key):
            st.success("🎵 음성이 녹음되었습니다!")
            st.session_state[audio_data_key] = audio_value.getvalue()
            st.audio(audio_value, format="audio/wav")
            with st.spinner("🔄 음성을 텍스트로 변환 중..."):
                transcript = voice_manager.speech_to_text(audio_value.getvalue())
            if transcript and not transcript.startswith("[Voice recording"):
                final_answer = transcript
                st.session_state[answer_key] = final_answer
                st.session_state[stt_flag_key] = True
                st.rerun()
            else:
                st.error("⚠️ 음성 변환 실패. 다시 시도하세요.")
        elif audio_value is None and st.session_state.get(stt_flag_key):
            st.session_state[stt_flag_key] = False

    # 💬 텍스트 입력 탭
    with tab2:
        st.markdown("#### 💬 텍스트로 답변하기")
        text_answer = st.text_area(
            "Your answer (English):",
            value=current_answer if not current_answer.startswith("[Voice") else "",
            key=f"text_input_{question_idx}",
            height=150
        )
        if text_answer.strip():
            final_answer = text_answer.strip()
            st.session_state[answer_key] = final_answer

    return st.session_state.get(answer_key, "")


def auto_convert_audio_if_needed(question_idx: int) -> str:
    """Next 버튼 클릭 시 자동 STT 변환"""
    answer_key = f"ans_{question_idx}"
    audio_key = f"audio_data_{question_idx}"

    existing_answer = st.session_state.get(answer_key, "")
    if existing_answer and not existing_answer.startswith("[Voice recording"):
        return existing_answer

    audio_data = st.session_state.get(audio_key)
    if audio_data:
        try:
            voice_manager = VoiceManager()
            transcript = voice_manager.speech_to_text(audio_data)
            if transcript and not transcript.startswith("[Voice recording"):
                st.session_state[answer_key] = transcript
                st.session_state[f"audio_{question_idx}"] = audio_data
                return transcript
            return "[Voice recording - conversion failed]"
        except Exception as e:
            return f"[Voice recording - STT error: {e}]"

    return existing_answer


def display_tts_button(text, message_index=0):
    """텍스트 → 음성 버튼"""
    col1, col2 = st.columns([2.5, 1.5])
    with col2:
        unique_key = f"tts_{message_index}_{hash(text)}"
        if st.button("🔊 음성으로 듣기", key=unique_key):
            voice_manager = VoiceManager()
            audio_data = voice_manager.text_to_speech(text)
            if audio_data:
                st.audio(audio_data, format="audio/mp3")
