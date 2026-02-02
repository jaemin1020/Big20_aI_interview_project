# 📊 DB 기반 질문 생성 및 평가 개선 완료 보고서

## 🎯 개선 목표
기존의 단순 LLM 생성 방식에서 **데이터베이스를 활용한 스마트 질문 관리 및 평가 품질 향상** 시스템으로 전환

---

## ✅ 구현된 개선 사항

### 1. **질문 생성 개선** (`ai-worker/tasks/question_generator.py`)

#### 1.1 DB 기반 질문 재활용
- **기능**: `questions` 테이블에서 동일 직무의 기존 질문을 조회하여 재사용
- **전략**: 
  - `reuse_ratio` 파라미터로 재사용 비율 조정 (기본값: 40%)
  - 평균 점수(`avg_score`)가 높고 사용 빈도(`usage_count`)가 낮은 질문 우선 선택
  - 선택 알고리즘: `score = avg_score - (usage_count * 0.01)` (점수 높고 덜 사용된 질문 우선)

> **📝 수정 사항 (2026-01-27 함유라)**
> 답변 점수(`avg_score`)를 질문의 품질로 보는 것은 논리적 오류가 있습니다.
> **변경**: `avg_score` 대신 **`quality_score` (LLM이 평가한 질문 자체 점수)**를 기준으로 변경합니다.

#### 1.2 사용 통계 추적
- **기능**: 질문이 사용될 때마다 `usage_count` 자동 증가
- **효과**: 
  - 인기 질문 파악 가능
  - 과도하게 사용된 질문 자동 필터링
  - 질문 풀(Pool) 다양성 유지

#### 1.3 혼합 전략
```python
# 예: 5개 질문 생성 시 (reuse_ratio=0.4)
# - DB에서 재사용: 2개 (40%)
# - LLM 신규 생성: 3개 (60%)
```

---

### 2. **평가 품질 개선** (`ai-worker/tasks/evaluator.py`)

#### 2.1 질문별 평균 점수 추적
- **기능**: 각 답변 평가 후 해당 질문의 `avg_score` 업데이트
- **알고리즘**: 이동 평균(Moving Average)
  ```python
  weight = min(usage_count, 10) / 10
  new_avg = old_avg * weight + new_score * (1 - weight)
  ```

> **📝 수정 사항 (2026-01-27 함유라)**
> **변경**: 답변 점수 단순 평균 대신, **LLM에게 "이 질문이 면접에 적합한가?"를 평가**하게 하여 그 점수(`quality_score`)를 추적하도록 로직을 전면 수정합니다.
- **효과**: 
  - 지원자의 답변 실력과 무관하게 **질문 자체의 퀄리티**를 객관적으로 검증
  - 모호하거나 직무와 관련 없는 질문 자동 도태
- **효과**: 
  - 초기 몇 개 답변에 과도하게 영향받지 않음
  - 10회 이상 사용 시 안정적인 평균값 유지

#### 2.2 평가 데이터 축적
- **저장 위치**: `transcripts.sentiment_score`, `transcripts.emotion`
- **활용**: 
  - 질문별 난이도 자동 조정 (향후 확장)
  - 지원자별 강약점 분석
  - 면접 전체 감정 흐름 추적

---

### 3. **데이터베이스 스키마 확장** (`ai-worker/db.py`)

#### 3.1 추가된 필드
```python
class Question(SQLModel, table=True):
    # ... 기존 필드 ...
    usage_count: int = Field(default=0)      # 사용 횟수
    avg_score: Optional[float] = None        # 평균 평가 점수 (0-100)
```

