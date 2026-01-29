# 🚀 자연어DB 빠른 시작 가이드

## 개요

**자연어DB**는 이미 구축되어 있습니다! PostgreSQL에 텍스트 데이터가 저장되어 있으며, 다양한 검색 방법을 사용할 수 있습니다.

---

## 1단계: 현재 데이터 확인

```bash
# PostgreSQL 컨테이너 접속
docker exec -it interview_db psql -U admin -d interview_db

# 테이블 목록 확인
\dt

# 질문 데이터 확인
SELECT COUNT(*) FROM questions;
SELECT * FROM questions LIMIT 3;

# 종료
\q
```

---

## 2단계: 검색 인덱스 생성 (성능 최적화)

```bash
# PostgreSQL 컨테이너 접속
docker exec -it interview_db psql -U admin -d interview_db

# 인덱스 생성 스크립트 실행
\i /docker-entrypoint-initdb.d/../create_indexes.sql

# 또는 직접 SQL 파일 실행
```

**또는 컨테이너 외부에서:**
```bash
docker exec -i interview_db psql -U admin -d interview_db < infra/postgres/create_indexes.sql
```

---

## 3단계: 자연어 검색 테스트

### Python 스크립트로 테스트

```bash
# Backend 컨테이너 접속
docker exec -it interview_backend bash

# 검색 유틸리티 실행
cd /app/scripts
python natural_language_utils.py
```

**예상 출력:**
```
🗣️ 자연어DB 검색 테스트
1️⃣ 질문 통계
총 질문 수: 7
카테고리별: {'technical': 3, 'behavioral': 2, ...}

2️⃣ 키워드 검색: 'Python'
1. [hard] Python에서 GIL(Global Interpreter Lock)이 무엇인지...

3️⃣ 다중 키워드 검색: ['데이터베이스', 'FastAPI']
1. [technical] FastAPI와 Flask의 차이점을 설명하고...
```

### SQL로 직접 테스트

```sql
-- 1. 키워드 검색 (ILIKE)
SELECT id, content, difficulty
FROM questions
WHERE content ILIKE '%Python%'
LIMIT 5;

-- 2. 전문 검색 (Full-Text Search)
SELECT
    id,
    content,
    ts_rank(to_tsvector('simple', content), query) AS rank
FROM questions,
     plainto_tsquery('simple', 'Python 멀티스레딩') query
WHERE to_tsvector('simple', content) @@ query
ORDER BY rank DESC
LIMIT 5;

-- 3. 필터링 + 검색
SELECT * FROM questions
WHERE position = 'Backend 개발자'
  AND difficulty = 'hard'
  AND content ILIKE '%데이터베이스%';

-- 4. 대화 기록 검색
SELECT speaker, text, timestamp
FROM transcripts
WHERE interview_id = 1
  AND text ILIKE '%Python%'
ORDER BY timestamp;
```

---

## 4단계: API 엔드포인트 추가 (선택)

`backend-core/main.py`에 다음 코드를 추가하세요:

```python
from scripts.natural_language_utils import (
    search_questions_by_keyword,
    filter_questions,
    search_transcripts_by_keyword,
    get_questions_paginated
)

@app.get("/api/search/questions")
async def search_questions(
    keyword: str,
    category: str = None,
    difficulty: str = None,
    position: str = None,
    limit: int = 20
):
    """질문 검색 API"""
    if category or difficulty or position:
        results = filter_questions(
            category=category,
            difficulty=difficulty,
            position=position,
            keyword=keyword,
            limit=limit
        )
    else:
        results = search_questions_by_keyword(keyword, limit)

    return {
        "keyword": keyword,
        "total": len(results),
        "results": [
            {
                "id": q.id,
                "content": q.content,
                "category": q.category,
                "difficulty": q.difficulty,
                "position": q.position
            }
            for q in results
        ]
    }

@app.get("/api/interviews/{interview_id}/transcripts/search")
async def search_interview_transcripts(
    interview_id: int,
    keyword: str
):
    """면접 대화 기록 검색 API"""
    results = search_transcripts_by_keyword(interview_id, keyword)

    return {
        "interview_id": interview_id,
        "keyword": keyword,
        "total": len(results),
        "results": [
            {
                "speaker": t.speaker,
                "text": t.text,
                "timestamp": t.timestamp,
                "emotion": t.emotion
            }
            for t in results
        ]
    }

@app.get("/api/questions/paginated")
async def get_questions(
    page: int = 1,
    page_size: int = 20,
    category: str = None,
    difficulty: str = None,
    position: str = None
):
    """페이지네이션 질문 조회 API"""
    result = get_questions_paginated(
        page=page,
        page_size=page_size,
        category=category,
        difficulty=difficulty,
        position=position
    )

    return result
```

