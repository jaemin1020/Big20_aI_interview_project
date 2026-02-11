# AI 워커 및 백엔드 연동 작업 요약 (Implementation Summary)

이 문서는 이력서 파싱부터 면접 질문 생성까지의 과정을 웹 서비스에 연동하기 위해 수정된 사항들을 정리한 보고서입니다.

## 1. 파일명 구조 개선 (Renaming & Cleaning)
기존의 단계별 파일명(`step2_`, `step3_` 등)을 직관적이고 표준적인 명칭으로 변경하여 유지보수성을 높였습니다.

| 기존 파일명 | 변경된 파일명 | 주요 역할 |
| :--- | :--- | :--- |
| `step2_parse_resume.py` | `parse_resume.py` | PDF 텍스트 및 표 구조 추출 |
| `step3_save_structured.py` | `save_structured.py` | 추출된 데이터를 관계형 DB에 저장 |
| `step4_chunking.py` | `chunking.py` | 텍스트를 의미 단위(Chunk)로 분할 |
| `step5_embedding.py` | `embedding.py` | 한국어 임베딩 모델을 이용한 벡터화 |
| `step6_pgvector_store.py` | `pgvector_store.py` | 변환된 벡터를 pgvector DB에 저장 |
| `step7_rag_retrieval.py` | `rag_retrieval.py` | 질문에 필요한 이력서 문맥 검색 (RAG) |
| `step8_question_generation.py` | `question_generation.py` | LLM(EXAONE) 기반 맞춤형 질문 생성 |

## 2. 핵심 수정 및 추가 사항

### ① 이력서 처리 통합 파이프라인 구축 (`tasks/resume_pipeline.py` 신규)
*   **기존**: 각 단계를 수동으로 하나씩 실행해야 했음.
*   **수정**: `parse` → `save` → `chunk` → `embed` → `store` 과정을 하나의 **비동기 통합 태스크(`process_resume_pipeline`)**로 구현했습니다. 이제 이력서 업로드 시 이 모든 과정이 한 번의 호출로 끝납니다.

### ② Celery 워커 태스크 등록 (`ai-worker/main.py`, `__init__.py`)
*   **수정**: 변경된 파일명들을 Celery 앱의 `include` 리스트에 반영하여 워커가 정상적으로 인식하도록 했습니다.
*   **수정**: `shared_task` 데코레이터를 사용하여 백엔드에서 원격 호출이 가능한 구조로 만들었습니다.

### ③ 백엔드(FastAPI) API 연동 (`backend-core/routes/`)
*   **이력서 API (`resumes.py`)**: 
    *   기존의 단순 파싱 태스크 호출을 **통합 파이프라인 태스크** 호출로 변경했습니다.
    *   재처리(`reprocess`) 기능에서도 동일한 파이프라인을 타도록 수정했습니다.
*   **인터뷰 API (`interviews.py`)**: 
    *   질문 생성 시 기존의 더미 로직 대신, 수정된 **RAG 기반 질문 생성 태스크**를 호출하도록 연동했습니다.
    *   호출 시 `resume_id`를 전달하여 해당 지원자의 실제 이력서 기반으로 질문이 생성됩니다.

### ④ DB 상태 업데이트 로직 보강
*   **수정**: `resume_pipeline` 내부에서 작업의 시작, 성공, 실패 여부를 DB의 `resumes` 테이블(`processing_status`)에 실시간으로 반영하도록 수정했습니다.

## 3. 코드 내부 참조 수정
*   모든 파일 내에서 `from stepX_... import ...` 구문을 변경된 파일명에 맞춰 일괄 수정하여 임포트 오류를 해결했습니다.
*   `sys.path` 설정 등을 최적화하여 Docker 환경과 로컬 환경 모두에서 범용적으로 작동하도록 조정했습니다.

## 4. 실행 환경 갱신 및 주의사항 (Troubleshooting)

코드 수정 후 웹 서비스에 즉시 반영되지 않는 경우, 다음 사항을 점검해야 합니다.

### ① Celery 워커 메모리 캐싱 문제
*   **증상**: 코드를 수정했음에도 로그에 `EXAONE으로 3개 질문 생성`과 같은 구형 로직의 메시지가 출력됨.
*   **원인**: Celery 워커는 실행 시점의 코드를 메모리에 상주시키므로, 파일이 바뀌어도 워커를 재시작하지 않으면 예전 코드를 계속 사용합니다.
*   **해결**: `docker restart interview_worker` (또는 전체 컨테이너 재시작) 명령어를 통해 워커 프로세스를 새로 갱신해야 합니다.

