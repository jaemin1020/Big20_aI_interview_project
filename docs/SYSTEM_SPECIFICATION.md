# Big20 AI 면접 프로젝트 시스템 명세서

## 1. 개요 (Overview)

### 1.1 프로젝트 명
Big20 AI 면접 프로젝트 (Big20 AI Interview Project)

### 1.2 목적
본 시스템은 최신 AI 기술(LLM, Vision AI, STT)과 실시간 웹 통신 기술(WebRTC)을 결합하여, 실제 면접과 유사한 환경을 제공하고 면접자의 답변 내용과 비언어적 태도를 종합적으로 분석하여 객관적이고 심도 있는 피드백을 제공하는 것을 목적으로 한다.

### 1.3 범위
- 웹 기반의 실시간 화상 면접 인터페이스 제공
- 직무 기반 맞춤형 면접 질문 자동 생성
- 실시간 음성/영상 스트리밍 및 저장
- 답변 내용에 대한 AI 기반 정밀 평가 (기술적/직무적 적합성)
- 면접자의 표정 및 감정 상태 분석
- 종합 결과 리포트 대시보드 제공

---

## 2. 시스템 아키텍처 (System Architecture)

### 2.1 전체 구성도
본 시스템은 마이크로서비스 아키텍처(MSA)를 지향하며, 다음과 같은 6개의 주요 컴포넌트로 구성된다.

*   **Frontend**: 사용자 인터페이스 (React)
*   **Backend-Core**: 메인 비즈니스 로직 및 API (FastAPI)
*   **Media-Server**: 실시간 스트리밍 처리 (WebRTC)
*   **AI-Worker**: 고부하 AI 연산 처리 (Celery)
*   **Database**: 데이터 영구 저장 (PostgreSQL)
*   **Message Broker**: 비동기 작업 통신 (Redis)

### 2.2 기술 스택 요약
| 구분 | 기술 스택 | 비고 |
|:---:|:---|:---|
| **OS** | Windows (WSL2), Linux | |
| **Frontend** | React 18, Vite 5, Axios | Glassmorphism UI |
| **Backend** | FastAPI, SQLModel | Async IO 지원 |
| **AI/ML** | PyTorch, TensorFlow, LangChain | Llama-3.1, Solar-10.7B, DeepFace |
| **Media** | aiortc, Deepgram SDK | WebRTC, STT |
| **DB** | PostgreSQL 18, pgvector | Vector Search 지원 |
| **Infra** | Docker Compose | 컨테이너 오케스트레이션 |

---

## 3. 구성 요소별 상세 명세 (Component Specifications)

### 3.1 Frontend (User Interface)
*   **기반 기술**: React 18.2, Vite 5.0
*   **주요 기능**:
    *   **사용자 인증**: 로그인/회원가입, JWT 토큰 관리
    *   **면접 설정**: 직무 선택, 카메라/마이크 테스트
    *   **실시간 면접**:
        *   WebRTC를 통한 비디오 스트림 전송 (Backend 분석용)
        *   실시간 질문 텍스트 표시 및 TTS(예정) 재생
        *   **Client-Side STT**: `@deepgram/sdk`를 사용하여 브라우저에서 직접 음성 인식 수행
        *   실시간 답변 자막 표시 및 전사 데이터(Transcript) 생성
    *   **대시보드**: 면접 결과 리포트 시각화 (차트, 점수, 상세 피드백)

### 3.2 Backend-Core (Main Server)
*   **기반 기술**: FastAPI, SQLModel, Celery Client
*   **포트**: 8000
*   **주요 기능**:
    *   **RESTful API**: 클라이언트 요청 처리 및 데이터 제공
    *   **Session Management**: 면접 세션 상태 관리 (대기, 진행, 완료)
    *   **Question Generation**: Llama-3.1-8B 모델을 이용한 Context 기반 질문 생성
    *   **Auth**: OAuth2 및 JWT 기반 인증/인가

