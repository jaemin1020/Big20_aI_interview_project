---
description: VectorDB와 자연어DB 구축 완벽 가이드
---

# 🗄️ VectorDB와 자연어DB 구축 가이드

## 📋 목차
1. [개요](#개요)
2. [VectorDB란?](#vectordb란)
3. [현재 프로젝트 구조](#현재-프로젝트-구조)
4. [구축 단계](#구축-단계)
5. [임베딩 생성 방법](#임베딩-생성-방법)
6. [벡터 검색 구현](#벡터-검색-구현)
7. [성능 최적화](#성능-최적화)

---

## 개요

이 프로젝트는 **PostgreSQL + pgvector**를 사용하여 관계형 DB와 VectorDB를 통합 운영합니다.

### 주요 특징
- ✅ 하나의 DB에서 관계형 데이터와 벡터 데이터 모두 관리
- ✅ 768차원 임베딩 벡터 저장 (HuggingFace 모델 사용)
- ✅ 코사인 유사도 기반 검색
- ✅ 질문-답변 매칭 및 유사 질문 추천

---

## VectorDB란?

### 1. 정의
**VectorDB**는 텍스트, 이미지 등을 고차원 벡터로 변환하여 저장하고, 유사도 검색을 수행하는 데이터베이스입니다.

### 2. 작동 원리
```
텍스트 입력 → 임베딩 모델 → 벡터(숫자 배열) → DB 저장 → 유사도 검색
```

**예시:**
```python
"Python 개발자 면접 질문" → [0.234, -0.567, 0.891, ...] (768개 숫자)
"파이썬 백엔드 질문"     → [0.221, -0.543, 0.876, ...] (768개 숫자)
# 두 벡터의 코사인 유사도 = 0.95 (매우 유사!)
```

### 3. 자연어DB vs VectorDB

| 구분 | 자연어DB (관계형) | VectorDB |
|------|------------------|----------|
| 저장 형식 | 텍스트 그대로 | 숫자 벡터 |
| 검색 방식 | 키워드 매칭 (LIKE, ILIKE) | 의미 기반 유사도 |
| 예시 쿼리 | `WHERE content LIKE '%Python%'` | `ORDER BY embedding <=> query_vector` |
| 장점 | 정확한 매칭 | 의미적 유사성 파악 |

**우리 프로젝트는 둘 다 사용합니다!**
- 자연어DB: 사용자 정보, 면접 기록, 대화 내용 저장
- VectorDB: 질문 유사도 검색, 우수 답변 매칭

---

## 현재 프로젝트 구조

### 1. 데이터베이스 설정
```yaml
# docker-compose.yml
db:
  image: pgvector/pgvector:pg18  # PostgreSQL + pgvector 확장
  environment:
    POSTGRES_USER: admin
    POSTGRES_PASSWORD: 1234
    POSTGRES_DB: interview_db
```

### 2. 벡터 테이블 구조

#### **Question 테이블** (질문 은행)
```python
class Question(SQLModel, table=True):
    id: int
    content: str                    # 자연어 질문 텍스트
    category: QuestionCategory      # technical, behavioral 등
    difficulty: QuestionDifficulty  # easy, medium, hard

    # 🔥 벡터 컬럼 (768차원)
    embedding: List[float] = Field(sa_column=Column(Vector(768)))

    # 계층적 분류 (필터링용)
    company: str   # "삼성전자", "카카오"
    industry: str  # "IT", "금융"
    position: str  # "Backend 개발자"
```

#### **AnswerBank 테이블** (우수 답변 은행)
```python
class AnswerBank(SQLModel, table=True):
    id: int
    question_id: int
    answer_text: str                # 자연어 답변 텍스트

    # 🔥 벡터 컬럼 (768차원)
    embedding: List[float] = Field(sa_column=Column(Vector(768)))

    score: float                    # 답변 점수 (0-100)
    evaluator_feedback: str         # 평가자 피드백
```

---

## 구축 단계

### Step 1: pgvector 확장 활성화 ✅

**이미 완료됨!** `infra/postgres/init.sql`에 설정되어 있습니다:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Docker Compose로 DB를 시작하면 자동으로 활성화됩니다.

### Step 2: 임베딩 모델 준비

#### 추천 모델 (HuggingFace)

1. **sentence-transformers/all-MiniLM-L6-v2** (권장)
   - 차원: 384
   - 속도: 빠름
   - 용도: 일반적인 문장 임베딩

2. **jhgan/ko-sroberta-multitask** (한국어 특화)
   - 차원: 768 ⭐ (현재 프로젝트 설정)
   - 속도: 중간
   - 용도: 한국어 면접 질문/답변

3. **intfloat/multilingual-e5-large**
   - 차원: 1024
   - 속도: 느림
   - 용도: 고품질 다국어 지원

#### 모델 설치 예시
```python
from sentence_transformers import SentenceTransformer

# 한국어 모델 다운로드
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 임베딩 생성
text = "Python FastAPI 경험에 대해 설명해주세요"
embedding = model.encode(text)  # [768개 숫자]
```

### Step 3: 데이터 삽입 스크립트 작성

아래 스크립트를 `backend-core/scripts/populate_vectordb.py`로 저장하세요:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select
from database import engine
from models import Question, AnswerBank, QuestionCategory, QuestionDifficulty

# 임베딩 모델 로드
print("🔄 임베딩 모델 로딩 중...")
model = SentenceTransformer('jhgan/ko-sroberta-multitask')
print("✅ 모델 로드 완료!")

def add_question_with_embedding(
    session: Session,
    content: str,
    category: QuestionCategory,
    difficulty: QuestionDifficulty,
    company: str = None,
    industry: str = None,
    position: str = None,
    rubric: dict = None
):
    """질문과 임베딩을 함께 저장"""

    # 1. 임베딩 생성
    embedding = model.encode(content).tolist()

    # 2. Question 객체 생성
    question = Question(
        content=content,
        category=category,
        difficulty=difficulty,
        embedding=embedding,
        company=company,
        industry=industry,
        position=position,
        rubric_json=rubric or {}
    )

    # 3. DB 저장
    session.add(question)
    session.commit()
    session.refresh(question)

    print(f"✅ 질문 저장 완료: {content[:50]}... (ID: {question.id})")
    return question

def add_answer_with_embedding(
    session: Session,
    question_id: int,
    answer_text: str,
    score: float,
    feedback: str = None
):
    """답변과 임베딩을 함께 저장"""

    # 1. 임베딩 생성
    embedding = model.encode(answer_text).tolist()

    # 2. AnswerBank 객체 생성
    answer = AnswerBank(
        question_id=question_id,
        answer_text=answer_text,
        embedding=embedding,
        score=score,
        evaluator_feedback=feedback
    )

    # 3. DB 저장
    session.add(answer)
    session.commit()
    session.refresh(answer)

    print(f"✅ 답변 저장 완료: {answer_text[:50]}... (점수: {score})")
    return answer

def populate_sample_data():
    """샘플 데이터 삽입"""

    with Session(engine) as session:
        # 예시 질문 1
        q1 = add_question_with_embedding(
            session,
            content="Python에서 GIL(Global Interpreter Lock)이 무엇인지 설명하고, 멀티스레딩 성능에 미치는 영향을 설명해주세요.",
            category=QuestionCategory.TECHNICAL,
            difficulty=QuestionDifficulty.HARD,
            company="카카오",
            industry="IT",
            position="Backend 개발자",
            rubric={
                "정확성": 30,
                "깊이": 30,
                "실무 적용": 40
            }
        )

        # 예시 답변 1
        add_answer_with_embedding(
            session,
            question_id=q1.id,
            answer_text="""
            GIL은 Python 인터프리터가 한 번에 하나의 스레드만 Python 바이트코드를 실행하도록
            제한하는 뮤텍스입니다. 이는 메모리 관리의 안전성을 보장하지만, CPU-bound 작업에서는
            멀티스레딩의 이점을 제한합니다. 실무에서는 multiprocessing 모듈이나 asyncio를
            사용하여 이를 우회합니다.
            """,
            score=95.0,
            feedback="GIL의 개념과 영향, 해결 방법을 모두 정확히 설명함"
        )

        # 예시 질문 2
        q2 = add_question_with_embedding(
            session,
            content="팀에서 의견 충돌이 발생했을 때 어떻게 해결하셨나요?",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=QuestionDifficulty.MEDIUM,
            industry="IT",
            position="Backend 개발자"
        )

        # 예시 답변 2
        add_answer_with_embedding(
            session,
            question_id=q2.id,
            answer_text="""
            이전 프로젝트에서 API 설계 방식에 대해 팀원과 의견이 달랐습니다.
            저는 각자의 방식을 프로토타입으로 구현하여 성능과 유지보수성을 비교했고,
            데이터를 기반으로 논의한 결과 합의점을 찾을 수 있었습니다.
            """,
            score=88.0,
            feedback="구체적인 상황과 해결 과정을 STAR 기법으로 잘 설명함"
        )

        print("\n🎉 샘플 데이터 삽입 완료!")

if __name__ == "__main__":
    populate_sample_data()
```

### Step 4: 벡터 인덱스 생성 (성능 최적화)

데이터가 1000개 이상일 때 인덱스를 생성하세요:

```sql
-- IVFFlat 인덱스 (빠른 근사 검색)
CREATE INDEX idx_questions_embedding
ON questions
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_answer_bank_embedding
ON answer_bank
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**인덱스 생성 시점:**
- 데이터 < 1000개: 인덱스 불필요 (순차 검색이 더 빠름)
- 데이터 > 1000개: IVFFlat 인덱스 생성
- 데이터 > 10000개: HNSW 인덱스 고려

---

## 임베딩 생성 방법

### 방법 1: Python에서 직접 생성 (권장)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 단일 텍스트
embedding = model.encode("질문 텍스트")

# 배치 처리 (효율적)
texts = ["질문1", "질문2", "질문3"]
embeddings = model.encode(texts, batch_size=32)
```

### 방법 2: HuggingFace API 사용

```python
import requests

API_URL = "https://api-inference.huggingface.co/models/jhgan/ko-sroberta-multitask"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

def get_embedding(text):
    response = requests.post(API_URL, headers=headers, json={"inputs": text})
    return response.json()
```

### 방법 3: OpenAI Embeddings (유료)

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

response = client.embeddings.create(
    model="text-embedding-3-small",  # 1536차원
    input="질문 텍스트"
)

embedding = response.data[0].embedding
```

---

## 벡터 검색 구현

### 1. 유사 질문 검색

```python
from sqlmodel import Session, select, text
from database import engine
from models import Question

def find_similar_questions(query_text: str, top_k: int = 5):
    """입력 텍스트와 유사한 질문 검색"""

    # 1. 쿼리 임베딩 생성
    query_embedding = model.encode(query_text).tolist()

    # 2. 벡터 유사도 검색 (코사인 거리)
    with Session(engine) as session:
        # pgvector의 <=> 연산자: 코사인 거리 (작을수록 유사)
        stmt = select(
            Question,
            text(f"embedding <=> '{query_embedding}' AS distance")
        ).order_by(text("distance")).limit(top_k)

        results = session.exec(stmt).all()

        return [
            {
                "question": result[0],
                "similarity": 1 - result[1]  # 거리 → 유사도 변환
            }
            for result in results
        ]

# 사용 예시
similar = find_similar_questions("파이썬 멀티스레딩에 대해 설명해주세요")
for item in similar:
    print(f"유사도: {item['similarity']:.2f} - {item['question'].content}")
```

### 2. 필터링과 벡터 검색 결합

```python
def find_questions_by_position(
    query_text: str,
    position: str,
    difficulty: str = None,
    top_k: int = 5
):
    """직무별 + 난이도별 + 유사도 검색"""

    query_embedding = model.encode(query_text).tolist()

    with Session(engine) as session:
        stmt = select(
            Question,
            text(f"embedding <=> '{query_embedding}' AS distance")
        ).where(
            Question.position == position
        )

        if difficulty:
            stmt = stmt.where(Question.difficulty == difficulty)

        stmt = stmt.order_by(text("distance")).limit(top_k)

        return session.exec(stmt).all()

# 사용 예시
results = find_questions_by_position(
    query_text="데이터베이스 최적화",
    position="Backend 개발자",
    difficulty="hard"
)
```

### 3. 답변 평가 (우수 답변과 비교)

```python
def evaluate_answer(question_id: int, user_answer: str):
    """사용자 답변을 우수 답변과 비교"""

    # 1. 사용자 답변 임베딩
    user_embedding = model.encode(user_answer).tolist()

    # 2. 해당 질문의 우수 답변들 가져오기
    with Session(engine) as session:
        stmt = select(
            AnswerBank,
            text(f"embedding <=> '{user_embedding}' AS distance")
        ).where(
            AnswerBank.question_id == question_id
        ).order_by(text("distance")).limit(3)

        similar_answers = session.exec(stmt).all()

        if not similar_answers:
            return {"score": 0, "feedback": "참고할 답변이 없습니다."}

        # 3. 가장 유사한 답변 기준으로 점수 계산
        best_match = similar_answers[0]
        similarity = 1 - best_match[1]

        return {
            "score": similarity * best_match[0].score,
            "reference_answer": best_match[0].answer_text,
            "reference_score": best_match[0].score,
            "similarity": similarity,
            "feedback": best_match[0].evaluator_feedback
        }
```

---

## 성능 최적화

### 1. 인덱스 전략

```sql
-- 벡터 인덱스 (데이터 1000개 이상일 때)
CREATE INDEX idx_questions_embedding
ON questions
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 복합 인덱스 (필터링 + 검색)
CREATE INDEX idx_questions_position_category
ON questions (position, category);
```

### 2. 배치 임베딩 생성

```python
# ❌ 느림: 하나씩 처리
for text in texts:
    embedding = model.encode(text)
    save_to_db(embedding)

# ✅ 빠름: 배치 처리
embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
for text, embedding in zip(texts, embeddings):
    save_to_db(embedding)
```

### 3. 캐싱 전략

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(text: str):
    """자주 사용되는 텍스트는 캐싱"""
    return model.encode(text).tolist()
```

### 4. 근사 검색 vs 정확 검색

```python
# 정확 검색 (느림, 데이터 < 1000개)
SELECT * FROM questions
ORDER BY embedding <=> query_vector
LIMIT 10;

# 근사 검색 (빠름, 인덱스 사용)
SET ivfflat.probes = 10;  -- 정확도 조절 (1-lists)
SELECT * FROM questions
ORDER BY embedding <=> query_vector
LIMIT 10;
```

---

## 실전 활용 예시

### 1. 면접 질문 추천 시스템

```python
def recommend_questions(
    user_id: int,
    position: str,
    num_questions: int = 5
):
    """사용자 이력서 기반 질문 추천"""

    # 1. 사용자 이력서/경력 가져오기
    user_profile = get_user_profile(user_id)

    # 2. 프로필을 텍스트로 변환
    profile_text = f"{user_profile.skills} {user_profile.experience}"

    # 3. 유사 질문 검색
    questions = find_questions_by_position(
        query_text=profile_text,
        position=position,
        top_k=num_questions
    )

    return questions
```

### 2. 실시간 답변 피드백

```python
async def provide_realtime_feedback(
    interview_id: int,
    question_id: int,
    user_answer: str
):
    """실시간 답변 평가"""

    # 1. 답변 평가
    evaluation = evaluate_answer(question_id, user_answer)

    # 2. 피드백 생성
    if evaluation["similarity"] > 0.8:
        feedback = "✅ 우수한 답변입니다!"
    elif evaluation["similarity"] > 0.6:
        feedback = "⚠️ 좋은 답변이지만 개선 여지가 있습니다."
    else:
        feedback = "❌ 답변을 보완해주세요."

    # 3. 참고 답변 제공
    return {
        "feedback": feedback,
        "score": evaluation["score"],
        "reference": evaluation["reference_answer"]
    }
```

---

## 다음 단계

1. ✅ `backend-core/scripts/populate_vectordb.py` 스크립트 작성
2. ✅ 임베딩 모델 다운로드 및 테스트
3. ✅ 샘플 데이터 삽입
4. ✅ 벡터 검색 API 엔드포인트 추가
5. ✅ 프론트엔드에서 유사 질문 추천 기능 구현

---

## 참고 자료

- [pgvector 공식 문서](https://github.com/pgvector/pgvector)
- [Sentence Transformers](https://www.sbert.net/)
- [HuggingFace 한국어 모델](https://huggingface.co/jhgan/ko-sroberta-multitask)
