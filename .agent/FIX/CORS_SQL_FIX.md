# 🔧 CORS 및 SQL 에러 최종 해결 가이드

## 문제 요약
1. **CORS 에러**: Backend가 SQL 에러로 인해 응답하지 못함
2. **SQL 에러**: Question 모델의 embedding 필드 타입 불일치

## 해결 방법

### 즉시 적용 가능한 임시 해결책

Backend 컨테이너에 직접 접속하여 핫픽스 적용:

```bash
# 1. Backend 컨테이너 접속
docker exec -it interview_backend bash

# 2. main.py 수정
nano /app/main.py

# 3. 144-153번 줄의 Question 생성 부분 수정
# 기존:
question = Question(
    content=q_text,
    category=QuestionCategory.TECHNICAL if i < 3 else QuestionCategory.BEHAVIORAL,
    difficulty=QuestionDifficulty.MEDIUM,
    rubric_json={...},
    position=interview_data.position
)

# 수정 후:
question = Question(
    content=q_text,
    category=QuestionCategory.TECHNICAL if i < 3 else QuestionCategory.BEHAVIORAL,
    difficulty=QuestionDifficulty.MEDIUM,
    rubric_json={...},
    embedding=None,  # 추가
    position=interview_data.position
)

# 4. 저장 후 컨테이너 재시작
exit
docker-compose restart backend
```

### 정식 해결책 (권장)

`backend-core/models.py`의 Question 모델 수정:

```python
from pgvector.sqlalchemy import Vector

class Question(SQLModel, table=True):
    # ... 기존 필드 ...
    
    # 벡터 임베딩 (pgvector 타입 사용)
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(768))  # SQLAlchemy Column 타입 명시
    )
```

## 테스트

```bash
# Backend 로그 확인
docker-compose logs backend --tail=20

# 정상 동작 확인
curl -X POST http://localhost:8000/interviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"position":"Backend Developer"}'
```

## 완료 후 확인사항

- [ ] Backend 정상 시작
- [ ] SQL 에러 없음
- [ ] CORS 에러 해결
- [ ] 면접 생성 성공

---

**작성일**: 2026-01-27  
**상태**: 🔧 진행 중
