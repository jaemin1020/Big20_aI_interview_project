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

### 2.1 환경 설정

**1. 환경 변수 설정**
```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 열어 실제 API 키로 교체
# - HUGGINGFACE_API_KEY: https://huggingface.co/settings/tokens
# - DEEPGRAM_API_KEY: https://console.deepgram.com/
```

⚠️ **보안 주의**: `.env` 파일은 절대 Git에 커밋하지 마세요!

**2. Docker 서비스 실행**
```bash
# 이미지 빌드
docker-compose build

# 서비스 시작 (백그라운드)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 상태 확인
docker-compose ps
```

**3. 서비스 접속**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Media Server: http://localhost:8080

### 2.2 테스트 실행

**백엔드 테스트**
```bash
# 테스트 의존성 설치
cd backend-core
pip install -r tests/requirements-test.txt

# 전체 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=. --cov-report=html

# 특정 테스트만 실행
pytest tests/test_auth.py -v
```

**프론트엔드 테스트** (향후 구현 예정)
```bash
cd frontend
npm test
```

### 2.3 보안 가이드

자세한 보안 가이드는 [`docs/SECURITY_GUIDE.md`](docs/SECURITY_GUIDE.md)를 참고하세요.

**핵심 체크리스트:**
- ✅ `.env` 파일이 `.gitignore`에 포함되어 있는지 확인
- ✅ API 키를 코드에 하드코딩하지 않기
- ✅ 프로덕션 환경에서는 강력한 비밀번호 사용
- ✅ HTTPS 강제 (프로덕션)


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
