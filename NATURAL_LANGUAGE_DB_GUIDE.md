# 🗣️ 자연어DB 구축 및 활용 가이드

## 📋 목차
1. [자연어DB란?](#자연어db란)
2. [현재 프로젝트의 자연어DB 구조](#현재-프로젝트의-자연어db-구조)
3. [자연어 검색 구현](#자연어-검색-구현)
4. [전문 검색(Full-Text Search) 설정](#전문-검색-설정)
5. [실전 활용 예시](#실전-활용-예시)
6. [성능 최적화](#성능-최적화)

---

## 자연어DB란?

**자연어DB**는 일반적인 관계형 데이터베이스에서 **자연어 텍스트**를 저장하고 검색하는 시스템입니다.

### VectorDB와의 차이점

| 구분 | 자연어DB | VectorDB |
|------|----------|----------|
| **저장 방식** | 텍스트 그대로 | 숫자 벡터 (임베딩) |
| **검색 방식** | 키워드 매칭, 패턴 매칭 | 의미적 유사도 |
| **검색 예시** | `LIKE '%Python%'` | 코사인 거리 계산 |
| **장점** | 정확한 매칭, 빠른 속도 | 의미 파악, 유연한 검색 |
| **단점** | 동의어/유사어 검색 어려움 | 계산 비용 높음 |

### 언제 사용하나요?

✅ **자연어DB 사용 케이스:**
- 사용자 이름, 이메일 검색
- 면접 기록, 대화 내용 조회
- 키워드 기반 필터링
- 정확한 텍스트 매칭

✅ **VectorDB 사용 케이스:**
- 유사한 질문 찾기
- 의미 기반 답변 평가
- 추천 시스템

---

## 현재 프로젝트의 자연어DB 구조

### 1. 데이터베이스 설정

```yaml
# docker-compose.yml
db:
  image: pgvector/pgvector:pg18
  environment:
    POSTGRES_USER: admin
    POSTGRES_PASSWORD: 1234
    POSTGRES_DB: interview_db
```

### 2. 자연어 텍스트를 저장하는 테이블

#### **Users 테이블** (사용자 정보)
```python
class User(SQLModel, table=True):
    id: int
    email: str              # 이메일 (자연어)
    username: str           # 사용자명 (자연어)
    full_name: str          # 전체 이름 (자연어)
    role: UserRole
```

**검색 예시:**
```sql
-- 이름으로 사용자 검색
SELECT * FROM users WHERE full_name ILIKE '%김철수%';

-- 이메일로 검색
SELECT * FROM users WHERE email = 'user@example.com';
```

#### **Interviews 테이블** (면접 세션)
```python
class Interview(SQLModel, table=True):
    id: int
    candidate_id: int
    position: str           # 지원 직무 (자연어)
    status: InterviewStatus
    emotion_summary: Dict   # 감정 분석 요약 (JSON)
```

**검색 예시:**
```sql
-- 특정 직무의 면접 조회
SELECT * FROM interviews WHERE position = 'Backend 개발자';

-- 완료된 면접만 조회
SELECT * FROM interviews WHERE status = 'completed';
```

#### **Transcripts 테이블** (대화 기록) ⭐ 핵심!
```python
class Transcript(SQLModel, table=True):
    id: int
    interview_id: int
    speaker: Speaker        # AI 또는 User
    text: str              # 대화 내용 (자연어) ⭐
    timestamp: datetime
    sentiment_score: float
    emotion: str
```

**검색 예시:**
```sql
-- 특정 면접의 모든 대화 조회
SELECT * FROM transcripts
WHERE interview_id = 1
ORDER BY timestamp;

-- 특정 키워드가 포함된 대화 검색
SELECT * FROM transcripts
WHERE text ILIKE '%Python%' OR text ILIKE '%FastAPI%';

-- 사용자 답변만 조회
SELECT * FROM transcripts
WHERE speaker = 'User' AND interview_id = 1;
```

#### **Questions 테이블** (질문 은행)
```python
class Question(SQLModel, table=True):
    id: int
    content: str           # 질문 내용 (자연어) ⭐
    category: QuestionCategory
    difficulty: QuestionDifficulty
    company: str           # 회사명 (자연어)
    position: str          # 직무 (자연어)
```

**검색 예시:**
```sql
-- 키워드로 질문 검색
SELECT * FROM questions WHERE content ILIKE '%데이터베이스%';

-- 회사별 질문 조회
SELECT * FROM questions WHERE company = '카카오';

-- 난이도별 필터링
SELECT * FROM questions
WHERE difficulty = 'hard' AND category = 'technical';
```

#### **EvaluationReports 테이블** (평가 리포트)
```python
class EvaluationReport(SQLModel, table=True):
    id: int
    interview_id: int
    summary_text: str      # 종합 평가 (자연어) ⭐
    details_json: Dict     # 상세 평가 (JSON)
```

---

## 자연어 검색 구현

### 1. 기본 키워드 검색 (LIKE, ILIKE)

```python
from sqlmodel import Session, select
from database import engine
from models import Transcript, Question

def search_transcripts_by_keyword(interview_id: int, keyword: str):
    """대화 기록에서 키워드 검색"""
    with Session(engine) as session:
        # ILIKE: 대소문자 구분 없이 검색
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id,
            Transcript.text.ilike(f"%{keyword}%")
        )
        results = session.exec(stmt).all()
        return results

# 사용 예시
transcripts = search_transcripts_by_keyword(1, "Python")
for t in transcripts:
    print(f"[{t.speaker}] {t.text}")
```

### 2. 다중 키워드 검색 (OR 조건)

```python
from sqlalchemy import or_

def search_questions_multi_keyword(keywords: list[str]):
    """여러 키워드로 질문 검색 (OR 조건)"""
    with Session(engine) as session:
        # 키워드 중 하나라도 포함되면 검색
        conditions = [Question.content.ilike(f"%{kw}%") for kw in keywords]
        stmt = select(Question).where(or_(*conditions))
        results = session.exec(stmt).all()
        return results

# 사용 예시
questions = search_questions_multi_keyword(["Python", "FastAPI", "Django"])
```

### 3. 정규식 검색 (고급)

```python
from sqlmodel import text

def search_with_regex(pattern: str):
    """정규식을 사용한 고급 검색"""
    with Session(engine) as session:
        # PostgreSQL의 정규식 연산자 ~*
        stmt = text(f"""
            SELECT * FROM questions
            WHERE content ~* :pattern
        """)
        results = session.exec(stmt, {"pattern": pattern}).all()
        return results

# 사용 예시
# "Python" 또는 "파이썬"이 포함된 질문 검색
questions = search_with_regex("Python|파이썬")
```

---

## 전문 검색(Full-Text Search) 설정

PostgreSQL의 **전문 검색(Full-Text Search)**을 사용하면 더 강력한 자연어 검색이 가능합니다.

### 1. 한국어 전문 검색 설정

```sql
-- PostgreSQL에 접속
docker exec -it interview_db psql -U admin -d interview_db

-- 1. 한국어 사전 확인
SELECT * FROM pg_ts_config WHERE cfgname = 'korean';

-- 2. 전문 검색 인덱스 생성 (Questions 테이블)
CREATE INDEX idx_questions_content_fts
ON questions
USING gin(to_tsvector('korean', content));

-- 3. 전문 검색 인덱스 생성 (Transcripts 테이블)
CREATE INDEX idx_transcripts_text_fts
ON transcripts
USING gin(to_tsvector('korean', text));
```

### 2. 전문 검색 쿼리

```python
from sqlmodel import text

def fulltext_search_questions(query: str, limit: int = 10):
    """전문 검색을 사용한 질문 검색"""
    with Session(engine) as session:
        stmt = text("""
            SELECT
                id,
                content,
                category,
                difficulty,
                ts_rank(to_tsvector('korean', content), query) AS rank
            FROM questions,
                 plainto_tsquery('korean', :query) query
            WHERE to_tsvector('korean', content) @@ query
            ORDER BY rank DESC
            LIMIT :limit
        """)

        results = session.exec(
            stmt,
            {"query": query, "limit": limit}
        ).all()

        return results

# 사용 예시
results = fulltext_search_questions("데이터베이스 최적화")
for r in results:
    print(f"[순위: {r[4]:.4f}] {r[1]}")
```

### 3. 전문 검색 + 필터링 결합

```python
def advanced_search(
    query: str,
    position: str = None,
    difficulty: str = None,
    limit: int = 10
):
    """전문 검색 + 필터링"""
    with Session(engine) as session:
        sql = """
            SELECT
                id, content, category, difficulty,
                ts_rank(to_tsvector('korean', content), plainto_tsquery('korean', :query)) AS rank
            FROM questions
            WHERE to_tsvector('korean', content) @@ plainto_tsquery('korean', :query)
        """

        params = {"query": query, "limit": limit}

        if position:
            sql += " AND position = :position"
            params["position"] = position

        if difficulty:
            sql += " AND difficulty = :difficulty"
            params["difficulty"] = difficulty

        sql += " ORDER BY rank DESC LIMIT :limit"

        results = session.exec(text(sql), params).all()
        return results

# 사용 예시
results = advanced_search(
    query="데이터베이스",
    position="Backend 개발자",
    difficulty="hard"
)
```

---

## 실전 활용 예시

### 1. 면접 대화 분석

```python
def analyze_interview_conversation(interview_id: int):
    """면접 대화 내용 분석"""
    with Session(engine) as session:
        # 모든 대화 조회
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id
        ).order_by(Transcript.timestamp)

        transcripts = session.exec(stmt).all()

        # 통계 계산
        total_words = sum(len(t.text.split()) for t in transcripts)
        user_responses = [t for t in transcripts if t.speaker == "User"]
        avg_response_length = sum(len(t.text.split()) for t in user_responses) / len(user_responses)

        # 키워드 빈도 분석
        from collections import Counter
        all_words = " ".join(t.text for t in user_responses).split()
        keyword_freq = Counter(all_words).most_common(10)

        return {
            "total_messages": len(transcripts),
            "total_words": total_words,
            "avg_response_length": avg_response_length,
            "top_keywords": keyword_freq
        }

# 사용 예시
analysis = analyze_interview_conversation(1)
print(f"총 대화: {analysis['total_messages']}개")
print(f"평균 답변 길이: {analysis['avg_response_length']:.1f}단어")
print(f"주요 키워드: {analysis['top_keywords']}")
```

### 2. 사용자 검색 (자동완성)

```python
def autocomplete_users(query: str, limit: int = 5):
    """사용자 이름 자동완성"""
    with Session(engine) as session:
        stmt = select(User).where(
            or_(
                User.username.ilike(f"{query}%"),
                User.full_name.ilike(f"%{query}%"),
                User.email.ilike(f"{query}%")
            )
        ).limit(limit)

        results = session.exec(stmt).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email
            }
            for u in results
        ]

# 사용 예시
suggestions = autocomplete_users("김")
# 결과: [{"username": "kim123", "full_name": "김철수", ...}, ...]
```

### 3. 질문 필터링 및 정렬

```python
def filter_questions(
    category: str = None,
    difficulty: str = None,
    company: str = None,
    position: str = None,
    keyword: str = None,
    sort_by: str = "created_at",
    order: str = "desc",
    limit: int = 20
):
    """다양한 조건으로 질문 필터링"""
    with Session(engine) as session:
        stmt = select(Question)

        # 필터 조건 추가
        conditions = []
        if category:
            conditions.append(Question.category == category)
        if difficulty:
            conditions.append(Question.difficulty == difficulty)
        if company:
            conditions.append(Question.company == company)
        if position:
            conditions.append(Question.position == position)
        if keyword:
            conditions.append(Question.content.ilike(f"%{keyword}%"))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 정렬
        if order == "desc":
            stmt = stmt.order_by(getattr(Question, sort_by).desc())
        else:
            stmt = stmt.order_by(getattr(Question, sort_by))

        stmt = stmt.limit(limit)

        results = session.exec(stmt).all()
        return results

# 사용 예시
questions = filter_questions(
    category="technical",
    difficulty="hard",
    position="Backend 개발자",
    keyword="데이터베이스",
    sort_by="usage_count",
    order="desc"
)
```

### 4. 대화 내용 하이라이트

```python
def highlight_keywords_in_transcript(interview_id: int, keywords: list[str]):
    """대화 내용에서 키워드 하이라이트"""
    with Session(engine) as session:
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id
        ).order_by(Transcript.timestamp)

        transcripts = session.exec(stmt).all()

        highlighted = []
        for t in transcripts:
            text = t.text
            for keyword in keywords:
                # 대소문자 구분 없이 하이라이트
                import re
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                text = pattern.sub(f"**{keyword}**", text)

            highlighted.append({
                "speaker": t.speaker,
                "text": text,
                "timestamp": t.timestamp,
                "emotion": t.emotion
            })

        return highlighted

# 사용 예시
highlighted = highlight_keywords_in_transcript(1, ["Python", "FastAPI", "데이터베이스"])
```

---

## 성능 최적화

### 1. 인덱스 생성

```sql
-- 자주 검색하는 컬럼에 인덱스 생성
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_interviews_position ON interviews(position);
CREATE INDEX idx_interviews_status ON interviews(status);
CREATE INDEX idx_questions_category ON questions(category);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_position ON questions(position);
CREATE INDEX idx_transcripts_interview_id ON transcripts(interview_id);

-- 복합 인덱스 (자주 함께 사용되는 컬럼)
CREATE INDEX idx_questions_pos_cat_diff
ON questions(position, category, difficulty);

-- 전문 검색 인덱스 (GIN)
CREATE INDEX idx_questions_content_gin
ON questions USING gin(to_tsvector('korean', content));

CREATE INDEX idx_transcripts_text_gin
ON transcripts USING gin(to_tsvector('korean', text));
```

### 2. 쿼리 최적화

```python
# ❌ 비효율적: N+1 쿼리 문제
def get_interviews_with_transcripts_bad(user_id: int):
    with Session(engine) as session:
        interviews = session.exec(
            select(Interview).where(Interview.candidate_id == user_id)
        ).all()

        for interview in interviews:
            # 각 면접마다 별도 쿼리 실행 (N+1 문제!)
            transcripts = session.exec(
                select(Transcript).where(Transcript.interview_id == interview.id)
            ).all()
            interview.transcripts = transcripts

        return interviews

# ✅ 효율적: JOIN 사용
def get_interviews_with_transcripts_good(user_id: int):
    with Session(engine) as session:
        # SQLModel의 Relationship을 활용한 자동 JOIN
        stmt = select(Interview).where(
            Interview.candidate_id == user_id
        )
        interviews = session.exec(stmt).all()

        # Relationship이 정의되어 있으면 자동으로 로드됨
        return interviews
```

### 3. 페이지네이션

```python
def get_questions_paginated(page: int = 1, page_size: int = 20):
    """페이지네이션을 사용한 질문 조회"""
    with Session(engine) as session:
        offset = (page - 1) * page_size

        # 전체 개수 조회
        total_count = session.exec(
            select(func.count(Question.id))
        ).one()

        # 페이지 데이터 조회
        stmt = select(Question).offset(offset).limit(page_size)
        questions = session.exec(stmt).all()

        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "data": questions
        }
```

### 4. 캐싱 전략

```python
from functools import lru_cache
from datetime import datetime, timedelta

# 메모리 캐싱 (자주 조회되는 데이터)
@lru_cache(maxsize=100)
def get_question_by_id_cached(question_id: int):
    """질문 조회 (캐싱)"""
    with Session(engine) as session:
        return session.get(Question, question_id)

# Redis 캐싱 (분산 환경)
import redis
import json

redis_client = redis.from_url("redis://redis:6379/0")

def get_interview_cached(interview_id: int):
    """면접 조회 (Redis 캐싱)"""
    cache_key = f"interview:{interview_id}"

    # 캐시 확인
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # DB 조회
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)

        # 캐시 저장 (5분 TTL)
        redis_client.setex(
            cache_key,
            300,
            json.dumps(interview.dict())
        )

        return interview
```

---

## 실전 API 엔드포인트 예시

```python
# backend-core/main.py

from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI()

@app.get("/api/search/questions")
async def search_questions(
    keyword: str = Query(..., description="검색 키워드"),
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    position: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """질문 검색 API"""
    results = filter_questions(
        category=category,
        difficulty=difficulty,
        position=position,
        keyword=keyword,
        limit=page_size
    )

    return {
        "keyword": keyword,
        "results": [
            {
                "id": q.id,
                "content": q.content,
                "category": q.category,
                "difficulty": q.difficulty
            }
            for q in results
        ]
    }

@app.get("/api/interviews/{interview_id}/transcripts")
async def get_interview_transcripts(
    interview_id: int,
    keyword: Optional[str] = None
):
    """면접 대화 기록 조회"""
    if keyword:
        transcripts = search_transcripts_by_keyword(interview_id, keyword)
    else:
        with Session(engine) as session:
            stmt = select(Transcript).where(
                Transcript.interview_id == interview_id
            ).order_by(Transcript.timestamp)
            transcripts = session.exec(stmt).all()

    return {
        "interview_id": interview_id,
        "total": len(transcripts),
        "transcripts": [
            {
                "speaker": t.speaker,
                "text": t.text,
                "timestamp": t.timestamp,
                "emotion": t.emotion
            }
            for t in transcripts
        ]
    }

@app.get("/api/users/search")
async def search_users(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20)
):
    """사용자 검색 (자동완성)"""
    results = autocomplete_users(query, limit)
    return {"suggestions": results}
```

---

## 다음 단계

✅ **자연어DB 구축 완료!**

이제 다음을 시도해보세요:
1. ✅ 전문 검색 인덱스 생성
2. ✅ API 엔드포인트 추가
3. ✅ 프론트엔드에서 검색 기능 구현
4. ✅ 캐싱 전략 적용

---

## 참고 자료

- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [SQLModel 공식 문서](https://sqlmodel.tiangolo.com/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
