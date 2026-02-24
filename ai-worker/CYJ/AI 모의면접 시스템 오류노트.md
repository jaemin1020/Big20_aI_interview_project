# 🛡️ AI 면접 시스템 개발 및 트러블슈팅 일지 (Dev Log)

**작성일**: 2026년 2월 5일 ~ 2월 13일 (최종 업데이트)
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
#### 🔴 Issue: MediaPipe 라이브러리 누락 (Web 통합 단계) (NEW 2026-02-12)

* **발생일**: 2026-02-12
* **위치**: `media-server/main.py`
* **증상**: `ModuleNotFoundError: No module named 'mediapipe'`
* **원인**: PoC 로직을 `media-server`에 이식했으나, Docker 빌드 설정 파일(`requirements.txt`)에 `mediapipe` 패키지가 누락됨.
* **해결**: `media-server/requirements.txt`에 `mediapipe==0.10.11` 추가 후 Docker 재빌드.

---

### 2.3. 👂 STT (음성 인식 - 듣기) (보강)

#### 🔴 Issue: STT 코드 파손 및 IndentationError (NEW 2026-02-12)

* **발생일**: 2026-02-12
* **위치**: `ai-worker/tasks/stt.py`
* **증상**: `IndentationError: unexpected indent` 및 서버 기동 실패.
* **원인**: 코드 수정 과정에서 AI 에이전트의 실수로 파일 중간에 JSON 형식의 메타데이터 조각이 삽입되어 파이썬 문법이 파손됨.
* **해결**: 파손된 코드 조각을 제거하고, `load_stt_pipeline` 등 함수명 불일치 및 정의되지 않은 변수 오류를 수정하여 복구 완료.

---

### 2.5. 🎨 Frontend (사용자 화면) (NEW 2026-02-12)

#### 🔴 Issue: 마이크 권한 차단 오인 에러 (JS Runtime Error)

* **발생일**: 2026-02-12
* **위치**: `frontend/src/pages/setup/EnvTestPage.jsx` (initAudio 함수)
* **증상**: `TypeError: Cannot set properties of undefined (setting 'onaudioprocess')`. 마이크 권한을 허용했음에도 "마이크 접근이 차단됨" 메시지 출력.
* **원인**: 마이크 입력 시각화를 위한 `javascriptNode`가 선언만 되고 `createScriptProcessor`로 생성되지 않은 상태에서 속성을 설정하려다 에러 발생. `try...catch`문이 이 에러를 마이크 권한 실패로 오인하여 사용자에게 잘못된 안내를 함.
* **해결**: `audioContext.createScriptProcessor`를 통해 노드를 정상 생성하고 `destination`에 연결하는 로직 추가.

---

## 3. 📅 2026-02-13 작업 일지 — WebRTC 영상 분석 연동 디버깅 (대형 세션)

> **작업 목표**: WebRTC를 통해 클라이언트(브라우저)에서 미디어 서버로 실시간 영상/음성 스트림을 전송하고, 서버에서 MediaPipe 기반 영상 분석(시선, 자세, 미소, 감정)이 정상 동작하여 점수를 계산하도록 하는 것.

---

### 3.1. 🔌 WebRTC 연결 (Media Server ↔ Frontend)

#### 🔴 Issue #1: SDP 파싱 에러 — `Failed to parse SessionDescription`

* **발생일**: 2026-02-13
* **위치**: `frontend/src/App.jsx` (WebRTC 연결 시)
* **증상**: 브라우저 콘솔에 `Uncaught DOMException: Failed to execute 'setRemoteDescription' on 'RTCPeerConnection': Failed to parse SessionDescription. Invalid SDP line: a=setup:active` 에러 발생. WebRTC 연결 자체가 수립되지 않음.
* **원인**: `media-server/main.py`의 `force_localhost_candidate()` 함수에서 SDP를 줄 단위(`splitlines()`)로 분해 후 `"\r\n".join()`으로 재조립하면서, **원본 SDP의 줄바꿈 포맷이 손상**됨. `a=setup:active` 같은 정상 SDP 라인이 파싱 불가능한 형태로 변형됨.
* **해결**: 
    1. `splitlines()` + `join()` 방식을 **전면 폐기**.
    2. `re.sub()` (정규표현식)을 사용하여 **원본 SDP 텍스트 구조를 유지하면서** 사설 IP(`172.x.x.x`, `10.x.x.x`, `192.168.x.x`)만 `127.0.0.1`로 치환하도록 변경.
    3. `\b` (단어 경계) 메타 문자를 추가하여 IP 주소가 아닌 다른 텍스트의 일부로 포함된 숫자까지 실수로 치환하는 **오탐(False Positive)** 방지.
