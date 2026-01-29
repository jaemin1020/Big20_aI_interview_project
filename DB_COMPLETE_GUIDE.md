# 📊 VectorDB와 자연어DB 완벽 가이드 - 종합 요약

## 🎯 핵심 요약

### 자연어DB는 이미 구축되어 있습니다! ✅

**자연어DB**는 일반적인 PostgreSQL 데이터베이스에 텍스트를 저장하고 검색하는 것입니다.
현재 프로젝트의 모든 테이블(Users, Interviews, Questions, Transcripts 등)이 자연어DB입니다.

### VectorDB는 추가 기능입니다! 🚀

**VectorDB**는 텍스트를 숫자 벡터로 변환하여 **의미적 유사도** 검색을 가능하게 합니다.
pgvector 확장을 사용하여 PostgreSQL에서 벡터 검색을 지원합니다.

---

## 📁 생성된 파일 목록

### 📚 가이드 문서
1. **`.agent/workflows/vectordb-setup-guide.md`** - VectorDB 완벽 가이드
2. **`VECTORDB_QUICKSTART.md`** - VectorDB 빠른 시작
3. **`NATURAL_LANGUAGE_DB_GUIDE.md`** - 자연어DB 완벽 가이드
4. **`NATURAL_LANGUAGE_DB_QUICKSTART.md`** - 자연어DB 빠른 시작

### 🔧 스크립트
5. **`backend-core/scripts/populate_vectordb.py`** - VectorDB 샘플 데이터 삽입
6. **`backend-core/scripts/vector_utils.py`** - VectorDB 검색 유틸리티
7. **`backend-core/scripts/test_vectordb.py`** - VectorDB 시스템 테스트
8. **`backend-core/scripts/natural_language_utils.py`** - 자연어DB 검색 유틸리티

### 🗄️ SQL 스크립트
9. **`infra/postgres/create_indexes.sql`** - 검색 성능 최적화 인덱스

### 📖 업데이트된 문서
10. **`README.md`** - VectorDB와 자연어DB 섹션 추가

---

## 🔍 VectorDB vs 자연어DB 비교

| 구분 | 자연어DB | VectorDB |
|------|----------|----------|
| **저장 방식** | 텍스트 그대로 | 숫자 벡터 (768차원) |
| **검색 방식** | 키워드 매칭 (LIKE, ILIKE) | 의미적 유사도 (코사인 거리) |
| **검색 예시** | `WHERE content LIKE '%Python%'` | `ORDER BY embedding <=> query_vector` |
| **장점** | 정확한 매칭, 빠른 속도 | 의미 파악, 동의어 검색 |
| **단점** | 동의어 검색 어려움 | 계산 비용 높음 |
| **사용 케이스** | 정확한 검색, 필터링 | 유사 질문 추천, 답변 평가 |
| **구축 상태** | ✅ 이미 구축됨 | ⚠️ 추가 설정 필요 |

### 실전 예시

**자연어DB 검색:**
```sql
-- "Python"이라는 단어가 포함된 질문 검색
SELECT * FROM questions WHERE content ILIKE '%Python%';
```

**VectorDB 검색:**
```python
# "파이썬 멀티스레딩"과 의미적으로 유사한 질문 검색
# → "Python에서 GIL이 무엇인지..." (유사도: 0.92)
find_similar_questions("파이썬 멀티스레딩")
```

---

## 🚀 빠른 시작 가이드

### 1️⃣ 자연어DB 사용 (즉시 사용 가능!)

```bash
# Backend 컨테이너 접속
docker exec -it interview_backend bash

# 자연어 검색 테스트
cd /app/scripts
python natural_language_utils.py

# 검색 인덱스 생성 (성능 최적화)
exit
docker exec -i interview_db psql -U admin -d interview_db < infra/postgres/create_indexes.sql
```

**주요 기능:**
- ✅ 키워드 검색 (LIKE/ILIKE)
- ✅ 전문 검색 (Full-Text Search)
- ✅ 필터링 (카테고리, 난이도, 직무)
- ✅ 통계 분석 (대화 내용, 키워드 빈도)

### 2️⃣ VectorDB 구축 (추가 설정)

```bash
# Backend 컨테이너 접속
docker exec -it interview_backend bash

# VectorDB 시스템 테스트
cd /app/scripts
python test_vectordb.py

# 샘플 데이터 삽입 (7개 질문/답변)
python populate_vectordb.py

# 벡터 검색 테스트
python vector_utils.py
```