### 3.3 Media-Server (Streaming Server)
*   **기반 기술**: aiortc, Deepgram SDK, Python
*   **포트**: 8080
*   **주요 기능**:
    *   **WebRTC Signaling**: SDP/ICE Candidate 교환 및 P2P 연결 수립
    *   **Video Processing**:
        *   **Eye Tracking**: OpenCV 활용 실시간 눈 깜빡임/시선 추적 (Latency < 200ms)
        *   **Frame Extraction**: 2초 간격 프레임 추출 및 Celery Task 발행
        *   *참고: 오디오 트랙은 서버에서 처리하지 않음 (Frontend STT 사용)*
    *   **Video Sampling**: 2초 간격 프레임 추출 및 AI-Worker 전달

### 3.4 AI-Worker (Data Processing Unit)
*   **기반 기술**: Celery, Redis, PyTorch/TensorFlow
*   **주요 기능**:
    *   **Evaluator**: Solar-10.7B-Instruct 모델을 활용한 답변 정밀 평가
        *   평가 항목: 기술적 정확성, 논리성, 직무 적합성
    *   **Vision Analysis**: DeepFace(VGG-Face) 모델을 활용한 감정/표정 분석
        *   분석 항목: dominant_emotion (happy, sad, neutral, fear, etc.)
    *   **Resume Parsing**: 이력서 업로드 시 텍스트 추출 및 구조화

---

## 4. 데이터 명세 (Data Specifications)

### 4.1 데이터베이스 스키마 (PostgreSQL + pgvector)

본 시스템은 `SQLModel`을 사용하여 ORM을 정의하며, 벡터 임베딩을 위해 `pgvector` 확장을 사용한다.

*   **Users (사용자 계정)**
    *   `id`: Primary Key (Int)
    *   `email`, `username`: Unique Index (String)
    *   `role`: `candidate` | `recruiter` | `admin`
    *   `password_hash`: Bcrypt Hash
    *   `full_name`: 사용자 실명

*   **Resumes (이력서 및 파싱 데이터)**
    *   `id`: Primary Key (Int)
    *   `candidate_id`: Foreign Key (`users.id`)
    *   `file_path`, `file_name`: 원본 파일 정보
    *   `extracted_text`: PDF 전체 텍스트
    *   `structured_data` (JSONB): 항목별 데이터 (학력, 경력, 기술스택)
    *   `embedding` (Vector 1024): 이력서 내용 임베딩 벡터

*   **Companies (기업 정보 및 인재상)**
    *   `id`: Primary Key String (예: "KAKAO")
    *   `company_name`: 기업명
    *   `ideal`: 인재상 텍스트
    *   `description`: 기업 소개
    *   `embedding` (Vector 1024): 기업 특성 벡터 (매칭용)

*   **Interviews (면접 세션)**
    *   `id`: Primary Key (Int)
    *   `candidate_id`: Foreign Key (`users.id`)
    *   `company_id`: Foreign Key (`companies.id`)
    *   `resume_id`: Foreign Key (`resumes.id`)
    *   `position`: 지원 직무 (예: "Backend Engineer")
    *   `status`: `scheduled` | `live` | `completed` | `cancelled`
    *   `overall_score`: 최종 점수 (Float)
    *   `emotion_summary` (JSONB): 감정 분석 요약

*   **Questions (질문 데이터)**
    *   `id`: Primary Key (Int)
    *   `content`: 질문 내용
    *   `category`: `technical` | `behavioral` | `situational` | `cultural_fit`
    *   `difficulty`: `easy` | `medium` | `hard`
    *   `question_type`: 질문 상세 유형 (자기소개, 직무지식 등)
    *   `is_follow_up`: 꼬리 질문 여부 (Boolean)
    *   `rubric_json` (JSONB): 평가 기준
    *   `embedding` (Vector 1024): 질문 유사도 검색용 벡터

*   **Transcripts (실시간 대화 기록)**
    *   `id`: Primary Key (Int)
    *   `interview_id`: Foreign Key (`interviews.id`)
    *   `speaker`: `AI` | `User`
    *   `text`: 발화 내용 (STT 결과)
    *   `sentiment_score`: 감성 점수 (-1.0 ~ 1.0)
    *   `emotion`: 감정 상태 (happy, neutral, etc.)