* **관련 파일**: `media-server/main.py` — `force_localhost_candidate()` 함수
* **교훈**: SDP(Session Description Protocol)는 매우 엄격한 텍스트 프로토콜이므로, 원본 포맷(줄바꿈, 공백)을 절대 변경해서는 안 됨. 필요한 부분만 정밀하게 치환해야 함.

---

#### 🔴 Issue #2: ICE Candidate 미수집 — 서버가 클라이언트 주소를 모름

* **발생일**: 2026-02-13
* **위치**: `frontend/src/App.jsx` — `setupWebRTC()` 함수
* **증상**: SDP 파싱 에러 해결 후에도 영상 프레임이 서버에 도달하지 않음. 서버 로그에 `⏰ 5초간 프레임 수신 없음 (타임아웃)` 반복.
* **원인**: 클라이언트가 `createOffer()` 직후 ICE Candidate 수집이 완료되기 **전에** SDP를 서버로 보내버림. 서버는 클라이언트의 네트워크 주소(Candidate)를 모르니 미디어 스트림을 받을 수 없음.
* **해결**: `setupWebRTC()` 함수에 **ICE Gathering 완료 대기 로직** 추가:
    ```javascript
    await new Promise((resolve) => {
        if (pc.iceGatheringState === 'complete') { resolve(); return; }
        const checkState = () => {
            if (pc.iceGatheringState === 'complete') {
                pc.removeEventListener('icegatheringstatechange', checkState);
                resolve();
            }
        };
        pc.addEventListener('icegatheringstatechange', checkState);
        setTimeout(() => { /* 1초 fallback */ resolve(); }, 1000);
    });
    ```
* **관련 파일**: `frontend/src/App.jsx` — `setupWebRTC()` 함수
* **교훈**: WebRTC에서 SDP Offer를 보내기 전에 반드시 `iceGatheringState === 'complete'`를 확인해야 함. 특히 Docker 환경에서는 STUN/TURN 없이 로컬 후보만 사용하므로 이 과정이 더 중요함.

---

#### 🔴 Issue #3: Docker 내부 IP 노출 — 클라이언트가 172.x.x.x에 접근 불가

* **발생일**: 2026-02-13
* **위치**: `media-server/main.py` — WebRTC `/offer` 엔드포인트
* **증상**: SDP Answer에 Docker 내부 네트워크 IP(`172.19.0.x`)가 포함되어 응답됨. 브라우저는 이 IP에 접근할 수 없으므로 미디어 연결 실패.
* **원인**: Docker 컨테이너 내부에서 aiortc가 자신의 IP를 Docker Bridge Network IP로 인식하여 SDP에 포함시킴.
* **해결**: `force_localhost_candidate()` 함수를 구현하여, 서버 응답 SDP에서 사설 IP 대역을 `127.0.0.1`로 자동 변환. 클라이언트는 `localhost:50000-50050` 포트 포워딩을 통해 미디어 서버에 접속.
* **관련 파일**: `media-server/main.py`, `docker-compose.yml` (포트 매핑: `50000-50050:50000-50050/udp`)

---

### 3.2. 📊 영상 분석 점수 계산 (Media Server)

#### 🔴 Issue #4: `_calculate_scores()` 변수 미정의 — `UnboundLocalError` 가능성

