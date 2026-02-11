# 🛡️ AI 면접 시스템 개발 및 트러블슈팅 일지 (Dev Log)

**작성일**: 2026년 2월 5일 ~ 2월 10일 (최종 업데이트)
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
* **해결**: `from db import ...`로 수정하여 해결.

#### 🔴 Issue: ImportError (ResumeSectionEmbedding 미정의) (NEW 2026-02-10)

* **발생일**: 2026-02-10
* **위치**: `ai-worker/tasks/resume_embedding.py`
* **증상**: `ImportError: cannot import name 'ResumeSectionEmbedding' from 'db'`
* **원인**: `resume_embedding.py` 코드는 작성되었으나, 정작 DB 모델 파일(`db.py`)에 해당 테이블 정의가 누락됨.
* **해결**: `db.py`에 `ResumeSectionType` Enum과 `ResumeSectionEmbedding` 테이블 클래스 추가 정의.
#### ℹ️ Info: AI Model Loading Strategy (Lazy Loading)

* **질문**: "모델도 처음에 로딩 되게 설계 안 되어 있니?"
* **현황**: 현재 `ResumeEmbedder`와 `STT` 모델은 **Lazy Loading (지연 로딩)** 방식을 사용 중.
    * **이유**: 서버 시작 시점에 모든 모델(LLM, Vision, TTS, STT, Embedding)을 한 번에 다 올리면 메모리 부족(OOM) 및 컨테이너 기동 실패 위험이 높음.
    * **특징**: 첫 번째 요청(First Request) 처리 시 모델을 메모리에 올리므로, **첫 요청은 평소보다 수 초~수십 초 더 걸릴 수 있음.** (정상 동작)

---
#### 🔴 Issue: 감정 인식 민감도 저하

* **발생일**: 2026-02-07
* **위치**: `CV_EMOTION_VERIFIER.py`
* **증상**: 슬픈 표정을 지어도 '평온(Neutral)'으로만 인식됨.
* **해결**: 가중치 적용(1.8배) 및 임계값 하향(0.25 -> 0.12)으로 튜닝 완료.

#### 🔴 Issue: DeepFace 실시간 렉 발생 및 기술 스택 변경 (MediaPipe 전환)

* **발생일**: 2026-02-05
* **증상**: DeepFace 사용 시 화면이 0.5초 이상 뚝뚝 끊기는 지연(Lag) 발생. 실시간 면접 피드백 불가능.
* **분석결과**:
    * **DeepFace**: 정확도는 높으나 무겁고 느림. (Batch 처리에는 적합하나 실시간 스트리밍 부적합)
    * **MediaPipe**: 정확도는 준수하며 매우 가볍고 빠름. (초당 30프레임 이상 처리 가능)
* **최종결정**: **DeepFace 사용 전면 폐기**. MediaPipe 단일 모델로 통합하여 실시간성 확보. **(사용 안 함으로 확정)**

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

#### 🔴 Issue: Faster-Whisper 무단 도입으로 인한 충돌 (NEW 2026-02-10)

* **발생일**: 2026-02-10
* **위치**: `ai-worker/tasks/stt.py`
* **증상**: `ModuleNotFoundError: No module named 'faster_whisper'`
* **원인**: **협의되지 않은 기술 스택(Faster-Whisper)을 AI가 임의로 도입**하여, Docker 이미지에 해당 라이브러리가 없는 상태임에도 코드를 변경함.
* **해결**: 
    1. 사용자 항의 수용 및 즉시 사과.
    2. 코드를 **어제 작업했던 `transformers` + `Whisper-Turbo` 원본 방식**으로 원상복구.
    3. Docker 재빌드 없이 즉시 실행 가능한 상태로 되돌림.

---

### 2.4. 🧠 LLM & Backend (AI 두뇌 및 서버)

#### 🔴 Issue: 백엔드 API Rounter 충돌 (404)

* **발생일**: 2026-02-09
* **위치**: `backend-core/routes/auth.py`
* **증상**: 회원가입 시 404 Not Found.
* **해결**: 라우터 Prefix 중복 제거.

#### 🔴 Issue: Resume 업로드 경로 불일치 (CORS) (NEW 2026-02-10)

* **발생일**: 2026-02-10
* **위치**: `frontend/src/api/interview.js`
* **증상**: `POST /api/resumes/upload 404 Not Found`
* **원인**: 백엔드는 `/resumes/upload`인데 프론트엔드가 `/api`를 붙여서 호출함. (404가 CORS처럼 보임)
* **해결**: `/api` Prefix 제거하여 경로 일치시킴.

#### 🔴 Issue: Structured Data JSON Parsing Error (Persistent)

* **발생일**: 2026-02-10
* **위치**: `backend-core/main.py`
* **증상**: `AttributeError: 'str' object has no attribute 'get'` 에러가 코드 수정 후에도 지속됨.
* **원인**: 
    1. **DB 데이터 오염**: 일부 이력서 데이터의 `structured_data` 컬럼이 JSONB가 아닌 문자열로 저장됨.
    2. **컨테이너 캐싱**: `docker-compose restart`만으로는 코드 변경 사항(JSON 파싱 로직)이 즉시 반영되지 않고 구버전 코드가 실행됨.
* **해결**: 
    1. `main.py`에 문자열을 딕셔너리로 변환하는 안전 장치(`json.loads`) 및 주석 추가.
    2. `docker-compose up -d --force-recreate --build backend` 명령어로 컨테이너를 강제 재생성하여 코드 반영.
    3. [추가] **이중 인코딩(Double Encoding)** 된 JSON 문자열 케이스 발견되어, 재귀적 파싱 로직 적용.
    4. [추가] `target_position` 필드가 문자열("Unknown")로 들어올 때 `.get()` 호출로 인한 `AttributeError` 해결 (타입 체크 로직 추가).

---