---

## 5단계: 프론트엔드에서 사용

```javascript
// 질문 검색
const searchQuestions = async (keyword, filters = {}) => {
  const params = new URLSearchParams({
    keyword,
    ...filters
  });

  const response = await fetch(`/api/search/questions?${params}`);
  const data = await response.json();
  return data.results;
};

// 사용 예시
const results = await searchQuestions('Python', {
  category: 'technical',
  difficulty: 'hard',
  position: 'Backend 개발자'
});

// 대화 기록 검색
const searchTranscripts = async (interviewId, keyword) => {
  const response = await fetch(
    `/api/interviews/${interviewId}/transcripts/search?keyword=${keyword}`
  );
  return await response.json();
};

// 페이지네이션
const getQuestions = async (page = 1, pageSize = 20) => {
  const response = await fetch(
    `/api/questions/paginated?page=${page}&page_size=${pageSize}`
  );
  return await response.json();
};
```

---

## 주요 검색 방법 비교

| 방법 | 속도 | 정확도 | 사용 케이스 |
|------|------|--------|------------|
| **LIKE/ILIKE** | 빠름 | 정확 | 정확한 키워드 매칭 |
| **전문 검색 (FTS)** | 중간 | 높음 | 자연어 쿼리, 랭킹 필요 |
| **벡터 검색** | 느림 | 매우 높음 | 의미적 유사도 |
| **하이브리드** | 중간 | 매우 높음 | 키워드 + 의미 결합 |

---

## 성능 최적화 팁

### 1. 인덱스 사용 확인
```sql
-- 쿼리 실행 계획 확인
EXPLAIN ANALYZE
SELECT * FROM questions WHERE content ILIKE '%Python%';

-- 인덱스가 사용되는지 확인
-- "Index Scan" 또는 "Bitmap Index Scan"이 나오면 OK
```

### 2. 쿼리 최적화
```python
# ❌ 비효율적: 여러 번 쿼리
for interview_id in interview_ids:
    transcripts = get_transcripts(interview_id)

# ✅ 효율적: 한 번에 조회
transcripts = get_transcripts_bulk(interview_ids)
```

### 3. 캐싱 활용
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_popular_questions(limit=10):
    """자주 조회되는 질문은 캐싱"""
    return search_questions_by_keyword("", limit)
```

---

## 문제 해결

### 1. 전문 검색 오류
```
ERROR: function to_tsvector(unknown, character varying) does not exist
```

**해결:**
```sql
-- 인덱스 생성 스크립트 실행
\i /path/to/create_indexes.sql
```

### 2. 검색 결과가 없음
```python
# 데이터 확인
with Session(engine) as session:
    count = session.exec(select(func.count(Question.id))).one()
    print(f"총 질문 수: {count}")

# 데이터가 없으면 샘플 데이터 삽입
python scripts/populate_vectordb.py
```

### 3. 느린 검색 속도
```sql
-- 인덱스 확인
SELECT * FROM pg_indexes WHERE tablename = 'questions';

-- 통계 업데이트
ANALYZE questions;
```

---

## 다음 단계

✅ 자연어DB 검색 준비 완료!

- [ ] API 엔드포인트 추가
- [ ] 프론트엔드 검색 UI 구현
- [ ] 자동완성 기능 추가
- [ ] 검색 히스토리 저장

---

## 참고 자료

- **완벽한 가이드**: `NATURAL_LANGUAGE_DB_GUIDE.md`
- **검색 유틸리티**: `backend-core/scripts/natural_language_utils.py`
- **인덱스 스크립트**: `infra/postgres/create_indexes.sql`
