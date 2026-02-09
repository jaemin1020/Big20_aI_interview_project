#!/usr/bin/env python3
# ============================================================
# EXAONE-3.5-7.8B-Instruct GGUF 모델 다운로드 스크립트
# ============================================================
# 파일명: download_exaone_model.py
# 목적: Hugging Face에서 EXAONE GGUF 모델을 자동으로 다운로드합니다.
# 실행: python download_exaone_model.py
# ============================================================

import os
import sys
from huggingface_hub import hf_hub_download

# ============================================================
# [Step 1] 다운로드 설정
# ============================================================
# Hugging Face 리포지토리 정보
REPO_ID = "bartowski/EXAONE-3.5-7.8B-Instruct-GGUF"  # GGUF 변환 버전
FILENAME = "EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"    # 4-bit 양자화 (약 4.7GB)

# 저장 경로 (Docker 컨테이너 내부 경로)
# 로컬에서 실행하는 경우 적절히 수정하세요
LOCAL_DIR = "/app/models"

# ============================================================
# [Step 2] 다운로드 디렉토리 생성
# ============================================================
print("=" * 80)
print("🚀 EXAONE-3.5-7.8B-Instruct GGUF 모델 다운로드 시작")
print("=" * 80)
print(f"📦 리포지토리: {REPO_ID}")
print(f"📄 파일명: {FILENAME}")
print(f"💾 저장 경로: {LOCAL_DIR}")
print("=" * 80)

# 디렉토리가 없으면 생성
if not os.path.exists(LOCAL_DIR):
    print(f"📁 디렉토리 생성 중: {LOCAL_DIR}")
    os.makedirs(LOCAL_DIR, exist_ok=True)

# ============================================================
# [Step 3] 모델 다운로드 실행
# ============================================================
try:
    print("\n⏳ 다운로드 시작... (약 4.7GB, 시간이 걸릴 수 있습니다)")
    print("   인터넷 속도에 따라 5~30분 소요될 수 있습니다.\n")
    
    # Hugging Face Hub에서 파일 다운로드
    # resume_download=True: 중단된 다운로드 재개 가능
    downloaded_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=LOCAL_DIR,
        local_dir_use_symlinks=False,  # 심볼릭 링크 대신 실제 파일 복사
        resume_download=True
    )
    
    print("\n" + "=" * 80)
    print("✅ 다운로드 완료!")
    print("=" * 80)
    print(f"📍 파일 위치: {downloaded_path}")
    
    # 파일 크기 확인
    file_size = os.path.getsize(downloaded_path)
    file_size_gb = file_size / (1024 ** 3)
    print(f"📊 파일 크기: {file_size_gb:.2f} GB")
    
    print("\n💡 다음 단계:")
    print("   1. 통합 테스트 실행: docker exec interview_worker python /app/CYJ/main_integrated_test.py")
    print("   2. 또는 직접 LLM 테스트: docker exec interview_worker python -c \"from utils.exaone_llm import get_exaone_llm; llm = get_exaone_llm(); print('LLM 로드 성공')\"")
    print("=" * 80)
    
except Exception as e:
    print("\n" + "=" * 80)
    print("❌ 다운로드 실패!")
    print("=" * 80)
    print(f"오류: {e}")
    print("\n💡 문제 해결:")
    print("   1. 인터넷 연결 확인")
    print("   2. Hugging Face Hub 계정이 필요한 경우: huggingface-cli login")
    print("   3. 디스크 공간 확인 (최소 5GB 필요)")
    print("   4. 수동 다운로드: https://huggingface.co/{REPO_ID}")
    print("=" * 80)
    sys.exit(1)