* **발생일**: 2026-02-13
* **위치**: `media-server/main.py` — `VideoAnalysisTrack._calculate_scores()` 메서드
* **증상**: 점수 계산이 되지 않거나, 변수 참조 에러 발생 가능성.
* **원인**: `avg_smile`, `avg_anxiety`, `gaze_ratio`, `posture_ratio` 변수를 **산출하기 전에** 보정(Adjustment) 수식에서 먼저 사용하려 함. 누적 리스트(`all_smiles`, `all_anxiety`)와 카운터(`total_gaze_center`, `total_posture_stable`)는 있지만, 이를 평균으로 환산하는 코드가 빠져 있었음.
* **해결**: 보정 수식 **앞에** 평균값 산출 로직 추가:
    ```python
    avg_smile = (sum(all_smiles) / len(all_smiles)) * 100 if all_smiles else 0.0
    avg_anxiety = (sum(all_anxiety) / len(all_anxiety)) * 100 if all_anxiety else 0.0
    gaze_ratio = (total_gaze_center / total_frames) * 100
    posture_ratio = (total_posture_stable / total_frames) * 100
    ```
* **관련 파일**: `media-server/main.py` — `_calculate_scores()` 메서드

---

#### 🔴 Issue #5: `process_vision()` 이벤트 루프 블로킹

* **발생일**: 2026-02-13
* **위치**: `media-server/main.py` — `VideoAnalysisTrack.process_vision()` 메서드
* **증상**: MediaPipe의 `process_frame()` 호출이 CPU 집약적(~50ms)이어서, 같은 이벤트 루프에서 실행 시 WebRTC 패킷 수신이 지연됨. `⏰ 5초간 프레임 수신 없음` 에러가 간헐적으로 재발.
* **원인**: `asyncio` 이벤트 루프는 싱글 스레드이므로, CPU 작업이 루프를 블로킹하면 네트워크 I/O(WebRTC 패킷 수신)가 밀림.
* **해결**: `loop.run_in_executor(None, self.analyzer.process_frame, img, timestamp_ms)`를 사용하여 **스레드 풀**에서 실행하도록 변경. 이벤트 루프가 블로킹되지 않음.
* **관련 파일**: `media-server/main.py` — `process_vision()` 메서드

---

### 3.3. 🎨 Frontend (App.jsx)

#### 🔴 Issue #6: `NotSupportedError: Failed to execute 'start' on 'MediaRecorder'`

* **발생일**: 2026-02-13
* **위치**: `frontend/src/pages/setup/EnvTestPage.jsx` (handleStartTest 함수)
* **증상**: 환경 테스트 페이지에서 음성 인식 테스트 시 `MediaRecorder` 시작 실패 에러 발생.
* **원인**: `MediaRecorder`가 이미 'recording' 상태이거나, 사용 중인 `stream`이 유효하지 않거나 종료되었을 때 발생. 페이지를 왔다 갔다 하거나 테스트를 반복할 때 상태 관리가 꼬임.
* **해결**: `mediaRecorder.start()` 호출을 `try-catch` 블록으로 감싸서 에러 핸들링 추가.
* **관련 파일**: `frontend/src/pages/setup/EnvTestPage.jsx`

---

#### 🔴 Issue #7: `App.jsx` 함수 구조 파손 — Vite 빌드 에러

* **발생일**: 2026-02-13
* **위치**: `frontend/src/App.jsx`
* **증상**: `[plugin:vite:react-babel] Unexpected token, expected ","` 빌드 에러. 웹사이트 자체가 뜨지 않음.
* **원인**: AI 에이전트의 연속적인 코드 수정 과정에서 `setupWebRTC()` 함수와 `toggleRecording()` 함수의 **중괄호/괄호 구조가 파손**됨. `setupWebRTC`의 `try-catch` 블록이 삭제되고, `toggleRecording`의 함수 선언(`const toggleRecording = async () => {`)이 사라지면서 두 함수의 코드가 뒤섞임.
* **해결**: Python 스크립트(`patch_app.py`)를 작성하여 파일 내용을 정밀하게 파싱하고, `setupWebRTC`와 `toggleRecording` 함수를 올바른 구조로 **통째로 재삽입**. (일반 코드 수정 도구로는 빈 줄이 많아 타겟팅 실패)
* **관련 파일**: `frontend/src/App.jsx`
* **교훈**: 복잡한 JSX 파일의 함수 경계를 수정할 때는 한 번에 큰 블록을 건드리지 말고, 작은 단위로 나눠서 수정해야 구조가 파손되지 않음.

---

### 3.4. ⚙️ 성능 최적화 및 기타

#### 🟡 Optimization #1: 디버그 로그 레벨 조정

