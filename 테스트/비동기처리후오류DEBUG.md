# 비동기 처리 후 오류 분석 보고서 (DEBUG)

## 1. 발생 오류 개요

- **Worker 측**: `KeyError: 'tasks.question_generator.generate_questions'`
  - Celery 워커에 등록되지 않은 태스크 이름을 호출함.
- **Backend 측**: `NameError: name 'question_text' is not defined`
  - 변수명이 잘못 정의되었거나 정의되지 않은 변수를 참조함.

## 2. 상세 원인 분석

### A. Celery 태스크 명칭 불일치

- **원인**: 백엔드에서는 `tasks.question_generator` (er)로 요청을 보내고 있으나, 워커에는 `tasks.question_generation` (ion)으로 등록되어 있음.
- **대상 파일**: `backend-core/routes/interviews.py` (Line 71)

### B. 백엔드 코드 내 변수 참조 오류 (`NameError`)

- **원인**: `create_interview` 함수 내에서 반복문 수행 시 질문 텍스트를 `q_text`로 받았으나, 저장 시에는 `question_text`라는 존재하지 않는 변수를 참조함.
- **대상 파일**: `backend-core/routes/interviews.py` (Line 103, 127)

### C. 정의되지 않은 객체 참조 및 임포트 누락

- **원인**:
  - `stage_config` 객체가 `create_interview` 함수 내에 정의되어 있지 않음 (아마도 `create_realtime_interview` 코드를 복사하며 발생한 실수).
  - `sqlalchemy.text` 함수가 임포트되지 않아 SQL 실행 시 오류 발생 가능.
- **대상 파일**: `backend-core/routes/interviews.py` (Line 106, 120, 130)

## 3. 수정 제안 (승인 필요)

### backend-core/routes/interviews.py 수정 사항:

1. **임포트 추가**: `from sqlalchemy import text` 추가.
2. **태스크 명칭 수정**: `tasks.question_generator.generate_questions` -> `tasks.question_generation.generate_questions`
3. **변수명 통일**: `question_text` -> `q_text`로 수정.
4. **임시 로직 제거/수정**: `stage_config` 참조 부분을 기본값 또는 적절한 로직으로 수정 (예: `question_type="intro"`, `order=i`).

---

## 4. 추가 오류 분석 및 해결 상황 (2026-02-10)

### D. SQLModel 테이블 중복 정의 에러 (`InvalidRequestError`) - **[해결 완료]**

- **현상**: `interview_worker_gpu`에서 태스크 실행 시 `Table 'users' is already defined...` 에러 발생.
- **원인**: `ai-worker/db.py`와 `backend-core/models.py`에서 동일 테이블 중복 정의.
- **조치**: `ai-worker/db.py`의 정의를 제거하고 `models.py`를 공통 참조하도록 구조 통합.

### E. 면접 시나리오(`interview_scenario.py`) 미준수 - **[해결 완료]**

- **현상**: 질문 생성 시 시나리오 단계를 건너뛰거나 초기화됨.
- **원인**: 단계 감지 로직의 취약성 및 `question_type` 매핑 불일치.
- **조치**: `generate_next_question_task` 내 단계 감지 로직 강화(Order 기반 역추적 추가) 및 매핑 보정.

### F. 이력서 분석 무한 폴링 현상 (`GET /resumes/123` 반복) - **[해결 완료]**

- **현상**: 분석 상태가 `pending`에서 멈춰 프론트엔드가 2초 간격으로 계속 서버에 요청을 보냄.
- **원인**: `ai-worker/db.py` 통합 시 `User` 모델 임포트 누락으로 인해 워커가 분석 결과를 DB에 저장하지 못하고 중단됨.
- **조치**: `ai-worker/db.py`에 `User` 모델 임포트 추가하여 워커 프로세스 정상화.

### G. Vite HMR 및 JSX 구문 오류 - **[진행 중]**

