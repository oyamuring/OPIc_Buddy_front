"""
음성 인식 관련 유틸리티
"""
import streamlit as st
import speech_recognition as sr

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
        return False, f"❌ 음성 인식 중 오류 발생: {e}"

def display_speech_interface():
    """
    사이드바에 음성 입력 인터페이스를 표시합니다.
    
    Returns:
        str or None: 인식된 음성 텍스트 또는 None
    """
    with st.sidebar:
        st.header("🎤 음성 입력")
        if st.button("🎙️ 마이크로 답변하기"):
            success, result = recognize_speech()
            
            if success:
                st.success(f"🗣️ 인식된 질문: {result}")
                return result
            else:
                st.error(result)
                return None
    
    return None