* **발생일**: 2026-02-13
* **위치**: `media-server/main.py` — 로깅 설정
* **증상**: Docker 로그에 `aiortc`의 RTP/RTCP 패킷 로그가 초당 수십 줄씩 출력되어 핵심 로그를 읽기 어려움.
* **해결**: `aiortc`, `aioice`, `av` 라이브러리의 로그 레벨을 `DEBUG` → `WARNING`으로 변경. 핵심 분석 로그(`[실시간 종합점수]`)만 출력되도록 정리.

#### 🟡 Optimization #2: 영상 분석 FPS 제한 (10FPS → 5FPS)

* **발생일**: 2026-02-13
* **위치**: `media-server/main.py` — `start_video_analysis()` 함수
* **이유**: 영상 분석이 실시간으로 동작하면서 CPU 자원을 많이 사용함. 같은 호스트 머신에서 동작하는 LLM 질문 생성 워커와 자원 경쟁이 발생하여 **질문 생성 속도가 체감상 느려짐**.
* **해결**: 분석 간격을 `0.1초(10FPS)` → `0.2초(5FPS)`로 변경. 면접 태도 분석에는 초당 5프레임으로 충분함.

#### 🟡 Optimization #3: STT GPU 가속 지원 추가

* **발생일**: 2026-02-13
* **위치**: `ai-worker/tasks/stt.py` — `load_stt_pipeline()` 함수
* **기존**: Whisper STT가 **강제 CPU 모드** (`device="cpu"`, `compute_type="int8"`)로 하드코딩 되어 있었음.
* **변경**: `USE_GPU` 환경 변수를 확인하여, GPU 워커에서는 `device="cuda"` + `compute_type="float16"`을 사용하도록 동적 설정.
* **주의**: 현재 Celery 라우팅 설정에서 STT 태스크는 `cpu_queue`로 배정되므로, 실질적으로 CPU 워커(`USE_GPU=false`)에서 실행됨. GPU 가속을 활용하려면 라우팅 변경 필요.

---

### 3.5. 🔍 GPU 사용 현황 점검

* **확인 결과**: `docker exec interview_worker_gpu nvidia-smi` 실행 → **"No running processes found"**
* **원인**: Celery Solo Pool은 첫 태스크 요청 시에만 모델을 로딩하는 **지연 로딩(Lazy Loading)** 구조. 서버 기동 직후에는 GPU에 올라간 프로세스가 없음.
* **EXAONE 7.8B 모델**: 첫 질문 생성 요청이 올 때 GPU에 로딩됨 (약 10~30초 소요). 이후 요청부터는 빠르게 응답.
* **결론**: 질문 생성 속도가 느려진 것은 **AI 코드를 수정한 것이 아니라**, (1) WebRTC 연결 성공으로 인해 영상 분석이 실제로 동작하기 시작하면서 호스트 리소스 경쟁이 생긴 것, (2) `docker-compose down/up` 시 모델이 GPU에서 언로드되어 첫 요청 시 재로딩이 필요한 것이 주된 원인.

---

### 3.6. 📋 2026-02-13 작업 요약 (최종)

| # | 작업 내용 | 관련 파일 | 상태 |
|---|----------|----------|------|
| 1 | SDP 파싱 에러 해결 (정규표현식 치환) | `media-server/main.py` | ✅ 완료 |
| 2 | ICE Candidate 수집 대기 로직 추가 | `frontend/src/App.jsx` | ✅ 완료 |
| 3 | Docker 내부 IP → localhost 변환 | `media-server/main.py` | ✅ 완료 |
| 4 | 점수 계산 로직 오류 수정 | `media-server/main.py` | ✅ 완료 |
| 5 | 이벤트 루프 블로킹 방지 (run_in_executor) | `media-server/main.py` | ✅ 완료 |
| 6 | MediaRecorder 에러 핸들링 | `frontend/EnvTestPage.jsx` | ✅ 완료 |
| 7 | App.jsx 함수 구조 파손 복구 | `frontend/src/App.jsx` | ✅ 완료 |
| 8 | aiortc 디버그 로그 숨김 | `media-server/main.py` | ✅ 완료 |
| 9 | 영상 분석 FPS 5로 제한 | `media-server/main.py` | ✅ 완료 |
| 10 | STT GPU 가속 옵션 추가 | `ai-worker/tasks/stt.py` | ✅ 완료 |

