---
description: Backend-Core와 PostgreSQL DB를 실행하는 방법
---

# 🚀 Backend-Core & DB 실행 가이드

이 가이드는 Big20 AI Interview Project의 Backend-Core 서비스와 PostgreSQL 데이터베이스를 실행하는 방법을 설명합니다.

---

## 📋 사전 요구사항

1. **Docker & Docker Compose** 설치 확인
   ```bash
   docker --version
   docker-compose --version
   ```

2. **환경 변수 설정** (`.env` 파일)
   ```bash
   # Database
   POSTGRES_USER=admin
   POSTGRES_PASSWORD=1234
   POSTGRES_DB=interview_db
   DATABASE_URL=postgresql://admin:1234@db:5432/interview_db
   
   # Redis
   REDIS_URL=redis://redis:6379/0
   
   # HuggingFace (질문 생성용)
   HUGGINGFACE_HUB_TOKEN=your_token_here
   
   # CORS
   ALLOWED_ORIGINS=http://localhost:3000
   ```

---

## 🎯 방법 1: Docker Compose로 전체 시스템 실행 (권장)

### 1-1. 모든 서비스 시작
```bash
cd c:\big20\Big20_aI_interview_project
docker-compose up -d
```

### 1-2. 특정 서비스만 시작 (Backend + DB만)
```bash
docker-compose up -d db redis backend
```

### 1-3. 서비스 상태 확인
```bash
docker-compose ps
```

출력 예시:
```
NAME                  IMAGE                          STATUS          PORTS
interview_db          pgvector/pgvector:pg18        Up 2 minutes    0.0.0.0:5432->5432/tcp
interview_redis       redis:7-alpine                Up 2 minutes    6379/tcp
interview_backend     big20_ai_interview_project-backend  Up 2 minutes    0.0.0.0:8000->8000/tcp
```

### 1-4. Backend 로그 확인
```bash
docker logs interview_backend -f
```

정상 실행 시 출력:
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 1-5. DB 초기화 확인
```bash
docker logs interview_db | Select-String "database system is ready"
```

---

## 🎯 방법 2: 개별 컨테이너 실행

### 2-1. PostgreSQL DB만 시작
```bash
docker-compose up -d db
```

### 2-2. Backend만 시작 (DB가 이미 실행 중일 때)
```bash
docker-compose up -d backend
```

---

## 🎯 방법 3: 로컬 개발 모드 (Docker 없이)

### 3-1. PostgreSQL 수동 실행 (Docker)
```bash
docker run -d \
  --name interview_db \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=interview_db \
  -p 5432:5432 \
  pgvector/pgvector:pg18
```

### 3-2. Backend 로컬 실행
```bash
cd backend-core

# 가상환경 생성 (선택사항)
python -m venv venv
.\venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (로컬용)
$env:DATABASE_URL="postgresql://admin:1234@localhost:5432/interview_db"
$env:REDIS_URL="redis://localhost:6379/0"
$env:HUGGINGFACE_HUB_TOKEN="your_token"

# Backend 실행
python main.py
```

또는 uvicorn 직접 실행:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔍 DB 접속 및 확인

### DB 컨테이너 내부 접속
```bash
docker exec -it interview_db psql -U admin -d interview_db
```

### 테이블 목록 확인
```sql
\dt
```

출력 예시:
```
                List of relations
 Schema |        Name         | Type  | Owner 
--------+---------------------+-------+-------
 public | evaluation_reports  | table | admin
 public | interviews          | table | admin
 public | job_postings        | table | admin
 public | questions           | table | admin
 public | transcripts         | table | admin
 public | users               | table | admin
```

### 특정 테이블 스키마 확인
```sql
\d users
```

### 데이터 조회
```sql
SELECT * FROM users;
SELECT * FROM interviews;
```

### DB 연결 종료
```sql
\q
```

---

## 🧪 API 테스트

### Health Check
```bash
curl http://localhost:8000/
```

응답:
```json
{
  "service": "AI Interview Backend v2.0",
  "status": "running",
  "database": "PostgreSQL with pgvector",
  "features": ["real-time STT", "emotion analysis", "AI evaluation"]
}
```

### 회원가입 테스트
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "test1234",
    "full_name": "Test User"
  }'
```

### 로그인 테스트
```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test1234"
  }'
```

---

## 🛠️ 문제 해결

### 1. Backend가 시작되지 않을 때

**증상**: `docker logs interview_backend`에서 에러 발생

**해결**:
```bash
# 컨테이너 재시작
docker-compose restart backend

# 또는 재빌드
docker-compose build --no-cache backend
docker-compose up -d backend
```

### 2. DB 연결 실패

**증상**: `OperationalError: could not connect to server`

**해결**:
```bash
# DB 상태 확인
docker-compose ps db

# DB 재시작
docker-compose restart db

# DB 로그 확인
docker logs interview_db --tail 50
```

### 3. 모델 로딩 실패

**증상**: `HUGGINGFACE_HUB_TOKEN` 관련 에러

**해결**:
1. `.env` 파일에 토큰 추가
2. 컨테이너 재시작
   ```bash
   docker-compose restart backend
   ```

### 4. 포트 충돌

**증상**: `port is already allocated`

**해결**:
```bash
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# 프로세스 종료 또는 docker-compose.yml에서 포트 변경
```

---

## 🔄 서비스 중지 및 정리

### 서비스 중지 (데이터 유지)
```bash
docker-compose stop
```

### 서비스 중지 및 컨테이너 삭제 (데이터 유지)
```bash
docker-compose down
```

### 완전 삭제 (볼륨 포함)
```bash
docker-compose down -v
```

⚠️ **주의**: `-v` 옵션은 DB 데이터를 포함한 모든 볼륨을 삭제합니다!

---

## 📊 모니터링

### 실시간 로그 확인
```bash
# Backend 로그
docker logs interview_backend -f

# DB 로그
docker logs interview_db -f

# 모든 서비스 로그
docker-compose logs -f
```

### 리소스 사용량 확인
```bash
docker stats interview_backend interview_db
```

---

## 🎓 추가 정보

- **Backend API 문서**: http://localhost:8000/docs (Swagger UI)
- **Backend Redoc**: http://localhost:8000/redoc
- **DB 포트**: localhost:5432
- **Backend 포트**: localhost:8000

---

**작성일**: 2026-01-26  
**버전**: 1.0