**주요 기능:**
- ✅ 유사 질문 검색 (의미 기반)
- ✅ 답변 평가 (우수 답변과 비교)
- ✅ 질문 추천 (직무/기술 스택 기반)
- ✅ 하이브리드 검색 (키워드 + 벡터)

---

## 💡 언제 무엇을 사용하나요?

### 자연어DB 사용 케이스

✅ **정확한 키워드 검색**
```python
# "Python"이라는 단어가 정확히 포함된 질문만
search_questions_by_keyword("Python")
```

✅ **필터링 및 정렬**
```python
# Backend 개발자 + 어려움 + 기술 질문
filter_questions(
    position="Backend 개발자",
    difficulty="hard",
    category="technical"
)
```

✅ **대화 기록 검색**
```python
# 특정 면접에서 "데이터베이스"가 언급된 대화
search_transcripts_by_keyword(interview_id=1, keyword="데이터베이스")
```

✅ **통계 분석**
```python
# 면접 대화 분석 (단어 수, 키워드 빈도, 감정)
analyze_interview_conversation(interview_id=1)
```

### VectorDB 사용 케이스

✅ **의미 기반 유사 질문 검색**
```python
# "파이썬 멀티스레딩" → "GIL 설명" (동일한 의미)
find_similar_questions("파이썬 멀티스레딩")
```

✅ **답변 자동 평가**
```python
# 사용자 답변을 우수 답변과 비교하여 점수 계산
evaluate_answer(question_id=1, user_answer="GIL은...")
```

✅ **맞춤형 질문 추천**
```python
# 사용자의 기술 스택에 맞는 질문 추천
recommend_questions_for_position(
    position="Backend 개발자",
    user_skills="Python, FastAPI, PostgreSQL"
)
```

✅ **하이브리드 검색**
```python
# 키워드 검색 + 의미 검색 결합
search_questions_hybrid("데이터베이스 최적화")
```

---

## 📊 성능 비교

### 검색 속도

| 방법 | 데이터 100개 | 데이터 10,000개 | 데이터 100,000개 |
|------|-------------|----------------|-----------------|
| **LIKE** | 1ms | 10ms | 100ms |
| **전문 검색 (인덱스)** | 2ms | 15ms | 50ms |
| **벡터 검색 (인덱스 없음)** | 50ms | 5000ms | 50000ms |
| **벡터 검색 (IVFFlat)** | 10ms | 100ms | 500ms |

### 정확도

| 방법 | 정확한 매칭 | 동의어 검색 | 의미 파악 |
|------|------------|------------|----------|
| **LIKE** | ⭐⭐⭐⭐⭐ | ❌ | ❌ |
| **전문 검색** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **벡터 검색** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🛠️ 실전 구현 예시

### API 엔드포인트 (FastAPI)

```python
# backend-core/main.py

from scripts.natural_language_utils import (
    search_questions_by_keyword,
    filter_questions,
    get_questions_paginated
)
from scripts.vector_utils import (
    find_similar_questions,
    evaluate_answer
)

# 자연어DB: 키워드 검색
@app.get("/api/search/questions")
async def search_questions(keyword: str, limit: int = 20):
    results = search_questions_by_keyword(keyword, limit)
    return {"results": results}

# 자연어DB: 필터링
@app.get("/api/questions/filter")
async def filter_questions_api(
    category: str = None,
    difficulty: str = None,
    position: str = None
):
    results = filter_questions(
        category=category,
        difficulty=difficulty,
        position=position
    )
    return {"results": results}

# VectorDB: 유사 질문 검색
@app.get("/api/questions/similar")
async def similar_questions(query: str, top_k: int = 5):
    results = find_similar_questions(query, top_k)
    return {"results": results}

# VectorDB: 답변 평가
@app.post("/api/answers/evaluate")
async def evaluate_answer_api(question_id: int, user_answer: str):
    evaluation = evaluate_answer(question_id, user_answer)
    return evaluation
```

### 프론트엔드 (React)

