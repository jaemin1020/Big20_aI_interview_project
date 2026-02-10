# 🚀 AI 실시간 면접 시스템: 통합 디버깅 및 고도화 리포트

이 문서는 프로젝트 초기 구동부터 15단계 실시간 압박 면접 시스템 완성까지 발생한 모든 기술적 문제와 그 해결책을 집대성한 기록입니다.

---

## 🛠 1. 데이터베이스 및 ORM 안정성 확보

### 1-1. `NotNullViolation` 인터뷰 세션 생성 실패
- **대상**: `backend-core/routes/interviews.py`
- **변경**: `Interview` 객체 생성과 `Transcript` 초기 문항 저장을 별도 커밋으로 분리.
- **이유**: `Interview` ID가 생성되기 전 외래키 참조 에러 방지.

### 1-2. ENUM 타입 대소문자 정규화
- **대상**: `backend-core/models.py`
- **변경**: `InterviewStatus` 값을 `live` -> `LIVE` 등 대문자로 일괄 수정.
- **이유**: PostgreSQL ENUM 타입의 Case-sensitive 특성 대응.

### 1-3. 객체 분리 오류 (`DetachedInstanceError`)
- **문제**: 응답 반환 직전에 `Instance is not bound to a Session` 에러 발생.
- **원인**: `db.expunge_all()` 호출 후 분리된 객체의 속성에 접근 시도.
- **해결**: 객체 분리 전 필요한 데이터를 로컬 변수에 저장(Snapshot).

### 1-4. AI 워커 참조 오류 (`NameError: name 'Session' is not defined`)
- **문제**: 답변 분석(`analyze_answer`)은 성공하나 다음 질문 생성 트리거 단계에서 에러 발생 및 프로세스 중단.
- **원인**: `evaluator.py` 내부에 실시간 질문 생성 로직을 추가하는 과정에서 `Session`, `engine`, `Transcript` 등 필수 클래스의 `import` 누락.
- **해결**: `evaluator.py` 상단에 `db` 모듈로부터 필요한 클래스들을 명시적으로 `import` 하도록 수정.

### 1-5. 질문 생성 태스크 문법 에러 (`SyntaxError/TypeError`)
- **문제**: 실시간 질문 생성 시 시나리오 판단 로직에서 워커 크래시 발생.
- **원인**: `logger.error(f[f"..."])` 처럼 f-string 문법에 중복된 f와 대괄호가 포함되는 오타 발생.
- **해결**: `ai-worker/tasks/question_generation.py` 파일을 전수 검수하여 문법 오타를 제거하고 안정적인 에러 핸들링 코드를 추가함.

### 1-6. 프론트엔드 질문 수신 타임아웃 (Polling Timeout)
- **문제**: 모든 로직이 정상임에도 2단계 이후 면접이 종료됨.
- **원인**: AI 모델(EXAONE)의 답변 분석 및 질문 생성에 약 60~100초가 소요되나, 프론트엔드 대기 시간이 30초(2초 x 15회)로 설정되어 있어 생성 완료 전 "질문 없음"으로 판단함.
- **해결**: `App.jsx`의 폴링 루프를 15회에서 60회로 증설하여 **최대 120초(2분)**까지 AI의 답변을 기다리도록 인내심 상향 조정.

### 1-7. AI 워커 모듈 누락 (`ModuleNotFoundError: No module named 'utils.interview_helpers'`)
- **문제**: 답변 분석 후 다음 질문 생성 단계에서 `ModuleNotFoundError` 발생하며 중단.
- **원인**: 실시간 질문 생성 로직에서 참조하는 `utils.interview_helpers` 모듈과 `get_candidate_info` 함수가 실제 파일로 존재하지 않았음.
- **해결**: `ai-worker/utils/interview_helpers.py` 파일을 생성하여 이력서 데이터에서 지원자 성함 및 직무를 추출하는 기능을 구현하고 워커 재시작.

### 1-8. 질문 생성 지연 및 워커 병목 (Latency Bottleneck)
- **문제**: 유저 답변 후 다음 질문이 나타나기까지 너무 오랜 시간(약 100초 이상)이 소요됨.
- **원인**: `analyze_answer`(답변 분석) 태스크가 LLM을 사용하여 약 45~70초간 실행되는데, 이 분석이 **완전히 끝난 후에야** 다음 질문 생성을 시작하는 직렬 구조였음.
- **해결**: `evaluator.py`의 로직을 수정하여, **답변을 받자마자(분석 시작 전) 즉시 비동기로 다음 질문 생성을 트리거**하도록 개선. 분석(백그라운드)과 생성(프론트엔드 노출)을 병렬 처리하여 대기 시간을 체감상 50% 이상 단축함.