### ② 백엔드 서비스 갱신
*   **원인**: API 엔드포인트(`interviews.py`)에서 호출하는 태스크 이름이 바뀌었으므로, 백엔드 서버(`interview_backend`)도 새로운 로직을 가리키도록 재시작이 필요합니다.

### ③ 구형 모듈(Legacy) 정리
*   **주의**: 기존의 `question_generator.py`나 `resume_parser.py` 등 `step_` 접두사가 붙어있던 구형 파일들이 남아 있으면 Celery가 태스크를 인지할 때 혼선이 생길 수 있으므로 삭제를 권장합니다.

## 5. 최근 발생 오류 분석 (TypeError 상세)

최근 질문 생성 과정에서 발생한 `TypeError: generate_questions_task() takes from 1 to 3 positional arguments but 4 were given` 오류에 대한 분석 결과입니다.

### ① 발생 원인: 인자(Argument) 불일치
*   **백엔드 호출부 (`interviews.py`)**: `celery_app.send_task` 호출 시 4개의 인자를 전달합니다.
    *   `args=[position, interview_id, 5, resume_id]`
*   **워커 정의부 (`question_generation.py`)**: 현재 작성된 함수는 최대 3개의 인자만 받도록 설정되어 있습니다.
    *   `def generate_questions_task(candidate_name, resume_id=1, count=6)`
*   **결과**: 인자 개수가 맞지 않아 Celery 실행 단계에서 즉시 오류가 발생하며 Fallback(기본 질문) 로직이 작동하게 됩니다.

### ② 반환 형식(Return Type) 문제 (잠재적 오류)
*   **현재 워커**: `[{"stage": "...", "question": "..."}]` 형태의 딕셔너리 리스트를 반환합니다.
*   **백엔드 기대치**: 질문 텍스트만 모인 문자열 리스트 `["질문1", "질문2", ...]`를 기대합니다.
*   **결과**: 인자 문제가 해결되더라도, 반환 형식을 맞추지 않으면 DB 저장 단계에서 데이터 형식이 맞지 않아 2차 오류가 발생할 수 있습니다.

### ③ 해결 방안
*   워커 태스크의 함수 서명을 `(position, interview_id, count=5, resume_id=1)`로 변경하고, 반환값을 질문 텍스트 리스트로 가공하여 전달해야 합니다.

## 6. 성함 및 지원 직무 파악 문제 분석

연동 후 발생한 "지원자 성함 및 직무 파악 미흡" 문제에 대한 정밀 분석 결과입니다.

### ① 지원자 성함 하드코딩 문제
*   **현상**: 이력서가 "최승우" 지원자의 것이더라도 질문 생성 시 항상 "**지원자님,**"으로 호칭함.
*   **원인**: `question_generation.py` 내부의 `generate_questions_task` 함수에서 `candidate_name = "지원자"`로 하드코딩되어 있습니다. 
*   **해결**: `resume_id`를 사용하여 DB(`resumes` 테이블)를 조회하고, `structured_data` 내의 실제 성함을 가져와야 합니다.

### ② 지원 직무(Position) 파악 미흡
*   **현상**: 로그에 `Position: General`로 찍히며 직무 특화 질문이 부족함.
*   **원인**: 
    1.  프론트엔드/백엔드에서 세션 생성 시 직무를 명시하지 않아 기본값인 `General`이 전달됨.
    2.  AI 워커가 전달받은 `position` 값만 사용할 뿐, 이력서 내의 `target_role`("보안엔지니어" 등)을 능동적으로 매칭하지 않음.
*   **해결**: 백엔드에서 온 값이 `General`일 경우, 이력서 데이터에서 지원 직무를 추출해 AI 워커의 면접 직무로 자동 보정하는 로직이 필요합니다.

### ③ 질문 가독성 문제 (Placeholders)
*   **현상**: 생성된 질문에 `[프로젝트]`와 같은 대문자 플레이스홀더가 그대로 노출됨.
*   **원인**: LLM 프롬프트에서 컨텍스트를 제공할 때, 이력서의 특정 프로젝트 이름을 명확히 지칭하도록 하는 가이드가 부족함.
*   **해결**: 프롬프트의 `[질문 스타일 가이드]`를 강화하여 구체적인 프로젝트 명칭을 문맥에 녹여내도록 지시해야 합니다.

## 7. 질문 생성 타임아웃(Timeout) 및 폴백(Fallback) 발생 분석

면접 시작 시 AI 질문 대신 기본 질문(General 직무 동기 등)이 출력되는 문제에 대한 분석입니다.