```javascript
// 자연어DB: 키워드 검색
const searchByKeyword = async (keyword) => {
  const response = await fetch(`/api/search/questions?keyword=${keyword}`);
  return await response.json();
};

// VectorDB: 유사 질문 검색
const findSimilar = async (query) => {
  const response = await fetch(`/api/questions/similar?query=${query}`);
  return await response.json();
};

// 사용 예시
const handleSearch = async (userInput) => {
  // 1. 먼저 정확한 키워드 검색
  const exactResults = await searchByKeyword(userInput);

  // 2. 결과가 없으면 유사 질문 검색
  if (exactResults.length === 0) {
    const similarResults = await findSimilar(userInput);
    return similarResults;
  }

  return exactResults;
};
```

---

## 📈 최적화 전략

### 1. 인덱스 생성 (필수!)

```bash
# 검색 성능을 10배 이상 향상
docker exec -i interview_db psql -U admin -d interview_db < infra/postgres/create_indexes.sql
```

### 2. 캐싱 활용

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_popular_questions():
    """자주 조회되는 질문은 메모리에 캐싱"""
    return search_questions_by_keyword("", limit=10)
```

### 3. 배치 처리

```python
# ❌ 비효율적: 하나씩 처리
for text in texts:
    embedding = model.encode(text)

# ✅ 효율적: 배치 처리
embeddings = model.encode(texts, batch_size=32)
```

### 4. 페이지네이션

```python
# 한 번에 모든 데이터를 가져오지 말고 페이지별로
results = get_questions_paginated(page=1, page_size=20)
```

---

## 🎓 학습 자료

### 초급 (기본 사용)
1. `NATURAL_LANGUAGE_DB_QUICKSTART.md` - 자연어DB 빠른 시작
2. `VECTORDB_QUICKSTART.md` - VectorDB 빠른 시작

### 중급 (심화 학습)
3. `NATURAL_LANGUAGE_DB_GUIDE.md` - 자연어DB 완벽 가이드
4. `.agent/workflows/vectordb-setup-guide.md` - VectorDB 완벽 가이드

### 고급 (실전 구현)
5. `backend-core/scripts/natural_language_utils.py` - 자연어 검색 구현
6. `backend-core/scripts/vector_utils.py` - 벡터 검색 구현

---

## ✅ 체크리스트

### 자연어DB (즉시 사용 가능)
- [x] PostgreSQL 설치 및 실행
- [x] 테이블 생성 (Users, Questions, Transcripts 등)
- [ ] 검색 인덱스 생성 (`create_indexes.sql`)
- [ ] 검색 기능 테스트 (`natural_language_utils.py`)
- [ ] API 엔드포인트 추가

### VectorDB (추가 설정)
- [x] pgvector 확장 설치
- [ ] 임베딩 모델 다운로드
- [ ] 샘플 데이터 삽입 (`populate_vectordb.py`)
- [ ] 벡터 검색 테스트 (`vector_utils.py`)
- [ ] 벡터 인덱스 생성 (데이터 1000개 이상일 때)
- [ ] API 엔드포인트 추가

---

## 🆘 문제 해결

### Q1: "자연어DB를 어떻게 만드나요?"
**A:** 이미 만들어져 있습니다! PostgreSQL에 텍스트를 저장하는 모든 테이블이 자연어DB입니다.

### Q2: "VectorDB와 자연어DB 중 뭘 써야 하나요?"
**A:** 둘 다 사용하세요!
- 정확한 검색: 자연어DB
- 의미 기반 추천: VectorDB

### Q3: "검색이 너무 느려요"
**A:** 인덱스를 생성하세요:
```bash
docker exec -i interview_db psql -U admin -d interview_db < infra/postgres/create_indexes.sql
```

### Q4: "VectorDB 샘플 데이터가 없어요"
**A:** 다음 명령어로 삽입하세요:
```bash
docker exec -it interview_backend bash
cd /app/scripts
python populate_vectordb.py
```

---

## 🎉 결론

✅ **자연어DB**: 이미 구축됨! 바로 사용 가능
✅ **VectorDB**: 추가 설정 필요, 의미 기반 검색 지원

**권장 사항:**
1. 먼저 자연어DB로 기본 검색 기능 구현
2. 필요시 VectorDB 추가하여 추천 시스템 구축
3. 두 시스템을 결합한 하이브리드 검색 사용

**다음 단계:**
- [ ] 검색 인덱스 생성
- [ ] VectorDB 샘플 데이터 삽입
- [ ] API 엔드포인트 구현
- [ ] 프론트엔드 검색 UI 개발

궁금한 점이 있으시면 언제든지 물어보세요! 🚀
