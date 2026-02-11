# 🚨 비동기 처리 및 이력서 데이터 흐름 오류 분석 리포트

본 문서는 이력서 업로드 후 질문 생성 과정에서 발생한 데이터 흐름 단절 및 비동기 워커 오류를 분석하고 수정한 내용을 정리합니다.

---

## 1. 🛑 주요 발견 문제 (Root Causes)

### A. 데이터 원천의 불일치 (Source of Truth Conflict)

- **문제**: 면접 질문 생성 시 프론트엔드에서 입력한 `position` 값을 우선적으로 사용함.
- **결과**: 이력서에는 '보안엔지니어'라고 적혀 있어도, 사용자가 웹에서 실수로 '백엔드'라고 입력하면 AI가 이력서와 관련 없는 백엔드 질문을 던짐.

### B. DB 컬럼 매핑 및 데이터 구조 오류

- **문제 1**: `resumes` 테이블에 존재하지 않는 `target_role` 또는 `target_position` 컬럼에 직접 업데이트를 시도하여 `UndefinedColumn` 에러 발생.
- **문제 2**: 파싱 데이터 내부 키 명칭 혼선 (`metadata` vs `header`). `save_structured`는 `metadata`를 찾고, `parse_resume`은 `header`를 생성하여 데이터 누락 발생.

### C. 비동기 워커(Celery) 환경 설정 오류

- **문제**: 워커 내에서 `utils`, `db` 모듈을 로드할 때 `ModuleNotFoundError` 발생. Docker 환경의 `/app` 경로가 `sys.path`에 우선순위로 잡히지 않음.

---

## 2. 🛠 코드 수정 내역 (Fix Details)

### [1] 이력서 파싱 및 저장 로직 통일

- **파일**: `ai-worker/tasks/parse_resume.py`, `save_structured.py`
- **수정**: 모든 추출 데이터는 `header`라는 키로 통일하여 JSONB(`structured_data`) 컬럼에 저장.

```python
# save_structured.py
header = parsed_data.get("header", {})
candidate_name = header.get("name")
# resumes 테이블의 structured_data(JSONB) 컬럼만 업데이트하여 무결성 유지
```

### [2] 백엔드 면접 생성 로직 교정 (프론트 의존성 제거)

- **파일**: `backend-core/routes/interviews.py`
- **수정**: 면접 생성(`POST /realtime`) 호출 시, 브라우저가 보낸 직무명을 무시하고 DB에서 이력서를 먼저 읽어 `target_role`을 강제 주입.

```python
# interviews.py
candidate_info = get_candidate_info(db, interview_data.resume_id)
target_role = candidate_info.get("target_role", "일반")
new_interview = Interview(position=target_role, ...) # 이력서 값으로 고정
```

### [3] 질문 생성 태스크 최적화 및 변수명 통일

- **파일**: `ai-worker/tasks/question_generation.py`, `utils/exaone_llm.py`
- **수정 1**: `generate_questions_task`에서 `position` 인자를 삭제하고 `interview_id`를 통해 DB에서 직접 이력서 정보를 pull-through 하도록 수정.
- **수정 2**: `real_role`, `position` 등으로 산재해 있던 변수명을 이력서 파싱 규격인 **`target_role`**로 전면 통합.

```python
# question_generation.py
def generate_questions_task(interview_id, count=5):
    # ... DB 조회 로직 ...
    target_role = header.get("target_role")
    return exaone.generate_questions(target_role, context=resume_context)
```

---

## 3. 📉 데이터 흐름 요약 (After Fix)

1. **PDF 파싱**: `parse_resume.py` -> `target_role` 추출.
2. **구조화 저장**: `save_structured.py` -> `resumes.structured_data` (JSONB)에 저장.
3. **세션 생성**: `interviews.py` -> DB에서 `target_role`을 읽어 면접 세션의 주인으로 설정.
4. **질문 생성**: `question_generation.py` -> 면접 세션에 고정된 `target_role`을 바탕으로 AI 질문 제조.

## 4. 🚀 향후 점검 사항

- CUDA 드라이버 버전 불일치로 인한 STT 오류 (별도 인프라 작업 필요).
- 워커 간의 시각 동기화(Clock Drift) 문제 모니터링.

**작성자**: Antigravity AI
**날짜**: 2026-02-11
