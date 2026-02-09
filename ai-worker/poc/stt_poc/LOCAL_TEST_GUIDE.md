# 온프레미스 STT (Whisper) 통합 테스트 가이드

이 가이드는 **온프레미스(로컬 서버) 환경**에서 Whisper STT 기능을 검증하기 위한 가이드입니다. 
로컬 PC 테스트와 도커 서버 테스트는 **서로 보완적인 관계**입니다.

---

## 📋 1. 테스트 이원화의 이유 (왜 두 번 하나요?)

사용하는 **모델(Whisper-Large-v3/Turbo)**은 로컬이나 도커나 동일합니다. 하지만 각 환경의 장점을 활용해 테스트합니다.

1.  **로컬 PC 테스트 (대상: 내 목소리/마이크)**
    *   **목적**: 내 목소리가 실제로 잘 들리고 인식되는지 **"정확도"**를 확인.
    *   **이유**: 도커 컨테이너는 내 PC 마이크에 직접 접근하기가 매우 까다롭기 때문에 로컬에서 직접 테스트합니다.
    *   **특이사항**: PC에 CUDA(GPU)가 없으면 **CPU로 자동 전환**되어 실행됩니다. (속도는 느리지만 정확도는 서버와 동일)

2.  **도커 서버 테스트 (대상: 하드웨어/GPU 가속)**
    *   **목적**: 실제 서버 환경에서 **"GPU 가속 속도"**가 얼마나 빠른지 확인.
    *   **이유**: 실제 서비스는 서버의 GPU를 사용하므로, 하드웨어 성능을 수치로 확인하기 위함입니다.
    *   **특이사항**: 마이크 대신 **샘플 음성 파일**을 사용하여 속도를 측정합니다.

---

## 📂 2. 테스트 파일 목록

### 🎤 A. 로컬 PC용 (마이크 정확도 테스트)
- `local_mic_test_whisper_large_v3_turbo.py`: **V3-Turbo** 모델 (현재 서비스 적용 모델)
- `local_mic_test_whisper_large_v3.py`: **Large-V3** 모델 (정확도 최우선 모델)

### 🐳 B. 도커 서버용 (GPU 가속/속도 테스트)
- `test_whisper_docker_gpu_v3_turbo.py`: **V3-Turbo** GPU 성능 확인
- `test_whisper_docker_gpu_v3.py`: **Large-V3** GPU 성능 확인

---

## 🚀 3. 테스트 실행 방법

### 1단계: 내 목소리 정확도 테스트 (로컬 PC)
PowerShell에서 아래 명령어 중 하나를 실행하세요. (약 30초간 녹음)

```powershell
cd c:\big20\git\Big20_aI_interview_project\ai-worker\stt_poc

# 현재 서비스 모델 테스트 (Turbo)
python local_mic_test_whisper_large_v3_turbo.py

# 고정밀 모델 테스트 (Large)
python local_mic_test_whisper_large_v3.py
```

### 2단계: 서버 GPU 가속 테스트 (도커)
PowerShell에서 아래 명령어를 입력하여 **서버 내부의 초고속 인식**을 확인하세요.

```powershell
# Turbo 모델 GPU 속도 및 정확도 확인
docker-compose exec media-server python /app/stt_poc/test_whisper_docker_gpu_v3_turbo.py

# Large-v3 모델 GPU 속도 및 정확도 확인
docker-compose exec media-server python /app/stt_poc/test_whisper_docker_gpu_v3.py
```

---

## 💡 4. 자주 묻는 질문 (FAQ)

**Q. 로컬 테스트에서 "GPU 인식 실패"가 떠요.**
A. **정상입니다.** Windows PC에 CUDA 라이브러리가 없기 때문입니다. 스크립트가 자동으로 **CPU로 전환**하여 인식을 완료하므로 정확도 테스트에는 문제가 없습니다.

**Q. 서버는 GPU인데 로컬은 왜 CPU인가요?**
A. 서버(도커)는 GPU 최적화 환경이 구축되어 있고, 로컬 PC는 개발 환경이기 때문입니다. **인식 결과(텍스트)는 장치와 상관없이 동일**하므로 안심하고 테스트하세요.

**Q. 가장 추천하는 모델은?**
A. **Whisper-Large-v3-Turbo**를 추천합니다. 정확도는 Large-v3와 거의 같으면서 속도는 3배 이상 빠릅니다.
