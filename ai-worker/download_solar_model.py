import os
import sys

# huggingface_hub 설치 확인 및 설치
try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("huggingface_hub 모듈이 없습니다. 설치를 시도합니다...")
    os.system(f"{sys.executable} -m pip install huggingface_hub")
    from huggingface_hub import hf_hub_download

# 설정
REPO_ID = "TheBloke/Solar-10.7B-Instruct-v1.0-GGUF"
FILENAME = "solar-10.7b-instruct-v1.0.Q8_0.gguf"
SAVE_DIR = "./models"

# 디렉토리 생성
os.makedirs(SAVE_DIR, exist_ok=True)

print("="*50)
print(f"📥 다운로드 시작: {FILENAME}")
print(f"🔗 저장소: {REPO_ID}")
print(f"📂 저장 위치: {os.path.abspath(SAVE_DIR)}")
print("⚠️ 파일 크기가 약 11GB입니다. 네트워크 환경에 따라 10분 이상 소요될 수 있습니다.")
print("="*50)

try:
    file_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=SAVE_DIR,
        local_dir_use_symlinks=False,  # 실제 파일 다운로드 (심볼릭 링크 X)
        resume_download=True  # 끊기면 이어받기
    )
    print("\n✅ 다운로드 완료!")
    print(f"파일 경로: {file_path}")
except Exception as e:
    print(f"\n❌ 다운로드 실패: {e}")
    print("인터넷 연결을 확인하거나, 잠시 후 다시 시도해주세요.")