> **📝 수정 사항 (2026-01-27 함유라)**
> **변경**: `avg_score` 필드를 삭제하고, 질문 평가 전용 점수인 **`quality_score` (1-5점 척도)** 필드를 추가합니다.
```

#### 3.2 새로운 헬퍼 함수
| 함수명 | 기능 | 사용처 |
|:---|:---|:---|
| `get_questions_by_position()` | 직무별 질문 조회 (평균 점수 높은 순) | 질문 재활용 |
| `increment_question_usage()` | 사용 횟수 증가 | 질문 선택 시 |
| `update_question_avg_score()` | 평균 점수 업데이트 (이동 평균) | 답변 평가 후 |

> **📝 수정 사항 (2026-01-27 함유라)**
> **변경**: `get_questions_by_position`은 품질 점수(`quality_score`) 기준으로, `update_question_avg_score`는 `update_question_quality`로 변경합니다.

---

## 📈 기대 효과

### 1. **질문 품질 향상**
- ✅ 검증된 질문 재사용으로 일관성 확보
- ✅ 낮은 점수를 받은 질문 자동 필터링
- ✅ LLM 생성 실패 시에도 안정적인 폴백

### 2. **시스템 효율성**
- ✅ LLM 호출 횟수 40% 감소 (재사용 비율만큼)
- ✅ 질문 생성 시간 단축
- ✅ GPU/CPU 리소스 절약

### 3. **데이터 기반 의사결정**
- ✅ 질문별 통계 데이터 축적
- ✅ 직무별 효과적인 질문 패턴 파악
- ✅ 지속적인 질문 풀 개선 가능

---

## 🔄 동작 흐름

```
[면접 시작]
    ↓
[질문 생성 요청] → AI-Worker
    ↓
[DB 조회: 기존 질문 2개 선택]
    ├─ quality_score 높은 순 정렬 (질문 자체 퀄리티 기준)
    ├─ usage_count 낮은 것 우선
    └─ increment_question_usage()
    ↓
[LLM 생성: 신규 질문 3개]
    ↓
[총 5개 질문 반환]
    ↓
[사용자 답변 제출]
    ↓
[Solar LLM 평가]
    ├─ 1. 답변 평가 (User 점수)
    └─ 2. 질문 평가 (Question 점수, 1-5점)
    ↓
[update_question_quality()] → DB 업데이트
    ↓
[다음 면접에서 고품질 질문(`quality_score` high) 재사용]
```

---

## 🚀 향후 확장 가능성

1. **난이도 자동 조정**: `avg_score`가 낮으면 `difficulty`를 'easy'로 자동 변경
2. **A/B 테스트**: 동일 직무에 대해 여러 질문 세트의 효과 비교
3. **Vector Search**: `pgvector`를 활용한 유사 질문 검색 및 중복 제거
4. **개인화**: 지원자의 이력서 키워드 기반 맞춤형 질문 생성

---

## 📝 변경된 파일 목록

1. ✅ `ai-worker/tasks/question_generator.py` - DB 기반 질문 재활용 로직
2. ✅ `ai-worker/tasks/evaluator.py` - 평가 후 질문 점수 업데이트
3. ✅ `ai-worker/db.py` - Question 모델 확장 및 헬퍼 함수 추가
4. ✅ `backend-core/main.py` - 평가 태스크 호출 시 question_id 전달
5. ✅ `backend-core/models.py` - Question 모델에 avg_score 필드 (이미 존재)

---

## ⚠️ 주의사항

1. **DB 마이그레이션**: `questions` 테이블에 `avg_score` 컬럼이 없다면 추가 필요
   ```sql
   ALTER TABLE questions ADD COLUMN avg_score FLOAT;
   ```

2. **초기 데이터**: 처음에는 `avg_score`가 `NULL`이므로 재사용되지 않음
   - 최소 1회 이상 평가된 질문만 재사용 대상

3. **재사용 비율 조정**: `reuse_ratio`를 너무 높이면 질문 다양성 감소
   - 권장값: 0.3 ~ 0.5 (30% ~ 50%)

---


### 6. **변경 이력**
- **2026-01-27 (함유라)**: 
  - **변경 사유**: 지원자의 답변 점수(`avg_score`)를 질문의 품질로 간주하는 기존 논리의 오류 수정. 답변 실력과 무관하게 **질문 자체의 퀄리티**를 평가하는 것이 더 타당함.
  - **변경 내용**: `avg_score` → `quality_score`로 변경 및 LLM의 질문 평가 단계 추가.

---

**작성일**: 2026-01-27  
**작성자**: AI Assistant & 함유라  
**버전**: v2.1
