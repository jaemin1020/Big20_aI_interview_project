# AI 모의면접 플랫폼 개발 가이드

## 📋 문서 정보
- **프로젝트명**: Big20 AI Interview Project
- **작성일**: 2026-01-27
- **목적**: 혼자서 프로젝트를 개발할 때 따라야 할 순서와 체크리스트 제공

---

## 🎯 프로젝트 개요

이 프로젝트는 AI 기반 실시간 모의면접 플랫폼으로, 다음과 같은 핵심 기능을 제공합니다:
- 실시간 음성/영상 스트리밍 (WebRTC)
- AI 기반 면접 질문 자동 생성 (Llama-3.1-8B)
- 답변 정밀 평가 (Solar-10.7B)
- 표정/감정 분석 (DeepFace)
- 음성-텍스트 변환 (Deepgram Nova-2)

---

## �️ 개발 순서 요약 (Quick Start Roadmap)

> **이 섹션을 먼저 읽고 전체 흐름을 파악한 후, 아래 상세 가이드를 따라 개발하세요!**

### 전체 개발 흐름 (한눈에 보기)

```
준비 단계 (1-3일)
    ↓
1. 환경 설정 과 DB 및 인프라 구축 (1-2일)
    ↓
2. Backend API 기본 구조 (2-3일)
    ↓
3. AI 질문 생성 기능 (1-2일)
    ↓
4. AI 평가 워커 구현 (2-3일)
    ↓
5. 미디어 서버 구축 (3-4일)
    ↓
6. 프론트엔드 UI (3-4일)
    ↓
7. 통합 및 테스트 (2-3일)
    ↓
8. 최적화 및 배포 (1-2일)
```

---

### 📝 상세 개발 순서 (Step-by-Step)

#### **준비 단계: 개발 환경 구축 (1-3일)**

<details>
<summary><b>Step 0: 필수 소프트웨어 설치</b> (반나절)</summary>

**순서:**
1. Docker Desktop 설치 (WSL2 백엔드)
2. NVIDIA GPU 드라이버 설치
3. NVIDIA Container Toolkit 설치
4. Git 설치
5. Visual Studio Code 설치
6. Node.js 설치 (v18 이상)

**확인 방법:**
```bash
docker --version
nvidia-smi
git --version
node --version
```

**다음 단계로 가는 조건:**
- [ ] 모든 명령어가 정상 실행됨
- [ ] `nvidia-smi`에서 GPU 정보 확인됨
</details>

<details>
<summary><b>Step 1: API 키 발급</b> (1-2시간)</summary>

**순서:**
1. HuggingFace 계정 생성 → Settings → Access Tokens → New Token 생성
2. Deepgram 계정 생성 → API Keys → Create New Key

**저장 위치:**
- `.env` 파일에 저장 (프로젝트 루트)

**다음 단계로 가는 조건:**
- [ ] `HUGGINGFACE_HUB_TOKEN` 발급 완료
- [ ] `DEEPGRAM_API_KEY` 발급 완료
</details>

<details>
<summary><b>Step 2: 환경 변수 설정</b> (30분)</summary>

**순서:**
1. `.env` 파일 열기
2. 필수 변수 입력:
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=interview_db
   DATABASE_URL=postgresql://postgres:your_password@db:5432/interview_db
   REDIS_URL=redis://redis:6379/0
   HUGGINGFACE_HUB_TOKEN=hf_xxxxx
   DEEPGRAM_API_KEY=xxxxx
   ```

**다음 단계로 가는 조건:**
- [ ] 모든 필수 환경 변수 입력 완료
</details>

---

#### **1단계: 데이터베이스 및 인프라 구축 (1-2일)**

<details>
<summary><b>Step 3: PostgreSQL + Redis 실행</b> (1시간)</summary>

**순서:**
```bash
# 1. 프로젝트 디렉토리로 이동
cd c:\big20\Big20_aI_interview_project

# 2. DB 초기화 스크립트 확인
# infra/postgres/init.sql 파일 존재 확인

# 3. DB와 Redis만 먼저 실행
docker-compose up -d db redis

# 4. 로그 확인
docker logs interview_db
docker logs interview_redis
```

**확인 방법:**
```bash
# PostgreSQL 접속 테스트
docker exec -it interview_db psql -U postgres -d interview_db

# 접속 후 실행
\dt  # 테이블 목록 확인
\q   # 종료
```

**다음 단계로 가는 조건:**
- [ ] `docker-compose ps`에서 db, redis 상태가 "Up"
- [ ] PostgreSQL 접속 성공
- [ ] 테이블 5개 생성 확인 (users, interviews, questions, transcripts, evaluation_reports)
</details>

<details>
<summary><b>Step 4: 데이터베이스 스키마 검증</b> (30분)</summary>

**순서:**
```sql
-- PostgreSQL 접속 후 실행
\d users
\d interviews
\d questions
\d transcripts
\d evaluation_reports
```

**확인 사항:**
- [ ] 각 테이블의 컬럼이 models.py와 일치
- [ ] 외래키 관계 설정 확인

**다음 단계로 가는 조건:**
- [ ] 모든 테이블 구조 확인 완료
</details>

---

#### **2단계: Backend-Core 기본 API 구축 (2-3일)**

<details>
<summary><b>Step 5: Backend 컨테이너 실행</b> (1시간)</summary>

**순서:**
```bash
# 1. Backend 빌드
docker-compose build backend

# 2. Backend 실행
docker-compose up -d backend

# 3. 로그 확인 (에러 없는지 체크)
docker logs -f interview_backend
```

**확인 방법:**
- 브라우저에서 `http://localhost:8000/docs` 접속
- Swagger UI 확인

**다음 단계로 가는 조건:**
- [ ] Backend 컨테이너 정상 실행
- [ ] Swagger UI 접속 가능
- [ ] 에러 로그 없음
</details>

