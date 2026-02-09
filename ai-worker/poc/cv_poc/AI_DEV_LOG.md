# 🛡️ AI 면접 시스템 개발 및 트러블슈팅 일지 (Dev Log)

**작성일**: 2026년 2월 5일 ~ 현재  
**작성자**: Project Big20 AI Team  
**문서 설명**: 본 문서는 AI 면접 시스템 개발 과정에서 발생한 주요 에러와 이슈, 그리고 해결 과정을 단계별로 상세히 기록한 **기술 회고록(Retrospective)**입니다.

---

## 1. 🏗️ 전체 시스템 개발 단계 (Milestones)

| 단계 | 파트명 | 주요 목표 | 상태 |
| :--- | :--- | :--- | :--- |
| **Phase 1** | 초기 환경 구축 | Python 환경 설정 및 필수 라이브러리(`mediapipe`, `opencv`) 설치 | ✅ 완료 |
| **Phase 2** | 핵심 엔진 구현 | 얼굴 랜드마크 추출 및 실시간 시선/자세 추적 로직 개발 | ✅ 완료 |
| **Phase 3** | UI/UX 고도화 | 한국어 폰트 적용 및 사용자 친화적 대시보드(영점 조절) 구현 | ✅ 완료 |
| **Phase 4** | 정밀 검증 (Tuning) | 감정 인식(슬픔/놀람) 민감도 최적화 및 평가 로직 확정 | ✅ 완료 |
| **Phase 5** | **시스템 통합 (Integration)** | **TTS/STT/Vision/LLM 모듈 연결 및 파이프라인 흐름 검증** | **🔄 진행 중** |
| **Final** | 결과 리포트 | JSON 데이터 저장 및 종합 성적표 산출 기능 탑재 | ✅ 완료 |

---

## 2. 🚨 에러 및 이슈 히스토리 (Troubleshooting)

### 🔴 Issue #1: MediaPipe 모델 파일 누락
*   **발생 위치**: [Phase 1] 초기 실행 단계 > 모델 로드(`vision.FaceLandmarker.create_from_options`)
*   **증상/에러**: `RuntimeError: Unable to open file: face_landmarker.task`
*   **원인 분석**: 코드 상에서는 `model_path = 'face_landmarker.task'`로 파일을 찾고 있었으나, 실제로 해당 경로에 구글의 학습된 모델 파일이 다운로드되어 있지 않았음.
*   **해결 방법**: 터미널에서 `curl` 명령어를 사용하여 구글 서버로부터 모델 파일을 직접 다운로드함.
    ```powershell
    curl -L -o face_landmarker.task https://storage.googleapis.com/...
    ```

### 🔴 Issue #2: IndentationError (들여쓰기 오류)
*   **발생 위치**: [Phase 2] 코드 수정 단계 > `replace_file_content` 툴 사용 후
*   **증상/에러**: 
    ```python
    File "CV-V2-TASK.py", line 66
        landmarks = result.face_landmarks[0]
    IndentationError: unexpected indent
    ```
*   **원인 분석**: AI가 코드를 수정하는 과정에서 `if result.face_landmarks:` 조건문 아래의 코드를 붙여넣을 때, 파이썬의 문법 규칙인 들여쓰기(Space 4칸)가 어긋남.
*   **해결 방법**: 코드를 전면 재작성(`write_to_file`)하여 들여쓰기 레벨을 완벽하게 맞춤.

### 🔴 Issue #3: 감정 인식 민감도 저하 (슬픔/놀람 인식 불가)
*   **발생 위치**: [Phase 4] 정밀 검증 단계 > `CV_EMOTION_VERIFIER.py` 테스트 중
*   **증상**: 사용자가 의도적으로 슬픈 표정을 지어도 AI가 이를 감지하지 못하고 계속 '평온(Neutral)'으로만 판정함. 행복(Happy)은 잘 인식됨.
*   **원인 분석**: 
    1.  슬픔(`mouthFrown`)의 랜드마크 변화량이 행복(`mouthSmile`)에 비해 상대적으로 미미함.
    2.  판정 문턱값(Threshold)이 0.25로 너무 높게 설정되어 있었음.
