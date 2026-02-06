# 🎯 Big20 AI Interview Project

**AI 기반 실시간 면접 시스템** - 맞춤형 질문 생성, 실시간 평가, 감정 분석

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)

---

## 📋 목차

1. [프로젝트 개요](#-프로젝트-개요)
2. [주요 기능](#-주요-기능)
3. [시스템 아키텍처](#-시스템-아키텍처)
4. [프로젝트 구조](#-프로젝트-구조)
5. [빠른 시작](#-빠른-시작)
6. [기술 스택](#-기술-스택)
7. [API 문서](#-api-문서)
8. [개발 가이드](#-개발-가이드)

---

## 🎯 프로젝트 개요

Big20 AI Interview Project는 **AI 기술을 활용한 차세대 면접 시스템**입니다.

### 핵심 가치
- ✅ **맞춤형 질문 생성**: 이력서와 직무 분석을 통한 개인화된 면접 질문
- ✅ **실시간 평가**: AI 기반 답변 평가 및 즉각적인 피드백
- ✅ **감정 분석**: 표정 및 음성 분석을 통한 종합적 평가
- ✅ **확장 가능한 구조**: 마이크로서비스 아키텍처로 유연한 확장

---

## 🚀 주요 기능

### 1. **이력서 기반 질문 생성**
- PDF/DOCX 이력서 자동 파싱
- 섹션별 임베딩 (경력, 프로젝트, 기술 스택 등)
- RAG 기반 맞춤형 질문 생성

### 2. **실시간 면접 진행**
- WebRTC 기반 영상/음성 스트리밍
- Deepgram STT (클라이언트 사이드)
- 실시간 감정 분석 (DeepFace)

### 3. **AI 평가 시스템**
- Solar-10.7B 기반 답변 평가
- 기술적/행동적 역량 분석
- 종합 피드백 리포트 생성

### 4. **관리자 대시보드**
- 면접 진행 상황 모니터링
- 지원자 이력서 검색
- 평가 결과 분석

---

## 🏗️ 시스템 아키텍처

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│ Backend-Core │─────▶│  AI-Worker  │
│   (React)   │      │   (FastAPI)  │      │   (Celery)  │
└─────────────┘      └──────────────┘      └─────────────┘
       │                     │                      │
       │                     ▼                      ▼
       │              ┌──────────┐          ┌──────────┐
       │              │PostgreSQL│          │  Redis   │
       │              │ + pgvector│         │  Broker  │
       │              └──────────┘          └──────────┘
       │
       ▼
┌─────────────┐
│Media-Server │
│  (WebRTC)   │
└─────────────┘
```

### 마이크로서비스 구성

| 서비스 | 역할 | 기술 스택 |
|--------|------|-----------|
| **Frontend** | 사용자 인터페이스 | React, Vite, WebRTC |
| **Backend-Core** | API 서버, 인증, 라우팅 | FastAPI, SQLModel, JWT |
| **AI-Worker** | 질문 생성, 평가, 이력서 파싱 | Celery, LangChain, Llama-3.1 |
| **Media-Server** | 실시간 스트리밍, 감정 분석 | aiortc, DeepFace |
| **PostgreSQL** | 데이터베이스 + 벡터 검색 | PostgreSQL 16 + pgvector |
| **Redis** | 메시지 브로커, 캐싱 | Redis 7 |

---

## 📁 프로젝트 구조

```
Big20_aI_interview_project/
├── backend-core/              # FastAPI 메인 서버
│   ├── main.py               # API 엔드포인트
│   ├── models.py             # DB 모델 (SQLModel)
│   ├── database.py           # DB 연결 설정
│   ├── routes/               # API 라우터 (분리 예정)
│   │   ├── auth.py          # 인증 관련
│   │   ├── interviews.py    # 면접 관련
│   │   └── resumes.py       # 이력서 관련
│   ├── utils/               # 유틸리티
│   │   ├── auth_utils.py    # JWT, 비밀번호 해싱
│   │   ├── rubric_generator.py  # 평가 루브릭
│   │   └── logging_config.py    # 로깅 설정
│   └── tests/               # 테스트 코드
│
├── ai-worker/                # Celery Worker
│   ├── main.py              # Worker 실행부
│   ├── db.py                # DB 연결 (공유 모델)
│   ├── tasks/               # Celery Task
│   │   ├── question_generator.py  # 질문 생성
│   │   ├── evaluator.py          # 답변 평가
│   │   ├── resume_parser.py      # 이력서 파싱
│   │   └── resume_embedding.py   # 섹션별 임베딩
│   ├── utils/               # 유틸리티
│   │   ├── vector_utils.py       # 벡터 임베딩 (KURE-v1)
│   │   ├── resume_embedder.py    # 이력서 섹션 임베딩
│   │   ├── pdf_parser.py         # PDF 파싱
│   │   └── section_splitter.py   # 섹션 분할
│   └── tools/               # LangChain 도구
│       ├── resume_tool.py        # 이력서 검색 도구
│       └── company_tool.py       # 회사 정보 도구
│
├── media-server/            # WebRTC 서버
│   ├── main.py             # aiortc 서버
│   └── requirements.txt
│
├── frontend/                # React 프론트엔드
│   ├── src/
│   │   ├── components/     # UI 컴포넌트
│   │   │   ├── AuthPage.jsx
│   │   │   ├── InterviewPage.jsx
│   │   │   └── ResultPage.jsx
│   │   ├── App.jsx         # 메인 앱
│   │   └── index.css       # 글로벌 스타일
│   ├── public/
│   └── package.json
│
├── docs/                    # 프로젝트 문서
│   ├── SYSTEM_SPECIFICATION.md    # 시스템 명세
│   ├── RESUME_EMBEDDING_GUIDE.md  # 이력서 임베딩 가이드
│   ├── SECURITY_GUIDE.md          # 보안 가이드
│   ├── DB_INSERT_GUIDE.md         # DB 데이터 삽입 가이드
│   └── TROUBLESHOOTING.md         # 문제 해결 가이드
│
├── docker-compose.yml       # 서비스 오케스트레이션
├── .env.example            # 환경 변수 예시
└── README.md               # 프로젝트 문서 (이 파일)
```

---

## 🚀 빠른 시작

### 1️⃣ 사전 요구사항

- **Docker** 및 **Docker Compose** 설치
- **Git** 설치
- **최소 시스템 사양**:
  - RAM: 16GB 이상
  - GPU: NVIDIA GPU (VRAM 6GB+) 권장
  - 디스크: 20GB 이상 여유 공간

### 2️⃣ 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/your-org/Big20_aI_interview_project.git
cd Big20_aI_interview_project

# 2. 환경 변수 설정
cp .env.example .env

# 3. .env 파일 편집 (API 키 입력)
# - HUGGINGFACE_API_KEY: https://huggingface.co/settings/tokens
# - DEEPGRAM_API_KEY: https://console.deepgram.com/
# - DATABASE_URL: PostgreSQL 연결 정보
```

### 3️⃣ 서비스 실행

```bash
# Docker Compose로 전체 서비스 시작
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f backend-core
```

### 4️⃣ 서비스 접속

| 서비스 | URL | 설명 |
|--------|-----|------|
| **Frontend** | http://localhost:3000 | 웹 인터페이스 |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Media Server** | http://localhost:8080 | WebRTC 서버 |

### 5️⃣ 초기 데이터 설정

```bash
# DB 초기화 및 샘플 데이터 삽입
docker-compose exec backend-core python populate_industry_position.py

# 관리자 계정 생성 (자동)
# Username: admin
# Password: admin1234
```

---

## 🛠️ 기술 스택

### Backend
- **Framework**: FastAPI 0.109+
- **ORM**: SQLModel 0.0.14+
- **Database**: PostgreSQL 16 + pgvector
- **Task Queue**: Celery 5.3.6+ + Redis
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt

### AI/ML
- **LLM**: Llama-3.1-8B (질문 생성), Solar-10.7B (평가)
- **Embedding**: KURE-v1 (한국어 특화, 1024차원)
- **Vision**: DeepFace (감정 분석)
- **STT**: Deepgram Nova-2 (한국어 최적화)
- **Framework**: LangChain, Transformers, PyTorch

### Frontend
- **Framework**: React 18.2
- **Build Tool**: Vite 5.0
- **Styling**: Vanilla CSS (Glassmorphism)
- **HTTP Client**: Axios
- **Real-time**: WebRTC, WebSocket

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Message Broker**: Redis 7
- **Vector Database**: pgvector (PostgreSQL extension)

---

## 📚 API 문서

### 주요 엔드포인트

#### 인증 (Authentication)
```http
POST /auth/register          # 회원가입
POST /auth/token            # 로그인 (JWT 발급)
GET  /users/me              # 현재 사용자 정보
```

#### 이력서 (Resumes)
```http
POST /resumes/upload        # 이력서 업로드
GET  /resumes/{id}          # 이력서 상태 조회
GET  /resumes               # 이력서 목록
POST /resumes/search        # 이력서 검색 (벡터 유사도)
```

#### 면접 (Interviews)
```http
POST /interviews            # 면접 생성
GET  /interviews/{id}       # 면접 정보 조회
POST /interviews/{id}/start # 면접 시작
POST /interviews/{id}/complete  # 면접 종료
GET  /interviews/{id}/report    # 평가 리포트
```

#### 질문 (Questions)
```http
GET  /interviews/{id}/questions     # 면접 질문 목록
POST /interviews/{id}/next-question # 다음 질문 생성
```

자세한 API 명세는 http://localhost:8000/docs 참조

---

## 👨‍💻 개발 가이드

### 로컬 개발 환경 설정

#### Backend 개발
```bash
cd backend-core

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend 개발
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 테스트 실행

```bash
# Backend 테스트
cd backend-core
pytest tests/ -v --cov=.

# 특정 테스트만 실행
pytest tests/test_auth.py -v
```

### 코드 품질 체크

```bash
# Python 문법 체크
python -m py_compile backend-core/main.py

# 전체 Python 파일 체크
find . -name "*.py" -exec python -m py_compile {} \;
```

---

## 📊 DB 스키마

### 주요 테이블

#### Users (사용자)
- 지원자, 채용담당자, 관리자 정보
- JWT 인증 기반

#### Resumes (이력서)
- 파일 정보, 파싱 상태
- structured_data (JSONB): 파싱된 정보

#### ResumeSectionEmbedding (섹션별 임베딩)
- 경력, 프로젝트, 자기소개 등 섹션별 벡터
- pgvector 기반 유사도 검색

#### ResumeChunk (청크 임베딩)
- 500자 단위 텍스트 청크
- 일반 RAG 검색용

#### Interviews (면접)
- 면접 세션 정보
- 상태 관리 (scheduled, live, completed)

#### Questions (질문)
- AI 생성 질문
- 재사용 통계 (usage_count, avg_score)

#### Transcripts (대화 기록)
- 실시간 대화 내용
- 감정 분석 결과

#### EvaluationReport (평가 리포트)
- 종합 평가 결과
- 기술적/행동적 점수

---

## 🔒 보안

자세한 보안 가이드는 [`docs/SECURITY_GUIDE.md`](docs/SECURITY_GUIDE.md) 참조

### 핵심 보안 사항
- ✅ `.env` 파일은 Git에 커밋하지 않기
- ✅ API 키를 코드에 하드코딩하지 않기
- ✅ JWT Secret Key는 강력한 랜덤 문자열 사용
- ✅ 프로덕션 환경에서는 HTTPS 강제
- ✅ 비밀번호는 bcrypt로 해싱

---

## 📖 추가 문서

- [시스템 명세서](docs/SYSTEM_SPECIFICATION.md)
- [이력서 임베딩 가이드](docs/RESUME_EMBEDDING_GUIDE.md)
- [DB 데이터 삽입 가이드](docs/DB_INSERT_GUIDE.md)
- [문제 해결 가이드](docs/TROUBLESHOOTING.md)
- [보안 가이드](docs/SECURITY_GUIDE.md)

---

## 🤝 기여 가이드

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

커밋 메시지는 [`commit_convention.md`](commit_convention.md) 참조

---

## 📝 라이선스

This project is licensed under the MIT License

---

## 👥 팀

**Big20 Team** - AI Interview System Development

---

## 📞 문의

프로젝트 관련 문의사항은 Issue를 통해 남겨주세요.

---

**Last Updated**: 2026-02-06