<details>
<summary><b>Step 6: 회원가입/로그인 API 구현 및 테스트</b> (반나절)</summary>

**개발 파일:**
- `backend-core/auth.py` - 인증 로직
- `backend-core/main.py` - API 엔드포인트

**구현 순서:**
1. `auth.py`에 비밀번호 해싱 함수 구현
2. `auth.py`에 JWT 토큰 생성/검증 함수 구현
3. `main.py`에 `POST /register` 엔드포인트 추가
4. `main.py`에 `POST /token` 엔드포인트 추가

**테스트:**
```bash
# 회원가입
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"test1234","role":"candidate","full_name":"테스트"}'

# 로그인
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=test1234"
```

**다음 단계로 가는 조건:**
- [ ] 회원가입 성공 (200 응답)
- [ ] 로그인 성공 및 JWT 토큰 발급
- [ ] DB에 사용자 데이터 저장 확인
</details>

<details>
<summary><b>Step 7: 면접 세션 CRUD API 구현</b> (반나절)</summary>

**구현 순서:**
1. `POST /interviews` - 면접 세션 생성 (질문 생성 제외)
2. `GET /interviews/{id}` - 면접 정보 조회
3. `GET /interviews/{id}/questions` - 질문 목록 조회
4. `POST /transcripts` - 대화 기록 저장
5. `GET /interviews/{id}/transcripts` - 대화 기록 조회

**테스트:**
```bash
# JWT 토큰을 변수로 저장
TOKEN="your_jwt_token_here"

# 면접 생성
curl -X POST "http://localhost:8000/interviews" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"position":"백엔드 개발자","difficulty":"medium"}'
```

**다음 단계로 가는 조건:**
- [ ] 모든 API 엔드포인트 정상 작동
- [ ] Swagger UI에서 테스트 성공
- [ ] DB에 데이터 정상 저장
</details>

---

#### **3단계: AI 질문 생성 기능 구현 (1-2일)**

<details>
<summary><b>Step 8: Llama-3.1-8B 모델 로딩</b> (반나절)</summary>

**개발 파일:**
- `backend-core/chains/llama_gen.py`

**구현 순서:**
1. HuggingFace Pipeline 설정
2. GPU 메모리 최적화 (4bit 양자화)
3. 모델 로딩 함수 작성

**코드 골격:**
```python
from transformers import pipeline, AutoTokenizer

def load_llama_model():
    model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    
    pipe = pipeline(
        "text-generation",
        model=model_id,
        device_map="auto",
        torch_dtype="auto"
    )
    
    return pipe
```

**테스트:**
```python
# Python 콘솔에서 테스트
pipe = load_llama_model()
result = pipe("안녕하세요", max_new_tokens=50)
print(result)
```

**다음 단계로 가는 조건:**
- [ ] 모델 로딩 성공 (에러 없음)
- [ ] GPU 메모리 사용량 확인 (`nvidia-smi`)
- [ ] 간단한 텍스트 생성 테스트 성공
</details>

<details>
<summary><b>Step 9: 질문 생성 로직 구현</b> (반나절)</summary>

**구현 순서:**
1. 프롬프트 템플릿 작성
2. 질문 생성 함수 구현
3. `POST /interviews` 엔드포인트에 통합

**프롬프트 예시:**
```python
PROMPT = """당신은 전문 면접관입니다. {position} 직무에 적합한 면접 질문 {count}개를 생성하세요.

요구사항:
- 기술적 질문과 경험 기반 질문을 섞어서 생성
- 난이도: {difficulty}
- 각 질문은 명확하고 구체적이어야 함

질문 목록:"""
```

**테스트:**
```bash
# 면접 생성 (질문 자동 생성 포함)
curl -X POST "http://localhost:8000/interviews" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"position":"백엔드 개발자","difficulty":"medium"}'

# 생성된 질문 확인
curl -X GET "http://localhost:8000/interviews/1/questions" \
  -H "Authorization: Bearer $TOKEN"
```

**다음 단계로 가는 조건:**
- [ ] 질문 5개 이상 자동 생성
- [ ] 생성 시간 < 10초
- [ ] 질문이 DB에 저장됨
</details>

---

#### **4단계: AI-Worker 평가 시스템 구현 (2-3일)**

<details>
<summary><b>Step 10: Celery Worker 설정</b> (1시간)</summary>

**순서:**
```bash
# 1. AI-Worker 빌드
docker-compose build ai-worker

# 2. AI-Worker 실행
docker-compose up -d ai-worker

# 3. 로그 확인
docker logs -f interview_worker
```

**확인 사항:**
- [ ] Worker가 Redis에 연결됨
- [ ] "celery@worker ready" 메시지 확인

**다음 단계로 가는 조건:**
- [ ] Worker 정상 실행
- [ ] Redis 연결 성공
</details>

<details>
<summary><b>Step 11: Solar-10.7B 모델 다운로드 및 설정</b> (1-2시간)</summary>

**순서:**
1. 모델 다운로드
   ```bash
   # ai-worker/models 디렉토리에 다운로드
   # https://huggingface.co/upstage/SOLAR-10.7B-Instruct-v1.0-GGUF
   ```

2. 모델 파일 확인
   ```bash
   ls ai-worker/models/
   # solar-10.7b-instruct-v1.0.Q8_0.gguf 파일 확인
   ```

**다음 단계로 가는 조건:**
- [ ] 모델 파일 다운로드 완료 (약 11GB)
- [ ] 파일 경로 확인
</details>

<details>
<summary><b>Step 12: 답변 평가 태스크 구현</b> (1일)</summary>

**개발 파일:**
- `ai-worker/tasks/evaluator.py`

