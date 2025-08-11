import os
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def test_openai_connection():
    """OpenAI API 연결 테스트"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI tutor for OPIc English speaking test."},
                {"role": "user", "content": "Hello! Can you help me practice English speaking?"}
            ],
            max_tokens=100
        )
        
        print("✅ OpenAI API 연결 성공!")
        print("🤖 AI 응답:", response.choices[0].message.content)
        return True
    except Exception as e:
        print("❌ OpenAI API 연결 실패:", str(e))
        return False

if __name__ == "__main__":
    test_openai_connection()