### ① 발생 원인: 백엔드 대기 시간 부족
*   **현상**: 웹 화면에서 질문 생성을 기다리다가 갑자기 기본 질문 리스트가 화면에 표시됨.
*   **원인**: `backend-core/routes/interviews.py`에서 AI 워커의 응답을 기다리는 타임아웃이 180초(3분)로 설정되어 있었습니다. 그러나 실제 로컬 LLM을 통한 질문 5개 생성 시간은 약 400초(약 6~7분)가 소요되어, 백엔드가 기다리지 못하고 예외 처리(Fallback) 로직을 실행한 것입니다.
*   **결과**: AI 워커는 뒤늦게 질문 생성을 완료하지만, 백엔드는 이미 타임아웃이 되어 기본 질문을 DB에 저장해버린 상태가 됩니다.

### ② 해결 방안
*   **백엔드 수정**: `interviews.py` 내 `task.get(timeout=180)` 값을 `600`(10분)으로 대폭 늘려 LLM이 충분히 질문을 생성할 시간을 확보했습니다.
*   **리프레시**: 수정 후 `docker restart interview_backend`를 통해 설정을 적용했습니다.

## 8. 백엔드 로직 누락 및 폴백(Fallback) 정책 수정 분석

타임아웃 수정 과정에서 발생한 백엔드 명령 누락 및 질문 생성 실패 시의 처리 방식 변경에 대한 분석입니다.

### ① 발생 원인: AI 워커 호출 명령(send_task) 누락
*   **현상**: 백엔드 타임아웃을 늘렸음에도 계속해서 "General" 기본 질문이 출력됨.
*   **원인**: `interviews.py` 수정 중 `celery_app.send_task(...)` 로직이 실수로 삭제되었습니다. 이로 인해 백엔드는 워커에게 일을 시키지 않은 채 빈 결과를 기다리다 타임아웃이 발생했고, 결국 예외 처리 로직인 '기본 질문 생성'으로 강제 진행되었습니다.

### ② 폴백(Fallback) 정책의 문제점 지적
*   **현상**: AI 질문 생성이 안 될 경우 "General 직무 지원동기" 등 준비된 질문으로 면접이 시작됨.
*   **문제점**: 사용자(면접자) 입장에서는 맞춤형 AI 질문을 기대했으나, 시스템이 임의로 일반적인 질문을 내보내면 서비스의 신뢰도가 떨어지고 데이터 싱크가 맞지 않게 됩니다.

### ③ 해결 방안 및 수정 사항
*   **명령 복구**: 삭제되었던 `send_task` 코드를 복구하여 AI 워커가 정상적으로 질문 생성을 시작하도록 수정했습니다.
*   **엄격한 실패 처리**: 질문 생성 실패 시 기본 질문으로 대체하는 폴백 로직을 **폐기**했습니다. 이제 AI 질문 생성에 실패하면 `HTTP 500` 에러를 반환하며 면접 생성을 중단합니다. 또한, 생성 도중 에러가 나면 이미 DB에 만들어진 면접(Interview) 레코드도 자동으로 삭제(Rollback)하도록 로직을 강화했습니다.

## 9. 실시간 대화형 면접 시스템 구현 계획

기존의 "질문 6개 사전 생성 후 일괄 제공" 방식에서 "실시간 질문 생성 및 꼬리질문 지원" 방식으로 전환하는 대규모 리팩토링 계획입니다.

### ① 현재 시스템의 문제점
*   **긴 대기 시간**: 면접 시작 시 질문 6개를 모두 생성하는 데 6~7분 소요 → 사용자 이탈 위험
*   **정적인 질문 구조**: 미리 정해진 질문만 제공 → 답변 기반 꼬리질문 불가능
*   **비현실적인 면접 경험**: 로봇 같은 느낌, 실제 면접과 동떨어짐

### ② 새로운 면접 시나리오 설계

**15단계 실시간 면접 플로우:**

