# 🏗️ AI 면접 시스템 아키텍처 설계서 (SAD)

**프로젝트명**: Big20 AI Interview Project
**버전**: v2.0
**작성일**: 2026-01-27

---

## 1. 시스템 개요 (System Overview)

### 1.1 목적

본 시스템은 대규모 언어 모델(LLM)을 활용하여 지원자에게 맞춤형 기술 면접을 제공하고, 답변을 실시간으로 분석하여 객관적인 평가 리포트를 생성하는 자동화된 면접 플랫폼입니다.

### 1.2 핵심 기능

- **직무별 맞춤 질문 생성**: DB의 우수 질문 재활용(40%) 및 LLM 기반 창의적 질문 생성(60%)
- **실시간 면접 진행**: STT(Speech-to-Text)를 통한 대화 기록 및 즉각적인 인터랙션
- **AI 기반 평가**: 답변의 기술적 정확성, 논리성, 의사소통 능력을 다각도로 평가
- **종합 리포트 제공**: 면접 종료 후 강약점 분석 및 채용 추천 의견이 담긴 리포트 생성
- **데이터 기반 개선**: 평가 결과가 질문의 품질 점수(Avg Score)에 반영되는 선순환 구조

---

## 2. 아키텍처 뷰 (Architecture Views)

### 2.1 논리 뷰 (Logical View) - 계층 구조

#### [Presentation Layer]

- **Frontend (React)**: 사용자 인터페이스, 면접 화면, 리포트 대시보드
- **Media Server**: 실시간 음성/영상 스트리밍 처리 (WebRTC 등)

#### [Application Layer]

- **Backend Core (FastAPI)**:
  - RESTful API 제공
  - 사용자 인증 및 권한 관리 (JWT)
  - 면접 세션 및 데이터 관리
  - 비동기 작업 요청 (Celery Producer)

#### [Service Layer]

- **AI Worker (Celery)**:
  - CPU/GPU 집약적 작업 처리
  - **Question Generator**: Llama-3.2 기반 질문 생성
  - **Evaluator**: Solar-10.7B 기반 답변 평가
  - **Answer Collector**: 우수 답변 벡터화 및 저장

#### [Data Layer]

- **PostgreSQL**: 관계형 데이터 및 벡터 데이터(pgvector) 저장
- **Redis**: Celery Task Broker 및 Result Backend, 캐싱

---

### 2.2 프로세스 뷰 (Process View) - 핵심 흐름

#### A. 면접 질문 생성 프로세스

1. **User** -> **Backend**: 면접 생성 요청 (`POST /interviews`)
2. **Backend**: DB에 면접 세션 생성 (Status: SCHEDULED)
3. **Backend** -> **Redis**: 질문 생성 태스크 발행 (`tasks.question_generator`)
4. **AI Worker**: 태스크 수신
   - DB에서 우수 질문 조회 (Reuse, 40%)
   - LLM으로 신규 질문 생성 (Few-Shot, 60%)
5. **AI Worker** -> **DB**: 질문 및 Transcript(AI 발화) 저장
6. **Backend**: 면접 상태 변경 (SCHEDULED -> LIVE)

#### B. 답변 평가 및 선순환 프로세스

1. **User**: 답변 제출 (음성 -> 텍스트 변환 완료 가정)
2. **Backend** -> **Redis**: 평가 태스크 발행 (`tasks.evaluator`)
3. **AI Worker**:
   - Solar LLM으로 기술/소통 점수 평가
   - 감정 분석 수행
4. **AI Worker** -> **DB**:
   - Transcript에 점수 업데이트
   - **해당 질문의 `avg_score` 업데이트 (질문 품질 재평가)**
   - 85점 이상 시 우수 답변 벡터 저장

---

### 2.3 배포 뷰 (Deployment View) - Docker Composition

| 컨테이너명              | 이미지/기반            | 역할                          | 포트 |
| :---------------------- | :--------------------- | :---------------------------- | :--- |
| `interview_react_web` | Node.js / Nginx        | 프론트엔드 서빙               | 3000 |
| `interview_backend`   | Python 3.10 (Slim)     | API 서버                      | 8000 |
| `interview_worker`    | Python 3.10 (Slim)     | AI 작업 처리 (4-bit LLM 로드) | -    |
| `interview_db`        | pgvector/pgvector:pg18 | 메인 데이터베이스             | 5432 |
| `interview_redis`     | redis:alpine           | 메시지 브로커                 | 6379 |
| `interview_media`     | (Custom)               | 미디어 스트리밍 (Optional)    | 8080 |