**최종 결과**: WebRTC 연결 성공 → 실시간 영상 분석 동작 확인 → 시선/자세/미소/감정 점수 계산 정상 출력 ✅

---

## 4. 📅 2026-02-23~24 작업 일지 — 음성 자신감 점수 계산 및 DB 저장

> **작업 목표**: 음성 자신감(confidence) 점수가 계산되지 않아 최종 리포트에 "(데이터 없음)"으로 표시되는 문제를 해결하고, 질문별 채점 결과를 DB에 저장하는 기능 추가.

---

### 4.1. 🔍 문제 추적 과정 (Root Cause Analysis)

#### 🔴 Issue #1: 음성 자신감 점수가 0점 — "(데이터 없음)" 표시

* **발생일**: 2026-02-23
* **위치**: `media-server/main.py` — `generate_final_report()` 함수
* **증상**: 면접 종료 시 최종 리포트에서 "음성자신감: 0.0점 | (데이터 없음)" 출력. `audio_scores` 리스트가 비어있음.
* **원인 추적 과정**:
    1. **디버그 로그 추가**: `start_remote_stt()` 함수 안에 STEP1~STEP7 디버그 프린트를 삽입하여 오디오 처리 파이프라인의 어느 단계에서 막히는지 추적.
    2. **STEP 로그 미출력 확인**: 면접 진행 후 docker 로그에서 STEP1~7이 전혀 출력되지 않음 → 150프레임 누적 로직에 도달조차 못 하고 있음.
    3. **오디오 프레임 자체 수신 여부 확인**: `audio_frame_count` 카운터를 추가하여 녹음 상태와 무관하게 100프레임마다 수신 로그 출력.
    4. **결과**: 오디오 프레임은 정상 수신 (2400+ 프레임) 되지만, `recording=False`가 지속됨.

---

#### 🔴 Issue #2 (핵심 원인): session_id 타입 불일치 — 정수 vs 문자열

* **발생일**: 2026-02-23
* **위치**: `media-server/main.py` — `/offer` 엔드포인트 (663번 줄) 및 WebSocket 엔드포인트
* **증상**: 오디오 프레임은 수신되지만 `recording` 플래그가 항상 `False`로 조회됨.
* **원인**: 
    ```python
    # WebSocket 엔드포인트 (URL 경로 파라미터 → 항상 문자열)
    @app.websocket("/ws/{session_id}")  
    # → active_recording_flags["1"] = True  (키: 문자열 "1")
    
    # offer 엔드포인트 (JSON 바디 파싱 → 숫자는 정수로 파싱)
    session_id = params.get("session_id", "unknown")
    # → start_remote_stt 에서 active_recording_flags.get(1, False)  (키: 정수 1)
    
    # Python에서 "1" ≠ 1 이므로 항상 False 반환!
    ```
    WebSocket은 URL 경로 파라미터라서 `session_id`가 **문자열 `"1"`** 으로 저장되고,  
    offer 엔드포인트는 JSON에서 숫자로 파싱되어 `session_id`가 **정수 `1`** 로 전달됨.  
    Python 딕셔너리에서 `"1"`과 `1`은 서로 다른 키이므로, `start_remote_stt` 안에서 `active_recording_flags.get(session_id, False)`가 항상 `False`를 반환.
* **해결**: 
    ```python
    # 변경 전
    session_id = params.get("session_id", "unknown")
    
    # 변경 후 (str()로 감싸서 타입 통일)
    session_id = str(params.get("session_id", "unknown"))
    ```
* **관련 파일**: `media-server/main.py` — `/offer` 엔드포인트
* **교훈**: FastAPI의 URL 경로 파라미터(`/ws/{session_id}`)는 항상 문자열이고, JSON 바디의 숫자는 파이썬에서 정수로 파싱된다. 같은 변수를 여러 엔드포인트에서 공유할 때 **타입을 반드시 통일**해야 한다.

---

### 4.2. 🎵 STUN 서버 제거 문제 (Git 기록 분석)

