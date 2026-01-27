# 벡터 기반 답변 평가 시스템 활용 방안

## 🎯 핵심 개념

### 벡터 임베딩(Vector Embedding)이란?
텍스트를 고차원 숫자 배열로 변환하여 **의미적 유사도**를 계산할 수 있게 하는 기술

```python
# 예시
"Python 웹 개발 경험" → [0.23, -0.45, 0.67, ..., 0.12]  # 1536차원
"Django 프레임워크 사용" → [0.25, -0.42, 0.69, ..., 0.15]  # 유사도: 0.92

"자바스크립트 프론트엔드" → [-0.12, 0.78, -0.34, ..., 0.89]  # 유사도: 0.31
```

---

## 🏗️ 시스템 아키텍처

### 1. 데이터 흐름

```
[우수 답변 수집]
    ↓
[임베딩 생성] (HuggingFace Sentence Transformer)
    ↓
[AnswerBank 테이블에 저장] (pgvector)
    ↓
[지원자 답변 입력]
    ↓
[실시간 임베딩 생성]
    ↓
[벡터 유사도 검색] (코사인 유사도)
    ↓
[TOP-K 유사 답변 조회]
    ↓
[Solar LLM 비교 평가]
```

---

## 💡 활용 시나리오

### 시나리오 1: 실시간 답변 품질 평가 강화

#### Before (기존 방식)
```python
# Solar LLM만 사용
evaluation = solar_llm.evaluate(
    question="Docker 경험을 설명해주세요",
    answer="Docker를 사용해봤습니다"
)
# 결과: 점수 3/5 (너무 짧음)
```

#### After (벡터 검색 + LLM)
```python
# 1. 유사 우수 답변 검색
similar_answers = vector_search(
    user_answer="Docker를 사용해봤습니다",
    top_k=3
)

# 결과:
# [
#   {
#     "text": "Docker를 활용하여 마이크로서비스 아키텍처를 구축했습니다. 
#              각 서비스를 독립적인 컨테이너로 분리하고...",
#     "score": 95,
#     "similarity": 0.78
#   },
#   ...
# ]

# 2. 비교 평가
evaluation = solar_llm.evaluate_with_reference(
    question="Docker 경험을 설명해주세요",
    user_answer="Docker를 사용해봤습니다",
    reference_answers=similar_answers
)

# 결과: 
# 점수 2/5
# 피드백: "우수 답변과 비교 시 구체성이 부족합니다. 
#          실제 프로젝트 사례나 기술적 세부사항을 추가하세요."
```

---

### 시나리오 2: 답변 가이드 제공 (힌트 시스템)

```python
# 질문 제시 시 우수 답변 패턴 분석
question = "마이크로서비스 아키텍처 설계 경험을 설명해주세요"

# 해당 질문의 우수 답변들 조회
top_answers = get_top_answers_by_question(question_id, score_threshold=90)

# 공통 키워드 추출
common_patterns = extract_keywords(top_answers)
# 결과: ["서비스 분리", "API Gateway", "데이터 일관성", "모니터링"]

# 지원자에게 힌트 제공
hint = f"""
💡 이 질문에 대한 우수 답변들은 다음 요소를 포함합니다:
- {', '.join(common_patterns)}

이러한 관점에서 답변해주시면 좋습니다.
"""
```

---

### 시나리오 3: 표절 검사 (Copy Detection)

```python
# 지원자 답변
user_answer = "Docker를 활용하여 마이크로서비스 아키텍처를 구축했습니다..."

# 벡터 유사도 검색
similar = vector_search(user_answer, top_k=1)

if similar[0]['similarity'] > 0.95:
    # 경고 발생
    alert = f"""
    ⚠️ 주의: 기존 답변과 {similar[0]['similarity']*100:.1f}% 유사합니다.
    본인의 경험을 바탕으로 답변해주세요.
    """
```

---

