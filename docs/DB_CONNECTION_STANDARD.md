# 데이터베이스 연동 기준서 (DB Connection Standards)

## 1. 개요 (Overview)
본 문서는 `Big20_aI_interview_project`의 백엔드 시스템(`backend-core`, `ai-worker`)에서 사용하는 데이터베이스 연동 및 관리 기준을 정의합니다.

### 1.1 기술 스택
- **DBMS**: PostgreSQL 18 (pgvector 확장 사용)
- **Driver**: `psycopg` (v3, 비동기 지원)
- **ORM**: SQLModel (SQLAlchemy 2.0 기반 wrapper)
- **Connection URL**: `postgresql+psycopg://<user>:<password>@<host>:<port>/<dbname>`

---

## 2. 연동 환경 설정 (Configuration)

### 2.1 연결 정보
환경 변수(`env`)를 통해 관리하는 것을 원칙으로 합니다.
- **Key**: `DATABASE_URL`
- **Default**: `postgresql+psycopg://admin:1234@db:5432/interview_db`

### 2.2 커넥션 풀 (Connection Pool)
안정적인 서비스 운영을 위해 SQLAlchemy의 커넥션 풀을 명시적으로 설정하여 사용합니다.

| 설정 항목 | 환경 변수 | 기본값 | 설명 |
|---|---|---|---|
| Pool Size | `DB_POOL_SIZE` | 20 | 기본적으로 유지할 활성 연결 수 |
| Max Overflow | `DB_MAX_OVERFLOW` | 10 | Pool Size 초과 시 허용할 최대 추가 연결 수 |
| Pool Recycle | `DB_POOL_RECYCLE` | 3600 | 연결 재활용 주기(초), DB 타임아웃 방지 (3600초) |
| Pool Pre-Ping | - | True | `create_engine` 시 설정. 쿼리 실행 전 연결 유효성 검사 |

### 2.3 세션 관리 (Session Management)
- **Backend-Core (FastAPI)**:
  - `Dependency Injection` 패턴 사용 (`get_session`).
  - Request-Response 주기마다 세션을 생성하고 종료(`yield`).
```python
# backend-core/database.py
def get_session():
    with Session(engine) as session:
        yield session
```

- **AI-Worker (Celery)**:
  - 작업(`Task`) 단위로 `Context Manager`(`with Session(engine)`) 사용.
  - 작업 완료 시 반드시 세션이 닫혀야 함.

---

## 3. 데이터 모델링 기준 (Data Modeling)

### 3.1 모델 정의 원칙 (Source of Truth)
- **Primary Definition**: `backend-core/models.py`가 모든 모델의 기준이 됩니다.
- **Worker Sync**: `ai-worker/db.py`는 `backend-core/models.py`의 정의를 복제하여 사용하되, 최신 상태를 유지해야 합니다. (추후 공유 패키지 도입 권장)

### 3.2 네이밍 컨벤션 (Naming Conventions)
- **Table Name**: 복수형, snake_case (예: `users`, `interviews`, `companies`)
- **Column Name**: snake_case (예: `created_at`, `company_name`)
- **Primary Key**:
  - 기본적으로 `id` 필드 사용.
  - 데이터 성격에 따라 `Integer` (Auto-increment) 또는 `String` (직접 지정) 사용.
    - 예: `Company.id`는 `VARCHAR` (ex: 'KAKAO'), `Question.id`는 `INTEGER`.

### 3.3 특수 데이터 타입
- **Vector (Embedding)**:
  - `pgvector` 확장을 사용.
  - 차원: **768** (사용 모델: `jhgan/ko-sroberta-multitask`).
  - SQLModel 정의 시 `sa_column=Column(Vector(768))` 사용.
- **JSON**:
  - 구조화되지 않은 데이터(평가 세부사항 등) 저장 시 `JSONB` 사용.
  - `sa_column=Column(JSONB)`.

---

## 4. 데이터 조작 및 쿼리 (CRUD & Query)

### 4.1 벡터 검색 (Vector Search)
- 코사인 유사도(`cosine_distance`)를 표준 거리 측정 방식으로 사용합니다.
- `pgvector.sqlalchemy`의 메서드 활용.
```python
# 예시: 유사 질문 검색
session.exec(
    select(Question)
    .order_by(Question.embedding.cosine_distance(target_embedding))
    .limit(5)
)
```

### 4.2 대량 데이터 삽입 (Bulk Insert)
- 초기 데이터나 배치 작업 시 `session.add()` 반복 후 1회 `session.commit()` 수행을 권장합니다.

---

## 5. 마이그레이션 및 변경 관리 (Migration)

### 5.1 스키마 변경 프로세스
1. **SQLModel 수정**: `backend-core/models.py` 수정.
2. **미러링**: `ai-worker/db.py` 동기화.
3. **마이그레이션 스크립트 작성**: `infra/postgres/migrations/` 경로에 `.sql` 파일 생성.
    - 파일명 규칙: `XXX_description.sql` (순서 보장).
4. **적용**:
    - 개발 환경: `docker-compose up` 시 볼륨 마운트로 DB 초기화 시 자동 적용.
    - 운영 환경: 배포 시 스크립트 실행 또는 관리 도구 사용.

### 5.2 초기화 정책
- `init_db()` 함수는 서버 시작 시(`startup` 이벤트) 호출되며 `create_all()`을 수행합니다.
- 이미 테이블이 존재하면 변경하지 않으므로, 스키마 변경 시에는 **수동 마이그레이션 스크립트**가 필수적입니다.

---

## 6. 트러블슈팅 가이드

### 6.1 `OperationalError: server closed the connection unexpectedly`
- **원인**: 장시간 유휴 상태로 인한 DB 연결 끊김.
- **해결**: `pool_pre_ping=True` 및 `pool_recycle` 설정이 되어 있는지 확인합니다.

### 6.2 `StatementError: (builtins.TypeError) ...`
- **원인**: SQLModel 타입과 DB 실제 타입 불일치 (특히 Vector나 JSON).
- **해결**: `models.py`의 `sa_column` 정의가 올바른지 확인 (예: `Vector` import 확인).

### 6.3 AI-Worker 모델 Import 에러
- **원인**: `backend-core` 모델 변경 후 `ai-worker` 미반영.
- **해결**: 두 서비스의 모델 정의를 일치시키고 이미지를 재빌드(`docker-compose build`)합니다.