#### 🟡 Issue #3: STUN 서버 설정 제거 — 코드 변경 추적

* **발생일**: 2026-02-19 (커밋 `2653900`)
* **위치**: `media-server/main.py` — `/offer` 엔드포인트
* **경위**:
    * **2026-02-12** (커밋 `9427940`): STUN 서버가 설정되어 있었음.
      ```python
      pc = RTCPeerConnection(
          configuration=RTCConfiguration(
              iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
          )
      )
      ```
    * **2026-02-19** (커밋 `2653900`): 누군가 "로컬 개발 환경 강제 (STUN 제거)" 주석과 함께 의도적으로 제거.
      ```python
      # [수정] 로컬 개발 환경 강제 (STUN 제거)
      pc = RTCPeerConnection()
      ```
    * `RTCConfiguration`, `RTCIceServer`가 **임포트는 되어 있지만 사용되지 않는 상태**로 남아있음.
* **영향**: 로컬 Docker 환경에서는 `force_localhost_candidate()` 함수가 IP를 127.0.0.1로 변환해주므로 큰 문제가 없었으나, 일부 네트워크 환경에서 UDP 경로를 못 찾아 프레임 수신 실패 가능성이 있음.
* **현재 상태**: STUN 없이도 영상/음성 프레임이 정상 수신되고 있으므로, 현재는 수정 보류.

---

### 4.3. 🎨 프론트엔드 크래시 (Vision HUD)

#### 🔴 Issue #4: visionData.scores.smile 접근 시 크래시 — `Cannot read properties of undefined`

* **발생일**: 2026-02-23
* **위치**: `frontend/src/pages/interview/InterviewPage.jsx` (292번 줄)
* **증상**: 면접 중 "답변 제출" 시 흰 화면 + 콘솔에 `TypeError: Cannot read properties of undefined (reading 'smile')` 에러.
* **원인**: 
    * 서버가 얼굴 미감지 시 `{"status": "not_detected"}` 데이터를 전송 (이 경우 `scores` 필드가 없음).
    * 프론트엔드는 `visionData && (...)` 조건만 체크하여, `not_detected` 상태에서도 `visionData.scores.smile`에 접근 시도 → `undefined.smile` 에러 발생.
    * **이 버그가 이전에 안 나타난 이유**: session_id 타입 불일치로 영상 파이프라인이 제대로 동작하지 않아 `visionData`가 null 상태를 유지했기 때문. session_id 수정 후 파이프라인이 정상 가동되면서 드러남.
* **해결**: 
    ```jsx
    // 변경 전 (얼굴 미감지 시 크래시)
    {visionData && (
    
    // 변경 후 (얼굴 감지된 경우에만 HUD 렌더링)
    {visionData && visionData.status === 'detected' && (
    ```
* **관련 파일**: `frontend/src/pages/interview/InterviewPage.jsx`

---

### 4.4. 🎯 음성 점수 보정 (Score Calibration)

#### 🟡 Issue #5: 음성 자신감 점수가 비정상적으로 낮음 (6.7점)

* **발생일**: 2026-02-23
* **위치**: `media-server/main.py` — `start_remote_stt()` 오디오 분석 블록
* **증상**: 정상적으로 말하고 있는데도 자신감 점수가 6.7점으로 측정됨.
* **원인**:
    1. **성량 점수**: `volume_score = min(volume_rms * 500, 100)` 공식이 WebRTC 오디오의 낮은 진폭(RMS ~0.023)에 비해 너무 보수적 → 11.5점
    2. **발화 비율**: `threshold = 0.05`가 너무 높아서 실제 발화 샘플도 잡히지 않음 → `speaking_ratio = 0.01` (1%) → 속도 점수 1.9점
* **해결**:
    ```python
    # 변경 전 (낮은 점수)
    volume_score = min(volume_rms * 500, 100)             # RMS 0.023 → 11.5점
    speaking_ratio = np.count_nonzero(np.abs(audio_np) > 0.05) / len(audio_np)  # 1%
    speed_score = min(speaking_ratio * 200, 100)           # 1.9점
    
    # 변경 후 (영상 점수와 동일한 40~100 스케일)
    volume_score = min(max((volume_rms - 0.02) / (0.15 - 0.02) * 60 + 40, 40), 100)  # 40~100
    speaking_ratio = np.count_nonzero(np.abs(audio_np) > 0.02) / len(audio_np)  # threshold 낮춤
    speed_score = min(max(speaking_ratio / 0.20 * 60 + 40, 40), 100)  # 40~100
    ```
