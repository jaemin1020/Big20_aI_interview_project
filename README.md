## 1. 프로젝트 폴더 구조

Big20_aI_interview_project/

```plaintext
├── .env                        # 공통 환경 변수 (API 키, DB 접속 정보)
├── docker-compose.yml          # 전체 서비스 오케스트레이션 (포트 및 네트워크 설정)
├── commit_convention.md        # 커밋 메시지 컨벤션 가이드
├── README.md                   # 프로젝트 문서
│
├── backend-core/               # [FastAPI] 실시간 질문 생성 및 메인 API
│   ├── main.py                 # API 라우팅, Celery 태스크 발행
│   ├── database.py             # PostgreSQL & SQLModel 설정
│   ├── models.py               # DB 테이블 정의 (InterviewSession, Question, Answer)
│   ├── auth.py                 # 사용자 인증 및 보안 관련 로직
│   ├── utils/                  # 유틸리티 모듈
│   │   ├── question_helper.py  # 질문 생성 헬퍼
│   │   └── rubric_generator.py # 평가 루브릭 생성기
│   ├── logs/                   # 백엔드 서비스 로그 저장
│   ├── Dockerfile
│   └── requirements.txt
│
├── ai-worker/                  # [Celery] 정밀 평가, 질문 생성, 감정 분석
│   ├── main.py                 # Celery Worker 실행부
│   ├── db.py                   # 워커용 데이터베이스 연결 유틸리티
│   ├── tasks/
│   │   ├── question_generator.py # Llama-3.1 기반 직무 맞춤형 질문 생성
│   │   ├── evaluator.py        # Solar-10.7B 기반 답변 정밀 평가
│   │   └── vision.py           # DeepFace 기반 표정/감정 분석 (예정)
│   ├── tools/                  # LangChain 도구 (ResumeTool, CompanyTool)
│   ├── models/                 # LLM 모델 파일 저장 (.gguf)
│   ├── logs/                   # 워커 상세 로그
│   ├── Dockerfile
│   └── requirements.txt
│
├── media-server/               # [WebRTC] 실시간 음성 및 영상 스트리밍 서버
│   ├── main.py                 # aiortc & Deepgram(Nova-2) STT 연동
│   ├── logs/                   # 스트리밍 로그
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # [React/Vite] 웹 인터페이스
│   ├── src/
│   │   ├── components/         # UI 컴포넌트
│   │   ├── api/                # API 통신 모듈
│   │   ├── App.jsx             # 메인 앱 로직
│   │   └── main.jsx            # 진입점
│   ├── public/                 # 정적 자원
│   ├── vite.config.js          # Vite 설정
│   ├── Dockerfile
│   └── package.json
│
├── docs/                       # 프로젝트 문서 및 가이드
│   ├── DB_CONNECTION_STANDARD.md
│   └── DB_INSERT_GUIDE.md
│
└── infra/                      # 인프라 데이터 저장소 (Volume)
    ├── postgres/               # DB 데이터
    └── redis/                  # Celery 브로커 데이터
```

## 2. 프로젝트 실행 (Workflow)

이 프로젝트는 Docker Compose를 사용하여 간편하게 실행할 수 있습니다.
자세한 단계는 `.agent/workflows/setup-project.md`를 참고하거나 다음 명령어를 실행하세요:

1. `docker-compose build`
2. `docker-compose up -d`

### 🗄️ VectorDB 구축 (선택)

프로젝트는 **PostgreSQL + pgvector**를 사용하여 질문/답변 유사도 검색을 지원합니다.

#### 빠른 시작
```bash
# 1. Backend 컨테이너 접속
docker exec -it interview_backend bash

# 2. VectorDB 테스트
cd /app/scripts
python test_vectordb.py

# 3. 샘플 데이터 삽입
python populate_vectordb.py

# 4. 검색 기능 테스트
python vector_utils.py
```

#### 주요 기능
- ✅ **유사 질문 검색**: 사용자 입력과 의미적으로 유사한 질문 추천
- ✅ **답변 평가**: 우수 답변과 비교하여 자동 채점
- ✅ **질문 추천**: 직무/기술 스택 기반 맞춤형 질문 생성
- ✅ **하이브리드 검색**: 키워드 + 벡터 검색 결합