*   **EvaluationReports (종합 평가 리포트)**
    *   `id`: Primary Key (Int)
    *   `interview_id`: Foreign Key (`interviews.id`)
    *   `technical_score`, `communication_score`, `cultural_fit_score`: 항목별 점수
    *   `summary_text`: 종합 평가 의견
    *   `details_json` (JSONB): 상세 피드백 데이터
    *   `evaluator_model`: 평가에 사용된 모델명 (예: "Solar-10.7B")

*   **AnswerBank (우수 답변 데이터베이스)**
    *   `id`: Primary Key (Int)
    *   `question_id`: Foreign Key (`questions.id`)
    *   `answer_text`: 모범 답변 내용
    *   `embedding` (Vector 1024): 답변 벡터
    *   `score`: 답변 품질 점수 (0-100)

### 4.2 데이터 흐름 (Data Flow Interface)

1.  **AI 질문 생성 요청**: `POST /api/v1/interviews/{session_id}/questions`
    *   **Input**: `resume_id` (이력서 벡터), `company_id` (기업 벡터), `position`
    *   **Process**: Llama-3.1이 Resume/Company Context를 기반으로 질문 생성
    *   **Output**: `question_id`, `content`, `rubric_json`

2.  **실시간 스트리밍 및 분석**:
    *   **Frontend (Audio)**: Browser Microphone -> Deepgram SDK (WebSocket) -> Real-time Transcript -> `createTranscript` API 호출 -> `Transcripts` DB 저장
    *   **Media-Server (Video)**: Browser Camera -> WebRTC -> VideoAnalysisTrack
        *   **Eye Tracking**: Media-Server에서 직접 수행 (WebSocket으로 Frontend에 좌표 전송)
        *   **Emotion Analysis**: 2초 간격 프레임 -> AI-Worker (Celery) -> `Interviews.emotion_summary` 업데이트

3.  **답변 평가 요청 (비동기)**: `Celery Task`
    *   **Trigger**: 사용자 답변 완료 (Silence Detection)
    *   **Input**: `question_text`, `answer_text` (Transcript), `rubric_json`
    *   **Process**: Solar-10.7B가 평가 수행 (Score & Feedback 생성)
    *   **Output**: `EvaluationReports` 및 `Transcripts`에 결과 반영

4.  **최종 리포트 조회**: `GET /api/v1/interviews/{session_id}/report`
    *   **Output JSON**:
        ```json
        {
          "summary": { "technical": 85, "communication": 90, "cultural": 80 },
          "details": [
            { "question": "...", "answer": "...", "feedback": "...", "score": 85 }
          ],
          "emotions": { "confidence": 70, "nervousness": 30 }
        }
        ```

---

## 5. 비기능 요구사항 (Non-Functional Requirements)

### 5.1 성능 (Performance)
*   **실시간성**: WebRTC 레이턴시 500ms 미만 유지
*   **STT 속도**: 발화 종료 후 2초 이내 텍스트 변환 완료
*   **질문 생성**: 요청 후 5초 이내 질문 생성 완료

### 5.2 보안 (Security)
*   모든 API 통신은 HTTPS 암호화 (Production 환경)
*   API Key 등 민감 정보는 환경 변수(.env)로 관리하며 코드에 노출 금지
*   사용자 비밀번호는 Salted Hash (bcrypt) 저장

### 5.3 가용성 및 확장성 (Availability & Scalability)
*   Docker Compose를 통한 컨테이너 기반 배포로 이식성 확보
*   Celery Worker는 부하에 따라 Scale-out 가능하도록 설계 (Redis 브로커 활용)

---

## 6. 배포 환경 (Deployment Environment)

### 6.1 하드웨어 요구사항 (권장)
*   **CPU**: 8 Core 이상 (AI 모델 추론 및 미디어 처리)
*   **RAM**: 32GB 이상 (LLM 모델 로드 및 빌드 캐시)
*   **GPU**: NVIDIA GPU (VRAM 6GB 이상) - Llama 모델 가속 권장
*   **Storage**: 50GB 이상 (Docker 이미지 및 DB 데이터)

### 6.2 소프트웨어 요구사항
*   Docker Desktop (Windows) 또는 Docker Engine (Linux)
*   NVIDIA Container Toolkit (GPU 사용 시)
*   Git Client