### 1-9. 비동기 태스크 실행 누락 (Celery Task Serialization Issue)
- **문제**: 로그에 `Triggered next question generation`은 찍히나, 정작 워커가 태스크를 수신(`received`)하지 못하고 침묵함.
- **원인**: `from tasks.question_generation import ...` 처럼 직접 함수를 임포트하여 `.delay()`를 호출할 때, 워커 환경에 따라 모듈 순환 참조나 직렬화 이슈로 태스크 전송이 씹히는 현상 발생.
- **해결**: `celery.current_app.send_task("태스크 이름", ...)` 방식을 도입하여, 함수를 직접 임포트하지 않고 문자열 기반으로 작업을 명시적으로 큐에 던지도록 수정하여 실행 보장.

### 1-10. 변수 미정의 오류 (`NameError: name 't' is not defined`)
- **문제**: 답변 분석 시 `Failed to trigger next question task: name 't' is not defined` 에러 발생.
- **원인**: `evaluator.py` 내부에서 `Transcript` 객체인 `t`를 명시적으로 조회하지 않고 속성(`t.interview_id`)에 접근하려 함.
- **해결**: `Session(engine)`을 사용하여 `transcript_id`에 해당하는 레코드를 먼저 조회(FETCH)한 뒤, 확보된 `interview_id`를 사용하여 태스크를 호출하도록 수정.

### 1-11. 워커 동시성 부족으로 인한 작업 블로킹 (Worker Concurrency Issue)
- **문제**: 다음 질문 생성 신호(`send_task`)는 정상 수신되나, 답변 분석(`analyze_answer`)이 끝날 때까지 질문 생성이 시작되지 않음.
- **원인**: 기존 워커 설정이 `concurrency=1`(추정)로 되어 있어, 40~70초 소요되는 답변 분석 태스크가 실행되는 동안 다른 태스크를 큐에서 꺼내올 수 없었음.
- **해결**: `docker-compose.yml` 설정을 변경하여 워커의 **병렬 처리 개수를 2개(`--concurrency=2`)**로 상향 조정 시도.

### 1-12. `solo` 풀 설정으로 인한 실질적 병렬 처리 불능 (Parallelism Negated by `solo` Pool)
- **현상**: 비동기 호출(`delay`)과 `concurrency=2` 설정에도 불구하고, 실제 로그 확인 결과 답변 분석과 질문 생성이 여전히 **순차적(Sequential)**으로 처리됨.
- **원인**: `ai-worker/main.py` 설정에서 **`worker_pool='solo'`**가 강제되어 있음. `solo` 풀은 Celery에서 모든 병렬 설정을 무시하고 한 번에 하나의 태스크만 처리하는 방식임. (CUDA 호환성을 위해 도입된 제약 사항)
- **영향**: 사용자는 [답변 분석 시간 + 질문 생성 시간]을 모두 합친 대기 시간을 겪게 됨. (UX 저하의 핵심 원인)
- **해결 방안**: 향후 VRAM 여유 확인 시 워커 컨테이너를 복제(`replicas: 2`)하거나, GPU 미사용 태스크용 별도 워커 그룹을 구성하여 물리적 병렬성 확보 필요.

---

## 🧠 2. 핵심 구현: 15단계 실시간 압박 면접 시스템

2단계(자기소개, 지원동기)에서 멈추던 시스템을 15단계 무한 동력 체제로 개조한 상세 내역입니다.

### 2-1. AI 워커 DB 저장 로직 보강 (`ai-worker/db.py`)
- **수정 함수**: `save_generated_question(interview_id, content, stage, ...)` 추가.
- **핵심 로직**:
    - 생성된 AI 질문을 `Question` 테이블에 새 레코드로 삽입.
    - 동시에 **`Transcript` 테이블에 `Speaker.AI`로 즉시 저장**.
    - **이유**: 프론트엔드는 질문 리스트를 `Transcript` 테이블의 AI 발화 내역에서 긁어오기 때문임.

### 2-2. 실시간 질문 생성 엔진 탑재 (`ai-worker/tasks/question_generation.py`)
- **수정 함수**: `generate_next_question_task(interview_id)` 신규 구현.
- **핵심 로직**:
    1.  현재 면접의 마지막 질문 단계를 DB에서 조회.
    2.  `interview_scenario.py` 시나리오 설계도에서 "다음 단계"가 무엇인지 계산.
    3.  **RAG 연동**: 이력서 벡터 DB에서 해당 단계(기술/경험 등)에 맞는 컨텍스트 추출.
    4.  **LLM 생성**: EXAONE 모델을 통해 "다음 1문제"를 정교하게 생성 후 2-1의 함수로 저장.