**구현 순서:**
1. `analyze_answer` 태스크 작성
2. Solar-10.7B 모델 로딩
3. 평가 프롬프트 작성
4. JSON 파싱 및 DB 업데이트

**테스트:**
```python
# Backend에서 태스크 발행
from celery import Celery

celery_app = Celery(broker=os.getenv("REDIS_URL"))
result = celery_app.send_task(
    "tasks.evaluator.analyze_answer",
    args=[1, 1, "저는 Python과 FastAPI를 사용한 경험이 있습니다."]
)
```

**다음 단계로 가는 조건:**
- [ ] 태스크 정상 실행
- [ ] 평가 점수 생성
- [ ] DB에 결과 저장
</details>

<details>
<summary><b>Step 13: DeepFace 감정 분석 구현</b> (반나절)</summary>

**개발 파일:**
- `ai-worker/tasks/vision.py`

**구현 순서:**
1. `analyze_emotion` 태스크 작성
2. Base64 이미지 디코딩
3. DeepFace 분석 실행

**테스트:**
```python
# 테스트 이미지로 감정 분석
import base64

with open("test_image.jpg", "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()

result = celery_app.send_task(
    "tasks.vision.analyze_emotion",
    args=[img_base64, 1]
)
```

**다음 단계로 가는 조건:**
- [ ] 감정 분석 성공
- [ ] 7가지 감정 점수 반환
- [ ] DB 업데이트 확인
</details>

---

#### **5단계: Media-Server 실시간 스트리밍 구현 (3-4일)**

<details>
<summary><b>Step 14: WebRTC 서버 기본 구조</b> (1일)</summary>

**순서:**
```bash
# 1. Media-Server 빌드 및 실행
docker-compose build media-server
docker-compose up -d media-server

# 2. 로그 확인
docker logs -f interview_media
```

**개발 파일:**
- `media-server/main.py`

**구현 순서:**
1. FastAPI 앱 생성
2. `POST /offer` 엔드포인트 구현
3. RTCPeerConnection 설정
4. SDP 교환 로직

**다음 단계로 가는 조건:**
- [ ] Media-Server 실행 성공
- [ ] `/offer` 엔드포인트 응답 확인
</details>

<details>
<summary><b>Step 15: Deepgram STT 통합</b> (1일)</summary>

**구현 순서:**
1. Deepgram WebSocket 연결
2. Audio Track 처리
3. 실시간 Transcript 수신
4. WebSocket으로 Frontend 전송

**테스트:**
- 간단한 오디오 파일로 STT 테스트

**다음 단계로 가는 조건:**
- [ ] Deepgram 연결 성공
- [ ] 한국어 음성 인식 확인
</details>

<details>
<summary><b>Step 16: 비디오 프레임 추출</b> (반나절)</summary>

**구현 순서:**
1. Video Track 처리
2. 2초 간격 프레임 추출
3. Base64 인코딩
4. Celery 태스크 발행

**다음 단계로 가는 조건:**
- [ ] 프레임 추출 성공
- [ ] AI-Worker로 전송 확인
</details>

---

#### **6단계: Frontend UI 구현 (3-4일)**

<details>
<summary><b>Step 17: React 프로젝트 설정</b> (1시간)</summary>

**순서:**
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

**확인:**
- 브라우저에서 `http://localhost:3000` 접속

**다음 단계로 가는 조건:**
- [ ] 개발 서버 정상 실행
- [ ] 기본 페이지 표시
</details>

<details>
<summary><b>Step 18: 로그인/회원가입 페이지</b> (반나절)</summary>

**개발 파일:**
- `src/pages/LoginPage.jsx`
- `src/pages/RegisterPage.jsx`
- `src/api/client.js`

**구현 순서:**
1. API 클라이언트 설정
2. 로그인 폼 구현
3. 회원가입 폼 구현
4. JWT 토큰 저장

**다음 단계로 가는 조건:**
- [ ] 로그인 성공
- [ ] 토큰 localStorage 저장
- [ ] 대시보드로 리다이렉트
</details>

<details>
<summary><b>Step 19: WebRTC 클라이언트 구현</b> (1일)</summary>

**개발 파일:**
- `src/components/WebRTCPlayer.jsx`

**구현 순서:**
1. 카메라/마이크 권한 요청
2. MediaStream 생성
3. RTCPeerConnection 설정
4. Offer 생성 및 전송
5. Answer 수신

**다음 단계로 가는 조건:**
- [ ] 카메라 화면 표시
- [ ] Media-Server 연결 성공
</details>

<details>
<summary><b>Step 20: 면접 페이지 UI</b> (1일)</summary>

**개발 파일:**
- `src/pages/InterviewPage.jsx`

**구현 순서:**
1. WebRTC 플레이어 통합
2. 질문 표시 영역
3. 실시간 STT 표시
4. 답변 제출 버튼

**다음 단계로 가는 조건:**
- [ ] 전체 UI 완성
- [ ] 실시간 데이터 표시
</details>

<details>
<summary><b>Step 21: 평가 리포트 페이지</b> (반나절)</summary>

**개발 파일:**
- `src/pages/ReportPage.jsx`

**구현 순서:**
1. 평가 데이터 조회
2. 점수 차트 표시
3. 피드백 표시

**다음 단계로 가는 조건:**
- [ ] 리포트 정상 표시
</details>

---

#### **7단계: 통합 테스트 (2-3일)**

<details>
<summary><b>Step 22: End-to-End 테스트</b> (1-2일)</summary>

**테스트 시나리오:**
1. [ ] 회원가입 → 로그인
2. [ ] 면접 세션 생성
3. [ ] WebRTC 연결
4. [ ] 실시간 STT
5. [ ] 답변 제출 및 평가
6. [ ] 감정 분석
7. [ ] 면접 종료
8. [ ] 리포트 조회