📖 **상세 가이드**: [`VECTORDB_QUICKSTART.md`](./VECTORDB_QUICKSTART.md) 또는 [`.agent/workflows/vectordb-setup-guide.md`](./.agent/workflows/vectordb-setup-guide.md)

### 🗣️ 자연어DB 활용 (기본 제공)

프로젝트는 **PostgreSQL**을 사용하여 자연어 텍스트를 저장하고 검색합니다. (이미 구축됨!)

#### 빠른 시작
```bash
# 1. Backend 컨테이너 접속
docker exec -it interview_backend bash

# 2. 자연어 검색 테스트
cd /app/scripts
python natural_language_utils.py

# 3. 검색 인덱스 생성 (성능 최적화)
docker exec -i interview_db psql -U admin -d interview_db < infra/postgres/create_indexes.sql
```

#### 주요 기능
- ✅ **키워드 검색**: LIKE/ILIKE를 사용한 정확한 텍스트 매칭
- ✅ **전문 검색**: PostgreSQL Full-Text Search (랭킹 지원)
- ✅ **필터링**: 카테고리, 난이도, 직무별 질문 필터링
- ✅ **통계 분석**: 면접 대화 내용 분석, 키워드 빈도 분석

#### VectorDB vs 자연어DB

| 구분 | 자연어DB | VectorDB |
|------|----------|----------|
| **검색 방식** | 키워드 매칭 | 의미적 유사도 |
| **사용 케이스** | 정확한 검색, 필터링 | 유사 질문 추천 |
| **예시** | "Python" 포함 질문 검색 | "파이썬 멀티스레딩"과 유사한 질문 |

📖 **상세 가이드**: [`NATURAL_LANGUAGE_DB_GUIDE.md`](./NATURAL_LANGUAGE_DB_GUIDE.md) 또는 [`NATURAL_LANGUAGE_DB_QUICKSTART.md`](./NATURAL_LANGUAGE_DB_QUICKSTART.md)

## 3. 핵심 구현 내용 (Technical Implementation)

### 🔹 Backend-Core (FastAPI)

- **RESTful API**: 면접 세션 관리, 질문 조회, 답변 제출 엔드포인트 구현.
- **ORM (SQLModel)**: PostgreSQL 연동을 통한 데이터 영속성 관리 (InterviewSession, Question, Answer).
- **LLM Integration**: Llama-3.1-8B 기반의 직무 맞춤형 실시간 면접 질문 생성 로직 (HuggingFace Pipeline).
- **Task Broker**: Celery를 통해 정밀 평가 및 감정 분석 작업을 비동기적으로 Worker에 전달.

### 🔹 AI-Worker (Celery & LangChain)

- **정밀 평가 (Evaluator)**: Solar-10.7B 모델과 LangChain `JsonOutputParser`를 활용한 기술적 피드백 생성.
- **시각 분석 (Vision)**: `DeepFace` 모델을 사용하여 수신된 영상 프레임에서 사용자 감정(Emotion) 추출.
- **Async DB Update**: 분석이 완료된 결과는 워커 프로세스에서 직접 DB에 반영하여 실시간성 확보.

### 🔹 Media-Server (WebRTC & STT)

- **Real-time Streaming**: `aiortc` 라이브러리를 사용해 프론트엔드와 WebRTC 연결 및 미디어 트랙 처리.
- **Frame Extraction**: CPU 부하 최적화를 위해 2초 간격으로 비디오 프레임을 추출하여 AI-Worker로 전달.
- **STT**: Deepgram SDK(Nova-2 모델)를 통한 음성-텍스트 실시간 변환 기반 마련.

### 🔹 Frontend (React & Vite)

- **Glassmorphism UI**: 프리미엄 다크 모드 테마와 반응형 레이아웃 적용.
- **Interview Flow**: 면접 시작 -> 질문 대기 -> 실시간 답변/분석 -> 최종 리포트 대시보드 구현.
- **WebRTC Client**: 브라우저 카메라/마이크 권한 획득 및 미디어 서버와의 P2P 통신 연동.

## 4. 모델 성능 및 사양

