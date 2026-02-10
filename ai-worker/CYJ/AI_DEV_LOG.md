# 🛡️ AI 면접 시스템 개발 및 트러블슈팅 일지 (Dev Log)

**작성일**: 2026년 2월 5일 ~ 현재
**작성자**: Project Big20 AI Team
**문서 설명**: 본 문서는 AI 면접 시스템 개발 과정에서 발생한 주요 에러와 이슈, 그리고 해결 과정을 체계적으로 정리한 **기술 회고록(Retrospective)**입니다.

---

## 1. 🏗️ 전체 프로젝트 로드맵 (Roadmap)

| 단계              | 파트명                   | 주요 목표                                                            | 상태                 |
| :---------------- | :----------------------- | :------------------------------------------------------------------- | :------------------- |
| **Phase 1** | **초기 환경 구축** | Python 환경, Docker, 필수 라이브러리(`mediapipe`, `opencv`) 설치 | ✅ 완료              |
| **Phase 2** | **Vision 모듈**    | 얼굴 랜드마크 추출, 실시간 시선/자세 추적, 감정 분석                 | ✅ 완료              |
| **Phase 3** | **UI/UX 고도화**   | 한국어 폰트 적용, 영점 조절 대시보드, 웹사이트 연동                  | ✅ 완료              |
| **Phase 4** | **정밀 튜닝**      | 감정 인식 민감도 조절, 모델 경량화                                   | ✅ 완료              |
| **Phase 5** | **시스템 통합**    | **TTS(말하기) + STT(듣기) + LLM(두뇌) + Vision(눈) 연결**      | **🔄 진행 중** |
| **Final**   | **최적화 및 배포** | 불필요한 파일 정리, Docker 이미지 최적화, 최종 배포                  | 📅 예정              |

---

## 2. 🚨 모듈별 트러블슈팅 로그 (Troubleshooting)

### 2.1. 👁️ Vision (영상 분석)

#### 🔴 Issue: MediaPipe 모델 파일 누락

* **발생일**: 2026-02-05
* **위치**: `vision.FaceLandmarker.create_from_options`
* **증상**: `RuntimeError: Unable to open file: face_landmarker.task`
* **원인**: 코드는 있는데 실제 학습된 모델 파일이 다운로드되지 않음.
* **해결**: `curl` 명령어로 구글 서버에서 모델 파일 다운로드 완료.

#### 🔴 Issue: IndentationError (들여쓰기 오류)

* **발생일**: 2026-02-06
* **위치**: `CV-V2-TASK.py` (Line 66)
* **증상**: `IndentationError: unexpected indent`
* **원인**: 코드 수정 중 복사 붙여넣기로 인해 파이썬 들여쓰기(Space 4칸)가 깨짐.
* **해결**: 코드 전체 재작성으로 들여쓰기 교정.

#### 🔴 Issue: 감정 인식 민감도 저하

* **발생일**: 2026-02-07
* **위치**: `CV_EMOTION_VERIFIER.py`
* **증상**: 슬픈 표정을 지어도 '평온(Neutral)'으로만 인식됨.
* **해결**: 가중치 적용(1.8배) 및 임계값 하향(0.25 -> 0.12)으로 튜닝 완료.

#### 🔴 Issue: DeepFace 실시간 렉 발생

* **발생일**: 2026-02-05
* **증상**: 화면이 뚝뚝 끊김 (0.5초 지연).
* **해결**: **하이브리드 아키텍처** 도입 (입장 시 DeepFace, 면접 중 MediaPipe 사용).

---

### 2.2. 🎙️ TTS (음성 합성 - 말하기)

#### 🔴 Issue: 'qwen_tts' 라이브러리 부재

* **발생일**: 2026-02-08
* **위치**: `CYJ/main_test.py`
* **증상**: `ModuleNotFoundError: No module named 'qwen_tts'`
* **원인**: Docker 컨테이너에 TTS 라이브러리가 설치되지 않음.
* **해결**: `pip install qwen-tts` 실행 및 **Supertonic2 모델로 전환** 결정.

#### 🔴 Issue: Supertonic2 모델 파일 경로 혼동

* **발생일**: 2026-02-10
* **증상**: 파일명이 `tts_supertonic.py`인지 `tts_supertonic2.py`인지 혼동.
* **해결**: `ai-worker/poc/tts_poc/tts_supertonic2.py`가 최신 파일임을 확인하고 정착.

---

### 2.3. 👂 STT (음성 인식 - 듣기)

#### 🔴 Issue: Whisper STT 환각 현상

* **발생일**: 2026-02-09
* **위치**: 프론트엔드 마이크 테스트
* **증상**: 아무 말 안 했는데 "한글 자막..." 같은 엉뚱한 텍스트 출력.
* **원인**: 오디오 입력이 없거나 너무 작을 때 Whisper가 소음을 말소리로 착각.
* **해결**: 마이크 입력 게인 조절 및 입력 감지 로직 개선.

#### 🔴 Issue: webm 파일 형식 오류

* **발생일**: 2026-02-09
* **위치**: `ai-worker/tasks/stt.py`
* **증상**: `ValueError: Soundfile is either not in the correct format...`
* **원인**: Whisper는 wav를 좋아하는데 브라우저는 webm을 보냄.
* **해결**: `ffmpeg` (또는 pydub)를 사용하여 **webm -> wav 변환 로직** 추가.

---

### 2.4. 🧠 LLM (AI 두뇌)

#### 🔴 Issue: EXAONE 모델 파일 누락

* **발생일**: 2026-02-08
* **위치**: `utils/exaone_llm.py`
* **증상**: `FileNotFoundError: /app/models/EXAONE...gguf`
* **해결**: Hugging Face에서 GGUF 모델 다운로드 스크립트 작성 및 실행.

#### 🔴 Issue: llama.cpp 아키텍처 미지원

* **발생일**: 2026-02-08
* **증상**: `unknown model architecture: 'exaone'`
* **해결**: `llama-cpp-python` 라이브러리 버전을 최신으로 업그레이드하여 해결.

---

### 2.5. 🌐 Backend & System (웹사이트/서버)

#### 🔴 Issue: 백엔드 API 404 에러

* **발생일**: 2026-02-09
* **위치**: `backend-core/routes/auth.py`
* **증상**: 회원가입 시 404 Not Found.
* **원인**: 라우터 Prefix 설정 불일치 (`/auth` 중복).
* **해결**: Prefix 제거로 경로 매칭 수정.

#### 🔴 Issue: 데이터베이스 컬럼 누락

* **발생일**: 2026-02-08
* **위치**: `tasks/vision.py`
* **증상**: `psycopg.errors.UndefinedColumn: company_id does not exist`
* **해결**: DB 스키마 마이그레이션 필요 (임시로 코드에서 해당 컬럼 참조 제외).

---

## 3. 📝 유지보수 및 가이드 (Maintenance)

### 💡 감정 인식 튜닝 방법

* **파일**: `CV-V2-TASK.py` (또는 `tasks/vision.py`)
* **조절**: `brow_down > 0.35` 수치를 낮추면(0.2) 예민해지고, 높이면(0.5) 둔해집니다.

### 💡 실제 목소리 테스트 방법

* **경로**: `/app/ai-worker/poc/tts_poc/tts_supertonic2.py` 실행
* **결과**: `outputs/*.wav` 파일 생성됨.