**다음 단계로 가는 조건:**
- [ ] 모든 시나리오 통과
</details>

---

#### **8단계: 최적화 및 배포 (1-2일)**

<details>
<summary><b>Step 23: 성능 최적화</b> (1일)</summary>

**작업 목록:**
- [ ] DB 쿼리 최적화
- [ ] LLM 추론 속도 개선
- [ ] Frontend 빌드 최적화

</details>

<details>
<summary><b>Step 24: 배포 준비</b> (반나절)</summary>

**작업 목록:**
- [ ] 환경 변수 보안 강화
- [ ] 로그 레벨 설정
- [ ] 모니터링 설정

</details>

---

### ✅ 각 단계 완료 기준

각 Step을 완료했다고 판단하는 기준:

| Step | 완료 기준 |
|------|----------|
| **Step 0-2** | 모든 소프트웨어 설치 및 API 키 발급 완료 |
| **Step 3-4** | DB 테이블 생성 확인, psql 접속 성공 |
| **Step 5-7** | Swagger UI에서 모든 API 테스트 성공 |
| **Step 8-9** | 질문 자동 생성 성공, DB 저장 확인 |
| **Step 10-13** | Celery 태스크 정상 실행, 평가 결과 DB 저장 |
| **Step 14-16** | WebRTC 연결 성공, STT 실시간 변환 확인 |
| **Step 17-21** | Frontend 모든 페이지 정상 작동 |
| **Step 22** | End-to-End 시나리오 전체 통과 |
| **Step 23-24** | 프로덕션 배포 가능 상태 |

---

### 🚨 막혔을 때 대처 방법

**각 Step에서 막혔을 때:**

1. **로그 확인**
   ```bash
   docker logs -f <container_name>
   ```

2. **컨테이너 재시작**
   ```bash
   docker-compose restart <service_name>
   ```

3. **완전 재빌드**
   ```bash
   docker-compose down
   docker-compose build --no-cache <service_name>
   docker-compose up -d
   ```

4. **다음 Step으로 넘어가기 전 체크리스트 재확인**

---

### 📊 예상 소요 시간

| 단계 | 예상 시간 | 누적 시간 |
|------|----------|----------|
| 준비 단계 | 1-3일 | 1-3일 |
| 1단계 (인프라) | 1-2일 | 2-5일 |
| 2단계 (Backend 기본) | 2-3일 | 4-8일 |
| 3단계 (AI 질문 생성) | 1-2일 | 5-10일 |
| 4단계 (AI 평가) | 2-3일 | 7-13일 |
| 5단계 (Media Server) | 3-4일 | 10-17일 |
| 6단계 (Frontend) | 3-4일 | 13-21일 |
| 7단계 (통합 테스트) | 2-3일 | 15-24일 |
| 8단계 (최적화) | 1-2일 | 16-26일 |

**총 예상 기간: 16-26일 (약 3-4주)**

---

## �📚 개발 전 필수 학습 사항

### 1단계: 기본 기술 스택 이해
개발을 시작하기 전에 다음 기술들에 대한 기본 이해가 필요합니다:

#### 백엔드 기술
- [ ] **Python 3.10+** 기본 문법 및 비동기 프로그래밍 (async/await)
- [ ] **FastAPI** 프레임워크 기초
- [ ] **SQLModel/SQLAlchemy** ORM 사용법
- [ ] **PostgreSQL** 기본 쿼리 및 관계형 DB 설계
- [ ] **Celery** 비동기 작업 큐 개념

#### AI/ML 기술
- [ ] **LangChain** 기본 개념 및 LLM 체인 구성
- [ ] **HuggingFace Transformers** 모델 로딩 및 추론
- [ ] **llama-cpp-python** 사용법
- [ ] **DeepFace** 감정 분석 라이브러리

#### 프론트엔드 기술
- [ ] **React 18** 기본 (컴포넌트, Hooks, State 관리)
- [ ] **Vite** 빌드 도구
- [ ] **WebRTC** 기본 개념 (미디어 스트리밍)
- [ ] **Axios** HTTP 클라이언트

#### 인프라 기술
- [ ] **Docker** 및 **Docker Compose** 기본 사용법
- [ ] **Redis** 기본 개념 (메시지 브로커)
- [ ] **WebSocket** 실시간 통신

---

## 🛠️ 개발 환경 설정

### 1단계: 시스템 요구사항 확인

#### 하드웨어 요구사항
```
최소 사양:
- CPU: 8코어 이상
- RAM: 32GB 이상
- GPU: NVIDIA GPU (VRAM 8GB+, CUDA 지원)
- 저장공간: 50GB 이상

권장 사양:
- CPU: 16코어 이상
- RAM: 64GB
- GPU: NVIDIA RTX 3090 이상 (VRAM 24GB)
- 저장공간: 100GB SSD
```

#### 소프트웨어 요구사항
- [ ] Windows 10/11 (WSL2 설치)
- [ ] Docker Desktop (WSL2 백엔드 활성화)
- [ ] NVIDIA GPU 드라이버 최신 버전
- [ ] NVIDIA Container Toolkit
- [ ] Git
- [ ] Visual Studio Code (권장)

### 2단계: 개발 환경 구축

#### 2.1 필수 소프트웨어 설치
```bash
# 1. Docker Desktop 설치 (WSL2 백엔드)
# https://www.docker.com/products/docker-desktop

# 2. NVIDIA Container Toolkit 설치
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html

# 3. Git 설치
# https://git-scm.com/download/win

# 4. Node.js 설치 (v18 이상)
# https://nodejs.org/
```

#### 2.2 프로젝트 클론 및 환경 변수 설정
```bash
# 프로젝트 디렉토리로 이동
cd c:\big20\Big20_aI_interview_project

# .env 파일 확인 및 수정
# 필수 환경 변수:
# - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
# - HUGGINGFACE_HUB_TOKEN
# - DEEPGRAM_API_KEY
# - DATABASE_URL, REDIS_URL
```

