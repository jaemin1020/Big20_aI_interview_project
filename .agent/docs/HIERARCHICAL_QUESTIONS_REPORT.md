# 📊 계층적 질문 분류 시스템 개선 완료

## 🎯 개선 목표

기존의 단순 직무별 분류에서 **회사별 → 산업별 → 직무별** 3단계 계층적 분류로 확장하여 더욱 정교한 질문 추천

---

## ✅ 구현된 개선 사항

### 1. **데이터 모델 확장**

#### 1.1 Question 테이블 스키마 변경

```python
class Question(SQLModel, table=True):
    # ... 기존 필드 ...
  
    # 계층적 분류 (3단계)
    company: Optional[str]   # 회사명 (예: "삼성전자", "카카오")
    industry: Optional[str]  # 산업 (예: "IT", "금융", "제조")
    position: Optional[str]  # 직무 (예: "Backend 개발자")
```

#### 1.2 인덱스 추가

- `company`, `industry`, `position` 필드에 인덱스 설정
- 빠른 계층적 탐색 지원

---

### 2. **계층적 질문 탐색 알고리즘**

#### 2.1 탐색 우선순위

```
1순위: company + industry + position (가장 구체적)
   ↓ (결과 없으면)
2순위: industry + position (중간 수준)
   ↓ (결과 없으면)
3순위: position (가장 일반적)
   ↓ (결과 없으면)
4순위: LLM 신규 생성
```

#### 2.2 함수 구현

```python
def get_questions_hierarchical(
    position: str,      # 필수
    company: str = None,   # 선택
    industry: str = None,  # 선택
    limit: int = 10
):
    # 1단계: 회사 + 산업 + 직무
    if company and industry:
        # 가장 구체적인 질문 조회
      
    # 2단계: 산업 + 직무
    if industry and not questions:
        # 산업 특화 질문 조회
      
    # 3단계: 직무만
    if not questions:
        # 일반적인 직무 질문 조회
```

---

### 3. **사용 시나리오**

#### 시나리오 1: 삼성전자 Backend 개발자 면접

```python
# 호출
questions = get_questions_hierarchical(
    position="Backend 개발자",
    company="삼성전자",
    industry="IT"
)

# 결과: 삼성전자 특화 질문 우선 반환
# - "삼성전자의 Tizen OS 플랫폼 개발 경험이 있으신가요?"
# - "대규모 트래픽 처리를 위한 마이크로서비스 아키텍처..."
```

#### 시나리오 2: 일반 IT 스타트업 Backend 개발자

```python
# 호출
questions = get_questions_hierarchical(
    position="Backend 개발자",
    industry="IT"
)

# 결과: IT 산업 일반 질문 반환
# - "Docker와 Kubernetes를 활용한..."
# - "CI/CD 파이프라인 구축 및 자동화..."
```

#### 시나리오 3: 금융권 Backend 개발자

```python
# 호출
questions = get_questions_hierarchical(
    position="Backend 개발자",
    industry="금융"
)

# 결과: 금융 특화 질문 반환
# - "금융 시스템의 트랜잭션 처리와 데이터 일관성..."
# - "금융권 보안 규정 준수 경험이 있으신가요?"
```

---

### 4. **로그 개선**

#### 4.1 질문 출처 추적

```
♻️ Reused [회사:삼성전자 > 산업:IT > 직무:Backend 개발자] (ID=1, usage=3): 삼성전자의 Tizen OS...
♻️ Reused [산업:IT > 직무:Backend 개발자] (ID=5, usage=1): Docker와 Kubernetes를...
♻️ Reused [직무:Backend 개발자] (ID=8, usage=2): RESTful API 설계 원칙과...
```

---

## 📈 기대 효과

### 1. **질문 정확도 향상**

- ✅ 회사별 특화 질문으로 실무 적합성 증가
- ✅ 산업별 도메인 지식 평가 가능
- ✅ 직무 일반 질문으로 폴백 보장

### 2. **데이터 활용도 증가**

