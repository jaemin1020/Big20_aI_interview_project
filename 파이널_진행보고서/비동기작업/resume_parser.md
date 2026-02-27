# Resume Parser 모듈 코드 상세 및 연결 구조 설명 (`resume_parser.py`)

이 모듈은 업로드된 이력서 PDF를 처리하여 구조화된 데이터를 생성하고, 후속 태스크로 인계하는 파이프라인의 입구를 담당합니다. 특히 **백엔드 서버와 AI 워커 간의 비동기 연결**을 보여주는 핵심 사례입니다.

## 1. AI-Worker 내부의 비동기 작업 설정

### 1.1 `@shared_task` 데코레이션
```python
@shared_task(bind=True, name="parse_resume_pdf", queue='cpu_queue')
def parse_resume_pdf(self, resume_id: int, file_path: str):
```
- **비동기 선언**: 이 코드는 함수를 Celery 작업 단위(Task)로 등록합니다. 이를 통해 서버 응답을 멈추지 않고 백그라운드에서 실행될 수 있습니다.
- **`bind=True`**: 함수 내부에서 `self` 인자를 통해 Celery 작업의 메타데이터(예: 재시도 횟수)에 접근 가능하게 합니다.
- **`name="parse_resume_pdf"`**: 시스템 전체에서 이 작업을 식별하는 고유 이름입니다. 백엔드에서 이 이름을 사용하여 호출합니다.
- **`queue='cpu_queue'`**: 이 작업은 CPU 연산 위주이므로, 전용 CPU 워커가 처리하도록 라우팅합니다.

### 1.2 태스크 체이닝 (Task Chaining)
```python
current_app.send_task(
    "tasks.resume_embedding.generate_resume_embeddings",
    args=[resume_id],
    queue='gpu_queue'
)
```
- 파싱 업무가 완료되면, 자동으로 임베딩 업무를 담당하는 다른 비동기 작업을 호출합니다. 이 과정 또한 비동기로 이루어지며, 이때는 GPU 큐를 사용하여 효율을 높입니다.

---

## 2. 백엔드(Backend-Core)와의 연결 구조

이 비동기 작업은 지원자가 홈페이지에서 이력서를 업로드하는 순간 시작됩니다.

### 2.1 연결 지점: `backend-core/routes/resumes.py`
지원자가 `/api/resumes/upload` 엔드포인트로 PDF를 업로드하면, 백엔드 API 서버는 다음과 같은 순서로 작업을 수행합니다.

```python
# [backend-core/routes/resumes.py 내부]
@router.post("/upload")
async def upload_resume(...):
    # 1. 파일 저장 및 DB 레코드 생성 (생략)
    
    # 2. 비동기 작업 전송 (AI-Worker 호출부)
    celery_app.send_task(
        "parse_resume_pdf",              # 호출할 작업 이름 (Worker와 일치해야 함)
        args=[resume.id, file_path],     # 전달할 인자 (DB ID, 파일 경로)
        queue='cpu_queue'                # 작업이 들어갈 큐 지정
    )
```

### 2.2 호출 흐름 요약
1.  **사용자**: 이력서 PDF 업로드 버튼 클릭.
2.  **백엔드(FastAPI)**: 파일을 `/app/uploads/resumes` 폴더에 저장하고 DB에 `pending` 상태로 기록.
3.  **백엔드(Celery)**: `send_task`를 통해 **"parse_resume_pdf"**라는 이름의 신호를 Redis(브로커)에 전달.
4.  **AI-Worker(Celery)**: Redis에 쌓인 수신 대기열에서 본인의 `name`과 일치하는 작업을 가져와 **비동기**로 실행 시작.
5.  **완료 후**: AI-Worker가 DB 상태를 `completed`로 업데이트하면, 사용자는 웹 화면에서 파싱된 결과를 확인할 수 있게 됨.

---

## 3. 코드 상세 로직 설명

- **경로 정규화**: `os.path.basename`을 사용하여 파일명만 추출한 뒤, 컨테이너 공용 경로인 `/app/uploads/resumes`에 맞춰 재구성합니다. 이는 백엔드와 워커가 다른 컨테이너 환경일 때 발생할 수 있는 경로 인식 차이를 해결합니다.
- **데이터베이스 업데이트**: `SQLModel`의 `Session(engine)`을 통해 DB에 접속하며, 파서가 추출한 `structured_data`와 `target_position`을 `Resume` 테이블에 즉시 영구 저장합니다.
- **예외 처리**: 파싱 중 오류 발생 시 `_update_status` 함수를 통해 DB 상태를 `failed`로 변경하여, 시스템 전체의 데이터 무결성을 유지하고 사용자에게 실패를 알립니다.