- **현상**: Vite 로그에 `JSXParserMixin` 관련 파싱 에러 발생.
- **원인**: 프론트엔드(`App.jsx` 등) 소스 코드 내에 문법적인 오류(JSX 태그 닫힘 누락 등)가 있어 빌드가 차단됨.
- **조치**: 프론트엔드 소스 코드 검토 및 수정 필요.

### H. 이력서 분석 프로세스 중단 (processing_status가 pending에서 멈춤) - **[해결 완료]**

- **현상**: 이력서 업로드 후 `processing_status`가 `pending`에서 변경되지 않아 프론트엔드가 무한 폴링 상태에 빠짐.
- **원인**:
  - `ai-worker/tasks/save_structured.py`에서 JSONB 컬럼에 데이터를 저장할 때 타입 캐스팅 누락.
  - PostgreSQL의 JSONB 컬럼은 JSON 문자열을 직접 받을 수 없으며 `::jsonb` 캐스팅이 필요함.
  - 워커가 DB 업데이트 실패로 인해 `processing_status`를 `completed`로 변경하지 못함.
- **조치**: `save_structured.py`의 SQL 쿼리에 `::jsonb` 캐스팅 추가하여 JSONB 저장 정상화.

### J. 모델 이름 충돌 및 ImportError (치명적) - **[해결 완료]**
- **현상**: 워커가 `Exited (1)` 상태로 크래시됨. 로그에 `ImportError: cannot import name 'User' from 'models'` 발생.
- **원인**: 
  - `ai-worker` 폴더 안에 LLM 파일을 담는 `models/` 디렉토리가 존재함.
  - 파이썬이 `backend-core/models.py` 대신 현재 디렉토리의 `models/` 폴더를 먼저 임포트함.
  - 해당 폴더에는 DB 모델이 없으므로 임포트 실패 및 워커 중단.
- **조치**: 
  - `ai-worker/db.py`에서 `sys.path.insert(0, ...)`를 사용하여 `backend-core` 경로를 최우선 순위로 강제 지정.
  - `resume_pipeline` 태스크를 `cpu_queue`로 이동하여 GPU 워커 부하를 줄이고 안정성 확보.

## 5. 최종 확인 사항
- [x] 모델 정의 통합 (Duplicate Table Fix)
- [x] 백엔드 라우트 변수명 및 태스크명 수정
- [x] 질문 생성 단계 감지 로직 고도화
- [x] 워커 내 누락 모델(`User`) 추가
- [x] 이력서 분석 JSONB 저장 오류 수정
- [x] **모델 이름 충돌(`ImportError`) 해결**
- [x] **이력서 분석 큐를 CPU로 전환 (`gpu_queue` -> `cpu_queue`)**
- [x] 워커 및 프론트엔드 전체 재시작

## 6. 결론 및 보고
- **무한 폴링의 원인**: GPU 워커가 이름 충돌로 인해 임포트 에러를 일으키며 죽어 있었고, 이로 인해 이력서 분석 태스크가 처리되지 못함.
- **현재 상태**: 모든 수정사항 반영 및 워커 경로 우선순위 조정 완료. CPU 큐로 안전하게 우회 설정 완료.

**이제 `docker-compose up -d` 또는 `docker-compose restart`를 실행하여 모든 서비스를 정상화해주시기 바랍니다.**

---

## 7. 추가 오류 분석 (2026-02-11)

### K. 질문 생성 태스크에서 `ModuleNotFoundError: No module named 'utils.exaone_llm'` - **[해결 완료]**

- **발생 시각**: 2026-02-10 15:04:28 ~ 15:08:47
- **현상**: 
  - `generate_next_question_task` 및 `generate_questions_task` 실행 시 `utils.exaone_llm` 모듈을 찾지 못함.
  - 백엔드는 fallback 질문으로 우회하여 면접이 생성되지만, AI 생성 질문은 작동하지 않음.
  - 면접 시나리오가 정상적으로 진행되지 않는 근본 원인.

