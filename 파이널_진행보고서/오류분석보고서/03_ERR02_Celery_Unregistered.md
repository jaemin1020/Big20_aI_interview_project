# ERR-02: Celery Unregistered Task 오류

- **오류 코드**: ERR-02  
- **카테고리**: Celery / 태스크 큐  
- **심각도**: 🔴 HIGH  
- **상태**: ✅ 해결 완료  
- **관련 파일**: `ai-worker/main.py`, `ai-worker/tasks/question_generator.py`

---

## 3.2.1 문제 정의

면접 시작 시 EXAONE 모델 사전 로딩을 위해 `preload_model` 태스크를 GPU 워커에 전송했으나, 워커가 해당 태스크를 인식하지 못하는 오류가 발생하였습니다.

- **에러 메시지**: `Received unregistered task of type 'tasks.question_generation.preload_model'`
- **재현 조건**: 면접 시작 API 호출 시 `preload_model_task.delay()` 실행 때마다 발생
- **발생 위치**: GPU 워커 로그

---

## 3.2.2 문제 영향 분석

- **서비스 영향**: 모델 사전 로딩 불가로 첫 질문 생성 시 15~30초 추가 지연 발생
- **사용자 영향**: 면접 시작 후 첫 질문까지 대기 시간 증가
- **워커 영향**: 태스크 수신 오류 메시지가 반복 출력되어 로그 오염

---

## 3.2.3 문제 파악 과정

**원인 분석**:

`question_generator.py`에서 태스크 이름이 `tasks.question_generation.preload_model`로 등록되어 있었으나, `main.py`의 `include` 목록에는 `tasks.question_generator`(파일명)로 등록되어 있어 모듈 경로 불일치 발생.

```python
# [문제 코드] question_generator.py L71
@shared_task(name="tasks.question_generation.preload_model")
#                        ↑ 'generation' (잘못된 이름)

# [문제 코드] main.py L43
include=['tasks.question_generator', ...]
#                  ↑ 'generator' (파일명 기준)
```

또한 `task_routes`에서도 동일한 불일치 발생:

```python
# main.py L68
task_routes = {
    'tasks.question_generation.*': {'queue': 'gpu_queue'},  # 'generation'
    'tasks.question_generator.*':  {'queue': 'gpu_queue'},  # 'generator' (중복)
}
```

두 패턴이 동시에 존재했으나 실제 태스크 이름(`tasks.question_generation.preload_model`)과 워커 등록 경로(`tasks.question_generator`)가 불일치했습니다.

---

## 3.2.4 해결 접근 전략

- 태스크 이름(`@shared_task name=`)과 `include` 경로, `task_routes` 패턴을 모두 일관되게 통일
- 태스크 이름은 실제 파일 모듈 경로 기준으로 정렬

---

## 3.2.5 해결 도출 및 실행

```python
# [수정 후] question_generator.py L71
@shared_task(name="tasks.question_generator.preload_model")
#                         ↑ 'generator'로 통일

# [수정 후] main.py - task_routes 중복 제거 및 통일
task_routes = {
    'tasks.question_generator.*': {'queue': 'gpu_queue'},  # 단일 패턴으로 통일
    'tasks.resume_embedding.*':   {'queue': 'gpu_queue'},
    'tasks.evaluator.analyze_answer':      {'queue': 'gpu_queue'},
    'tasks.evaluator.generate_final_report': {'queue': 'gpu_queue'},
    'tasks.evaluator.finalize_report_task':  {'queue': 'gpu_queue'},
    # CPU 태스크
    'tasks.evaluator.*': {'queue': 'cpu_queue'},  # 위의 GPU 태스크 외 나머지
    'tasks.stt.*':        {'queue': 'cpu_queue'},
    'tasks.tts.*':        {'queue': 'cpu_queue'},
    'tasks.vision.*':     {'queue': 'cpu_queue'},
    'tasks.resume_parser.*': {'queue': 'cpu_queue'},
}
```

---

## 3.2.6 해결 결과

- **Before**: `preload_model` 태스크 전송 시 `Unregistered task` 오류 발생
- **After**: 태스크 이름 통일 후 GPU 워커가 정상적으로 태스크 수신 및 실행
- **교훈**: Celery 태스크 등록 시 `@shared_task(name=...)`, `include` 경로, `task_routes` 패턴을 반드시 동일한 네이밍 규칙으로 관리해야 함
