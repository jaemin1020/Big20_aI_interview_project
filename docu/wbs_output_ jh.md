# 담당 : 권준호
# 산출물1 : Final_Project_Data_수립_설계서
# 산출물2 : Final_Project_Dataset_Specification_데이터정의서
# 산출물3 : Final_Project_ERD_DB_설계서


# 산출물1 : Final_Project_Data_수립_설계서

---

## 1. 문서 개요

### 1.1 목적
본 문서는 생성형 AI 기반 멀티모달 면접 서비스 개발을 위해 필요한 데이터 수립 전반에 대한 설계 기준을 정의한다.  
데이터 요구사항 정의부터 수집, 스키마 설계, 라벨링 기준, 데이터 분할 및 평가셋 구성까지의 전 과정을 체계적으로 정리하는 것을 목표로 한다.

### 1.2 담당자
- 담당: 권준호

---

## 2. 데이터 요구사항 정의

### 2.1 데이터 목적
- 면접 질문 생성
- 지원자 답변 평가(직무/인성)
- 후속 질문 생성
- 상태(State) 판단 및 학습 데이터 확보

### 2.2 데이터 유형
- 텍스트 데이터(질문, 답변, 평가 기준)
- 메타 데이터(직무, 산업, 난이도, 단계)
- 평가 데이터(점수, 평가 상태, 부족 사유)

---

## 3. 데이터 소스 선정 및 수집 전략

### 3.1 데이터 소스
- 공개 면접 질문 데이터
- 직무별 질문 데이터셋
- 기업 인재상 및 평가 기준 문서
- 프로젝트 내부 생성 데이터(AI 생성 질문/평가 로그)

### 3.2 수집 전략
- 공개 데이터: 크롤링 및 파일 수집
- 내부 데이터: API 로그 및 결과 저장
- JSON / CSV 중심의 구조화 수집

---

## 4. 데이터 스키마 설계

### 4.1 질문 데이터 스키마
- question_id
- question_text
- job_category
- industry
- difficulty
- scenario
- stage

### 4.2 답변 데이터 스키마
- answer_id
- question_id
- answer_text
- user_id
- timestamp

### 4.3 평가 데이터 스키마
- evaluation_id
- answer_id
- evaluation_type (직무/인성/혼합)
- score
- status
- lack_reason

---

## 5. 라벨링 기준 설계

### 5.1 평가 라벨
- SUFFICIENT
- INSUFFICIENT
- NOT_EVALUABLE

### 5.2 부족 사유 라벨
- logic
- experience
- keyword
- structure
- null

### 5.3 라벨링 기준
- 루브릭 기반 수동/반자동 라벨링
- 동일 기준 반복 적용으로 일관성 유지

---

## 6. 데이터 규모 계획

### 6.1 질문 데이터
- 직무별 질문: 약 300~500개
- 전체 질문 데이터: 약 500~1000개

### 6.2 답변 및 평가 데이터
- 질문당 답변 5~10개
- 총 답변 데이터: 약 2500~5000건

---

## 7. 데이터 분할 및 평가셋 설계

### 7.1 데이터 분할 비율
- 학습(Train): 70%
- 검증(Validation): 15%
- 평가(Test): 15%

### 7.2 분할 기준
- 질문 기준 중복 제거
- 동일 질문의 답변은 동일 셋에 포함
- 직무/산업 분포 균등 유지

---

## 8. 데이터 품질 관리 기준

### 8.1 품질 기준
- 중복 데이터 제거
- 라벨 누락 데이터 제외
- 질문-답변 불일치 데이터 제거

### 8.2 관리 방안
- 정기적인 데이터 검증
- 라벨 분포 모니터링
- 로그 기반 추적 관리

---

## 9. 기대 효과
- 학습 데이터의 일관성 및 신뢰성 확보
- 평가 모델 성능 안정화
- 직무 및 산업 확장 시 데이터 재사용 용이
- RAG 및 LLM 품질 향상

# ____________________________________

# 산출물2 : Final_Project_Dataset_Specification_데이터정의서

# Final_Project_Dataset_Specification_데이터정의서

---

## 1. 문서 개요

### 1.1 목적
본 문서는 프로젝트 전반에서 사용되는 데이터셋의 구조와 의미를 정의한다.  
각 데이터 항목의 역할, 형식, 허용 값 범위를 명확히 하여 데이터 일관성과 재사용성을 확보하는 것을 목표로 한다.

---

## 2. 데이터셋 구성 개요

### 2.1 데이터 구분
- 사용자 데이터
- 질문 데이터
- 답변 데이터
- 평가 데이터
- 상태(State) 데이터

---
## 컬럼별 정의

## 3. 사용자 데이터 정의

