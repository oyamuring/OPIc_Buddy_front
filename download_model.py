# generator모델 다운로드 스크립트
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
import shutil

# macOS/Linux 환경에 맞게 경로 수정
model_cache_path = os.path.expanduser("~/models/huggingface/OPIc_Buddy/model")

# 다운로드 디렉토리 생성
os.makedirs(model_cache_path, exist_ok=True)

print(f"모델 저장 경로: {model_cache_path}")

# 모델 다운로드
model_id = "microsoft/phi-1_5"
print(f"모델 {model_id} 다운로드 시작...")

try:
    # 토크나이저 다운로드
    print("토크나이저 다운로드 중...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        force_download=True,
        cache_dir=model_cache_path
    )
    
    # 모델 다운로드
    print("모델 다운로드 중... (시간이 오래 걸릴 수 있습니다)")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        force_download=True,
        cache_dir=model_cache_path
    )
    
    print(f"✅ phi-1.5 모델 다운로드 및 저장 완료: {model_cache_path}")
    
    # 다운로드된 파일들 확인
    print("\n다운로드된 파일들:")
    for root, dirs, files in os.walk(model_cache_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB 단위
            print(f"  {file}: {file_size:.2f} MB")
            
except Exception as e:
    print(f"❌ 모델 다운로드 중 오류 발생: {e}")
