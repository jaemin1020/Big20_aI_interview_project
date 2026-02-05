# PDF 이력서 파싱 시스템

## 📋 개요
PDF 이력서를 업로드하면 자동으로 텍스트를 추출하고 구조화하여 DB에 저장하는 시스템입니다.

---

## 🔧 필요한 라이브러리

### ai-worker/requirements.txt
```txt
# PDF Processing & Document Parsing
PyPDF2>=3.0.0          # PDF 텍스트 추출 (기본)
pdfplumber>=0.10.0     # PDF 텍스트 추출 (고급, 더 정확함)
python-docx>=1.1.0     # DOCX 파일 처리 (선택)
```

### 설치 방법
```bash
# ai-worker 컨테이너에서
pip install PyPDF2 pdfplumber python-docx

# 또는 Docker 재빌드
docker-compose build ai-worker
```

---

## 📁 생성된 파일

### 1. `ai-worker/utils/pdf_parser.py`
PDF 텍스트 추출 유틸리티

**기능**:
- PyPDF2 방식 추출
- pdfplumber 방식 추출 (더 정확)
- 자동 fallback
- 메타데이터 추출
- 텍스트 정제

**사용 예시**:
```python
from utils.pdf_parser import ResumePDFParser

# 텍스트 추출
text = ResumePDFParser.extract_text("resume.pdf")

# 정제
cleaned = ResumePDFParser.clean_text(text)

# 메타데이터
metadata = ResumePDFParser.extract_metadata("resume.pdf")
```

---

### 2. `ai-worker/utils/resume_structurer.py`
LLM 기반 이력서 구조화 파서

**기능**:
- LLM 기반 구조화 (선택)
- 규칙 기반 구조화 (fallback)
- Pydantic 모델 정의

**구조화 결과**:
```json
{
  "summary": "5년차 AI/백엔드 개발자...",
  "experience": [
    {
      "company": "카카오",
      "position": "AI 엔지니어",
      "duration": "2021-03 ~ 현재",
      "description": "LLM 기반 챗봇 개발",
      "achievements": ["GPT-4 챗봇 개발", "RAG 시스템 구축"],
      "tech_stack": ["Python", "FastAPI", "LangChain"]
    }
  ],
  "education": [...],
  "skills": {
    "programming_languages": ["Python", "Java"],
    "frameworks": ["FastAPI", "Django"],
    "ai_ml": ["LangChain", "HuggingFace"],
    "databases": ["PostgreSQL", "Redis"],
    "devops": ["Docker", "AWS"]
  },
  "projects": [...],
  "certifications": [...],
  "awards": [...]
}
```

**사용 예시**:
```python
from utils.resume_structurer import ResumeStructurer

structurer = ResumeStructurer()  # LLM 없이
structured = structurer.structure_with_rules(resume_text)

# 또는 LLM 사용
from langchain_community.llms import HuggingFacePipeline
llm = HuggingFacePipeline(...)
structurer = ResumeStructurer(llm=llm)
structured = structurer.structure_with_llm(resume_text)
```

---

### 3. `ai-worker/tasks/resume_parser.py`
Celery Task (자동화)

**Task**: `parse_resume_pdf`
1. PDF 텍스트 추출
2. 이력서 구조화
3. 임베딩 생성 (768차원)
4. DB 업데이트

**사용 예시**:
```python
# Celery Task 전송
celery_app.send_task(
    "parse_resume_pdf",
    args=[resume_id, file_path]
)
```

---

### 4. `backend-core/routes/resumes.py`
FastAPI 엔드포인트

**엔드포인트**:

#### POST `/api/resumes/upload`
이력서 업로드

**Request**:
```bash
curl -X POST "http://localhost:8000/api/resumes/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf"
```

**Response**:
```json
{
  "resume_id": 1,
  "file_name": "resume.pdf",
  "file_size": 245678,
  "status": "processing",
  "message": "이력서 업로드 완료. 파싱 중입니다."
}
```

---

#### GET `/api/resumes/{resume_id}`
이력서 조회

