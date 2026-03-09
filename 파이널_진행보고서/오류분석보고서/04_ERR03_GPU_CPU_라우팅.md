# ERR-03: GPU/CPU 태스크 라우팅 충돌 오류

- **오류 코드**: ERR-03  
- **카테고리**: Celery / 태스크 큐  
- **심각도**: 🔴 HIGH  
- **상태**: ✅ 해결 완료  
- **관련 파일**: `ai-worker/main.py`

---

## 3.2.1 문제 정의

Celery 다중 워커 구조에서 GPU 전용 태스크(질문 생성, 평가 등)가 CPU 워커로 라우팅되거나, CPU 전용 태스크(STT, TTS)가 GPU 워커로 라우팅되는 혼선이 발생하였습니다.

- **현상**: GPU 워커에서 받아서는 안 되는 `tasks.evaluator.*` 태스크가 수신되거나, CPU 워커에서 `generate_final_report` 실행 시도하여 OOM(Out of Memory) 에러 발생
- **재현 조건**: 면접 종료 후 최종 평가 리포트 생성 시 발생

---

## 3.2.2 문제 영향 분석

- **서비스 영향**: 리포트 생성 실패 또는 무한 대기
- **시스템 영향**: CPU 워커에서 LLM 추론 시도로 메모리 부족 및 프로세스 크래시
- **로그 오염**: GPU/CPU 워커 모두 오류 로그 다량 출력

---

## 3.2.3 문제 파악 과정

`task_routes`에서 와일드카드 패턴의 우선순위 충돌이 원인이었습니다.

```python
# [문제 코드] main.py
task_routes = {
    'tasks.evaluator.generate_final_report': {'queue': 'gpu_queue'},  # 특정 태스크 → GPU
    'tasks.evaluator.analyze_answer':         {'queue': 'gpu_queue'},  # 특정 태스크 → GPU
    'tasks.evaluator.*':                      {'queue': 'cpu_queue'},  # 와일드카드 → CPU
}
```

Celery는 `task_routes`를 딕셔너리 순서대로 매칭하는데, Python 3.7+ 기준으로 삽입 순서가 보장되지만 **와일드카드(`*`)가 구체적 패턴보다 먼저 선언**된 경우 와일드카드가 먼저 매칭되는 현상 발생.

즉, `tasks.evaluator.generate_final_report`가 `tasks.evaluator.*`에 먼저 매칭되어 의도와 반대로 `cpu_queue`로 전송됨.

---

## 3.2.4 해결 접근 전략

- 구체적인 태스크 패턴을 와일드카드보다 **반드시 앞에** 선언
- GPU/CPU 경계를 명확히 분리하여 혼동 최소화

---

## 3.2.5 해결 도출 및 실행

```python
# [수정 후] main.py L66-83
task_routes = {
    # ── GPU 전용 (LLM 추론 필요) ─ 구체적 패턴 먼저 선언
    'tasks.question_generator.*':              {'queue': 'gpu_queue'},
    'tasks.resume_embedding.*':                {'queue': 'gpu_queue'},
    'tasks.evaluator.generate_final_report':   {'queue': 'gpu_queue'},
    'tasks.evaluator.analyze_answer':          {'queue': 'gpu_queue'},
    'tasks.evaluator.finalize_report_task':    {'queue': 'gpu_queue'},

    # ── CPU 전용 (와일드카드는 나머지를 처리) ─ 나중에 선언
    'tasks.stt.*':           {'queue': 'cpu_queue'},
    'tasks.tts.*':           {'queue': 'cpu_queue'},
    'tasks.vision.*':        {'queue': 'cpu_queue'},
    'tasks.resume_parser.*': {'queue': 'cpu_queue'},
    'tasks.evaluator.*':     {'queue': 'cpu_queue'},  # 위에서 지정 안 된 나머지
}
```

---

## 3.2.6 해결 결과

- **Before**: `generate_final_report`가 CPU 워커로 라우팅되어 OOM 발생
- **After**: GPU 전용 태스크가 정확히 `gpu_queue`로, CPU 태스크가 `cpu_queue`로 분리
- **교훈**: Celery `task_routes`에서 구체적 패턴은 와일드카드 패턴보다 항상 먼저 선언해야 하며, docker-compose에서 워커별 큐 바인딩(`-Q gpu_queue`, `-Q cpu_queue`)도 함께 관리해야 함
