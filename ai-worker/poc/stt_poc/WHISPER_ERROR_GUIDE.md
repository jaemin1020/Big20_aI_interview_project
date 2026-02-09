# 🥊 Whisper STT 에러 & 해결 백과사전 (POC 정밀 가이드)

본 문서는 `Whisper Large-v3`와 `Turbo` 모델을 로컬/컨테이너 환경에서 운영하며 발생하는 모든 기술적 문제와 해결책을 기록합니다. **(Assistant 지속 최신화 중)**

---

## 1. 🚨 치명적 에러 (실행 불가 관련)

| 에러 메시지 | 발생 원인 | 해결 방법 |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'faster_whisper'` | 파이썬 환경에 위스퍼 엔진 라이브러리가 설치되지 않음. | `pip install faster-whisper` 실행. (가상환경 사용 시 해당 환경 활성화 확인) |
| `ModuleNotFoundError: No module named 'torch'` | 딥러닝 핵심 라이브러리인 PyTorch가 누락됨. | `pip install torch` 실행. (GPU 사용 시 CUDA 버전에 맞는 토치 설치 권장) |
| `Incompatible Model Name: ...` | `WhisperModel()` 호출 시 오타가 있거나 존재하지 않는 모델명을 사용함. | `large-v3`, `large-v3-turbo`, `base`, `medium` 등 정확한 모델명 확인 필수. |
| `FileNotFoundError: recorded_audio.wav` | 녹음 단계에서 오류가 발생하여 분석할 파일이 생성되지 않음. | 마이크 장치 연결 상태 확인 및 `sounddevice` 라이브러리 권한 확인. |

---

## 2. 🛠️ 리소스 및 하드웨어 에러

| 에러 메시지 | 발생 원인 | 해결 방법 |
| :--- | :--- | :--- |
| `CUDA Out of Memory (OOM)` | 그래픽 카드 메모리(VRAM)가 대형 모델을 감당하지 못함. | 1. `compute_type="int8"`로 설정 (품질 희생 없이 메모리 절반 로드)<br>2. `large-v3` 대신 `turbo` 또는 `small` 모델 사용 |
| `SoX could not be found!` | 시스템에 음성 파일 처리 도구인 `SoX`가 설치되지 않음. | **로컬**: SoX 설치파일 다운로드<br>**도커**: `apt-get install -y sox` 실행 |
| `FlashAttention2... not installed` | 고성능 가속 기술을 켜려 했으나 관련 라이브러리가 없음. | 1. `pip install flash-attn`<br>2. 코드에서 `attn_implementation="eager"`로 변경하여 회피 |

---

## 3. 📉 성능 및 정확도 관련 에러

| 이상 현상 | 발생 원인 | 해결 방법 |
| :--- | :--- | :--- |
| **인식 속도가 너무 느림** | CPU 모드로 대형 모델(`large-v3`)을 돌리고 있음. | 1. GPU 모드 전환 (`device="cuda"`) <br>2. `large-v3-turbo` 모델로 즉시 변경 (8배 이상 빠름) |
| **정확도가 비정상적으로 낮음** | 마이크 감도가 너무 낮거나 주변 소음이 큼. | 1. 마이크 레벨 체크 (최대 0.1 이상 권장)<br>2. `vad_filter=True` 옵션 활성화로 무음 제거 |
| **첫 실행 시 프리징(멈춤) 현상** | 모델 다운로드(3~5GB)가 백그라운드에서 진행 중. | 터미널을 중단하지 말고 다운로드가 완료될 때까지 대기. |

---

## 🧐 핵심 차이점 요약 (Large-v3 vs Turbo)

*   **Large-v3**: 완벽주의자. 하지만 걸음걸이가 느림. (정교한 인터뷰 분석용)
*   **Turbo**: 마하의 속도. 실전 지향형. 정확도는 99% 유지. (실시간 가답 면접 대응용)

**💡 팁**: 새로운 에러가 발생하여 저에게 질문하시면, 그 즉시 이 문서에 최신 정보를 추가하겠습니다.