* **개선 결과**: 6.7점 → 73.3점 (정상적인 발화 기준)

---

### 4.5. 📊 질문별 채점 및 DB 저장 기능 추가

#### 🟢 Feature #1: 질문별 영상+음성 통합 채점

* **날짜**: 2026-02-23
* **관련 파일**: `media-server/main.py` — `VideoAnalysisTrack` 클래스
* **구현 내용**:
    1. `_get_empty_q_data()`에 `audio_scores` 필드 추가 → 질문별 음성 점수 분리 관리
    2. `_score_question()` 메서드 신규 추가 → 질문 하나의 영상+음성 통합 점수 계산
    3. `switch_question()`에서 질문 전환 시 자동 채점 수행
    4. `generate_final_report()`에서 질문별 내역 테이블 + 총합 출력
* **최종 리포트 출력 예시**:
    ```
    ============================================================
    🏆 AI 면접 최종 리포트 [3]
    ============================================================
    질문 |  시선 |  음성 |  미소 |  자세 |  정서 |   합계
    ------------------------------------------------------------
      Q0 |  41.0 |  73.3 |  40.0 |  40.0 |  94.7 |   55.3
      Q1 |  52.0 |  68.5 |  42.0 |  40.0 |  91.2 |   57.8
    ------------------------------------------------------------
      평균 |  46.0 |  70.9 |  41.0 |  40.0 |  93.0 |   56.4
    ============================================================
       ✅ 최종 종합 점수: 56.4점
    ============================================================
    ```

#### 🟢 Feature #2: DB 저장 (행동 분석 점수)

* **날짜**: 2026-02-24
* **관련 파일**: 
    * `backend-core/routes/interviews.py` — `PATCH /interviews/{id}/behavior-scores` 엔드포인트 추가
    * `media-server/main.py` — `generate_final_report()` 내 HTTP 전송 로직
* **저장 구조**:
    * **`interviews` 테이블 → `emotion_summary` (JSONB)**: 최종 평균 점수만 저장
      ```json
      {
        "averages": {"gaze": 46.0, "audio": 70.9, "smile": 41.0, "posture": 40.0, "emotion": 93.0, "total": 56.4},
        "interview_duration_sec": 120,
        "total_questions": 3
      }
      ```
    * **`transcripts` 테이블 → `emotion` (str)**: 각 질문별 채점 상세 (User 발화 행)
      ```json
      {"q_idx": 0, "gaze": 41.0, "audio": 73.3, "smile": 40.0, "posture": 40.0, "emotion": 94.7, "total": 55.3}
      ```
    * **`transcripts` 테이블 → `sentiment_score` (float)**: 해당 질문 합계 점수

---

### 4.6. 🐛 기타 발견된 버그

#### 🟡 Issue #6: stt.py 환경변수 이름에 백틱 포함

* **발생일**: 2026-02-23 (발견)
* **위치**: `ai-worker/tasks/stt.py` (21번 줄)
* **증상**: 환경변수 `WHISPER_MODEL_SIZE`를 설정해도 항상 기본값 `large-v3-turbo` 사용.
* **원인**: 
    ```python
    # 현재 (버그) — 백틱이 따옴표 안에 포함
    MODEL_SIZE = os.getenv("`WHISPER_MODEL_SIZE`", "large-v3-turbo")
    # → 환경변수 이름이 "`WHISPER_MODEL_SIZE`" (백틱 포함)으로 조회됨
    ```
* **영향**: STT 동작 자체에는 영향 없음 (기본값이 올바른 모델명). 환경변수로 모델을 변경하고 싶을 때만 문제.
* **상태**: 발견만 됨, 수정 보류.

#### 🟡 Issue #7: TTS AbortError — play() interrupted by pause()

