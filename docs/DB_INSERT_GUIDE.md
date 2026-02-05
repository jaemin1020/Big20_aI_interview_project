# 데이터베이스 삽입 가이드

## 📋 목차
1. [Company 데이터 삽입](#1-company-데이터-삽입)
2. [Question 데이터 삽입](#2-question-데이터-삽입)
3. [AnswerBank 데이터 삽입](#3-answerbank-데이터-삽입)
4. [벡터 임베딩 생성](#4-벡터-임베딩-생성)

---

## 1. Company 데이터 삽입

### 📊 테이블 구조
```sql
CREATE TABLE companies (
    id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    ideal TEXT,
    description TEXT,
    embedding vector(768),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 🔧 삽입 방법

#### 방법 1: SQL 직접 실행
```sql
INSERT INTO companies (id, company_name, ideal, description)
VALUES 
    ('KAKAO', '카카오', 
     '도전적이고 창의적인 인재, 사용자 중심의 사고를 가진 분',
     '카카오는 기술과 사람을 연결하여 더 나은 세상을 만듭니다.'),
    
    ('NAVER', '네이버', 
     '기술로 세상을 변화시키고자 하는 열정을 가진 인재',
     '네이버는 글로벌 ICT 기업으로 검색, AI, 커머스 등 다양한 서비스를 제공합니다.');
```

#### 방법 2: Python 코드
```python
from sqlmodel import Session
from backend.models import Company
from backend.database import engine
from sentence_transformers import SentenceTransformer

# 임베딩 모델
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 회사 데이터
company_data = {
    "id": "KAKAO",
    "company_name": "카카오",
    "ideal": "도전적이고 창의적인 인재",
    "description": "카카오는 기술과 사람을 연결합니다."
}

# 벡터 임베딩 생성
text = f"{company_data['ideal']} {company_data['description']}"
embedding = model.encode(text).tolist()

# DB 삽입
with Session(engine) as session:
    company = Company(
        **company_data,
        embedding=embedding
    )
    session.add(company)
    session.commit()
```

#### 방법 3: API 사용
```bash
curl -X POST "http://localhost:8000/companies/" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "KAKAO",
    "company_name": "카카오",
    "ideal": "도전적이고 창의적인 인재",
    "description": "카카오는 기술과 사람을 연결합니다."
  }'
```

---

## 2. Question 데이터 삽입

### 📊 테이블 구조
```sql
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    category VARCHAR(50),  -- TECHNICAL, BEHAVIORAL, SITUATIONAL, CULTURAL_FIT
    difficulty VARCHAR(20), -- EASY, MEDIUM, HARD
    rubric_json JSONB,
    embedding vector(768),
    company VARCHAR(255),
    industry VARCHAR(100),
    position VARCHAR(100),
    created_at TIMESTAMP,
    is_active BOOLEAN,
    usage_count INTEGER,
    avg_score FLOAT
);
```

### 🔧 삽입 방법

#### 방법 1: SQL 직접 실행
```sql
INSERT INTO questions (content, category, difficulty, rubric_json, is_active)
VALUES 
    ('딥러닝이란 무엇인가요?', 
     'TECHNICAL', 
     'MEDIUM',
     '{"criteria": ["정확성", "명확성", "깊이"], "scoring": {"excellent": "80-100", "good": "60-79"}}',
     true);
```

#### 방법 2: Python 코드
```python
from sqlmodel import Session
from backend.models import Question, QuestionCategory, QuestionDifficulty
from backend.database import engine
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 질문 데이터
question_text = "딥러닝이란 무엇인가요?"
embedding = model.encode(question_text).tolist()

# 평가 기준
rubric = {
    "criteria": [
        "정확성: 개념을 정확하게 이해하고 있는가?",
        "명확성: 설명이 명확하고 이해하기 쉬운가?",
        "깊이: 개념에 대한 깊이 있는 이해를 보여주는가?"
    ],
    "scoring": {
        "excellent": "개념을 정확히 이해하고 명확하게 설명함 (80-100점)",
        "good": "개념을 이해하고 있으나 설명이 다소 부족함 (60-79점)",
        "fair": "개념에 대한 이해가 부족함 (40-59점)",
        "poor": "개념을 이해하지 못함 (0-39점)"
    }
}

# DB 삽입
with Session(engine) as session:
    question = Question(
        content=question_text,
        category=QuestionCategory.TECHNICAL,
        difficulty=QuestionDifficulty.MEDIUM,
        rubric_json=rubric,
        embedding=embedding,
        is_active=True
    )
    session.add(question)
    session.commit()
    print(f"질문 ID: {question.id}")
```

---

## 3. AnswerBank 데이터 삽입

### 📊 테이블 구조
```sql
CREATE TABLE answer_bank (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id),
    answer_text TEXT NOT NULL,
    embedding vector(768),
    score FLOAT,
    evaluator_feedback TEXT,
    company VARCHAR(255),
    industry VARCHAR(100),
    position VARCHAR(100),
    created_at TIMESTAMP,
    is_active BOOLEAN,
    reference_count INTEGER
);
```

### 🔧 삽입 방법

#### 방법 1: SQL 직접 실행
```sql
INSERT INTO answer_bank (question_id, answer_text, score, evaluator_feedback, is_active)
VALUES 
    (1, 
     '머신러닝의 한 종류로 인공신경망을 기반으로 데이터에서 패턴을 학습하여 새로운 데이터에 대한 예측을 하는 알고리즘입니다.',
     85.0,
     '표준 답변',
     true);
```

#### 방법 2: Python 코드
```python
from sqlmodel import Session
from backend.models import AnswerBank
from backend.database import engine
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 답변 데이터
answer_text = "머신러닝의 한 종류로 인공신경망을 기반으로 데이터에서 패턴을 학습하여 새로운 데이터에 대한 예측을 하는 알고리즘입니다."
embedding = model.encode(answer_text).tolist()

# DB 삽입
with Session(engine) as session:
    answer = AnswerBank(
        question_id=1,  # 연결할 질문 ID
        answer_text=answer_text,
        embedding=embedding,
        score=85.0,
        evaluator_feedback="표준 답변",
        is_active=True
    )
    session.add(answer)
    session.commit()
    print(f"답변 ID: {answer.id}")
```

---

## 4. 벡터 임베딩 생성

### 🎯 임베딩 모델
한국어 지원 모델: `jhgan/ko-sroberta-multitask`

### 🔧 사용 방법

#### Python 코드
```python
from sentence_transformers import SentenceTransformer

# 모델 로드 (최초 1회)
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 텍스트 → 벡터 (768차원)
text = "딥러닝이란 무엇인가요?"
embedding = model.encode(text)

# 리스트로 변환 (DB 저장용)
embedding_list = embedding.tolist()

print(f"벡터 차원: {len(embedding_list)}")  # 768
print(f"벡터 샘플: {embedding_list[:5]}")
```

### 📊 벡터 검색 예시

#### 유사 질문 찾기
```python
from sqlmodel import Session, select
from backend.models import Question
from backend.database import engine

# 검색할 질문
query_text = "머신러닝과 딥러닝의 차이는?"
query_embedding = model.encode(query_text).tolist()

# 벡터 유사도 검색
with Session(engine) as session:
    stmt = select(Question).where(
        Question.embedding.isnot(None)
    ).order_by(
        Question.embedding.cosine_distance(query_embedding)
    ).limit(5)
    
    similar_questions = session.exec(stmt).all()
    
    for q in similar_questions:
        print(f"- {q.content}")
```

---

## 📝 일괄 삽입 예시

### JSON 데이터 → DB

#### 데이터 형식
```json
[
  {
    "질문": "딥러닝이란 무엇인가요?",
    "답변": "머신러닝의 한 종류로 인공신경망을 기반으로..."
  },
  {
    "질문": "딥러닝과 머신러닝의 차이는?",
    "답변": "딥러닝은 특징 추출을 자동으로..."
  }
]
```

#### Python 삽입 코드
```python
import json
from sqlmodel import Session
from backend.models import Question, AnswerBank, QuestionCategory, QuestionDifficulty
from backend.database import engine
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# JSON 파일 읽기
with open('qa_data.json', 'r', encoding='utf-8') as f:
    qa_data = json.load(f)

with Session(engine) as session:
    for item in qa_data:
        # 1. 질문 삽입
        question_text = item["질문"]
        question_embedding = model.encode(question_text).tolist()
        
        question = Question(
            content=question_text,
            category=QuestionCategory.TECHNICAL,
            difficulty=QuestionDifficulty.MEDIUM,
            rubric_json={
                "criteria": ["정확성", "명확성", "깊이"],
                "scoring": {"excellent": "80-100", "good": "60-79"}
            },
            embedding=question_embedding,
            is_active=True
        )
        session.add(question)
        session.flush()  # question.id 생성
        
        # 2. 답변 삽입
        answer_text = item["답변"]
        answer_embedding = model.encode(answer_text).tolist()
        
        answer = AnswerBank(
            question_id=question.id,
            answer_text=answer_text,
            embedding=answer_embedding,
            score=85.0,
            evaluator_feedback="표준 답변",
            is_active=True
        )
        session.add(answer)
        
        print(f"✅ 추가: {question_text[:30]}...")
    
    session.commit()
    print(f"🎉 총 {len(qa_data)}개 삽입 완료!")
```

---

## 🔍 데이터 조회 예시

### Company 조회
```python
from sqlmodel import Session, select
from backend.models import Company
from backend.database import engine

with Session(engine) as session:
    # ID로 조회
    company = session.get(Company, "KAKAO")
    print(f"회사명: {company.company_name}")
    
    # 전체 조회
    stmt = select(Company)
    companies = session.exec(stmt).all()
    for c in companies:
        print(f"- {c.id}: {c.company_name}")
```

### Question 조회
```python
from sqlmodel import Session, select
from backend.models import Question, QuestionCategory
from backend.database import engine

with Session(engine) as session:
    # 카테고리별 조회
    stmt = select(Question).where(
        Question.category == QuestionCategory.TECHNICAL,
        Question.is_active == True
    )
    questions = session.exec(stmt).all()
    
    for q in questions:
        print(f"- {q.content}")
```

---

## ⚠️ 주의사항

1. **벡터 임베딩**
   - 텍스트 변경 시 반드시 임베딩도 재생성
   - 모델은 한 번만 로드하여 재사용

2. **트랜잭션**
   - 대량 삽입 시 `session.commit()` 한 번만 호출
   - 에러 발생 시 자동 롤백

3. **인덱스**
   - 벡터 검색 성능 향상을 위해 IVFFlat 인덱스 생성 권장
   - 데이터가 1000개 이상일 때 생성

4. **문자 인코딩**
   - JSON 파일은 UTF-8 인코딩 필수
   - Python 파일 상단에 `# -*- coding: utf-8 -*-` 추가

---

**작성일**: 2026-01-28  
**버전**: 1.0