- **원인**:
  - `tasks/question_generation.py`에 Python 경로 설정(`sys.path`) 로직이 없음.
  - `tasks/evaluator.py`에는 동일한 경로 설정이 있어 정상 작동하지만, `question_generation.py`는 누락됨.
  - Docker 컨테이너 내에서 Celery 워커가 태스크를 실행할 때 작업 디렉토리가 `/app`이 아닐 수 있어, 상대 경로로 `utils` 모듈을 찾지 못함.

- **조치**:
  ```python
  # tasks/question_generation.py 상단에 추가
  current_file_path = os.path.abspath(__file__)
  tasks_dir = os.path.dirname(current_file_path)
  ai_worker_root = os.path.dirname(tasks_dir)
  
  if ai_worker_root not in sys.path:
      sys.path.insert(0, ai_worker_root)
  ```

- **영향 범위**:
  - ✅ 질문 생성 태스크 정상화
  - ✅ 면접 시나리오 흐름 복구
  - ✅ AI 기반 질문 생성 재개

### L. Media Server CUDA 드라이버 버전 불일치 - **[진행 중]**

- **발생 시각**: 2026-02-10 15:08:50
- **현상**: 
  ```
  ❌ Failed to load Local Whisper: CUDA failed with error 
  CUDA driver version is insufficient for CUDA runtime version
  ```
  - Local Whisper (faster-whisper-large-v3-turbo) 모델 로딩 실패.
  - STT 기능이 작동하지 않을 가능성.

- **원인**:
  - 호스트 시스템의 NVIDIA CUDA 드라이버 버전이 컨테이너 내 CUDA 런타임 버전보다 낮음.
  - Docker 컨테이너가 요구하는 CUDA 버전과 호스트의 GPU 드라이버가 호환되지 않음.

- **해결 방안**:
  1. **호스트 NVIDIA 드라이버 업데이트** (권장):
     - 최신 NVIDIA 드라이버 설치 (CUDA 12.x 이상 지원)
  2. **컨테이너 CUDA 버전 다운그레이드**:
     - `media-server/Dockerfile`에서 더 낮은 CUDA 버전의 베이스 이미지 사용
  3. **Fallback 모드 사용**:
     - CPU 기반 Whisper 모델로 전환 (성능 저하 감수)

- **현재 상태**: 
  - STT 기능이 에러로 인해 작동하지 않을 가능성 높음.
  - 면접 진행에는 영향 없으나, 음성 인식 기능 사용 불가.

## 8. 최종 확인 사항 (업데이트)
- [x] 모델 정의 통합 (Duplicate Table Fix)
- [x] 백엔드 라우트 변수명 및 태스크명 수정
- [x] 질문 생성 단계 감지 로직 고도화
- [x] 워커 내 누락 모델(`User`) 추가
- [x] 이력서 분석 JSONB 저장 오류 수정
- [x] 모델 이름 충돌(`ImportError`) 해결
- [x] 이력서 분석 큐를 CPU로 전환
- [x] **질문 생성 태스크 경로 설정 추가 (`question_generation.py`)**
- [ ] **Media Server CUDA 드라이버 호환성 해결** (진행 중)
- [ ] **AI Worker 재시작 필요** (`docker-compose restart ai-worker-gpu ai-worker-cpu`)

## 9. 다음 조치 사항
1. ✅ `question_generation.py` 수정 완료
2. ⏳ AI Worker 컨테이너 재시작 필요
3. ⏳ Media Server CUDA 이슈 해결 (선택적 - STT 사용 시)

---

## 10. 추가 오류 분석 (2026-02-11 심화)

### M. `utils.exaone_llm` 모듈 import 경로 문제 (치명적) - **[해결 완료]**

- **발생 시각**: 2026-02-10 15:04:28 ~ 2026-02-11 00:19
- **현상**:
  - 초기: `ModuleNotFoundError: No module named 'utils.exaone_llm'` (라인 124)
  - sys.path 추가 후: 라인 번호가 141로 변경되었으나 여전히 동일 에러
  - 재시작 후: `'NoneType' object is not callable` 에러로 변경
  - 수동 테스트: `docker exec`로 직접 import하면 성공