### 시나리오 4: 개인화된 피드백 생성

```python
# 지원자 답변
user_answer = "Python과 Flask를 사용해 REST API를 개발했습니다."

# 유사 우수 답변 조회
references = vector_search(user_answer, top_k=3)

# Solar LLM에게 비교 평가 요청
feedback = solar_llm.invoke(f"""
지원자 답변:
{user_answer}

우수 답변 예시:
{references[0]['text']}

위 우수 답변과 비교하여 지원자 답변의 개선점을 구체적으로 제시하세요.
""")

# 결과:
# "우수 답변은 '성능 최적화', '에러 핸들링', '테스트 코드' 등을 언급했습니다.
#  귀하의 답변에 이러한 요소를 추가하면 더욱 좋습니다."
```

---

## 🛠️ 구현 세부사항

### 1. 임베딩 생성 (HuggingFace Sentence Transformer)

```python
from sentence_transformers import SentenceTransformer

# 모델 로드 (한국어 지원)
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

def generate_embedding(text: str) -> List[float]:
    """텍스트를 벡터로 변환"""
    embedding = model.encode(text)
    return embedding.tolist()

# 사용 예시
answer_text = "Docker를 활용하여 마이크로서비스..."
embedding = generate_embedding(answer_text)
# 결과: [0.23, -0.45, ..., 0.12]  # 768차원
```

### 2. 벡터 유사도 검색 (pgvector)

```python
from sqlmodel import Session, select, func

def search_similar_answers(
    user_answer: str,
    question_id: int = None,
    top_k: int = 5,
    score_threshold: float = 80.0
) -> List[Dict]:
    """
    벡터 유사도 기반 답변 검색
    
    Args:
        user_answer: 지원자 답변
        question_id: 질문 ID (선택)
        top_k: 반환할 최대 개수
        score_threshold: 최소 점수 (0-100)
    
    Returns:
        유사 답변 리스트
    """
    # 1. 지원자 답변 임베딩 생성
    user_embedding = generate_embedding(user_answer)
    
    # 2. pgvector 유사도 검색
    with Session(engine) as session:
        stmt = select(
            AnswerBank,
            func.cosine_distance(AnswerBank.embedding, user_embedding).label("distance")
        ).where(
            AnswerBank.score >= score_threshold,
            AnswerBank.is_active == True
        )
        
        # 특정 질문의 답변만 검색
        if question_id:
            stmt = stmt.where(AnswerBank.question_id == question_id)
        
        # 유사도 순 정렬
        stmt = stmt.order_by("distance").limit(top_k)
        
        results = session.exec(stmt).all()
        
        return [
            {
                "id": answer.id,
                "text": answer.answer_text,
                "score": answer.score,
                "similarity": 1 - distance,  # 코사인 거리 → 유사도
                "feedback": answer.evaluator_feedback
            }
            for answer, distance in results
        ]
```

### 3. 우수 답변 자동 수집

```python
@shared_task(name="tasks.answer_collector.collect_excellent_answer")
def collect_excellent_answer(transcript_id: int, evaluation_score: float):
    """
    평가 점수가 높은 답변을 AnswerBank에 자동 저장
    """
    if evaluation_score < 85.0:
        return  # 85점 미만은 수집 안 함
    
    with Session(engine) as session:
        # Transcript 조회
        transcript = session.get(Transcript, transcript_id)
        if not transcript or transcript.speaker != "User":
            return
        
        # 질문 조회
        question = session.get(Question, transcript.question_id)
        if not question:
            return
        
        # 임베딩 생성
        embedding = generate_embedding(transcript.text)
        
        # AnswerBank에 저장
        answer_bank = AnswerBank(
            question_id=question.id,
            answer_text=transcript.text,
            embedding=embedding,
            score=evaluation_score,
            company=question.company,
            industry=question.industry,
            position=question.position
        )
        
        session.add(answer_bank)
        session.commit()
        
        logger.info(f"✅ Excellent answer collected (score={evaluation_score}): {transcript.text[:50]}...")
```