*   **해결 방법**: '밸런스 튜닝' 적용
    1.  **가중치 증폭**: `sad_score` 산출 시 입력값에 **1.8배**를 곱함.
    2.  **임계값 하향**: 문턱값을 0.25 → **0.12**로 대폭 낮춤. -> **[해결 완료]**

### 🔴 Issue #4: DeepFace 모델의 실시간성 한계
*   **발생 위치**: [Phase 1] 기획 및 초기 테스트 단계
*   **증상**: `DeepFace` 라이브러리를 사용했을 때 프레임 처리 속도가 0.5초 이상 지연되어 화면이 뚝뚝 끊김(Lag).
*   **원인 분석**: DeepFace의 VGG-Face 모델은 무거운 연산을 수행하므로 실시간(30FPS) 추론에는 부적합함.
*   **해결 방법 (아키텍처 변경)**:
    - **Before**: DeepFace + MediaPipe 동시 사용
    - **After**: **하이브리드 아키텍처** 도입
        - 입장 시(1회): DeepFace (본인 인증, 느려도 됨)
        - 면접 중(실시간): MediaPipe (태도 분석, 매우 빠름)

---

### 🔴 Issue #5: [TTS 통합] 'qwen_tts' 라이브러리 부재로 인한 Import Error
*   **발생 위치**: [Phase 5] 시스템 통합 단계 > `CYJ/main_test.py` 실행 시
*   **에러 메시지**: `ModuleNotFoundError: No module named 'qwen_tts'`
*   **발생 상황**: 온프레미스 AI 워커 컨테이너 내부에서 TTS 모델(`Qwen3-TTS-12Hz-0.6B-CustomVoice`)을 호출하려 했으나, 해당 파이썬 패키지가 설치되어 있지 않음이 발견됨.
*   **원인 분석**: 
    1.  이전 작업 세션에서 `qwen_tts`를 임시로 설치했으나, 도커 이미지를 리빌드하거나 컨테이너를 재생성하는 과정에서 휘발되었을 가능성.
    2.  또는 로컬 환경과 도커 환경의 혼동으로 도커 내부에 실제로는 설치되지 않았던 상태.
*   **임시 조치**: **Mock-Up 전략 사용**
    *   라이브러리가 없을 경우 에러를 뱉고 죽는 대신, `WARNING` 로그를 출력하고 **가짜 오디오(Sine Wave Beep)**를 생성하도록 `tts_service.py` 로직 수정.
    *   이를 통해 파이프라인의 뒷단(파일 생성 확인, API 응답 등) 검증을 멈춤 없이 진행함.
*   **해결 방법**: `docker exec`를 통해 컨테이너 내부에 `pip install qwen-tts` 직접 실행 완료. ✅

### 🔴 Issue #6: [TTS 코드] `NameError: name 'torch' is not defined`
*   **발생 위치**: `CYJ/tts_service.py` 내 `get_tts_model` 함수
*   **증상**: 모델 로딩 중 `torch.bfloat16` 호출 시 `torch` 모듈이 정의되지 않았다는 에러 발생.
*   **원인**: 파일 상단에 `import torch`가 누락됨.
*   **해결**: `import torch` 및 `import sys` 추가 완료. ✅

### 🟡 Issue #7: [시스템 환경] `sox` 및 `flash-attn` 부재 (경고)
*   **증상**: `qwen-tts` 실행 시 `SoX could not be found!` 및 `flash-attn is not installed` 경고 출력.
*   **영향**: `sox`는 오디오 처리에 필요할 수 있으며, `flash-attn`은 추론 속도 최적화에 사용됨.
*   **현재 상태**: 경고만 출력될 뿐, **TTS 음성 생성은 정상 작동함**. (PyTorch 전용 모드 사용)
*   **향후 조치**: 필요 시 `apt-get install sox` 실행 예정.

### [Issue #8] StyleTTS2 & Qwen3-TTS 의존성 충돌 및 로딩 실패 (해결됨)
- **현상**: `styletts2` 패키지 설치 후 `qwen-tts`가 `transformers` 버전 충돌로 임포트 안 됨. 또한 StyleTTS2는 PyTorch 2.6+에서 `WeightsUnpickler` 에러 발생.
- **원인**: 패키지간 요구하는 `transformers` 버전 상이, PyTorch 보안 설정(`weights_only`) 변경.
- **해결**: 
  1. `qwen-tts`를 `--force-reinstall`하여 의존성 자동 복구.
  2. `torch.load`를 monkey-patch하여 `weights_only=False` 강제 적용 (StyleTTS2용).
  3. 최종적으로는 더 안정적이고 한국어를 공식 지원하는 `Supertonic 2`로 전환 제안.

