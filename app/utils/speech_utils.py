"""
TTS(Text-to-Speech) 및 음성 인식 유틸리티
Google TTS와 SpeechRecognition을 사용한 빠르고 가벼운 음성 처리 기능
"""
import streamlit as st
import speech_recognition as sr
import tempfile
import os
from gtts import gTTS
import io

def display_tts_button(text, message_index=0):
    """텍스트를 음성으로 변환하는 버튼을 표시합니다."""
    # 우측 정렬을 위한 컬럼 사용
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # 메시지 인덱스를 포함한 유니크한 키 생성
        unique_key = f"tts_{message_index}_{hash(text)}"
        if st.button("🔊", key=unique_key, 
                     help="음성으로 듣기",
                     use_container_width=True):
            _generate_google_tts(text)

def _generate_google_tts(text, lang="en"):
    """Google TTS로 빠른 음성 생성"""
    try:
        # 텍스트 검증
        if not text or len(text.strip()) == 0:
            st.error("재생할 텍스트가 없습니다.")
            return
            
        # 텍스트 길이 제한
        if len(text) > 500:
            text = text[:500] + "..."
            st.info("텍스트가 길어서 500자까지만 재생됩니다.")
            
        with st.spinner("🎵 음성 생성 중..."):
            # Google TTS로 음성 생성
            tts = gTTS(text=text, lang=lang, slow=False)
            
            # 임시 파일 방식 사용
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                # 파일 읽기
                with open(tmp_file.name, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                    
                # Streamlit에서 음성 재생
                st.audio(audio_bytes, format='audio/mp3')
                st.success("🎧 음성 재생 준비 완료!")
                
            # 임시 파일 삭제
            os.unlink(tmp_file.name)
            
    except Exception as e:
        st.error(f"음성 생성 오류: {e}")
        st.info("인터넷 연결을 확인해주세요.")

def recognize_speech():
    """
    마이크로부터 음성을 인식하여 텍스트로 변환합니다.
    
    Returns:
        tuple: (성공 여부, 인식된 텍스트 또는 에러 메시지)
    """
    try:
        recognizer = sr.Recognizer()
        
        with sr.Microphone() as source:
            st.info("🎧 말해주세요 (최대 60초)...")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=60)
            st.info("🧠 음성 인식 중...")
        
        # Google STT 사용
        question = recognizer.recognize_google(audio, language="en-US")
        return True, question
        
    except sr.UnknownValueError:
        return False, "😵 음성을 인식하지 못했습니다."
    except sr.RequestError as e:
        return False, f"🔌 Google STT 요청 실패: {e}"
    except Exception as e:
        return False, f"⚠️ 음성 인식 오류: {e}"

def display_speech_interface():
    """음성 인식 인터페이스를 표시합니다."""
    if st.button("🎤 음성으로 질문하기", key="speech_input"):
        with st.spinner("음성 입력을 기다리는 중..."):
            success, text = recognize_speech()
            
        if success:
            st.success(f"✅ 인식된 질문: {text}")
            st.session_state.user_input = text
        else:
            st.error(text)
