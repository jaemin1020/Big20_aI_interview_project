# 시스템 아키텍처 설계서 (System Architecture Design - SAD)

## 문서 정보
- **프로젝트명**: A4 Project
- **작성일**: 2026-01-26
- **버전**: 2.0
- **담당자**: 엄재민
- **문서 목적**: AI 기반 모의면접 플랫폼의 전체 시스템 아키텍처 설계 및 기술 스택 정의

---

## 목차
1. [시스템 개요](#1-시스템-개요)
2. [아키텍처 설계 원칙](#2-아키텍처-설계-원칙)
3. [전체 시스템 구성도](#3-전체-시스템-구성도)
4. [서비스 계층 구조](#4-서비스-계층-구조)
5. [데이터베이스 설계](#5-데이터베이스-설계)
6. [데이터 흐름 설계](#6-데이터-흐름-설계)
7. [멀티모달 처리 파이프라인](#7-멀티모달-처리-파이프라인)
8. [AI 모델 아키텍처](#8-ai-모델-아키텍처)
9. [인프라 및 배포 구조](#9-인프라-및-배포-구조)
10. [보안 및 인증 설계](#10-보안-및-인증-설계)
11. [성능 및 확장성 설계](#11-성능-및-확장성-설계)
12. [로깅 및 모니터링](#12-로깅-및-모니터링)
13. [기술 스택 상세](#13-기술-스택-상세)
14. [한계 및 향후 확장](#14-한계-및-향후-확장)

---

## 1. 시스템 개요

### 1.1 설계 목적
실시간 멀티모달(음성, 영상, 텍스트) 데이터를 분석하여 사용자에게 개인화된 면접 경험과 정교한 피드백 리포트를 제공하는 AI 기반 모의면접 플랫폼 구축

### 1.2 적용 범위
- 웹 기반 AI 모의면접 플랫폼
- 실시간 음성/영상 스트리밍 및 분석
- AI 기반 질문 생성 및 답변 평가
- 결과 분석 및 리포트 관리 시스템

### 1.3 시스템 목표
- **저지연(Low Latency)**: 실시간 데이터 처리 및 즉각적인 피드백
- **평가 객관성**: LLM 기반의 일관된 평가 기준 적용
- **높은 확장성**: 마이크로서비스 기반의 수평 확장 가능
- **안정성**: 비동기 처리 및 장애 격리를 통한 시스템 안정성 확보

### 1.4 설계 전제 조건
- 안정적인 STT 전송을 위한 비동기 처리
- LLM 토큰 관리 최적화
- GPU 자원의 효율적 활용
- WebRTC 기반 실시간 미디어 스트리밍

---

## 2. 아키텍처 설계 원칙

### 2.1 아키텍처 패턴
**비동기 이벤트 기반 마이크로서비스 아키텍처 (Event-Driven Architecture, EDA)**

### 2.2 선택 근거
1. **LLM 추론 시간 최적화**: 질문 생성과 평가를 분리하여 응답 속도 향상
2. **멀티모달 분석 부하 분산**: 음성, 영상, 텍스트 분석을 독립적인 워커에서 병렬 처리
3. **장애 격리**: 각 서비스의 독립적 운영으로 부분 장애 시에도 시스템 지속 가능
4. **확장성**: 부하에 따라 특정 서비스만 선택적으로 확장 가능

### 2.3 핵심 설계 원칙
- **단일 책임 원칙**: 각 서비스는 하나의 명확한 역할 수행
- **느슨한 결합**: Redis 메시지 브로커를 통한 서비스 간 통신
- **비동기 처리**: Celery를 활용한 백그라운드 작업 처리
- **상태 관리**: PostgreSQL을 통한 중앙 집중식 상태 관리

---

## 3. 전체 시스템 구성도

### 3.1 시스템 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Frontend (React + Vite)                                  │   │
│  │  - WebRTC Client                                          │   │
│  │  - Interview UI                                           │   │
│  │  - Real-time Dashboard                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Backend-Core (FastAPI)                                   │   │
│  │  - RESTful API                                            │   │
│  │  - Authentication & Authorization                         │   │
│  │  - Session Management                                     │   │
│  │  - Real-time Question Generation (Llama-3.1-8B)          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Task Queue
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Message Broker Layer                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Redis                                                     │   │
│  │  - Task Queue (Celery Broker)                            │   │
│  │  - Session Cache                                          │   │
│  │  - Real-time Data Buffer                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  AI Worker       │ │  Media Server    │ │  Database        │
│  (Celery)        │ │  (WebRTC + STT)  │ │  (PostgreSQL)    │
│                  │ │                  │ │                  │
│ - Evaluator      │ │ - WebRTC Handler │ │ - Users          │
│   (Solar-10.7B)  │ │ - Deepgram STT   │ │ - Interviews     │
│ - Vision         │ │   (Nova-2)       │ │ - Questions      │
│   (DeepFace)     │ │ - Frame Extract  │ │ - Transcripts    │
│ - Question Gen   │ │ - Audio Stream   │ │ - Evaluations    │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

### 3.2 서비스 구성 요소

| 서비스 | 역할 | 기술 스택 | 포트 |
|--------|------|-----------|------|
| **Frontend** | 사용자 인터페이스 | React, Vite, WebRTC | 3000 |
| **Backend-Core** | API 서버, 질문 생성 | FastAPI, Llama-3.1-8B | 8000 |
| **AI-Worker** | 평가 및 감정 분석 | Celery, Solar-10.7B, DeepFace | - |
| **Media-Server** | 실시간 스트리밍 | aiortc, Deepgram Nova-2 | 8080 |
| **Database** | 데이터 저장 | PostgreSQL + pgvector | 5432 |
| **Redis** | 메시지 브로커 | Redis 7 | 6379 |

---

# docker 분리 이유
서비스별 컨테이너 분리는 확장성, 장애 격리, 배포 독립성 확보를 위한 구조로,
각 컴포넌트를 역할 단위로 분리하여 운영 효율성과 안정성을 향상시킨다.
또는
백엔드, 워커, DB, 캐시를 분리하여
실시간 처리와 비동기 처리를 독립적으로 확장 가능하도록 설계했다.
→ 각 서비스별 컨테이너를 분리하여 오류나 수정이 필요할 경우 해당 컨테이너에 해당하는 부분만 수정 후 해당 컨테이너만 재배포

## 4. 서비스 계층 구조

### 4.1 Backend-Core (FastAPI)

**역할**: 중앙 API 서버 및 실시간 질문 생성

**주요 기능**:
- RESTful API 제공 (면접 세션 관리, 질문 조회, 답변 제출)
- JWT 기반 사용자 인증 및 권한 관리
- Llama-3.1-8B를 활용한 실시간 질문 생성
- Celery를 통한 비동기 작업 발행

**기술 스택**:
```python
# 주요 의존성
fastapi >= 0.109.0
sqlmodel >= 0.0.14
celery[redis] >= 5.3.6
langchain >= 0.1.0
transformers >= 4.39.0
torch >= 2.2.0
```

**API 엔드포인트**:
- `POST /register`: 사용자 회원가입
- `POST /token`: 로그인 및 JWT 토큰 발급
- `GET /users/me`: 현재 사용자 정보 조회
- `POST /interviews`: 면접 세션 생성 및 질문 생성
- `GET /interviews/{id}/questions`: 면접 질문 목록 조회
- `POST /transcripts`: 실시간 대화 기록 저장
- `GET /interviews/{id}/transcripts`: 대화 기록 조회
- `POST /interviews/{id}/complete`: 면접 종료 및 평가 요청
- `GET /interviews/{id}/report`: 평가 리포트 조회

**GPU 자원 활용**:
- Llama-3.1-8B 모델 로딩 (FP16/GGUF Q4 양자화)
- VRAM 요구사항: 5GB+
- HuggingFace Pipeline을 통한 추론

### 4.2 AI-Worker (Celery)

**역할**: 정밀 평가 및 멀티모달 분석

**주요 기능**:
- Solar-10.7B 기반 답변 정밀 평가
- DeepFace 기반 표정/감정 분석
- 최종 평가 리포트 생성
- 비동기 DB 업데이트

**기술 스택**:
```python
# 주요 의존성
celery[redis] >= 5.3.6
llama-cpp-python >= 0.2.56
deepface >= 0.0.91
tensorflow >= 2.16.0
langchain >= 0.1.0
opencv-python-headless >= 4.9.0
```

**Celery Tasks**:
1. `tasks.evaluator.analyze_answer`: 답변 평가
2. `tasks.evaluator.generate_final_report`: 최종 리포트 생성
3. `tasks.vision.analyze_emotion`: 감정 분석

**자원 할당**:
- CPU: 8 코어
- RAM: 32GB
- GPU: 1개 (질문 생성용, 선택적)

### 4.3 Media-Server (WebRTC + STT)

**역할**: 실시간 음성 및 영상 스트리밍 처리

**주요 기능**:
- WebRTC P2P 연결 관리
- Deepgram Nova-2 기반 실시간 STT
- 비디오 프레임 추출 (2초 간격)
- WebSocket을 통한 실시간 데이터 전송

**기술 스택**:
```python
# 주요 의존성
aiortc == 1.14.0
deepgram-sdk >= 5.3.1
websockets == 14.1
av >= 14.0.0
opencv-python-headless == 4.9.0.80
```

**주요 엔드포인트**:
- `POST /offer`: WebRTC SDP 교환
- `WebSocket /ws/{session_id}`: 실시간 STT 결과 전송

**처리 흐름**:
1. 클라이언트로부터 WebRTC Offer 수신
2. Audio Track → Deepgram STT → WebSocket 전송
3. Video Track → 프레임 추출 → AI-Worker 전달

### 4.4 Frontend (React + Vite)

**역할**: 사용자 인터페이스 및 WebRTC 클라이언트

**주요 기능**:
- Glassmorphism 기반 프리미엄 UI
- WebRTC 미디어 스트리밍
- 실시간 면접 진행 및 피드백 표시
- 평가 리포트 대시보드

**기술 스택**:
```json
{
  "react": "^18.2.0",
  "react-router-dom": "^6.21.0",
  "axios": "^1.6.2",
  "vite": "^5.0.8"
}
```

**주요 컴포넌트**:
- `App.jsx`: 메인 애플리케이션 라우팅
- `components/`: WebRTC 플레이어, 채팅 UI
- `api/`: Backend API 통신 모듈

---

## 5. 데이터베이스 설계

### 5.1 데이터베이스 선택
**PostgreSQL 18 + pgvector 확장**

**선택 이유**:
- 관계형 데이터의 무결성 보장
- JSONB 타입을 통한 유연한 메타데이터 저장
- pgvector를 통한 벡터 검색 지원 (RAG 연동)
- 트랜잭션 지원으로 데이터 일관성 확보

### 5.2 데이터베이스 스키마

#### 5.2.1 Users (사용자 테이블)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL,  -- candidate, recruiter, admin
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**필드 설명**:
- `id`: 사용자 고유 식별자
- `email`: 이메일 (로그인 ID)
- `username`: 사용자명
- `role`: 사용자 역할 (지원자/채용담당자/관리자)
- `password_hash`: bcrypt 해시된 비밀번호
- `full_name`: 전체 이름

#### 5.2.2 Interviews (면접 세션 테이블)
```sql
CREATE TABLE interviews (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER REFERENCES users(id),
    job_posting_id INTEGER REFERENCES job_postings(id),
    position VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- scheduled, live, completed, cancelled
    scheduled_time TIMESTAMP,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    overall_score FLOAT,
    emotion_summary JSONB
);
```

**필드 설명**:
- `id`: 면접 세션 고유 식별자
- `candidate_id`: 지원자 ID (외래키)
- `position`: 지원 직무
- `status`: 면접 상태 (예정/진행중/완료/취소)
- `overall_score`: 전체 평가 점수
- `emotion_summary`: 감정 분석 요약 (JSON)

#### 5.2.3 Questions (질문 은행 테이블)
```sql
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,  -- technical, behavioral, situational, cultural_fit
    difficulty VARCHAR(20) NOT NULL,  -- easy, medium, hard
    rubric_json JSONB NOT NULL,
    vector_id VARCHAR(255),
    position VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    avg_score FLOAT
);
```

**필드 설명**:
- `content`: 질문 내용
- `category`: 질문 유형
- `difficulty`: 난이도
- `rubric_json`: 평가 기준 (JSON 형식)
- `vector_id`: 벡터 DB 참조 ID (RAG 연동)
- `position`: 특정 직무 전용 질문

#### 5.2.4 Transcripts (대화 기록 테이블)
```sql
CREATE TABLE transcripts (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interviews(id),
    speaker VARCHAR(10) NOT NULL,  -- AI, User
    text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sentiment_score FLOAT,  -- -1.0 ~ 1.0
    emotion VARCHAR(50),  -- happy, neutral, sad, angry
    question_id INTEGER REFERENCES questions(id),
    "order" INTEGER
);
```

**필드 설명**:
- `speaker`: 발화자 (AI/사용자)
- `text`: 대화 내용 (STT 결과)
- `sentiment_score`: 감정 점수
- `emotion`: 감정 분류
- `question_id`: 연관된 질문 ID
- `order`: 대화 순서

#### 5.2.5 Evaluation Reports (평가 리포트 테이블)
```sql
CREATE TABLE evaluation_reports (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER UNIQUE REFERENCES interviews(id),
    technical_score FLOAT,
    communication_score FLOAT,
    cultural_fit_score FLOAT,
    summary_text TEXT,
    details_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evaluator_model VARCHAR(100)
);
```

**필드 설명**:
- `technical_score`: 기술 역량 점수
- `communication_score`: 의사소통 점수
- `cultural_fit_score`: 조직 적합성 점수
- `summary_text`: 종합 평가 요약
- `details_json`: 상세 평가 내용 (JSON)
- `evaluator_model`: 평가에 사용된 LLM 모델명

### 5.3 데이터베이스 관계도

```
users (1) ──────< (N) interviews
                        │
                        ├──< (N) transcripts
                        │
                        └──< (1) evaluation_reports

job_postings (1) ──< (N) interviews

questions (1) ──< (N) transcripts
```

---

## 6. 데이터 흐름 설계

### 6.1 End-to-End 데이터 흐름

```
1. 사용자 로그인
   Frontend → Backend-Core (POST /token)
   ↓
   JWT 토큰 발급 및 반환

2. 면접 세션 생성
   Frontend → Backend-Core (POST /interviews)
   ↓
   Backend-Core: Interview 레코드 생성
   ↓
   Backend-Core: Llama-3.1-8B로 질문 생성
   ↓
   Backend-Core: Questions 및 Transcripts 저장
   ↓
   Frontend: 면접 시작

3. 실시간 미디어 스트리밍
   Frontend (WebRTC) → Media-Server (POST /offer)
   ↓
   Media-Server: WebRTC 연결 수립
   ↓
   Audio Track → Deepgram STT → WebSocket → Frontend
   Video Track → Frame Extract → AI-Worker (Celery)

4. 답변 저장 및 평가
   Frontend → Backend-Core (POST /transcripts)
   ↓
   Backend-Core: Transcript 저장 (Speaker=User)
   ↓
   Backend-Core: Celery Task 발행 (analyze_answer)
   ↓
   AI-Worker: Solar-10.7B로 답변 평가
   ↓
   AI-Worker: Transcript 업데이트 (sentiment_score, emotion)

5. 감정 분석
   Media-Server: Video Frame 추출
   ↓
   AI-Worker (Celery Task: analyze_emotion)
   ↓
   AI-Worker: DeepFace로 감정 분석
   ↓
   AI-Worker: Transcript 업데이트 (emotion)

6. 면접 종료 및 리포트 생성
   Frontend → Backend-Core (POST /interviews/{id}/complete)
   ↓
   Backend-Core: Interview 상태 → COMPLETED
   ↓
   Backend-Core: Celery Task 발행 (generate_final_report)
   ↓
   AI-Worker: 전체 Transcripts 분석
   ↓
   AI-Worker: EvaluationReport 생성 및 저장
   ↓
   Frontend → Backend-Core (GET /interviews/{id}/report)
   ↓
   Frontend: 평가 리포트 표시
```

### 6.2 비동기 작업 흐름

```
Backend-Core (FastAPI)
    │
    │ send_task()
    ▼
Redis (Message Broker)
    │
    │ consume
    ▼
AI-Worker (Celery)
    │
    ├─> tasks.evaluator.analyze_answer
    │   ├─> Solar-10.7B 추론
    │   └─> DB 업데이트
    │
    ├─> tasks.vision.analyze_emotion
    │   ├─> DeepFace 분석
    │   └─> DB 업데이트
    │
    └─> tasks.evaluator.generate_final_report
        ├─> 전체 데이터 집계
        └─> EvaluationReport 생성
```

---

## 7. 멀티모달 처리 파이프라인

### 7.1 음성 처리 파이프라인 (STT)

**기술**: Deepgram Nova-2 API

**처리 흐름**:
```
1. Frontend: 마이크 권한 획득 및 Audio Track 생성
   ↓
2. Media-Server: WebRTC Audio Track 수신
   ↓
3. Media-Server: Deepgram WebSocket 연결
   ↓
4. Media-Server: Audio Frame → Deepgram 전송
   ↓
5. Deepgram: 실시간 음성 인식 (Nova-2 모델)
   ↓
6. Media-Server: Transcript 수신
   ↓
7. Media-Server: WebSocket → Frontend (실시간 표시)
   ↓
8. Backend-Core: Transcript 저장 (POST /transcripts)
```

**특징**:
- 실시간 스트리밍 처리 (WebSocket 기반)
- 한국어 최적화 (Nova-2 모델)
- Smart Format 적용 (구두점, 대소문자 자동 처리)
- 16kHz, Linear16 인코딩

### 7.2 영상 처리 파이프라인 (Vision)

**기술**: DeepFace (VGG 기반)

**처리 흐름**:
```
1. Frontend: 카메라 권한 획득 및 Video Track 생성
   ↓
2. Media-Server: WebRTC Video Track 수신
   ↓
3. Media-Server: 2초 간격 프레임 추출
   ↓
4. Media-Server: Frame → Base64 인코딩
   ↓
5. Media-Server: Celery Task 발행 (analyze_emotion)
   ↓
6. AI-Worker: Base64 → Image 디코딩
   ↓
7. AI-Worker: DeepFace 감정 분석
   ↓
8. AI-Worker: Transcript 업데이트 (emotion)
```

**특징**:
- CPU 부하 최적화 (2초 간격 샘플링)
- 비동기 처리 (Celery를 통한 백그라운드 작업)
- 감정 분류: happy, sad, angry, fear, surprise, disgust, neutral

### 7.3 텍스트 처리 파이프라인 (NLP)

**기술**: LangChain + LLM (Solar-10.7B)

**처리 흐름**:
```
1. Backend-Core: Transcript 수신 (STT 결과)
   ↓
2. Backend-Core: Celery Task 발행 (analyze_answer)
   ↓
3. AI-Worker: 질문 및 답변 텍스트 로드
   ↓
4. AI-Worker: LangChain Prompt 구성
   ↓
5. AI-Worker: Solar-10.7B 추론
   ↓
6. AI-Worker: JSON 파싱 (JsonOutputParser)
   ↓
7. AI-Worker: 평가 점수 및 피드백 추출
   ↓
8. AI-Worker: Transcript 업데이트 (sentiment_score)
```

**특징**:
- 루브릭 기반 평가 (기술적 정확성, 논리적 구성, 전문성)
- JSON 구조화 출력 (시스템 연동 용이)
- 평가 근거 로깅 (추적 가능성)

### 7.4 병렬 처리 전략

```
┌─────────────────────────────────────────┐
│  Media-Server (WebRTC)                  │
└─────────────────────────────────────────┘
              │
              ├──> Audio Track
              │    └─> Deepgram STT (실시간)
              │        └─> WebSocket → Frontend
              │
              └──> Video Track
                   └─> Frame Extract (2초 간격)
                       └─> Celery → AI-Worker
                           └─> DeepFace (비동기)

┌─────────────────────────────────────────┐
│  Backend-Core (FastAPI)                 │
└─────────────────────────────────────────┘
              │
              └──> Transcript 저장
                   └─> Celery → AI-Worker
                       └─> Solar-10.7B (비동기)
```

**병렬성 확보**:
- 음성, 영상, 텍스트 분석이 독립적인 워커에서 실행
- Redis를 통한 작업 큐 관리
- 각 파이프라인의 독립적 확장 가능

---

## 8. AI 모델 아키텍처

### 8.1 LLM 모델 구성

#### 8.1.1 실시간 질문 생성: Llama-3.1-8B

**배포 위치**: Backend-Core (GPU)

**모델 사양**:
- 파라미터: 8B
- 양자화: FP16 / GGUF Q4
- VRAM 요구사항: 5GB+
- 추론 프레임워크: HuggingFace Transformers

**사용 목적**:
- 지원 직무 기반 맞춤형 질문 생성
- 빠른 응답 속도 (실시간 면접 진행)

**프롬프트 전략**:
```python
System: "당신은 전문 면접관입니다. {position} 직무에 적합한 질문을 생성하세요."
User: "직무: {position}, 질문 개수: {count}"
```

**출력 형식**: 텍스트 리스트

#### 8.1.2 정밀 평가: Solar-10.7B

**배포 위치**: AI-Worker (CPU)

**모델 사양**:
- 파라미터: 10.7B
- 양자화: GGUF Q8_0
- RAM 요구사항: 12GB
- 추론 프레임워크: llama-cpp-python

**사용 목적**:
- 답변의 기술적 정확성 평가
- 논리적 구성 및 전문성 분석
- 루브릭 기반 정량적 평가

**프롬프트 전략**:
```python
System: "당신은 면접 평가 전문가입니다. 다음 루브릭에 따라 답변을 평가하세요."
Context: {rubric_json}
User: "질문: {question}\n답변: {answer}"
```

**출력 형식**: JSON
```json
{
  "technical_score": 85,
  "communication_score": 90,
  "depth_score": 75,
  "feedback": "기술적 이해도가 우수하나, 구체적 사례 추가 필요"
}
```

### 8.2 Vision 모델: DeepFace

**배포 위치**: AI-Worker (CPU)

**모델 사양**:
- 백엔드: VGG-Face
- 프레임워크: TensorFlow 2.16+
- 처리 속도: ~100ms/frame (CPU)

**사용 목적**:
- 실시간 표정 분석
- 감정 분류 (7가지 감정)
- 면접 중 긴장도 수치화

**출력 형식**:
```python
{
  "emotion": "neutral",
  "dominant_emotion": "neutral",
  "emotion_scores": {
    "angry": 0.02,
    "disgust": 0.01,
    "fear": 0.05,
    "happy": 0.15,
    "sad": 0.07,
    "surprise": 0.10,
    "neutral": 0.60
  }
}
```

### 8.3 STT 모델: Deepgram Nova-2

**배포 방식**: Cloud API

**모델 사양**:
- 버전: Nova-2
- 언어: 한국어 (ko)
- 샘플레이트: 16kHz
- 인코딩: Linear16

**사용 목적**:
- 실시간 음성-텍스트 변환
- 높은 한국어 인식 정확도
- 낮은 지연 시간

**특징**:
- Smart Format (자동 구두점, 대소문자)
- WebSocket 스트리밍
- 잡음 대응력 우수

### 8.4 모델 성능 비교

| 역할 | 모델명 | 양자화 | 자원 | 추론 속도 | 정확도 |
|------|--------|--------|------|-----------|--------|
| **실시간 질문** | Llama-3.1-8B | FP16/Q4 | GPU (5GB) | ~2초 | 높음 |
| **정밀 평가** | Solar-10.7B | Q8_0 | CPU (12GB) | ~5초 | 매우 높음 |
| **감정 분석** | DeepFace (VGG) | - | CPU | ~100ms | 높음 |
| **음성 인식** | Deepgram Nova-2 | - | Cloud API | 실시간 | 매우 높음 |

---

## 9. 인프라 및 배포 구조

### 9.1 컨테이너 구성 (Docker Compose)

**서비스 구성**:
```yaml
services:
  db:           # PostgreSQL + pgvector
  redis:        # Message Broker
  backend:      # FastAPI + Llama-3.1-8B (GPU)
  ai-worker:    # Celery + Solar-10.7B + DeepFace (CPU)
  media-server: # WebRTC + Deepgram STT
  frontend:     # React + Vite
```

**네트워크**:
- Bridge 네트워크: `interview_network`
- 서비스 간 내부 통신: 컨테이너명으로 DNS 해석

**볼륨**:
- `postgres_data`: DB 데이터 영구 저장
- `./backend-core:/app`: 코드 핫 리로드
- `./ai-worker/models:/app/models`: LLM 모델 파일 마운트

### 9.2 GPU 자원 할당

**Backend-Core**:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**AI-Worker**:
```yaml
deploy:
  resources:
    limits:
      cpus: '8.0'
      memory: 32G
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### 9.3 환경 변수 관리

**.env 파일**:
```bash
# Database
POSTGRES_USER=interview_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=interview_db
DATABASE_URL=postgresql://interview_user:secure_password@db:5432/interview_db

# Redis
REDIS_URL=redis://redis:6379/0

# API Keys
HUGGINGFACE_API_KEY=hf_xxxxx
HUGGINGFACE_HUB_TOKEN=hf_xxxxx
DEEPGRAM_API_KEY=xxxxx

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000
```

### 9.4 배포 환경

**개발 환경**:
- Docker Compose를 통한 로컬 실행
- 코드 핫 리로드 활성화
- 로그 레벨: DEBUG

**프로덕션 환경**:
- GPU 가속 클라우드 인스턴스 (AWS G4dn, GCP T4 등)
- Nginx 리버스 프록시
- HTTPS 적용 (Let's Encrypt)
- 로그 레벨: INFO

### 9.5 CI/CD 파이프라인

**GitHub Actions 워크플로우**:
```yaml
1. Code Push → GitHub
2. GitHub Actions Trigger
3. Docker Image Build
4. Unit Test 실행
5. Integration Test 실행
6. Docker Hub Push
7. Production Server Deploy
```

---

## 10. 보안 및 인증 설계

### 10.1 인증 방식

**JWT (JSON Web Token) 기반 인증**

**토큰 발급 흐름**:
```
1. 사용자 로그인 (POST /token)
   ↓
2. Backend-Core: 사용자 인증 (username + password)
   ↓
3. Backend-Core: JWT 토큰 생성
   - Payload: {"sub": username, "exp": expiration_time}
   - 서명: HS256 알고리즘
   ↓
4. Frontend: 토큰 저장 (localStorage)
   ↓
5. 이후 모든 요청: Authorization: Bearer {token}
```

**토큰 검증**:
```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
        return get_user_by_username(username)
    except JWTError:
        raise HTTPException(status_code=401)
```

### 10.2 비밀번호 보안

**해싱 알고리즘**: bcrypt

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 비밀번호 해싱
hashed_password = pwd_context.hash(plain_password)

# 비밀번호 검증
is_valid = pwd_context.verify(plain_password, hashed_password)
```

### 10.3 CORS 설정

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트엔드 도메인
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 10.4 데이터 보안

**전송 중 데이터**:
- HTTPS 적용 (TLS 1.3)
- WebSocket Secure (WSS)
- WebRTC DTLS 암호화

**저장 데이터**:
- 비밀번호: bcrypt 해싱
- API 키: 환경 변수로 관리 (.env)
- 민감 정보: PostgreSQL 암호화 컬럼 (선택적)

### 10.5 접근 제어

**역할 기반 접근 제어 (RBAC)**:
- `candidate`: 면접 참여, 자신의 리포트 조회
- `recruiter`: 모든 면접 조회, 평가 관리
- `admin`: 시스템 전체 관리

```python
def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

@app.get("/admin/users")
async def get_all_users(admin: User = Depends(require_role(UserRole.ADMIN))):
    # 관리자만 접근 가능
    pass
```

---

## 11. 성능 및 확장성 설계

### 11.1 성능 최적화 전략

#### 11.1.1 LLM 추론 최적화
- **양자화**: GGUF Q4/Q8 적용으로 메모리 사용량 감소
- **배치 처리**: 여러 질문을 한 번에 생성
- **캐싱**: 자주 사용되는 질문 Redis 캐싱

#### 11.1.2 데이터베이스 최적화
- **인덱싱**: 자주 조회되는 컬럼 (user_id, interview_id) 인덱스 생성
- **커넥션 풀링**: SQLModel의 커넥션 풀 활용
- **쿼리 최적화**: N+1 문제 방지 (Eager Loading)

#### 11.1.3 미디어 스트리밍 최적화
- **프레임 샘플링**: 2초 간격으로 프레임 추출 (CPU 부하 감소)
- **비동기 처리**: aiortc의 비동기 I/O 활용
- **버퍼링**: Redis를 통한 임시 데이터 버퍼링

### 11.2 확장성 설계

#### 11.2.1 수평 확장 (Horizontal Scaling)

**Backend-Core**:
```bash
# Docker Compose Scale
docker-compose up -d --scale backend=3
```
- Nginx 로드 밸런서 추가
- 세션 상태는 Redis에 저장 (Stateless)

**AI-Worker**:
```bash
# Celery Worker 증설
docker-compose up -d --scale ai-worker=5
```
- Redis 큐를 통한 작업 분산
- 각 워커는 독립적으로 작업 처리

**Media-Server**:
- WebRTC 특성상 P2P 연결
- 동시 접속자 증가 시 서버 인스턴스 추가

#### 11.2.2 수직 확장 (Vertical Scaling)

**GPU 자원**:
- 더 큰 VRAM을 가진 GPU로 업그레이드
- 더 큰 모델 (Llama-70B 등) 사용 가능

**CPU/RAM**:
- AI-Worker의 CPU 코어 및 RAM 증설
- 더 많은 동시 평가 작업 처리

### 11.3 병목 현상 방지

**LLM 응답 지연 대응**:
- STT 스트리밍으로 사용자에게 실시간 피드백
- 로딩 애니메이션 및 진행 상태 표시
- 비동기 평가로 면접 진행과 평가 분리

**동시 접속자 증가 대응**:
- Redis 큐를 통한 작업 순서 관리
- Celery Worker 자동 확장 (Auto-scaling)
- 우선순위 큐 적용 (실시간 질문 > 평가)

### 11.4 성능 모니터링

**메트릭 수집**:
- API 응답 시간 (FastAPI middleware)
- LLM 추론 시간 (로깅)
- Celery 작업 처리 시간
- DB 쿼리 시간

**모니터링 도구** (향후 확장):
- Prometheus: 메트릭 수집
- Grafana: 대시보드 시각화
- Sentry: 에러 추적

---

## 12. 로깅 및 모니터링

### 12.1 로깅 전략

**로그 레벨**:
- `DEBUG`: 개발 환경 상세 로그
- `INFO`: 일반 작업 흐름
- `WARNING`: 잠재적 문제
- `ERROR`: 에러 발생
- `CRITICAL`: 시스템 장애

**로그 형식**:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
```

**로그 저장 위치**:
- Backend-Core: `./backend-core/logs/`
- AI-Worker: `./ai-worker/logs/`
- Media-Server: `./media-server/logs/`

### 12.2 추적 가능성 (Traceability)

**Rationale Log**:
- AI가 특정 점수를 부여한 텍스트 근거 기록
- `details_json` 필드에 평가 근거 저장

**RAG Trace**:
- 질문 생성 시 참조한 문서 ID 기록
- `vector_id` 필드에 벡터 DB 참조 저장

**Error Log**:
- API 장애 발생 시 재시도 로직
- 에러 스택 트레이스 저장

### 12.3 모니터링 대상

**시스템 메트릭**:
- CPU/GPU 사용률
- 메모리 사용량
- 디스크 I/O
- 네트워크 대역폭

**애플리케이션 메트릭**:
- API 요청 수 및 응답 시간
- Celery 작업 큐 길이
- DB 커넥션 풀 상태
- WebRTC 연결 수

**비즈니스 메트릭**:
- 면접 세션 수
- 평균 면접 시간
- 평균 평가 점수
- 사용자 만족도

---

## 13. 기술 스택 상세

### 13.1 Backend 기술 스택

| 분류 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **Framework** | FastAPI | 0.109+ | RESTful API 서버 |
| **ORM** | SQLModel | 0.0.14+ | 데이터베이스 ORM |
| **Task Queue** | Celery | 5.3.6+ | 비동기 작업 처리 |
| **Message Broker** | Redis | 7.0 | Celery 브로커 및 캐시 |
| **Database** | PostgreSQL | 18 | 관계형 데이터베이스 |
| **Vector DB** | pgvector | - | 벡터 검색 (RAG) |
| **Authentication** | python-jose | 3.3.0+ | JWT 토큰 생성/검증 |
| **Password Hashing** | passlib[bcrypt] | 1.7.4+ | 비밀번호 해싱 |

### 13.2 AI/ML 기술 스택

| 분류 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **LLM Framework** | LangChain | 0.1.0+ | LLM 체인 구성 |
| **LLM (질문 생성)** | Llama-3.1-8B | - | 실시간 질문 생성 |
| **LLM (평가)** | Solar-10.7B | - | 답변 정밀 평가 |
| **Inference** | llama-cpp-python | 0.2.56+ | GGUF 모델 추론 |
| **Transformers** | transformers | 4.39+ | HuggingFace 모델 |
| **Deep Learning** | PyTorch | 2.2.0+ | GPU 가속 추론 |
| **Vision** | DeepFace | 0.0.91+ | 표정/감정 분석 |
| **Vision Backend** | TensorFlow | 2.16+ | DeepFace 백엔드 |
| **Image Processing** | OpenCV | 4.9.0+ | 프레임 처리 |
| **STT** | Deepgram SDK | 5.3.1+ | 실시간 음성 인식 |

### 13.3 Media 기술 스택

| 분류 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **WebRTC** | aiortc | 1.14.0 | 실시간 미디어 스트리밍 |
| **Audio/Video** | PyAV | 14.0+ | 미디어 프레임 처리 |
| **WebSocket** | websockets | 14.1 | 실시간 데이터 전송 |
| **HTTP Client** | aiohttp | 3.11.11 | 비동기 HTTP 통신 |

### 13.4 Frontend 기술 스택

| 분류 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **Framework** | React | 18.2.0 | UI 프레임워크 |
| **Build Tool** | Vite | 5.0.8 | 빌드 도구 |
| **Routing** | react-router-dom | 6.21.0 | 클라이언트 라우팅 |
| **HTTP Client** | axios | 1.6.2 | API 통신 |
| **WebSocket** | socket.io-client | 4.7.2 | 실시간 통신 |

### 13.5 Infrastructure 기술 스택

| 분류 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **Containerization** | Docker | 20.10+ | 컨테이너화 |
| **Orchestration** | Docker Compose | 2.0+ | 멀티 컨테이너 관리 |
| **GPU Runtime** | NVIDIA Docker | - | GPU 컨테이너 지원 |
| **OS** | Ubuntu | 22.04 | 서버 운영체제 |

---

## 14. 한계 및 향후 확장

### 14.1 현재 시스템의 한계

#### 14.1.1 기술적 한계
1. **실시간 영상 분석의 높은 연산 비용**
   - DeepFace 모델의 CPU 의존성
   - 프레임 샘플링으로 인한 정보 손실 가능성
   - GPU 가속 미지원

2. **LLM 추론 지연**
   - Solar-10.7B의 CPU 추론 시간 (~5초)
   - 동시 다수 사용자 처리 시 대기 시간 증가

3. **하드웨어 의존성**
   - GPU 필수 (Llama-3.1-8B)
   - 고사양 CPU 및 RAM 요구 (AI-Worker)

4. **Deepgram API 의존성**
   - 클라우드 API 비용 발생
   - 네트워크 장애 시 STT 불가

#### 14.1.2 기능적 한계
1. **단일 언어 지원**
   - 현재 한국어만 지원
   - 다국어 면접 미지원

2. **제한적인 감정 분석**
   - 표정만 분석 (음성 톤 미분석)
   - 2초 간격 샘플링으로 순간적 감정 변화 놓칠 수 있음

3. **평가 기준의 고정성**
   - 루브릭이 사전 정의되어야 함
   - 직무별 세밀한 커스터마이징 제한적

### 14.2 향후 확장 계획

#### 14.2.1 단기 확장 (3개월 이내)
1. **음성 톤 분석 추가**
   - librosa를 활용한 음성 특징 추출
   - 긴장도, 자신감 수치화

2. **RAG 시스템 고도화**
   - 기업별 인재상 데이터베이스 구축
   - 최신 기술 트렌드 자동 업데이트

3. **평가 리포트 고도화**
   - 시각화 차트 추가 (감정 변화 그래프)
   - 개선 방안 구체적 제시

4. **모니터링 시스템 구축**
   - Prometheus + Grafana 연동
   - 실시간 성능 대시보드

#### 14.2.2 중기 확장 (6개월 이내)
1. **다국어 지원**
   - 영어 면접 모드 추가
   - Deepgram 다국어 모델 연동
   - 다국어 LLM (Llama-3.1 Multilingual)

2. **GPU 가속 감정 분석**
   - DeepFace → GPU 기반 모델 전환
   - 실시간 프레임 분석 (샘플링 제거)

3. **사용자 맞춤형 훈련 기능**
   - 표정 훈련 모드 (피드백 제공)
   - 음성 톤 개선 가이드

4. **면접관 대시보드**
   - 실시간 면접 모니터링
   - 수동 평가 기능 추가

#### 14.2.3 장기 확장 (1년 이내)
1. **온프레미스 STT 모델**
   - Whisper 모델 자체 호스팅
   - Deepgram 의존성 제거

2. **멀티모달 통합 평가**
   - 음성, 영상, 텍스트를 통합한 종합 평가
   - 멀티모달 LLM (GPT-4V 등) 활용

3. **AI 면접관 아바타**
   - TTS (Text-to-Speech) 연동
   - 가상 면접관 영상 생성

4. **모바일 앱 개발**
   - React Native 기반 모바일 앱
   - 모바일 WebRTC 지원

5. **기업용 SaaS 전환**
   - 멀티 테넌시 아키텍처
   - 기업별 커스터마이징 기능
   - 구독 기반 과금 시스템

### 14.3 확장 시 고려사항

1. **비용 최적화**
   - Deepgram API 비용 관리
   - GPU 인스턴스 비용 최적화
   - 오픈소스 모델 우선 활용

2. **데이터 프라이버시**
   - GDPR, 개인정보보호법 준수
   - 면접 영상/음성 데이터 암호화
   - 사용자 동의 절차 강화

3. **모델 업데이트 전략**
   - A/B 테스트를 통한 모델 성능 비교
   - 점진적 모델 교체 (Blue-Green Deployment)
   - 모델 버전 관리

4. **확장성 테스트**
   - 부하 테스트 (Locust, JMeter)
   - 동시 접속자 1000명 이상 대응
   - 자동 확장 정책 수립

---

## 부록

### A. 참조 문서
- `README.md`: 프로젝트 개요 및 실행 방법
- `docker-compose.yml`: 서비스 구성 및 환경 설정
- `wbs_output_jm.md`: 산출물 및 PoC 검증 보고서
- `.agent/workflows/`: 프로젝트 워크플로우

### B. 용어 정리
- **EDA**: Event-Driven Architecture (이벤트 기반 아키텍처)
- **STT**: Speech-to-Text (음성-텍스트 변환)
- **LLM**: Large Language Model (대규모 언어 모델)
- **RAG**: Retrieval-Augmented Generation (검색 증강 생성)
- **WebRTC**: Web Real-Time Communication (웹 실시간 통신)
- **JWT**: JSON Web Token (JSON 웹 토큰)
- **CORS**: Cross-Origin Resource Sharing (교차 출처 리소스 공유)
- **ORM**: Object-Relational Mapping (객체-관계 매핑)

### C. 버전 히스토리
- **v1.0** (2026-01-20): 초기 시스템 설계
- **v2.0** (2026-01-26): 마이크로서비스 아키텍처 전환, 멀티모달 파이프라인 추가

---

**문서 작성자**: 엄재민  
**최종 수정일**: 2026-01-26  
**문서 버전**: 2.0