| 순서 | 단계 | 질문 타입 | 생성 방식 | 예상 대기 시간 |
|------|------|----------|----------|--------------|
| 1 | 자기소개 | 템플릿 | DB 조회 후 변수 삽입 | 0초 |
| 2 | 지원동기 | 템플릿 | DB 조회 후 변수 삽입 | 0초 |
| 3 | 직무 지식 평가 | AI 생성 | RAG + LLM | 30초~1분 |
| 4 | └ 꼬리질문 | AI 생성 | 답변 분석 + LLM | 30초~1분 |
| 5 | 직무 경험 평가 | AI 생성 | RAG + LLM | 30초~1분 |
| 6 | └ 꼬리질문 | AI 생성 | 답변 분석 + LLM | 30초~1분 |
| 7 | 문제 해결 능력 | AI 생성 | RAG + LLM | 30초~1분 |
| 8 | └ 꼬리질문 | AI 생성 | 답변 분석 + LLM | 30초~1분 |
| 9 | 의사소통/협업 | AI 생성 | RAG + LLM | 30초~1분 |
| 10 | └ 꼬리질문 | AI 생성 | 답변 분석 + LLM | 30초~1분 |
| 11 | 책임감/가치관 | AI 생성 | RAG + LLM | 30초~1분 |
| 12 | └ 꼬리질문 | AI 생성 | 답변 분석 + LLM | 30초~1분 |
| 13 | 성장의지 | AI 생성 | RAG + LLM | 30초~1분 |
| 14 | └ 꼬리질문 | AI 생성 | 답변 분석 + LLM | 30초~1분 |
| 15 | 최종 발언 | 템플릿 | 고정 문구 | 0초 |

**질문 개인화 예시:**
- 기존: "간단히 자기소개 부탁드립니다."
- 개선: "**최승우 지원자님**, 간단히 자기소개 부탁드립니다."
- 기존: "지원 동기를 말씀해주세요."
- 개선: "**최승우 지원자님**, 지원하신 직무인 **'보안엔지니어'**에 지원하게 된 동기는 무엇입니까?"

### ③ 구현 계획 상세

#### A. 데이터베이스 스키마 확장
**수정 대상:** `backend-core/models.py`

**추가 컬럼:**
```python
# Question 테이블
- stage_type: String  # "intro", "motivation", "skill", "skill_followup", ...
- parent_question_id: Integer (nullable)  # 꼬리질문의 경우 원본 질문 ID
- requires_ai: Boolean  # AI 생성 필요 여부
- generation_time: Float  # 질문 생성 소요 시간 (성능 모니터링용)
```

#### B. 백엔드 API 재설계
**수정 대상:** `backend-core/routes/interviews.py`

**기존 API:**
- `POST /interviews` → 면접 생성 + 질문 6개 사전 생성 (6~7분 대기)

**새로운 API 구조:**
1. `POST /interviews` → 면접 생성 + 템플릿 질문 2개만 즉시 반환 (0초)
2. `POST /interviews/{id}/next-question` → 실시간 다음 질문 생성 (신규)
   - Request: `{"previous_answer": "...", "current_stage": "skill"}`
   - Response: `{"question_id": 123, "content": "...", "stage": "skill_followup"}`
3. `GET /interviews/{id}/status` → 현재 진행 상태 조회 (신규)

#### C. AI 워커 태스크 분리
**수정 대상:** `ai-worker/tasks/question_generation.py`

**기존:**
- `generate_questions_task()` → 질문 5개 일괄 생성

**신규 태스크:**
1. `generate_single_question()` → 단일 질문 생성 (30초~1분)
   - stage_type에 따라 RAG 검색 카테고리 자동 매핑
   - 지원자 정보(이름, 직무) DB 조회 후 프롬프트에 포함
2. `generate_followup_question()` → 꼬리질문 생성 (30초~1분)
   - 이전 답변을 evaluator로 분석
   - 부족한 부분, 모호한 부분을 파악하여 추가 질문 생성

#### D. 면접 시나리오 설정 파일
**신규 파일:** `ai-worker/config/interview_scenario.py`

```python
INTERVIEW_STAGES = [
    {
        "stage": "intro",
        "type": "template",
        "template": "{candidate_name} 지원자님, 간단히 자기소개 부탁드립니다.",
        "variables": ["candidate_name"]
    },
    {
        "stage": "motivation",
        "type": "template",
        "template": "{candidate_name} 지원자님, 지원하신 직무인 '{target_role}'에 지원하게 된 동기는 무엇입니까?",
        "variables": ["candidate_name", "target_role"]
    },
    {
        "stage": "skill",
        "type": "ai",
        "category": "certification",
        "guide": "지원자가 사용한 기술의 구체적인 설정법이나 기술적 원리를 물어볼 것."
    },
    # ... (총 15단계)
]
```

#### E. 헬퍼 함수 추가
**신규 파일:** `backend-core/utils/interview_helpers.py`

**주요 함수:**
- `get_candidate_info(db, resume_id)` → 이력서에서 이름, 직무 추출
- `generate_template_question(template, variables)` → 템플릿 변수 치환
- `get_next_stage(current_stage)` → 다음 면접 단계 결정

### ④ 예상 효과

