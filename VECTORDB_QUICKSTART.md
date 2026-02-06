# 🚀 VectorDB 빠른 시작 가이드

## 1단계: 환경 확인

현재 Docker Compose가 실행 중인지 확인하세요:
```bash
docker-compose ps
```

## 2단계: 필요한 패키지 설치

Backend 컨테이너에 접속하여 패키지를 설치합니다:

```bash
# 컨테이너 접속
docker exec -it interview_backend bash

# 패키지 설치 (이미 requirements.txt에 포함됨)
pip install sentence-transformers pgvector
```

## 3단계: 샘플 데이터 삽입

```bash
# 컨테이너 내부에서 실행
cd /app/scripts
python populate_vectordb.py
```

**예상 출력:**
```
🔄 임베딩 모델 로딩 중...
📦 모델: jhgan/ko-sroberta-multitask (768차원)
✅ 모델 로드 완료!

📊 VectorDB 샘플 데이터 삽입 시작
🔧 [기술 질문] 카테고리 삽입 중...
✅ 질문 저장 완료 (ID: 1)
✅ 답변 저장 완료 (ID: 1)
...
🎉 샘플 데이터 삽입 완료!
```

## 4단계: 벡터 검색 테스트

```bash
# 검색 유틸리티 실행
python vector_utils.py
```

**예상 출력:**
```
1️⃣ 유사 질문 검색
1. 유사도: 0.9234
   질문: Python에서 GIL(Global Interpreter Lock)이 무엇인지...
   난이도: hard

2️⃣ 답변 평가
점수: 78.5
유사도: 0.8263
피드백: 👍 좋은 답변입니다. 일부 개선 여지가 있습니다.
```

## 5단계: API 엔드포인트 추가 (선택)

`backend-core/main.py`에 다음 엔드포인트를 추가하세요:

```python
from scripts.vector_utils import find_similar_questions, evaluate_answer

@app.get("/api/questions/similar")
async def search_similar_questions(
    query: str,
    position: str = None,
    top_k: int = 5
):
    """유사 질문 검색 API"""
    results = find_similar_questions(
        query_text=query,
        top_k=top_k,
        position=position
    )
    return {
        "query": query,
        "results": [
            {
                "id": item["question"].id,
                "content": item["question"].content,
                "similarity": item["similarity"],
                "category": item["question"].category,
                "difficulty": item["question"].difficulty
            }
            for item in results
        ]
    }

@app.post("/api/answers/evaluate")
async def evaluate_user_answer(
    question_id: int,
    user_answer: str
):
    """답변 평가 API"""
    evaluation = evaluate_answer(question_id, user_answer)
    return evaluation
```

## 6단계: 프론트엔드에서 사용

```javascript
// 유사 질문 검색
const searchQuestions = async (query) => {
  const response = await fetch(
    `/api/questions/similar?query=${encodeURIComponent(query)}&position=Backend 개발자&top_k=5`
  );
  const data = await response.json();
  return data.results;
};

// 답변 평가
const evaluateAnswer = async (questionId, userAnswer) => {
  const response = await fetch('/api/answers/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question_id: questionId,
      user_answer: userAnswer
    })
  });
  return await response.json();
};
```

## 성능 최적화 (데이터 1000개 이상일 때)

```sql
-- PostgreSQL에 접속
docker exec -it interview_db psql -U admin -d interview_db

-- 벡터 인덱스 생성
CREATE INDEX idx_questions_embedding
ON questions
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_answer_bank_embedding
ON answer_bank
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## 문제 해결

### 1. 모델 다운로드 실패
```bash
# 수동 다운로드
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('jhgan/ko-sroberta-multitask')"
```

### 2. pgvector 확장 오류
```sql
-- PostgreSQL에서 확인
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 없으면 생성
CREATE EXTENSION vector;
```

### 3. 메모리 부족
```python
# 배치 크기 줄이기
embeddings = model.encode(texts, batch_size=8)  # 기본값 32 → 8
```

## 다음 단계

✅ VectorDB 구축 완료!
- [ ] 더 많은 질문/답변 데이터 추가
- [ ] API 엔드포인트 구현
- [ ] 프론트엔드 통합
- [ ] 실시간 답변 평가 시스템 구축