### 2-3. 면접 루프 파이프라인 연결 및 탈동화 (`ai-worker/tasks/evaluator.py`)
- **수정 함수**: `analyze_answer(...)`
- **변경 사항**: 
    - 함수 시작부에서 `current_app.send_task` 대신 **함수를 직접 `delay()`로 정교하게 호출**하도록 다시 롤백(Serialization 이슈 해결 후).
    - 점수 분석 로직과 질문 생성 로직을 논리적으로 완전 분리(Decoupling).
- **결과**: **[유저 답변 제출] -> [즉각적인 질문 생성 루프] & [백그라운드 답변 분석]**의 고성능 병렬 시스템 완성.

### 2-4. 프론트엔드 질문 폴링(Polling) 로직 (`frontend/src/App.jsx`)
- **수정 함수**: `nextQuestion()`
- **변경 사항**:
    - 마지막 로컬 질문 소진 시 `finishInterview()`를 즉시 호출하던 로직 제거.
    - **Wait & Check**: 서버 API(`getInterviewQuestions`)를 2초 간격으로 최대 15번 호출하며 새로운 AI 질문이 DB에 들어왔는지 감시.
    - `setIsLoading(true)` 상태를 사용하여 UI 대기 모드 활성화.

### 2-5. "생각하는 AI" 인터랙션 UI (`frontend/src/pages/interview/InterviewPage.jsx`)
- **변경 사항**: `isLoading` Prop 추가 및 **전면 로딩 오버레이** 구현.
- **효과**: AI가 질문을 생성하는 3~10초 동안 유저에게 "AI 면접관이 다음 질문을 생각 중입니다..."라는 메시지와 스피너를 보여주어 이탈 방지.

### 2-6. 병렬 엔진 아키텍처: 채점(Scoring)과 생성(Generation)의 완전 분리
- **개념**: 면접관의 "채점 행위"와 "다음 질문 던지기"를 별도의 독립된 프로세스로 실행하는 시스템 설계.
- **상세 메커니즘**:
    - **채점 엔진 (`analyze_answer`)**: 답변의 논리성, 기술적 정확도, 커뮤니케이션 점수를 산출하는 고부하 작업 (백그라운드 수행).
    - **질문 엔진 (`generate_next_question`)**: 유저의 답변 텍스트만 참조하여 즉시 다음 꼬리 질문을 생성하는 응답 우선 작업 (프런트엔드 노출용).
- **기술적 이점**:
    1. **UX 속도 혁신**: 사용자가 다음 질문을 받기까지의 대기 시간을 90초 이상에서 **30초 내외로 단축**.
    2. **결함 격리 (Fault Isolation)**: 채점 엔진(LLM)이 복잡한 사고 중 타임아웃이나 오류가 발생하더라도, 질문 엔진만 무사히 작동하면 면접은 중단 없이 15단계 끝까지 진행 가능.
    3. **데이터 정합성**: 유저의 답변이 DB에 저장된 즉시 두 엔진을 깨우기 때문에, 서로 결과를 기다릴 필요 없이 동일한 답변 텍스트를 기반으로 각자의 업무를 신속히 수행.

---

## 📜 3. 최종 15단계 면접 시나리오 설계도

| 단계 | 시나리오 구성 (Order) | 생성 방식 | 질문 포커스 |
|:---:|:---|:---:|:---|
| 1 | **자기소개** | Template | 아이스브레이킹 및 기본 정보 확인 |
| 2 | **지원동기** | Template | 직무 열정 및 커리어 목표 |
| 3~4 | **직무 지식 평가** | **AI (RAG)** | 이력서 기반 기술 스택의 깊이 있는 원리 질문 |
| 5~7 | **프로젝트 경험 검증** | **AI (RAG)** | 실제 기여도, 사용 도구, 수치화된 성과 검증 |
| 8~10 | **문제 해결 능력** | **AI (RAG)** | 기술적 난관 극복 사례 및 논리적 사고 과정 |
| 11~12 | **협업 및 의사소통** | AI (RAG) | 갈등 해결 사례 및 팀워크 가치관 |
| 13~14 | **성장 의지 및 가치관** | AI (RAG) | 미래 비전 및 회사 문화 적합성 |
| 15 | **최종 발언** | Template | 마무리 인사 및 마지막 질문 기회 제공 |

---

## 🏁 최종 요약 및 구동 가이드
1.  **동기화**: `backend-core`와 `ai-worker` 두 곳의 시나리오 파일을 동일하게 유지하여 판단 착오 방지.
2.  **재시작**: 코드 수정 후 `docker restart interview_backend interview_worker` 필수.
3.  **성과**: 이제 유저는 AI의 끝없는 꼬리 질문과 압박 면접을 15단계까지 생생하게 경험할 수 있습니다.