- ✅ 동일 직무라도 회사/산업별로 다른 질문 제공
- ✅ 질문 풀(Pool) 다양성 극대화
- ✅ 사전 질문 데이터의 효율적 재사용

### 3. **확장성**

- ✅ 새로운 회사/산업 추가 용이
- ✅ 질문 데이터 축적에 따라 자동으로 품질 향상
- ✅ 향후 4단계(팀/부서) 분류도 쉽게 확장 가능

---

## 🗂️ 사전 질문 데이터 구조

### 계층별 질문 예시

| 회사     | 산업 | 직무    | 질문 예시              |   우선순위   |
| :------- | :--- | :------ | :--------------------- | :-----------: |
| 삼성전자 | IT   | Backend | Tizen OS 개발 경험     | 1 (가장 높음) |
| 카카오   | IT   | Backend | 카카오톡 메시징 시스템 |       1       |
| NULL     | IT   | Backend | Docker/K8s 경험        |       2       |
| NULL     | 금융 | Backend | 트랜잭션 처리 경험     |       2       |
| NULL     | NULL | Backend | RESTful API 설계       |   3 (폴백)   |

---

## 🚀 사용 방법

### 1. 사전 질문 데이터 삽입

```bash
# Docker 컨테이너 내부에서 실행
docker exec -i interview_db psql -U admin -d interview_db < infra/postgres/sample_questions.sql
```

### 2. Backend에서 면접 생성 시 회사/산업 정보 전달

```python
# backend-core/main.py
task = celery_app.send_task(
    "tasks.question_generator.generate_questions",
    args=[
        interview_data.position,  # "Backend 개발자"
        5,                         # 질문 개수
        "삼성전자",                # company (선택)
        "IT"                       # industry (선택)
    ]
)
```

### 3. 질문 조회 결과 확인

```sql
-- 삼성전자 Backend 질문 조회
SELECT content, company, industry, position, avg_score, usage_count
FROM questions
WHERE company = '삼성전자' AND industry = 'IT' AND position = 'Backend 개발자'
ORDER BY avg_score DESC;
```

---

## ⚠️ 주의사항

### 1. DB 마이그레이션

기존 `questions` 테이블에 컬럼 추가 필요:

```sql
ALTER TABLE questions 
ADD COLUMN company VARCHAR(100),
ADD COLUMN industry VARCHAR(100);

CREATE INDEX idx_questions_company ON questions(company);
CREATE INDEX idx_questions_industry ON questions(industry);
```

### 2. 기존 질문 데이터

- 기존 질문은 `company`, `industry`가 `NULL`이므로 3순위(직무만)로 분류됨
- 점진적으로 회사/산업 정보를 추가하면 자동으로 우선순위 상승

### 3. Frontend 연동

- 면접 생성 시 회사명/산업 입력 필드 추가 권장
- 선택 사항이므로 기존 플로우도 정상 동작

---

## 📝 변경된 파일 목록

1. ✅ `backend-core/models.py` - Question 모델에 company, industry 필드 추가
2. ✅ `ai-worker/db.py` - Question 모델 동기화 및 계층적 탐색 함수 추가
3. ✅ `ai-worker/tasks/question_generator.py` - 계층적 탐색 로직 적용
4. ✅ `infra/postgres/sample_questions.sql` - 사전 질문 데이터 샘플

---

## 🔮 향후 확장 계획

1. **4단계 분류**: 팀/부서 레벨 추가 (예: "카카오 > IT > 추천팀 > Backend")
2. **지역별 분류**: 글로벌 기업의 경우 국가/지역별 질문 (예: "삼성전자 > 베트남 > IT")
3. **시간별 트렌드**: 최신 기술 스택 반영 (예: 2025년 이후 질문만 조회)
4. **난이도 자동 조정**: 회사별 평균 점수에 따라 difficulty 자동 업데이트

---

**작성일**: 2026-01-26
**버전**: v2.1 (계층적 분류 시스템)
