"""
AI 모델 인터페이스 - 로컬/API 모두 지원
"""
import streamlit as st
import os
from typing import Optional

# 환경 변수로 모델 타입 설정 (나중에 API로 쉽게 변경 가능)
MODEL_TYPE = os.getenv("MODEL_TYPE", "local")  # "local" or "api"
API_KEY = os.getenv("OPENAI_API_KEY", "")

def load_model():
    """
    모델을 로드합니다. 
    로컬 모델 또는 API 설정에 따라 적절한 인터페이스를 반환합니다.
    """
    if MODEL_TYPE == "api":
        return _load_api_client()
    else:
        return _load_local_model()

@st.cache_resource
def _load_local_model():
    """로컬 FLAN-T5 모델을 로드합니다."""
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
        tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
        model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")
        return {
            "type": "local",
            "pipeline": pipeline("text2text-generation", model=model, tokenizer=tokenizer)
        }
    except Exception as e:
        st.error(f"로컬 모델 로딩 중 오류: {e}")
        return None

def _load_api_client():
    """API 클라이언트를 설정합니다. (향후 OpenAI/다른 API 연동용)"""
    return {
        "type": "api",
        "api_key": API_KEY,
        "model": "gpt-3.5-turbo"  # 나중에 사용할 모델
    }

def generate_response(model_interface: Optional[dict], prompt: str, max_tokens: int = 150) -> str:
    """
    통합 응답 생성 함수 - 로컬/API 모두 지원
    
    Args:
        model_interface: 모델 인터페이스 (로컬 파이프라인 또는 API 설정)
        prompt: 완성된 프롬프트
        max_tokens: 최대 토큰 수
    
    Returns:
        생성된 응답
    """
    if model_interface is None:
        return "❌ 모델이 로드되지 않았습니다."
    
    if model_interface["type"] == "api":
        return _generate_api_response(model_interface, prompt, max_tokens)
    else:
        return _generate_local_response(model_interface, prompt, max_tokens)

def _generate_local_response(model_interface: dict, prompt: str, max_tokens: int) -> str:
    """로컬 모델로 응답 생성"""
    try:
        pipeline_model = model_interface["pipeline"]
        response = pipeline_model(prompt, max_new_tokens=max_tokens, do_sample=True, temperature=0.7)
        answer = response[0]["generated_text"].replace(prompt, "").strip()
        
        if not answer:
            answer = "🤖 죄송해요, 답변을 생성하지 못했어요. 질문을 더 구체적으로 해주세요!"
        
        return answer
    except Exception as e:
        return f"❌ 로컬 모델 응답 생성 오류: {e}"

def _generate_api_response(model_interface: dict, prompt: str, max_tokens: int) -> str:
    """API로 응답 생성 (향후 구현 예정)"""
    # TODO: OpenAI API 또는 다른 API 연동
    return "🚧 API 모드는 아직 구현 중입니다. 현재는 로컬 모델을 사용해주세요."