**Response**:
```json
{
  "id": 1,
  "file_name": "resume.pdf",
  "file_size": 245678,
  "uploaded_at": "2026-01-29T10:00:00",
  "processed_at": "2026-01-29T10:01:30",
  "processing_status": "completed",
  "has_structured_data": true,
  "structured_data": {
    "summary": "...",
    "experience": [...],
    ...
  }
}
```

---

#### GET `/api/resumes/user/{user_id}`
사용자의 이력서 목록

**Response**:
```json
{
  "user_id": 123,
  "total": 2,
  "resumes": [
    {
      "id": 1,
      "file_name": "resume_v2.pdf",
      "uploaded_at": "2026-01-29T10:00:00",
      "processing_status": "completed"
    },
    {
      "id": 2,
      "file_name": "resume_v1.pdf",
      "uploaded_at": "2026-01-28T15:30:00",
      "processing_status": "completed"
    }
  ]
}
```

---

#### POST `/api/resumes/{resume_id}/reprocess`
이력서 재처리

**Response**:
```json
{
  "resume_id": 1,
  "status": "pending",
  "message": "재처리 작업이 시작되었습니다."
}
```

---

#### DELETE `/api/resumes/{resume_id}`
이력서 삭제 (soft delete)

**Response**:
```json
{
  "resume_id": 1,
  "message": "이력서가 삭제되었습니다."
}
```

---

## 🔄 전체 워크플로우

### 1. 이력서 업로드
```
사용자 → POST /api/resumes/upload
  ↓
파일 저장 (./uploads/resumes/)
  ↓
Resume 레코드 생성 (status: pending)
  ↓
Celery Task 전송 (parse_resume_pdf)
  ↓
응답 반환 (resume_id, status: processing)
```

### 2. 비동기 파싱 (Celery Worker)
```
Celery Worker 수신
  ↓
PDF 텍스트 추출 (PyPDF2/pdfplumber)
  ↓
텍스트 정제
  ↓
이력서 구조화 (규칙 기반 또는 LLM)
  ↓
임베딩 생성 (sentence-transformers)
  ↓
DB 업데이트 (status: completed)
```

### 3. 이력서 조회
```
사용자 → GET /api/resumes/{resume_id}
  ↓
Resume 조회
  ↓
structured_data 반환
```

### 4. 면접 생성 시 이력서 연결
```
POST /api/interviews
{
  "candidate_id": 123,
  "resume_id": 1,  ← 이력서 연결
  "position": "AI 엔지니어"
}
  ↓
질문 생성 시 이력서 정보 활용
  ↓
"이력서에 RAG 시스템 경험이 있는데..."
```

---

## 📊 처리 상태 (processing_status)

| 상태 | 설명 |
|------|------|
| `pending` | 파싱 대기 중 |
| `processing` | 파싱 진행 중 |
| `completed` | 파싱 완료 |
| `failed` | 파싱 실패 |

---

## 🧪 테스트 방법

### 1. PDF 파서 테스트
```bash
# ai-worker 컨테이너에서
python utils/pdf_parser.py /path/to/resume.pdf
```

### 2. 구조화 파서 테스트
```bash
python utils/resume_structurer.py
```

### 3. API 테스트
```bash
# 이력서 업로드
curl -X POST "http://localhost:8000/api/resumes/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf"

# 조회
curl "http://localhost:8000/api/resumes/1" \
  -H "Authorization: Bearer <token>"
```

---

## ⚙️ 환경 변수

```bash
# backend-core/.env
RESUME_UPLOAD_DIR=./uploads/resumes
CELERY_BROKER_URL=redis://redis:6379/0
```

---

## 🚀 다음 단계

1. **LLM 기반 구조화 개선**
   - GPT-4 또는 Solar-10.7B 사용
   - 더 정확한 정보 추출

2. **이미지 OCR 지원**
   - 스캔된 PDF 처리
   - Tesseract OCR 통합

3. **다국어 지원**
   - 영문 이력서 파싱
   - 자동 언어 감지

4. **이력서 검증**
   - 필수 항목 체크
   - 형식 검증

---

**작성일**: 2026-01-29  
**버전**: 1.0