| 역할                  | 모델 명         | 양자화(Format) | 가동 자원        | 비고               |
| :-------------------- | :-------------- | :------------- | :--------------- | :----------------- |
| **실시간 질문** | Llama-3.1-8B    | FP16/GGUF Q4   | GPU (VRAM 5GB+)  | 빠른 반응성 중심   |
| **정밀 평가**   | Solar-10.7B     | GGUF (Q8_0)    | CPU + RAM (12GB) | 높은 평가 정확도   |
| **감정 분석**   | DeepFace (VGG)  | -              | CPU              | 실시간 프레임 분석 |
| **음성 인식**   | Deepgram Nova-2 | Cloud API      | Network          | 한국어 최적화      |

## 5. 기술 스택 및 의존성 요약 (Tech Stack & Dependencies)

### 서비스별 주요 라이브러리

| 서비스                 | 분류                | 주요 라이브러리 및 버전                                                             |
| :--------------------- | :------------------ | :---------------------------------------------------------------------------------- |
| **Backend-Core** | **Framework** | `FastAPI (>=0.109)`, `SQLModel (>=0.0.14)`, `Celery (>=5.3.6)`                |
|                        | **AI/ML**     | `LangChain (>=0.1.0)`, `Transformers (>=4.39)`, `PyTorch (>=2.2.0)`           |
| **AI-Worker**    | **Inference** | `llama-cpp-python (>=0.2.56)`, `DeepFace (>=0.0.91)`, `TensorFlow (>=2.16.0)` |
|                        | **Analysis**  | `LangChain-Community (>=0.0.1)`, `OpenCV (>=4.9.0)`                             |
| **Media-Server** | **Streaming** | `aiortc (>=1.14.0)`, `Deepgram SDK (>=5.3.1)`, `PyAV (>=14.0)`                |
|                        | **Network**   | `websockets (>=14.1)`, `aiohttp (>=3.11.11)`                                    |
| **Frontend**     | **UI/UX**     | `React (>=18.2)`, `Vite (>=5.0.8)`, `Axios (>=1.6.2)`                         |

---

### 📦 세부 의존성 목록 (Full Dependency List)

<details>
<summary>📂 <b>Backend-Core Dependencies</b> (클릭하여 펼치기)</summary>

- **Web/API**: `fastapi>=0.109.0`, `uvicorn[standard]>=0.27.0`, `python-multipart>=0.0.9`
- **Database**: `sqlmodel>=0.0.14`, `psycopg2-binary>=2.9.9`
- **AI Engine**: `langchain>=0.1.0`, `langchain-huggingface>=0.0.1`, `transformers>=4.39.0`, `torch>=2.2.0`, `bitsandbytes>=0.42.0`
- **Task Queue**: `celery[redis]>=5.3.6`, `redis>=5.0.3`
- **Security**: `python-jose[cryptography]>=3.3.0`, `passlib[bcrypt]>=1.7.4`, `bcrypt>=4.0.1`, `python-dotenv>=1.0.1`

</details>

<details>
<summary>📂 <b>AI-Worker Dependencies</b> (클릭하여 펼치기)</summary>

- **Inference**: `llama-cpp-python>=0.2.56` (Dockerfile build), `deepface>=0.0.91`, `tensorflow>=2.16.0`
- **Core**: `langchain>=0.1.0`, `langchain-community>=0.0.1`, `pydantic>=1.10.13,<2.0.0`
- **Processing**: `opencv-python-headless>=4.9.0.8`, `numpy>=1.23.0,<2.0.0`, `librosa>=0.10.1`
- **Infrastructure**: `celery[redis]>=5.3.6`, `redis>=5.0.3`, `sqlmodel>=0.0.14`

</details>

<details>
<summary> <b>Media-Server Dependencies</b> (클릭하여 펼치기)</summary>

- **Real-time**: `aiortc==1.14.0`, `deepgram-sdk>=5.3.1`, `websockets==14.1`
- **Multimedia**: `av>=14.0.0`, `opencv-python-headless==4.9.0.80`, `pylibsrtp==0.10.0`
- **Network**: `aiohttp==3.11.11`, `fastapi==0.115.6`, `uvicorn==0.34.0`
- **Bridge**: `celery[redis]==5.4.0`, `redis==5.2.1`

</details>

<details>
<summary>📂 <b>Frontend Dependencies</b> (클릭하여 펼치기)</summary>

- **Core**: `react^18.2.0`, `react-dom^18.2.0`, `react-router-dom^6.21.0`
- **HTTP/WS**: `axios^1.6.2`, `socket.io-client^4.7.2`
- **Build**: `vite^5.0.8`, `@vitejs/plugin-react^4.2.1`

</details>