---

### 2.4 데이터 뷰 (Data View) - ERD 개요

#### Users (사용자)

- `id`, `email`, `role` (candidate, recruiter, admin)

#### Interviews (면접 세션)

- `id`, `candidate_id`, `position`, `status`, `overall_score`

#### Questions (질문 은행)

- `id`, `content`, `category`, `position`
- `usage_count`, `avg_score` (**핵심 지표**)
- `start_vector` (유사도 검색용, 확장 예정)

#### AnswerBank (우수 답변)

- `id`, `question_id`, `answer_text`
- `embedding` (vector-1536), `score`

#### Transcripts (대화 기록)

- `id`, `interview_id`, `speaker` (AI/User), `text`
- `sentiment_score`

#### EvaluationReports (종합 리포트)

- `id`, `interview_id`, `technical_score`, `summary_text`

---

## 3. 기술 스택 (Technology Stack)

### Backend

- **Framework**: FastAPI (Async, Type Hinting)
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Authentication**: Python-Jose (JWT), Passlib (Bcrypt)
- **Task Queue**: Celery 5.x
- **Dependency Mgmt**: pip, requirements.txt

### AI / ML

- **LLM**: Meta Llama 3.2 (3B), Solar 10.7B (Instruct)
- **Inference**: HuggingFace Transformers, LlamaCpp (GGUF)
- **Optimization**: BitsAndBytes (4-bit Quantization), Accelerate
- **Vector Search**: pgvector, Sentence-Transformers

### Database

- **DBMS**: PostgreSQL 18
- **Cache/Broker**: Redis

### Infrastructure

- **Containerization**: Docker, Docker Compose
- **OS**: Linux (Container), Windows (Host)

---

## 4. 인터페이스 명세 (Key API Endpoints)

### Auth

- `POST /register`: 회원가입
- `POST /token`: 로그인 (Access Token 발급)

### Interview

- `POST /interviews`: 면접 생성 (질문 생성 트리거)
- `GET /interviews/{id}/questions`: AI 질문 목록 조회 (Transcript 기반)
- `POST /interviews/{id}/complete`: 면접 종료 및 리포트 생성 요청

### Transcript

- `POST /transcripts`: 대화 내용 저장 (평가 트리거)
- `GET /interviews/{id}/transcripts`: 전체 대화록 조회

### Report

- `GET /interviews/{id}/report`: 최종 평가 리포트 조회

---

## 5. 비기능 요구사항 및 품질 속성

### 5.1 성능 (Performance)

- **응답 시간**:
  - API: 200ms 이내
  - 질문 생성: 10초 이내 (하이브리드 전략으로 단축)
- **처리량**: 동시 면접 10세션 지원 (단일 Worker 기준)
- **메모리 효율**: 4-bit 양자화 적용으로 VRAM 4GB 미만에서도 동작

### 5.2 확장성 (Scalability)

- **Scale-Out**:
  - Backend는 Stateless하므로 수평 확장 용이
  - Worker는 Redis Queue를 공유하며 다중 인스턴스 실행 가능
- **DB 확장**: PostgreSQL Connection Pooling 적용

### 5.3 안정성 (Reliability)

- **Fallback**: LLM 모델 로딩 실패 또는 생성 오류 시 기본 질문 세트 제공
- **Retry**: Celery 태스크 실패 시 자동 재시도 (Max 3회)
- **Isolation**: AI 작업이 API 서버를 블로킹하지 않도록 비동기 분리

### 5.4 보안 (Security)

- 모든 API 요청에 Bearer Token 인증
- 비밀번호 단방향 해싱 저장
- SQL Injection 방지 (ORM 사용)
- 환경 변수(`.env`)를 통한 민감 정보 관리

---

**참고 문서**:

- `.agent/QUALITY_REPORT_2026-01-27.md`
- `.agent/SIMPLIFIED_LOGIC_ANALYSIS.md`
