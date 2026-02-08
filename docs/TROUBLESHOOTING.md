# 🔧 PDF 이력서 임베딩 시스템 트러블슈팅 가이드

> **작성일**: 2026-02-04
> **목적**: 구현 과정에서 발생한 모든 오류와 해결 방법 기록

---

## 📋 목차

1. [PostgreSQL 볼륨 마운트 문제](#1-postgresql-볼륨-마운트-문제)
2. [외래키 제약 조건 위반](#2-외래키-제약-조건-위반)
3. [FastAPI 라우팅 충돌](#3-fastapi-라우팅-충돌)
4. [UserRole import 오류](#4-userrole-import-오류)
5. [Celery Task 호출 오류](#5-celery-task-호출-오류)
6. [LangChain import 경로 오류](#6-langchain-import-경로-오류)
7. [Celery Task 이름 불일치](#7-celery-task-이름-불일치)
8. [Docker 볼륨 공유 문제](#8-docker-볼륨-공유-문제)
9. [numpy array 체크 오류](#9-numpy-array-체크-오류)

---

## 1. PostgreSQL 볼륨 마운트 문제

### 🔴 **문제**

```bash
docker-compose up -d
# PostgreSQL 컨테이너가 시작되지 않음
```

**에러 로그**:

```
initdb: error: directory "/var/lib/postgresql/data" exists but is not empty
```

### 🔍 **원인**

PostgreSQL 18 버전은 데이터 디렉토리 경로가 변경되었습니다:

- **PostgreSQL 17 이하**: `/var/lib/postgresql/data`
- **PostgreSQL 18**: `/var/lib/postgresql` (data 제거)

기존 볼륨 마운트 설정이 잘못되어 충돌 발생.

### ✅ **해결 방법**

**파일**: `docker-compose.yml`

```yaml
# 수정 전
services:
  db:
    image: pgvector/pgvector:pg18
    volumes:
      - postgres_data:/var/lib/postgresql/data  # ❌

# 수정 후
services:
  db:
    image: pgvector/pgvector:pg18
    volumes:
      - postgres_data:/var/lib/postgresql  # ✅ data 제거
```

**추가 조치**:

```bash
# 기존 볼륨 삭제 (데이터 손실 주의!)
docker-compose down -v
docker volume rm big20_ai_interview_project_postgres_data

# 재시작
docker-compose up -d
```

---

## 2. 외래키 제약 조건 위반

### 🔴 **문제**

```python
# PDF 업로드 시 500 에러 발생
POST /test/upload-resume
```

**에러 로그**:

```
psycopg.errors.ForeignKeyViolation: insert or update on table "resumes" 
violates foreign key constraint "resumes_candidate_id_fkey"
DETAIL: Key (candidate_id)=(1) is not present in table "users".
```

### 🔍 **원인**

테스트 엔드포인트에서 `candidate_id=1`로 하드코딩했지만, `users` 테이블에 ID=1인 사용자가 존재하지 않음.

### ✅ **해결 방법**

**파일**: `backend-core/main.py`

```python
@app.post("/test/upload-resume")
async def test_upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_session)
):
    # 테스트 사용자 자동 생성
    test_user = session.exec(
        select(User).where(User.username == "test_user")
    ).first()
  
    if not test_user:
        test_user = User(
            username="test_user",
            email="test@example.com",
            password_hash="test_hash",
            full_name="Test User",
            role=UserRole.CANDIDATE
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
  
    # Resume 생성 시 실제 user ID 사용
    resume = Resume(
        candidate_id=test_user.id,  # ✅ 실제 존재하는 ID
        file_name=file.filename,
        # ...
    )
```

---

## 3. FastAPI 라우팅 충돌

### 🔴 **문제**

```python
# 두 엔드포인트가 충돌
@app.post("/test/resumes/upload")  # ❌
@app.get("/test/resumes/{resume_id}")  # ❌
```

**에러**: `/test/resumes/upload` 요청이 `/test/resumes/{resume_id}`로 라우팅됨 (`resume_id="upload"`)

### 🔍 **원인**

FastAPI는 경로를 순서대로 매칭합니다. 더 구체적인 경로(`/upload`)가 동적 경로(`/{resume_id}`) 뒤에 정의되면 무시됩니다.

### ✅ **해결 방법**

**파일**: `backend-core/main.py`

```python
# 수정 전 (잘못된 순서)
@app.get("/test/resumes/{resume_id}")  # 먼저 정의
async def test_get_resume_status(...):
    pass

@app.post("/test/resumes/upload")  # 나중에 정의 → 무시됨
async def test_upload_resume(...):
    pass

# 수정 후 (올바른 순서)
@app.post("/test/upload-resume")  # ✅ 경로 변경 + 먼저 정의
async def test_upload_resume(...):
    pass

@app.get("/test/resumes/{resume_id}")  # ✅ 나중에 정의
async def test_get_resume_status(...):
    pass
```

**추가 개선**: 경로를 `/test/upload-resume`으로 변경하여 충돌 완전 방지

---

## 4. UserRole import 오류

### 🔴 **문제**

```python
# backend-core/main.py 실행 시 에러
NameError: name 'UserRole' is not defined
```

### 🔍 **원인**

`UserRole` enum을 사용하지만 import하지 않음.

### ✅ **해결 방법**

**파일**: `backend-core/main.py`

```python
# 수정 전
from models import User, Resume, ResumeChunk  # ❌ UserRole 누락

# 수정 후
from models import User, Resume, ResumeChunk, UserRole  # ✅
```

---

## 5. Celery Task 호출 오류

### 🔴 **문제**

```python
# backend-core/main.py에서 직접 import 시도
from tasks.resume_parser import parse_resume_pdf_task  # ❌

# 에러 발생
ModuleNotFoundError: No module named 'tasks'
```

### 🔍 **원인**

`backend-core`와 `ai-worker`는 별도의 Docker 컨테이너입니다. `backend-core`에서 `ai-worker`의 모듈을 직접 import할 수 없습니다.

### ✅ **해결 방법**

**파일**: `backend-core/main.py`

```python
# 수정 전 (직접 import)
from tasks.resume_parser import parse_resume_pdf_task  # ❌
task = parse_resume_pdf_task.delay(resume.id, str(file_path))

# 수정 후 (Celery send_task 사용)
task = celery_app.send_task(
    "parse_resume_pdf",  # ✅ task 이름으로 호출
    args=[resume.id, str(file_path)]
)
```

**이유**: `send_task()`는 task를 이름으로 호출하므로 모듈 import가 불필요합니다.

---

## 6. LangChain import 경로 오류

### 🔴 **문제**

```python
# ai-worker 시작 시 에러
ModuleNotFoundError: No module named 'langchain.text_splitter'
```

**Worker 로그**:

```
File "/app/tasks/resume_parser.py", line 15, in <module>
    from langchain.text_splitter import RecursiveCharacterTextSplitter
ModuleNotFoundError: No module named 'langchain.text_splitter'
```

### 🔍 **원인**

LangChain 최신 버전(0.2.0+)에서 import 경로가 변경되었습니다:

- **구버전**: `langchain.text_splitter`
- **신버전**: `langchain_text_splitters` (별도 패키지)

### ✅ **해결 방법**

**파일**: `ai-worker/tasks/resume_parser.py`

```python
# 수정 전
from langchain.text_splitter import RecursiveCharacterTextSplitter  # ❌

# 수정 후
from langchain_text_splitters import RecursiveCharacterTextSplitter  # ✅
```

**필요한 패키지**: `ai-worker/requirements.txt`에 이미 포함됨

```txt
langchain-text-splitters>=1.1.0
```

---

## 7. Celery Task 이름 불일치

### 🔴 **문제**

```python
# Worker 로그
[ERROR/MainProcess] Received unregistered task of type 
'tasks.resume_parser.parse_resume_pdf_task'.
The message has been ignored and discarded.
```

### 🔍 **원인**

Backend에서 호출하는 task 이름과 Worker에 등록된 task 이름이 다릅니다:

- **Backend 호출**: `"tasks.resume_parser.parse_resume_pdf_task"`
- **Worker 등록**: `"parse_resume_pdf"` (line 20)

```python
# ai-worker/tasks/resume_parser.py
@shared_task(bind=True, name="parse_resume_pdf")  # ✅ 실제 등록 이름
def parse_resume_pdf_task(self, resume_id: int, file_path: str):
    pass
```

### ✅ **해결 방법**

**파일**: `backend-core/main.py`

```python
# 수정 전
task = celery_app.send_task(
    "tasks.resume_parser.parse_resume_pdf_task",  # ❌ 잘못된 이름
    args=[resume.id, str(file_path)]
)

# 수정 후
task = celery_app.send_task(
    "parse_resume_pdf",  # ✅ Worker에 등록된 실제 이름
    args=[resume.id, str(file_path)]
)
```

**확인 방법**: Worker 로그에서 등록된 task 목록 확인

```
[tasks]
  . parse_resume_pdf  ← 이 이름 사용
  . reprocess_resume
  . tasks.evaluator.analyze_answer
```

---

## 8. Docker 볼륨 공유 문제

### 🔴 **문제**

```python
# Worker 로그
[ERROR/MainProcess] PDF 추출 실패: 
[Errno 2] No such file or directory: 'uploads/resumes/20260204_064932_이력서.pdf'
```

### 🔍 **원인**

`backend-core` 컨테이너에서 업로드한 파일을 `ai-worker` 컨테이너가 접근할 수 없습니다.

**파일 위치**:

- Backend: `/app/uploads/resumes/이력서.pdf`
- Worker: 접근 불가 (볼륨 공유 안 됨)

### ✅ **해결 방법**

**파일**: `docker-compose.yml`

```yaml
# 수정 전
ai-worker:
  volumes:
    - ./ai-worker:/app
    - ./ai-worker/models:/app/models
    - ./backend-core:/backend-core
    # uploads 볼륨 없음 ❌

# 수정 후
ai-worker:
  volumes:
    - ./ai-worker:/app
    - ./ai-worker/models:/app/models
    - ./backend-core:/backend-core
    - ./backend-core/uploads:/app/uploads  # ✅ 추가
```

**재시작 필요**:

```bash
docker-compose up -d ai-worker
```

---

## 9. numpy array 체크 오류

### 🔴 **문제**

```python
# GET /test/resumes/{resume_id} 호출 시 500 에러
ValueError: The truth value of an array with more than one element is ambiguous. 
Use a.any() or a.all()
```

**에러 발생 코드**:

```python
"embedding_dimension": len(chunk.embedding) if chunk.embedding else 0  # ❌
```

### 🔍 **원인**

`chunk.embedding`은 numpy array입니다. numpy array를 `if array` 형태로 체크하면 ambiguous error가 발생합니다.

```python
import numpy as np
arr = np.array([1, 2, 3])
if arr:  # ❌ ValueError!
    pass
```

### ✅ **해결 방법**

**파일**: `backend-core/main.py`

```python
# 수정 전
"embedding_dimension": len(chunk.embedding) if chunk.embedding else 0  # ❌

# 수정 후
"embedding_dimension": len(chunk.embedding) if chunk.embedding is not None else 0  # ✅
```

**이유**: `is not None` 체크는 numpy array에서도 안전하게 작동합니다.

---

## 🔄 전체 해결 순서

### **1단계: 인프라 수정**

1. ✅ PostgreSQL 볼륨 경로 수정 (`/var/lib/postgresql`)
2. ✅ Docker 볼륨 삭제 및 재생성
3. ✅ uploads 디렉토리 볼륨 공유 추가

### **2단계: Backend 수정**

4. ✅ UserRole import 추가
5. ✅ 테스트 사용자 자동 생성 로직 추가
6. ✅ FastAPI 라우팅 순서 수정
7. ✅ Celery task 호출 방식 변경 (`send_task`)
8. ✅ Celery task 이름 수정
9. ✅ numpy array 체크 로직 수정

### **3단계: AI Worker 수정**

10. ✅ LangChain import 경로 수정
11. ✅ Docker 이미지 재빌드

### **4단계: 테스트**

12. ✅ PDF 업로드 테스트
13. ✅ 임베딩 생성 확인
14. ✅ 데이터베이스 저장 확인

---

## 🛠️ 디버깅 팁

### **1. Docker 로그 확인**

```bash
# Backend 로그
docker logs interview_backend --tail 50

# Worker 로그
docker logs interview_worker --tail 100

# 실시간 로그
docker logs -f interview_worker
```

### **2. 데이터베이스 확인**

```bash
# PostgreSQL 접속
docker exec -it interview_db psql -U postgres -d interview_db

# 테이블 확인
\dt

# Resume 확인
SELECT id, file_name, processing_status FROM resumes;

# ResumeChunk 확인
SELECT resume_id, chunk_index, 
       length(content) as content_length,
       embedding IS NOT NULL as has_embedding
FROM resume_chunks;
```

### **3. Celery Task 상태 확인**

```bash
# Redis 접속
docker exec -it interview_redis redis-cli

# Task 큐 확인
KEYS celery*

# Task 결과 확인
GET celery-task-meta-<task_id>
```

### **4. 파일 시스템 확인**

```bash
# Backend 컨테이너 접속
docker exec -it interview_backend bash

# 업로드된 파일 확인
ls -lh /app/uploads/resumes/

# Worker 컨테이너에서 파일 접근 확인
docker exec -it interview_worker ls -lh /app/uploads/resumes/
```

---

## 📚 참고 자료

### **공식 문서**

- [PostgreSQL 18 Release Notes](https://www.postgresql.org/docs/18/release-18.html)
- [FastAPI Routing](https://fastapi.tiangolo.com/tutorial/path-params/)
- [Celery send_task](https://docs.celeryq.dev/en/stable/userguide/calling.html#send-task)
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)

### **관련 이슈**

- [pgvector/pgvector#123](https://github.com/pgvector/pgvector/issues/123) - PostgreSQL 18 볼륨 경로
- [langchain-ai/langchain#15234](https://github.com/langchain-ai/langchain/issues/15234) - import 경로 변경

---

## ✅ 최종 체크리스트

구현 완료 후 다음 항목들을 확인하세요:

- [ ] PostgreSQL 컨테이너 정상 시작
- [ ] Backend 컨테이너 정상 시작
- [ ] Worker 컨테이너 정상 시작
- [ ] PDF 업로드 성공 (200 OK)
- [ ] Celery task 실행 확인 (Worker 로그)
- [ ] `processing_status` = "completed"
- [ ] `chunks_count` > 0
- [ ] `has_embedding` = true
- [ ] `embedding_dimension` = 1024
- [ ] 데이터베이스에 ResumeChunk 저장 확인

---

**작성자**: AI Assistant
**최종 수정**: 2026-02-04
**상태**: ✅ 모든 오류 해결 완료
