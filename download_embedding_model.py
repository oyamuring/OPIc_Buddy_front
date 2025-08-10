# 임베딩 모델 다운로드 스크립트
from transformers import AutoModel, AutoTokenizer
import os

# macOS/Linux 환경에 맞게 경로 수정
model_cache_path = os.path.expanduser("~/models/huggingface/OPIc_Buddy/model")

# 다운로드 디렉토리 생성
os.makedirs(model_cache_path, exist_ok=True)

print(f"임베딩 모델 저장 경로: {model_cache_path}")

# 임베딩 모델 다운로드
model_id = "intfloat/e5-base-v2"
print(f"임베딩 모델 {model_id} 다운로드 시작...")

try:
    # 토크나이저 다운로드
    print("임베딩 모델 토크나이저 다운로드 중...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_id, 
        cache_dir=model_cache_path
    )
    
    # 모델 다운로드
    print("임베딩 모델 다운로드 중... (시간이 오래 걸릴 수 있습니다)")
    model = AutoModel.from_pretrained(
        model_id, 
        cache_dir=model_cache_path
    )
    
    print(f"✅ e5-base-v2 임베딩 모델 다운로드 및 저장 완료: {model_cache_path}")
    
    # 다운로드된 파일들 확인
    print("\n다운로드된 파일들:")
    for root, dirs, files in os.walk(model_cache_path):
        for file in files:
            if "e5-base-v2" in root.lower():  # e5 모델 파일들만 표시
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB 단위
                print(f"  {file}: {file_size:.2f} MB")
                
except Exception as e:
    print(f"❌ 임베딩 모델 다운로드 중 오류 발생: {e}")