### 3.1 USER 데이터셋
- user_id: 사용자 고유 식별자
- created_at: 가입 일시
- last_access_at: 최근 접속 일시

---

## 4. 질문 데이터 정의

### 4.1 QUESTION 데이터셋
- question_id: 질문 ID
- question_text: 질문 내용
- job_category: 직무 분류
- industry: 산업 분류
- scenario: 면접 시나리오
- stage: 면접 단계
- difficulty: 난이도

---

## 5. 답변 데이터 정의

### 5.1 ANSWER 데이터셋
- answer_id: 답변 ID
- question_id: 질문 ID
- answer_text: 답변 내용
- response_time: 응답 소요 시간
- created_at: 생성 시각

---

## 6. 평가 데이터 정의

### 6.1 EVALUATION 데이터셋
- evaluation_id: 평가 ID
- answer_id: 답변 ID
- evaluation_type: 직무 / 인성 / 혼합
- score: 평가 점수
- status: 평가 상태
- lack_reason: 부족 사유

---

## 7. 상태(State) 데이터 정의

### 7.1 STATE 데이터셋
- scenario: 입사지원 / 직무평가 / 인성평가
- stage: 3 / 3-1 / 4 / 4-1
- intent: ANSWERING 등
- next_action: NEXT / FOLLOWUP / RETRY
- retry_count: 재시도 횟수

---

## 8. 데이터 값 정의 및 규칙

### 8.1 상태 값 규칙
- SUFFICIENT
- INSUFFICIENT
- NOT_EVALUABLE

### 8.2 부족 사유 규칙
- logic
- experience
- keyword
- structure
- null

---

## 9. 데이터 관리 기준
- 필수 컬럼 누락 데이터 제외
- 값 범위 검증 필수
- 로그 기반 추적 가능 구조 유지

---

## 10. 기대 효과
- 데이터 의미 명확화
- 협업 시 해석 차이 최소화
- 모델 학습 및 평가 효율 향상
- DB 설계 및 RAG 연계 용이

# ______________________________________________

# 산출물3 : Final_Project_ERD_DB_설계서

# Final_Project_ERD_DB_설계서

---

## 1. 문서 개요

### 1.1 목적
본 문서는 생성형 AI 기반 멀티모달 면접 서비스의 데이터 저장 구조를 정의하기 위해  
DB 테이블 도출, ERD 설계, 테이블 간 관계, 키 및 제약조건을 명확히 설계하는 것을 목적으로 한다.

---

## 2. 요구 데이터 정의

### 2.1 핵심 데이터 영역
- 사용자 정보
- 면접 시나리오 및 단계 정보
- 질문 데이터
- 답변 데이터
- 평가 결과 데이터
- 상태(State) 관리 데이터

---

## 3. 테이블 도출

### 3.1 주요 테이블 목록
- USER
- INTERVIEW_SESSION
- QUESTION
- ANSWER
- EVALUATION
- STATE_HISTORY

---

## 4. 테이블 관계 정의

### 4.1 관계 구조
- USER : INTERVIEW_SESSION = 1 : N
- INTERVIEW_SESSION : QUESTION = 1 : N
- QUESTION : ANSWER = 1 : N
- ANSWER : EVALUATION = 1 : 1
- INTERVIEW_SESSION : STATE_HISTORY = 1 : N

### 4.2 N:M 관계 처리
- 다대다 관계는 중간 테이블로 분리하여 관리
- 예: QUESTION_TAG, JOB_QUESTION_MAP

---

## 5. 키(Key) 및 제약조건 설계

### 5.1 기본 키(Primary Key)
- 각 테이블은 고유 식별자 ID 사용
- 예: user_id, question_id, answer_id

### 5.2 외래 키(Foreign Key)
- 참조 무결성 유지
- 세션 삭제 시 하위 데이터 연쇄 처리 제한 또는 Cascade 적용

### 5.3 제약조건
- NOT NULL: 필수 데이터
- UNIQUE: 중복 불가 항목
- CHECK: 상태 값 제한(SUFFICIENT, INSUFFICIENT 등)

---

## 6. 데이터 타입 및 길이 설계

### 6.1 주요 컬럼 기준
- ID: VARCHAR(36) 또는 BIGINT
- 텍스트: TEXT 또는 VARCHAR(1000~3000)
- 상태값: VARCHAR(30)
- 점수: FLOAT
- 시간 정보: TIMESTAMP

---

## 7. 정규화 수준 결정

### 7.1 정규화 기준
- 제3정규형(3NF) 기준 설계
- 데이터 중복 최소화
- 조회 성능을 고려한 일부 반정규화 허용

---

## 8. 기대 효과
- 데이터 무결성 확보
- ERD 기반 구조적 확장 용이
- 서비스 상태 추적 및 분석 가능
- RAG 및 평가 로직 연계 최적화