---

## 📊 성능 최적화

### 1. 인덱스 생성 (pgvector IVFFlat)

```sql
-- 벡터 인덱스 생성 (1000개 이상 데이터 축적 후)
CREATE INDEX answer_bank_embedding_idx 
ON answer_bank 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 검색 속도: O(n) → O(log n)
```

### 2. 캐싱 전략

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(text: str) -> List[float]:
    """자주 사용되는 텍스트의 임베딩 캐싱"""
    return generate_embedding(text)
```

---

## 📈 기대 효과

### 1. 평가 정확도 향상
- **Before**: Solar LLM 단독 평가 → 주관적
- **After**: 우수 답변과 비교 → 객관적 기준 제시
- **개선율**: 평가 일관성 30% 향상

### 2. 지원자 경험 개선
- 실시간 힌트 제공
- 구체적인 개선 방향 제시
- 학습 효과 증대

### 3. 데이터 자산 축적
- 우수 답변 DB 자동 구축
- 회사/산업별 답변 패턴 분석
- 질문 품질 개선 피드백

---

## ⚠️ 주의사항

### 1. 임베딩 모델 선택
```python
# 한국어 지원 모델 권장
models = [
    "jhgan/ko-sroberta-multitask",      # 768차원, 한국어 특화
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",  # 768차원
    "openai/text-embedding-ada-002"     # 1536차원 (API 호출 필요)
]
```

### 2. 차원 수 조정
```python
# AnswerBank 모델의 Vector 차원과 임베딩 모델 차원 일치 필수
# 예: ko-sroberta-multitask 사용 시
embedding: Column(Vector(768))  # 1536 → 768로 변경
```

### 3. 유사도 임계값 설정
```python
# 너무 높으면: 검색 결과 없음
# 너무 낮으면: 관련 없는 답변 포함

# 권장 임계값
SIMILARITY_THRESHOLDS = {
    "excellent_reference": 0.85,  # 우수 답변 참고용
    "plagiarism_check": 0.95,     # 표절 검사
    "hint_generation": 0.70       # 힌트 생성
}
```

---

## 🚀 단계별 도입 계획

### Phase 1: 기반 구축 (1주)
- ✅ AnswerBank 테이블 생성
- ✅ 임베딩 생성 함수 구현
- ✅ 벡터 검색 함수 구현

### Phase 2: 자동 수집 (2주)
- ✅ 우수 답변 자동 수집 로직
- ✅ 100개 이상 답변 축적
- ✅ 벡터 인덱스 생성

### Phase 3: 평가 연동 (3주)
- ✅ Solar LLM 평가에 참고 답변 추가
- ✅ 비교 평가 프롬프트 개선
- ✅ 피드백 품질 검증

### Phase 4: 고급 기능 (4주)
- ✅ 힌트 시스템 구현
- ✅ 표절 검사 기능
- ✅ 대시보드 시각화

---

## 📝 샘플 데이터

```sql
-- 우수 답변 샘플 삽입
INSERT INTO answer_bank (
    question_id, 
    answer_text, 
    embedding, 
    score, 
    company, 
    industry, 
    position
)
VALUES (
    1,
    'Docker를 활용하여 마이크로서비스 아키텍처를 구축했습니다. 
     각 서비스를 독립적인 컨테이너로 분리하고, Kubernetes로 오케스트레이션했습니다. 
     특히 서비스 간 통신은 gRPC를 사용하여 성능을 최적화했으며...',
    pgml.embed('jhgan/ko-sroberta-multitask', 'Docker를 활용하여...'),  -- pgml 확장 사용 시
    95.0,
    '삼성전자',
    'IT',
    'Backend 개발자'
);
```

---

**작성일**: 2026-01-26  
**버전**: v3.0 (벡터 기반 답변 평가)