#### 2.3 API 키 발급
- [ ] **HuggingFace Token**: https://huggingface.co/settings/tokens
- [ ] **Deepgram API Key**: https://console.deepgram.com/

---

## 🚀 단계별 개발 가이드

### Phase 1: 인프라 및 데이터베이스 구축 (1-2일)

#### 1.1 데이터베이스 설정
```bash
# PostgreSQL + pgvector 컨테이너 실행
docker-compose up -d db redis

# DB 연결 확인
docker exec -it interview_db psql -U postgres -d interview_db
```

**체크리스트:**
- [ ] PostgreSQL 컨테이너 정상 실행
- [ ] Redis 컨테이너 정상 실행
- [ ] DB 초기화 스크립트 실행 확인 (`infra/postgres/init.sql`)
- [ ] 테이블 생성 확인 (users, interviews, questions, transcripts, evaluation_reports)

#### 1.2 데이터베이스 스키마 검증
```sql
-- 테이블 목록 확인
\dt

-- 각 테이블 구조 확인
\d users
\d interviews
\d questions
\d transcripts
\d evaluation_reports
```

**작업 파일:**
- `infra/postgres/init.sql` - DB 초기화 스크립트
- `backend-core/models.py` - SQLModel 테이블 정의

---

### Phase 2: Backend-Core 개발 (3-5일)

#### 2.1 기본 API 서버 구축
**목표:** FastAPI 서버 실행 및 기본 엔드포인트 구현

```bash
# Backend 컨테이너 빌드 및 실행
docker-compose build backend
docker-compose up -d backend

# 로그 확인
docker logs -f interview_backend
```

**개발 순서:**
1. **데이터베이스 연결 설정** (`backend-core/database.py`)
   - [ ] SQLModel 엔진 생성
   - [ ] 세션 관리 함수 구현
   - [ ] 연결 테스트

2. **모델 정의** (`backend-core/models.py`)
   - [ ] User 모델
   - [ ] Interview 모델
   - [ ] Question 모델
   - [ ] Transcript 모델
   - [ ] EvaluationReport 모델

3. **인증 시스템** (`backend-core/auth.py`)
   - [ ] 비밀번호 해싱 (bcrypt)
   - [ ] JWT 토큰 생성/검증
   - [ ] 사용자 인증 미들웨어

4. **API 엔드포인트** (`backend-core/main.py`)
   - [ ] `POST /register` - 회원가입
   - [ ] `POST /token` - 로그인
   - [ ] `GET /users/me` - 사용자 정보 조회
   - [ ] `POST /interviews` - 면접 세션 생성
   - [ ] `GET /interviews/{id}/questions` - 질문 조회
   - [ ] `POST /transcripts` - 대화 기록 저장
   - [ ] `POST /interviews/{id}/complete` - 면접 종료
   - [ ] `GET /interviews/{id}/report` - 평가 리포트 조회

**테스트 방법:**
```bash
# API 문서 확인
# 브라우저에서 http://localhost:8000/docs 접속

# 회원가입 테스트
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"test1234","role":"candidate"}'

# 로그인 테스트
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=test1234"
```

#### 2.2 LLM 질문 생성 기능 구현
**목표:** Llama-3.1-8B를 사용한 실시간 질문 생성

**개발 순서:**
1. **LLM 모델 로딩** (`backend-core/chains/llama_gen.py`)
   - [ ] HuggingFace 모델 다운로드 및 캐싱
   - [ ] GPU 메모리 최적화 (4bit 양자화)
   - [ ] 파이프라인 생성

2. **질문 생성 체인 구현**
   - [ ] 프롬프트 템플릿 작성
   - [ ] LangChain 체인 구성
   - [ ] 출력 파싱 로직

3. **API 통합**
   - [ ] `POST /interviews` 엔드포인트에 질문 생성 로직 추가
   - [ ] 생성된 질문 DB 저장
   - [ ] 에러 핸들링

**테스트:**
```bash
# 면접 세션 생성 및 질문 생성 테스트
curl -X POST "http://localhost:8000/interviews" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"position":"백엔드 개발자","difficulty":"medium"}'
```

#### 2.3 Celery 태스크 발행 설정
**목표:** 비동기 작업을 AI-Worker로 전달

```python
# backend-core/main.py
from celery import Celery

celery_app = Celery(
    "interview",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

# 평가 태스크 발행 예시
celery_app.send_task(
    "tasks.evaluator.analyze_answer",
    args=[interview_id, question_id, answer_text]
)
```

**체크리스트:**
- [ ] Celery 앱 초기화
- [ ] Redis 연결 확인
- [ ] 태스크 발행 테스트

---

### Phase 3: AI-Worker 개발 (4-6일)

#### 3.1 Celery Worker 설정
**목표:** 비동기 작업 처리 워커 구축

```bash
# AI-Worker 컨테이너 빌드
docker-compose build ai-worker
docker-compose up -d ai-worker

# 워커 로그 확인
docker logs -f interview_worker
```

**개발 순서:**
1. **Worker 초기화** (`ai-worker/main.py`)
   - [ ] Celery 앱 설정
   - [ ] Redis 브로커 연결
   - [ ] 로깅 설정

2. **데이터베이스 연결** (`ai-worker/db.py`)
   - [ ] SQLModel 세션 관리
   - [ ] 비동기 DB 업데이트 함수

#### 3.2 Solar-10.7B 평가 모델 구현
**목표:** 답변 정밀 평가 시스템