### [Issue #9] Supertonic 2 한국어 TTS 구현 및 모델 초기화 (성공)
- **현상**: 사용자가 다운로드한 ONNX 파일과 `supertonic` pip 패키지 API 불일치.
- **원인**: 공식 패키지는 `synthesize` 메서드와 특정 데이터 구조(`voice_style`)를 사용함.
- **해결**: 
  1. `pip install supertonic` 설치.
  2. 공식 GitHub(`supertone-inc/supertonic`) 예제 기반으로 `tts_supertonic.py` 재작성.
  3. `auto_download=True`를 통해 공식 한국어 지원 모델(v1.6.0) 자동 캐싱.
  4. 한국어 발화 성공 (약 1초 내 생성 완료).

### [Issue #10] Docker 컨테이너 재시작으로 TTS 패키지 및 생성 파일 소실 (해결됨)
- **현상 (2026-02-08)**: 
  - 사용자가 `docker cp`로 TTS 결과 파일을 복사하려고 했으나 "파일이 없다"는 오류 발생.
  - 확인 결과 컨테이너가 재시작되어 `/app/stt_poc/outputs/` 폴더가 비어 있음.
  - `pip install supertonic`으로 설치한 패키지들도 모두 사라짐.
- **원인**: 
  - Docker 컨테이너 내부의 **비영구 저장소** 특성으로, 컨테이너 재시작 시 설치한 패키지와 생성 파일이 모두 휘발됨.
  - `pip install`로 설치한 패키지는 컨테이너 재빌드 시에만 유지됨 (Dockerfile 또는 requirements.txt 필요).
- **해결 (즉시 조치)**:
  1. 패키지 재설치: `docker exec interview_worker pip install supertonic qwen-tts -q`
  2. TTS 테스트 재실행:
     - Supertonic 2: `docker exec interview_worker python /app/stt_poc/tts_supertonic.py`
     - Qwen3-TTS: `docker exec interview_worker python /app/stt_poc/tts_qwen3.py`
  3. 생성 즉시 파일 복사:
     ```powershell
     docker cp interview_worker:/app/stt_poc/outputs/supertonic_korean_test.wav .
     docker cp interview_worker:/app/stt_poc/outputs/qwen3_test_output.wav .
     ```
- **해결 (영구적)**:
  - **방법 1 (권장)**: `requirements.txt`에 `supertonic`와 `qwen-tts` 추가 후 Docker 이미지 재빌드
  - **방법 2**: Docker Compose의 `volumes` 설정으로 `/app/stt_poc/outputs/`를 호스트와 마운트하여 영구 저장
  - **방법 3**: 테스트 후 즉시 `docker cp`로 로컬로 복사하는 습관 들이기
- **재발 방지**: 
  - 중요한 TTS 생성 파일은 **즉시 로컬로 복사**할 것.
  - 컨테이너 재시작 전 출력 파일을 확인할 것.



## 3. 📝 유지보수 가이드 (Maintenance Guide)

### 💡 특정 감정이 너무 잘 뜨거나 안 뜰 때
*   **수정 파일**: `CV-V2-TASK.py` 내 `[Step 7] 감정 분석` 파트
*   **방법**: `if brow_down > 0.35:` 부분의 숫자를 조절하세요.
    - 숫자를 **낮추면** 더 예민해집니다. (0.35 -> 0.2)
    - 숫자를 **높이면** 더 둔해집니다. (0.35 -> 0.5)

### 💡 리포트 점수 배점 변경
*   **수정 파일**: `CV-V2-TASK.py` 상단 `[Step 1] 사용자 설정` 파트
*   **방법**: `WEIGHT_CONFIDENCE` 등의 변수 값을 수정하세요. (단, 총합은 1.0이 되도록 권장)

### 💡 실제 목소리 재생
*   이제 라이브러리 설치와 코드 수정이 완료되어 Mock 모드 대신 **실제 음성 생성이 가능**합니다.
*   생성된 파일 경로: `/app/CYJ/outputs/test_interview_XXXXX.wav`
