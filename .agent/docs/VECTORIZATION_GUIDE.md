# 📊 벡터화 시스템 구현 완료 가이드

## ✅ 추가된 기능

### 1. Question 테이블 벡터화
- **embedding 필드 추가** (768차원)
- 질문 중복 감지 및 유사 질문 검색 가능

### 2. 벡터 생성 유틸리티
- **파일**: `ai-worker/utils/vector_utils.py`
- **모델**: `jhgan/ko-sroberta-multitask` (한국어 특화)
- **차원**: 768 (질문/답변 공통)

### 3. 우수 답변 자동 수집
- **파일**: `ai-worker/tasks/answer_collector.py`
- **기준**: 평가 점수 85점 이상
- **저장**: AnswerBank 테이블 (벡터 포함)

---

## 🚀 사용 방법

### A. 기존 질문 벡터화 (마이그레이션)

```python
# Celery 태스크 실행
from celery import Celery
app = Celery('tasks', broker='redis://redis:6379/0')

# 100개씩 배치 처리
result = app.send_task('tasks.answer_collector.vectorize_existing_questions', args=[100])
```

또는 Python 스크립트:
```python
from ai-worker.tasks.answer_collector import vectorize_existing_questions

# 동기 실행
result = vectorize_existing_questions(batch_size=100)
print(result)  # {"status": "success", "count": 100}
```

---

### B. 우수 답변 자동 수집 (평가 후 트리거)

`evaluator.py`에서 평가 완료 후 자동 호출:

```python
# evaluator.py 수정 예시
@shared_task(name="tasks.evaluator.analyze_answer")
def analyze_answer(transcript_id, question, answer, rubric):
    # ... 평가 로직 ...
    
    evaluation_score = (tech_score + comm_score) * 10  # 0-100 변환
    
    # 우수 답변 수집 태스크 발행
    if evaluation_score >= 85.0:
        celery_app.send_task(
            "tasks.answer_collector.collect_excellent_answer",
            args=[transcript_id, evaluation_score]
        )
    
    return result
```

---

### C. 벡터 유사도 검색 (평가 시 활용)

```python
from sqlmodel import Session, select, func
from db import engine
from models import AnswerBank
from utils.vector_utils import generate_answer_embedding

def search_similar_answers(user_answer: str, question_id: int, top_k: int = 3):
    """유사한 우수 답변 검색"""
    
    # 1. 사용자 답변 벡터화
    user_embedding = generate_answer_embedding(user_answer)
    
    # 2. pgvector 코사인 유사도 검색
    with Session(engine) as session:
        stmt = select(
            AnswerBank,
            func.cosine_distance(AnswerBank.embedding, user_embedding).label("distance")
        ).where(
            AnswerBank.question_id == question_id,
            AnswerBank.score >= 80.0
        ).order_by("distance").limit(top_k)
        
        results = session.exec(stmt).all()
        
        return [
            {
                "text": answer.answer_text,
                "score": answer.score,
                "similarity": 1 - distance  # 거리 -> 유사도
            }
            for answer, distance in results
        ]

# 사용 예시
similar = search_similar_answers(
    user_answer="Docker를 사용해봤습니다",
    question_id=5
)
# 결과: [{"text": "Docker를 활용하여...", "score": 95, "similarity": 0.82}, ...]
```

---

## 📊 DB 마이그레이션

### 1. pgvector 인덱스 생성 (1000개 이상 데이터 축적 후)

```sql
-- Question 테이블 벡터 인덱스
CREATE INDEX question_embedding_idx 
ON questions 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- AnswerBank 테이블 벡터 인덱스
CREATE INDEX answer_bank_embedding_idx 
ON answer_bank 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### 2. 기존 데이터 벡터화

```bash
# Docker 컨테이너 내부에서
docker exec -it interview_worker python -c "
from tasks.answer_collector import vectorize_existing_questions
result = vectorize_existing_questions(batch_size=500)
print(result)
"
```

---

## ⚠️ 주의사항

### 1. 메모리 사용량
- Sentence Transformer 모델: ~500MB
- 벡터 저장: 질문 1000개 = 약 3MB (768차원 * 4바이트 * 1000)

### 2. 성능 최적화
- **배치 처리**: 여러 텍스트를 한 번에 벡터화 (`encode_batch`)
- **캐싱**: 자주 사용되는 질문/답변은 Redis에 벡터 캐싱
- **인덱스**: 1000개 이상 데이터 축적 후 IVFFlat 인덱스 생성

### 3. 차원 수 일치
- Question: 768차원
- AnswerBank: 1536차원 (현재 설정)
- **권장**: 일관성을 위해 AnswerBank도 768차원으로 변경

```python
# backend-core/models.py 수정
class AnswerBank(SQLModel, table=True):
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(768))  # 1536 -> 768로 변경
    )
```

---

## 🎯 다음 단계

1. ✅ 컨테이너 재빌드
   ```bash
   docker-compose build --no-cache ai-worker
   docker-compose up -d ai-worker
   ```

2. ✅ 기존 질문 벡터화 실행
   ```python
   vectorize_existing_questions(batch_size=100)
   ```

3. ✅ 평가 로직에 우수 답변 수집 연동
   - `evaluator.py`에서 85점 이상 시 `collect_excellent_answer` 호출

4. ✅ 벡터 검색 기반 평가 강화
   - 유사 우수 답변과 비교하여 피드백 생성

---

**작성일**: 2026-01-27  
**버전**: v3.0 (벡터화 시스템)