**개발 순서:**
1. **모델 다운로드 및 설정**
   ```bash
   # ai-worker/models 디렉토리에 모델 파일 다운로드
   # https://huggingface.co/upstage/SOLAR-10.7B-Instruct-v1.0-GGUF
   ```

2. **평가 태스크 구현** (`ai-worker/tasks/evaluator.py`)
   - [ ] `analyze_answer` 태스크
     - 질문 및 답변 로드
     - 루브릭 기반 프롬프트 구성
     - Solar-10.7B 추론
     - JSON 파싱 및 점수 추출
     - DB 업데이트
   
   - [ ] `generate_final_report` 태스크
     - 전체 Transcript 집계
     - 종합 평가 생성
     - EvaluationReport 저장

**프롬프트 예시:**
```python
EVALUATION_PROMPT = """
당신은 면접 평가 전문가입니다. 다음 루브릭에 따라 답변을 평가하세요.

평가 기준:
- 기술적 정확성 (0-100점)
- 논리적 구성 (0-100점)
- 의사소통 능력 (0-100점)

질문: {question}
답변: {answer}

JSON 형식으로 평가 결과를 출력하세요:
{{
  "technical_score": <점수>,
  "communication_score": <점수>,
  "logic_score": <점수>,
  "feedback": "<피드백 내용>"
}}
"""
```

#### 3.3 DeepFace 감정 분석 구현
**목표:** 비디오 프레임 기반 감정 분석

**개발 순서:**
1. **감정 분석 태스크** (`ai-worker/tasks/vision.py`)
   - [ ] `analyze_emotion` 태스크
     - Base64 이미지 디코딩
     - DeepFace 분석 실행
     - 감정 결과 추출
     - Transcript 업데이트

```python
from deepface import DeepFace
import cv2
import numpy as np
import base64

@celery_app.task(name="tasks.vision.analyze_emotion")
def analyze_emotion(frame_base64: str, transcript_id: int):
    # Base64 디코딩
    img_data = base64.b64decode(frame_base64)
    nparr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # DeepFace 분석
    result = DeepFace.analyze(
        frame,
        actions=['emotion'],
        enforce_detection=False
    )
    
    # DB 업데이트
    # ...
```

**테스트:**
```bash
# 태스크 직접 호출 테스트
docker exec -it interview_worker python -c "
from tasks.vision import analyze_emotion
result = analyze_emotion.delay('base64_encoded_image', 1)
print(result.get())
"
```

---

### Phase 4: Media-Server 개발 (5-7일)

#### 4.1 WebRTC 서버 구축
**목표:** 실시간 음성/영상 스트리밍 처리

```bash
# Media-Server 컨테이너 실행
docker-compose up -d media-server

# 로그 확인
docker logs -f interview_media
```

**개발 순서:**
1. **WebRTC Offer/Answer 처리** (`media-server/main.py`)
   - [ ] `POST /offer` 엔드포인트
   - [ ] SDP 교환 로직
   - [ ] RTCPeerConnection 생성
   - [ ] Audio/Video Track 핸들러

```python
from aiortc import RTCPeerConnection, RTCSessionDescription
from fastapi import FastAPI

app = FastAPI()
pcs = set()

@app.post("/offer")
async def offer(params: dict):
    offer = RTCSessionDescription(
        sdp=params["sdp"],
        type=params["type"]
    )
    
    pc = RTCPeerConnection()
    pcs.add(pc)
    
    @pc.on("track")
    async def on_track(track):
        if track.kind == "audio":
            # Audio 처리
            pass
        elif track.kind == "video":
            # Video 처리
            pass
    
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    }
```

#### 4.2 Deepgram STT 통합
**목표:** 실시간 음성-텍스트 변환

**개발 순서:**
1. **Deepgram WebSocket 연결**
   - [ ] Audio Track → Deepgram 스트리밍
   - [ ] 실시간 Transcript 수신
   - [ ] WebSocket으로 Frontend 전송

```python
from deepgram import Deepgram
import asyncio

async def process_audio(track):
    dg_client = Deepgram(os.getenv("DEEPGRAM_API_KEY"))
    
    dg_connection = dg_client.transcription.live({
        "language": "ko",
        "model": "nova-2",
        "smart_format": True
    })
    
    async for frame in track:
        # Audio frame → Deepgram
        await dg_connection.send(frame.to_ndarray().tobytes())
    
    @dg_connection.on("transcript")
    def on_transcript(transcript):
        # WebSocket으로 Frontend 전송
        pass
```

#### 4.3 비디오 프레임 추출 및 전송
**목표:** 2초 간격 프레임 추출 및 AI-Worker 전달

```python
import cv2
import base64
from celery import Celery

celery_app = Celery(broker=os.getenv("REDIS_URL"))

async def process_video(track):
    last_frame_time = 0
    
    async for frame in track:
        current_time = time.time()
        
        # 2초 간격 체크
        if current_time - last_frame_time >= 2.0:
            # Frame → Base64 인코딩
            img = frame.to_ndarray(format="bgr24")
            _, buffer = cv2.imencode('.jpg', img)
            frame_base64 = base64.b64encode(buffer).decode()
            
            # Celery 태스크 발행
            celery_app.send_task(
                "tasks.vision.analyze_emotion",
                args=[frame_base64, transcript_id]
            )
            
            last_frame_time = current_time
```

---

### Phase 5: Frontend 개발 (5-7일)

#### 5.1 프로젝트 초기 설정
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

**개발 순서:**
1. **라우팅 설정** (`src/App.jsx`)
   - [ ] 로그인 페이지 (`/login`)
   - [ ] 회원가입 페이지 (`/register`)
   - [ ] 대시보드 (`/dashboard`)
   - [ ] 면접 페이지 (`/interview/:id`)
   - [ ] 리포트 페이지 (`/report/:id`)