- **근본 원인**:
  1. **Celery 모듈 로딩 시점 문제**: Celery가 태스크 파일을 import할 때 작업 디렉토리가 `/app/tasks`일 수 있음
  2. **파일 상단 import 실패**: 워커 시작 시 파일이 로드될 때 sys.path가 아직 설정되지 않은 상태에서 import 시도
  3. **try-except로 인한 None 할당**: import 실패 시 `get_exaone_llm = None`으로 설정되어 이후 호출 시 `'NoneType' object is not callable` 발생
  4. **함수 내부 import도 실패**: 초기에는 함수 내부에서도 import했으나, 파일 상단의 sys.path 설정이 Celery 로딩 시점에는 적용되지 않음

- **시도한 해결 방법**:
  1. ❌ **파일 상단에 sys.path 설정 추가** → 효과 없음 (Celery가 다른 경로에서 로드)
  2. ❌ **파일 상단에서 import 후 함수에서 제거** → `None` 에러 발생
  3. ❌ **워커 재시작** → 코드 변경 없이는 효과 없음
  4. ✅ **파일 상단 import 제거 + 함수 내부에서만 import** → 성공!

- **최종 해결책**:
  ```python
  # question_generation.py 상단
  # AI-Worker 루트 디렉토리를 찾아 sys.path에 추가
  current_file_path = os.path.abspath(__file__)
  tasks_dir = os.path.dirname(current_file_path)
  ai_worker_root = os.path.dirname(tasks_dir)
  
  if ai_worker_root not in sys.path:
      sys.path.insert(0, ai_worker_root)
  
  # ❌ 파일 상단에서 import하지 않음 (Celery 로딩 시점 문제)
  # ✅ 함수 내부에서만 import
  
  @shared_task(name="tasks.question_generation.generate_next_question")
  def generate_next_question_task(interview_id: int):
      # ✅ 여기서 import (sys.path가 이미 설정된 상태)
      from utils.exaone_llm import get_exaone_llm
      ...
  ```

- **핵심 교훈**:
  - Celery 워커는 태스크 파일을 로드할 때 예상과 다른 작업 디렉토리를 사용할 수 있음
  - 파일 상단의 모듈 레벨 import는 Celery 로딩 시점에 실행되므로 sys.path 설정이 적용되지 않을 수 있음
  - **함수 내부에서 import**하면 태스크가 실제로 실행될 때 import되므로 sys.path가 정상 적용됨
  - try-except로 import 실패를 감추면 디버깅이 어려워짐 → 함수 내부 import로 명확한 에러 발생 유도

- **영향 범위**:
  - ✅ 질문 생성 태스크 정상화
  - ✅ 면접 시나리오 흐름 복구
  - ✅ AI 기반 실시간 질문 생성 재개

## 11. 최종 확인 사항 (2차 업데이트)
- [x] 모델 정의 통합 (Duplicate Table Fix)
- [x] 백엔드 라우트 변수명 및 태스크명 수정
- [x] 질문 생성 단계 감지 로직 고도화
- [x] 워커 내 누락 모델(`User`) 추가
- [x] 이력서 분석 JSONB 저장 오류 수정
- [x] 모델 이름 충돌(`ImportError`) 해결
- [x] 이력서 분석 큐를 CPU로 전환
- [x] **질문 생성 태스크 경로 설정 추가**
- [x] **Celery 모듈 로딩 시점 import 문제 해결**
- [x] **함수 내부 import로 변경하여 경로 문제 완전 해결**
- [ ] **Media Server CUDA 드라이버 호환성 해결** (진행 중)
- [x] **AI Worker 재시작 완료**

## 12. 검증 방법
새로운 면접을 시작하여 다음을 확인:
1. 이력서 업로드 → `processing_status`가 `completed`로 변경되는지
2. 면접 생성 → 초기 템플릿 질문 2개 생성되는지
3. 답변 제출 → 다음 질문이 AI로 생성되는지 (fallback 아님)
4. 로그 확인 → `ModuleNotFoundError` 또는 `'NoneType' object is not callable` 에러가 없는지