| 항목 | 현재 | 개선 후 |
|------|------|---------|
| 첫 질문까지 대기 시간 | 6~7분 | **0초** |
| 질문당 평균 대기 시간 | - | 30초~1분 |
| 전체 면접 소요 시간 | 7분(대기) + 15분(답변) = 22분 | 15분(답변) + 5분(생성) = 20분 |
| 사용자 경험 | 로봇 같음, 정적 | **실제 면접 느낌, 동적** |
| 꼬리질문 지원 | ❌ | ✅ |
| 답변 기반 질문 조정 | ❌ | ✅ |

### ⑤ 구현 순서
1. DB 스키마 수정 및 마이그레이션
2. 시나리오 설정 파일 작성
3. 백엔드 헬퍼 함수 구현
4. 면접 생성 API 수정 (템플릿 질문 즉시 반환)
5. AI 워커 단일 질문 생성 태스크 구현
6. 백엔드 실시간 질문 생성 API 구현
7. 프론트엔드 연동 (WebSocket 또는 Polling)
8. 통합 테스트 및 최적화

## 10. 실시간 면접 시스템 구현 중 발생한 오류 및 해결

### ① utils 모듈 임포트 오류

**오류:**
```
ModuleNotFoundError: No module named 'utils.exaone_llm'
```

**발생 위치:** `ai-worker/tasks/evaluator.py`

**원인:**
- `ai-worker/utils/` 디렉토리에 `__init__.py` 파일이 없어 Python이 해당 디렉토리를 패키지로 인식하지 못함
- `evaluator.py`에서 `from utils.exaone_llm import get_exaone_llm` 임포트 실패

**해결:**
1. **`ai-worker/utils/__init__.py` 생성** (신규)
   ```python
   from .exaone_llm import get_exaone_llm
   __all__ = ["get_exaone_llm"]
   ```

2. **`ai-worker/tasks/evaluator.py` 수정**
   ```python
   # 상위 디렉토리(ai-worker)를 경로에 추가
   parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
   if parent_dir not in sys.path:
       sys.path.insert(0, parent_dir)
   from utils.exaone_llm import get_exaone_llm
   ```

### ② 실시간 면접 시스템 1차 구현 완료

**구현된 파일:**

1. **`ai-worker/config/interview_scenario.py`** (신규)
   - 15단계 면접 시나리오 정의
   - 템플릿 질문 (자기소개, 지원동기) + AI 생성 질문 13개 구조
   - 각 단계별 RAG 검색 카테고리 및 가이드 명시

2. **`backend-core/utils/interview_helpers.py`** (신규)
   - `get_candidate_info()`: 이력서 DB에서 지원자 성함 및 직무 추출
   - `generate_template_question()`: 템플릿 문자열에 변수 치환
   - `get_next_stage_name()`: 다음 면접 단계 조회

3. **`backend-core/routes/interviews.py`** (수정)
   - 기존 `POST /interviews` 엔드포인트 로직 변경
   - **변경 전**: AI 워커에 질문 5개 요청 → 6~7분 대기 → 반환
   - **변경 후**: DB 조회 → 템플릿 질문 2개 즉시 생성 → 0초 대기 → 반환

**개인화된 질문 예시:**
- 기존: "간단히 자기소개 부탁드립니다."
- 개선: "**최승우 지원자님**, 간단히 자기소개 부탁드립니다."
- 기존: "지원 동기를 말씀해주세요."
- 개선: "**최승우 지원자님**, 지원하신 직무인 **'보안엔지니어'**에 지원하게 된 동기는 무엇입니까?"

**성능 개선:**
| 항목 | 기존 | 개선 후 |
|------|------|---------|
| 첫 질문까지 대기 시간 | 6~7분 | **0초** |
| 면접 시작 즉시성 | ❌ | ✅ |
| 지원자 정보 개인화 | ❌ | ✅ (이름, 직무 반영) |

### ③ 향후 작업 (미완료)

실시간 면접 시스템의 완전한 구현을 위해 다음 작업이 추가로 필요합니다:

1. **AI 워커 단일 질문 생성 태스크 추가**
   - `generate_single_question()`: 답변 제출 시 다음 질문 1개만 생성
   - `generate_followup_question()`: 답변 분석 후 꼬리질문 생성

2. **백엔드 실시간 질문 생성 API 추가**
   - `POST /interviews/{id}/next-question`: 답변 제출 시 다음 질문 요청
   - Request: `{"previous_answer": "...", "current_stage": "skill"}`
   - Response: `{"question_id": 123, "content": "...", "stage": "skill_followup"}`

3. **프론트엔드 연동**
   - 답변 제출 시 `/next-question` API 호출
   - 로딩 UI 개선 ("AI가 답변을 분석하고 있습니다...")

---
**보고서 수정 일자**: 2026-02-09
**담당**: Antigravity AI Assistant