2. **API 클라이언트** (`src/api/client.js`)
   - [ ] Axios 인스턴스 생성
   - [ ] JWT 토큰 인터셉터
   - [ ] 에러 핸들링

```javascript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// 요청 인터셉터: JWT 토큰 추가
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default apiClient;
```

#### 5.2 WebRTC 클라이언트 구현
**목표:** 미디어 스트리밍 및 실시간 통신

**개발 순서:**
1. **WebRTC 컴포넌트** (`src/components/WebRTCPlayer.jsx`)
   - [ ] 카메라/마이크 권한 요청
   - [ ] MediaStream 생성
   - [ ] RTCPeerConnection 설정
   - [ ] Offer 생성 및 전송
   - [ ] Answer 수신 및 처리

```javascript
import { useEffect, useRef, useState } from 'react';

function WebRTCPlayer({ sessionId }) {
  const videoRef = useRef(null);
  const [pc, setPc] = useState(null);
  
  useEffect(() => {
    async function startStream() {
      // 미디어 스트림 획득
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      
      videoRef.current.srcObject = stream;
      
      // RTCPeerConnection 생성
      const peerConnection = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });
      
      // 트랙 추가
      stream.getTracks().forEach(track => {
        peerConnection.addTrack(track, stream);
      });
      
      // Offer 생성
      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);
      
      // Media-Server로 Offer 전송
      const response = await fetch('http://localhost:8080/offer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
          session_id: sessionId
        })
      });
      
      const answer = await response.json();
      await peerConnection.setRemoteDescription(
        new RTCSessionDescription(answer)
      );
      
      setPc(peerConnection);
    }
    
    startStream();
    
    return () => {
      if (pc) {
        pc.close();
      }
    };
  }, [sessionId]);
  
  return <video ref={videoRef} autoPlay muted />;
}

export default WebRTCPlayer;
```

#### 5.3 면접 UI 구현
**개발 순서:**
1. **면접 페이지** (`src/pages/InterviewPage.jsx`)
   - [ ] WebRTC 플레이어 통합
   - [ ] 질문 표시 영역
   - [ ] 실시간 STT 결과 표시
   - [ ] 답변 제출 버튼
   - [ ] 면접 종료 버튼

2. **WebSocket 연결** (실시간 STT)
   ```javascript
   const ws = new WebSocket(`ws://localhost:8080/ws/${sessionId}`);
   
   ws.onmessage = (event) => {
     const data = JSON.parse(event.data);
     setTranscript(prev => prev + ' ' + data.text);
   };
   ```

3. **스타일링** (`src/index.css`)
   - [ ] Glassmorphism 효과
   - [ ] 다크 모드 테마
   - [ ] 반응형 레이아웃
   - [ ] 애니메이션 효과

#### 5.4 평가 리포트 대시보드
**개발 순서:**
1. **리포트 페이지** (`src/pages/ReportPage.jsx`)
   - [ ] 종합 점수 표시
   - [ ] 카테고리별 점수 차트
   - [ ] 감정 분석 결과
   - [ ] 상세 피드백
   - [ ] 대화 기록 타임라인

2. **차트 라이브러리 통합**
   ```bash
   npm install recharts
   ```

---

### Phase 6: 통합 테스트 및 디버깅 (3-5일)

#### 6.1 전체 시스템 실행
```bash
# 모든 서비스 빌드 및 실행
docker-compose build
docker-compose up -d

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f
```

#### 6.2 End-to-End 테스트 시나리오

**시나리오 1: 회원가입 및 로그인**
1. [ ] Frontend에서 회원가입 (`/register`)
2. [ ] 로그인 (`/login`)
3. [ ] JWT 토큰 발급 확인
4. [ ] 대시보드 접근 확인

**시나리오 2: 면접 세션 생성**
1. [ ] 면접 생성 요청 (`POST /interviews`)
2. [ ] 질문 자동 생성 확인
3. [ ] DB에 데이터 저장 확인

**시나리오 3: 실시간 면접 진행**
1. [ ] WebRTC 연결 수립
2. [ ] 카메라/마이크 스트리밍 확인
3. [ ] STT 실시간 변환 확인
4. [ ] 답변 제출 및 저장
5. [ ] 비동기 평가 태스크 실행 확인
6. [ ] 감정 분석 실행 확인

**시나리오 4: 평가 리포트 생성**
1. [ ] 면접 종료 (`POST /interviews/{id}/complete`)
2. [ ] 최종 리포트 생성 태스크 실행
3. [ ] 리포트 조회 (`GET /interviews/{id}/report`)
4. [ ] Frontend에서 리포트 표시

#### 6.3 디버깅 체크리스트

**데이터베이스 문제**
- [ ] 연결 문자열 확인
- [ ] 테이블 생성 확인
- [ ] 외래키 제약 조건 확인

**LLM 모델 문제**
- [ ] GPU 메모리 사용량 확인 (`nvidia-smi`)
- [ ] 모델 파일 경로 확인
- [ ] HuggingFace 토큰 유효성 확인

**WebRTC 문제**
- [ ] STUN/TURN 서버 설정
- [ ] 방화벽 포트 개방 확인
- [ ] 브라우저 콘솔 에러 확인

**Celery 문제**
- [ ] Redis 연결 확인
- [ ] Worker 실행 상태 확인
- [ ] 태스크 큐 상태 확인 (`celery -A main inspect active`)

---

### Phase 7: 최적화 및 배포 준비 (2-3일)

#### 7.1 성능 최적화

**Backend 최적화**
- [ ] DB 쿼리 최적화 (인덱스 추가)
- [ ] LLM 추론 배치 처리
- [ ] 캐싱 전략 (Redis)
- [ ] 연결 풀 설정

**Frontend 최적화**
- [ ] 코드 스플리팅
- [ ] 이미지 최적화
- [ ] Lazy Loading
- [ ] 프로덕션 빌드 (`npm run build`)

**AI 모델 최적화**
- [ ] 모델 양자화 (4bit/8bit)
- [ ] 배치 크기 조정
- [ ] GPU 메모리 관리

#### 7.2 보안 강화
- [ ] HTTPS 설정 (프로덕션)
- [ ] CORS 정책 설정
- [ ] Rate Limiting
- [ ] SQL Injection 방어
- [ ] XSS 방어
- [ ] 환경 변수 암호화

#### 7.3 모니터링 및 로깅
- [ ] 로그 레벨 설정
- [ ] 에러 추적 (Sentry 등)
- [ ] 성능 모니터링
- [ ] GPU 사용량 모니터링

---

## 📊 개발 진행 체크리스트

### 전체 진행 상황
- [ ] Phase 1: 인프라 및 데이터베이스 구축 (1-2일)
- [ ] Phase 2: Backend-Core 개발 (3-5일)
- [ ] Phase 3: AI-Worker 개발 (4-6일)
- [ ] Phase 4: Media-Server 개발 (5-7일)
- [ ] Phase 5: Frontend 개발 (5-7일)
- [ ] Phase 6: 통합 테스트 및 디버깅 (3-5일)
- [ ] Phase 7: 최적화 및 배포 준비 (2-3일)

**예상 총 개발 기간: 23-35일 (약 1-1.5개월)**

---

## 🔧 트러블슈팅 가이드

### 자주 발생하는 문제

#### 1. GPU 메모리 부족
```bash
# 증상: CUDA out of memory
# 해결:
# - 모델 양자화 레벨 증가 (FP16 → 8bit → 4bit)
# - 배치 크기 감소
# - 불필요한 모델 언로드
```

#### 2. Docker 컨테이너 실행 실패
```bash
# 로그 확인
docker logs <container_name>

