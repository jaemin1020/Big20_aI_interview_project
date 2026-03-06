# 이력서 임베딩 및 파싱 통합 가이드

## 📚 개요

root 디렉토리의 `embedding.py`에 있던 이력서 멀티 섹션 임베딩 기능을 프로젝트에 통합했습니다.

## 🎯 주요 기능

### 1. **멀티 섹션 임베딩 생성**
이력서를 섹션별(프로필, 경력, 프로젝트, 자기소개 등)로 분리하여 각각 임베딩을 생성합니다.

### 2. **RAG 기반 검색**
질문에 가장 관련있는 이력서 섹션을 벡터 유사도 기반으로 검색합니다.

## 📁 추가된 파일

### 1. `ai-worker/utils/resume_embedder.py`
- **ResumeEmbedder 클래스**: 이력서 섹션별 임베딩 생성
- **섹션 직렬화 함수**: 각 섹션을 텍스트로 변환
- **검색 함수**: 쿼리와 관련있는 섹션 검색

### 2. `ai-worker/tasks/resume_embedding.py`
- **generate_resume_embeddings_task**: 멀티 섹션 임베딩 생성 Celery Task
- **search_resume_sections_task**: 이력서 섹션 검색 Celery Task

## 🔧 사용 방법

### 1. 이력서 파싱 후 멀티 섹션 임베딩 생성

```python
from tasks.resume_embedding import generate_resume_embeddings_task

# 이력서 파싱 완료 후 호출
result = generate_resume_embeddings_task.delay(resume_id=1)

# 결과 확인
print(result.get())
# {
#   "status": "success",
#   "resume_id": 1,
#   "total_embeddings": 15,
#   "stats": {
#     "profile": 1,
#     "experience": 3,
#     "projects": 2,
#     ...
#   }
# }
```

### 2. 이력서 섹션 검색

```python
from tasks.resume_embedding import search_resume_sections_task

# 특정 키워드로 관련 섹션 검색
result = search_resume_sections_task.delay(
    resume_id=1,
    query="프로젝트 경험",
    top_k=3
)

# 결과 확인
print(result.get())
# {
#   "status": "success",
#   "resume_id": 1,
#   "query": "프로젝트 경험",
#   "results": [
#     {
#       "section": "project",
#       "id": "proj_1",
#       "text": "프로젝트명: AI 챗봇 개발...",
#       "similarity": 0.87
#     },
#     ...
#   ]
# }
```

### 3. 직접 사용 (Celery 없이)

```python
from utils.resume_embedder import get_resume_embedder

embedder = get_resume_embedder()

# 이력서 데이터 준비
resume_data = {
    "resume_id": "res_001",
    "profile": {
        "name": "홍길동",
        "target_position": "백엔드 개발자",
        "target_company": "ABC Corp",
        "contact": "hong@example.com"
    },
    "experience": [
        {
            "company": "XYZ Inc",
            "role": "백엔드 개발자",
            "period": "2020-2023",
            "description": "FastAPI 기반 API 개발..."
        }
    ],
    "projects": [
        {
            "title": "AI 챗봇 개발",
            "period": "2022-2023",
            "description": "LangChain을 활용한..."
        }
    ],
    # ... 기타 섹션
}

# 임베딩 생성
embeddings = embedder.build_resume_embeddings(resume_data)

# 검색
results = embedder.search_relevant_sections(
    query="프로젝트 경험",
    resume_embeddings=embeddings,
    top_k=3
)
```

## 🔄 기존 시스템과의 통합

### 청크 기반 vs 섹션 기반

| 방식 | 용도 | 장점 |
|------|------|------|
| **청크 기반** (`resume_parser.py`) | 일반적인 RAG 검색 | 세밀한 검색, 긴 문서 처리 |
| **섹션 기반** (`resume_embedder.py`) | 구조화된 정보 추출 | 의미 단위 검색, 질문 생성 |

두 방식은 **병행 사용**을 권장합니다:
- **청크 기반**: 전체 이력서 내용 검색
- **섹션 기반**: 특정 섹션(경력, 프로젝트 등) 타겟팅

## 📊 데이터 구조

### 생성된 임베딩 구조

```json
{
  "resume_id": "res_001",
  "role": "백엔드 개발자",
  "embeddings": {
    "profile": {
      "text": "이름: 홍길동\n지원직무: 백엔드 개발자...",
      "vector": [0.123, -0.456, ...]  // 1024차원
    },
    "experience": [
      {
        "id": "exp_1",
        "text": "회사: XYZ Inc\n직무: 백엔드 개발자...",
        "vector": [0.234, -0.567, ...]
      }
    ],
    "projects": [...],
    "self_introduction": [
      {
        "type": "지원동기/성장계획",
        "text": "질문: ...\n답변: ...",
        "vector": [...]
      }
    ],
    ...
  }
}
```

## 🚀 활용 사례

### 1. 맞춤형 질문 생성
```python
# 프로젝트 경험 기반 질문 생성
results = embedder.search_relevant_sections(
    query="프로젝트 경험",
    resume_embeddings=embeddings,
    top_k=2
)

for result in results:
    print(f"섹션: {result['section']}")
    print(f"내용: {result['text']}")
    print(f"유사도: {result['similarity']}")
    # 이 내용을 바탕으로 질문 생성
```

### 2. 지원 동기 분석
```python
# 자기소개서에서 지원동기 추출
results = embedder.search_relevant_sections(
    query="지원 동기",
    resume_embeddings=embeddings,
    top_k=1
)
```

### 3. 기술 스택 매칭
```python
# 특정 기술 관련 경험 검색
results = embedder.search_relevant_sections(
    query="FastAPI Python 백엔드",
    resume_embeddings=embeddings,
    top_k=3
)
```

## ⚙️ 설정

### 임베딩 모델
- **모델**: `nlpai-lab/KURE-v1` (한국어 특화)
- **차원**: 1024
- **접두어**: 
  - Query: `"query: "` (검색 쿼리)
  - Passage: `"passage: "` (문서 내용)

### 성능 최적화
- **싱글톤 패턴**: 모델은 한 번만 로드
- **배치 처리**: 여러 섹션 동시 임베딩 가능
- **캐싱**: 생성된 임베딩은 DB에 저장

## 📝 TODO

- [ ] 이력서 파싱 시 자동으로 멀티 섹션 임베딩 생성
- [ ] 질문 생성 시 섹션 기반 검색 활용
- [ ] 섹션별 가중치 조정 기능
- [ ] 이력서 비교/매칭 기능

## 🔗 관련 파일

- `ai-worker/utils/resume_embedder.py` - 임베딩 생성기
- `ai-worker/utils/vector_utils.py` - 기본 벡터 유틸리티
- `ai-worker/tasks/resume_embedding.py` - Celery Task
- `ai-worker/tasks/resume_parser.py` - 기존 청크 기반 파싱

---

**작성일**: 2026-02-06  
**작성자**: AI Agent (Antigravity)