* **발생일**: 2026-02-23 (발견)
* **위치**: `frontend/src/pages/interview/InterviewPage.jsx` — `playTTS()` 함수
* **증상**: 콘솔에 `AbortError: The play() request was interrupted by a call to pause()` 에러.
* **원인**: 질문 전환 시 `audioRef.current.pause()` 직후 새 Audio 객체를 만들어 `play()` 호출. 브라우저가 pause 처리 완료 전에 play가 호출되어 충돌.
* **영향**: TTS 오디오가 간헐적으로 재생 안 됨 (기능적 영향 낮음).
* **상태**: 발견만 됨, 수정 보류.

---

### 4.7. 📋 2026-02-23~24 작업 요약

| # | 파트 | 문제 | 원인 | 해결 | 상태 |
|---|------|------|------|------|------|
| 1 | 미디어 서버 | 음성 자신감 점수가 항상 0점으로 표시 | `/offer`에서 session_id가 정수(1)로, WebSocket에서는 문자열("1")로 저장되어 딕셔너리 키가 불일치 → 녹음 플래그가 항상 False | session_id를 `str()`로 감싸서 타입 통일 | ✅ 완료 |
| 2 | 프론트엔드 (영상 분석 HUD) | 답변 제출 시 흰 화면 크래시 발생 | 서버가 얼굴 미감지 시 `scores` 필드 없이 전송하는데, 프론트에서 `visionData.scores.smile`에 바로 접근하여 `undefined` 에러 | `visionData.status === 'detected'` 조건 추가 후 scores 접근 | ✅ 완료 |
| 3 | 미디어 서버 (음성 분석) | 정상 발화인데 자신감 점수가 6.7점으로 측정 | WebRTC 오디오의 RMS 값이 0.023 수준으로 낮은데, 기존 공식(`RMS * 500`)이 이 범위에 맞지 않음. 발화 임계값(0.05)도 너무 높음 | 점수 공식을 40~100 스케일로 재보정, 발화 임계값을 0.02로 하향 → 73.3점으로 정상화 | ✅ 완료 |
| 4 | 미디어 서버 | Docker 로그에 불필요한 로그가 초당 수십 줄씩 출력 | aiortc/aioice/av 라이브러리의 RTP/RTCP 패킷 디버그 로그가 과도하게 출력 | 해당 라이브러리 로그 레벨을 WARNING으로 상향 | ✅ 완료 |
| 5 | 미디어 서버 (채점 시스템) | 질문별 개별 채점이 불가, 전체 평균만 존재 | 질문 단위로 영상+음성 데이터를 분리 관리하는 구조가 없었음 | `_score_question()` 메서드 추가, `switch_question()` 시 자동 채점, 질문별 내역 테이블 출력 | ✅ 완료 |
| 6 | 백엔드 API | 행동 분석 점수를 DB에 저장할 API가 없음 | 미디어 서버에서 계산된 점수를 백엔드 DB에 전달하는 엔드포인트 미구현 | `PATCH /interviews/{id}/behavior-scores` API 신규 추가 (interviews.emotion_summary + transcripts.emotion 저장) | ✅ 완료 |
| 7 | 미디어 서버 → 백엔드 연동 | 미디어 서버에서 백엔드로 점수를 보내는 로직이 없음 | generate_final_report()에서 점수 계산만 하고 DB 전송 코드가 없었음 | `urllib.request`로 백엔드 API에 HTTP PATCH 요청 전송하는 로직 추가 | ✅ 완료 |
| 8 | STT (음성 인식) | 환경변수 `WHISPER_MODEL_SIZE` 설정이 무시됨 | `os.getenv()` 호출 시 변수명에 백틱(`)이 포함되어 있어 OS 환경변수와 이름 불일치 | 발견만 됨 (기본값이 올바른 모델이라 동작에는 영향 없음) | 🔍 발견 |
| 9 | TTS (음성 합성) / 프론트엔드 | 질문 전환 시 TTS 오디오가 간헐적으로 재생 안 됨 | `pause()` 처리 완료 전에 새 Audio 객체의 `play()` 호출 → 브라우저가 AbortError 발생 | 발견만 됨 (기능적 영향 낮음) | 🔍 발견 |

**핵심 해결**: `session_id` 타입 불일치(정수 vs 문자열) → 음성 녹음 플래그가 False로 고정 → 오디오 점수 계산 불가. `str()` 한 줄 추가로 해결.