# 컨테이너 재시작
docker-compose restart <service_name>

# 완전 재빌드
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 3. WebRTC 연결 실패
```javascript
// 브라우저 콘솔에서 확인
// - getUserMedia 권한 확인
// - ICE candidate 수집 확인
// - STUN 서버 응답 확인
```

#### 4. Celery 태스크 실행 안 됨
```bash
# Worker 상태 확인
docker exec -it interview_worker celery -A main inspect active

# Redis 연결 확인
docker exec -it interview_redis redis-cli ping
```

---

## 📚 참고 자료

### 공식 문서
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [LangChain 문서](https://python.langchain.com/)
- [Celery 문서](https://docs.celeryq.dev/)
- [aiortc 문서](https://aiortc.readthedocs.io/)
- [React 문서](https://react.dev/)
- [WebRTC 가이드](https://webrtc.org/getting-started/overview)

### 모델 문서
- [Llama-3.1 HuggingFace](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B)
- [Solar-10.7B](https://huggingface.co/upstage/SOLAR-10.7B-Instruct-v1.0)
- [DeepFace](https://github.com/serengil/deepface)
- [Deepgram API](https://developers.deepgram.com/)

### 추가 학습 자료
- Docker Compose GPU 지원: https://docs.docker.com/compose/gpu-support/
- PostgreSQL 성능 튜닝: https://wiki.postgresql.org/wiki/Performance_Optimization
- WebRTC 보안: https://webrtc-security.github.io/

---

## 💡 개발 팁

### 효율적인 개발을 위한 조언

1. **단계별 개발**
   - 한 번에 모든 기능을 구현하려 하지 말고, Phase별로 순차적으로 진행
   - 각 Phase 완료 후 반드시 테스트 수행

2. **로그 활용**
   - 모든 주요 작업에 로그 추가
   - 에러 발생 시 스택 트레이스 확인

3. **버전 관리**
   - Git을 활용한 주기적인 커밋
   - 기능별 브랜치 생성 권장

4. **문서화**
   - 코드 주석 작성
   - API 변경 사항 기록
   - 트러블슈팅 경험 기록

5. **성능 모니터링**
   - GPU 사용량 주기적 확인
   - API 응답 시간 측정
   - DB 쿼리 성능 분석

---

## 🎓 학습 로드맵

### 초급 → 중급 → 고급

**초급 (1-2주)**
- Python 기본 문법
- FastAPI 튜토리얼
- React 기초
- Docker 기본 명령어

**중급 (2-4주)**
- 비동기 프로그래밍 (async/await)
- LangChain 기본
- WebRTC 개념
- PostgreSQL 쿼리 최적화

**고급 (4주 이상)**
- LLM 파인튜닝
- 분산 시스템 설계
- 실시간 스트리밍 최적화
- 프로덕션 배포 전략

---

## ✅ 최종 체크리스트

배포 전 반드시 확인해야 할 사항:

### 기능 테스트
- [ ] 회원가입/로그인 정상 작동
- [ ] 면접 세션 생성 및 질문 생성
- [ ] WebRTC 스트리밍 정상 작동
- [ ] STT 실시간 변환
- [ ] 답변 평가 정상 실행
- [ ] 감정 분석 정상 실행
- [ ] 최종 리포트 생성

### 성능 테스트
- [ ] API 응답 시간 < 2초
- [ ] LLM 추론 시간 < 5초
- [ ] WebRTC 지연 시간 < 500ms
- [ ] 동시 사용자 10명 이상 지원

### 보안 테스트
- [ ] JWT 토큰 검증
- [ ] SQL Injection 방어
- [ ] XSS 방어
- [ ] CORS 정책 적용

### 문서화
- [ ] API 문서 작성 (Swagger)
- [ ] 배포 가이드 작성
- [ ] 사용자 매뉴얼 작성

---

**개발 과정에서 막히는 부분이 있다면, 각 Phase의 체크리스트를 참고하여 단계별로 진행하세요!**
