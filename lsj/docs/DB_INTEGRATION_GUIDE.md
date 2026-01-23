# DB 연동 기준서 (Database Integration Guide)

## 1. 개요 (Overview)

본 문서는 **Big20 AI Interview Project**의 데이터베이스 연동 및 데이터 구조에 대한 기준을 정의합니다. 백엔드 시스템(`backend-core`)과 PostgreSQL 데이터베이스 간의 데이터 교환 규격, 테이블 구조, 그리고 주요 JSON 데이터 필드의 스키마를 명시하여 개발자 간의 일관된 이해를 돕는 것을 목적으로 합니다.

*   **프로젝트명**: Big20 AI Interview Project
*   **DBMS**: PostgreSQL 15+
*   **ORM 프레임워크**: SQLModel (SQLAlchemy 기반)
*   **드라이버**: `asyncpg` (비동기 처리)
*   **주요 확장 모듈**: `vector` (임베딩 저장용 - 예정), `uuid-ossp`

## 2. 연동 환경 (Environment)

데이터베이스 접속 정보는 보안을 위해 환경변수(`.env`) 파일에서 관리하며, 소스코드에 하드코딩하지 않습니다.

### 2.1 Connection String Format
SQLAlchemy 비동기 연결을 위해 다음과 같은 형식을 사용합니다.

```ini
# .env examples
DATABASE_URL=postgresql+asyncpg://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB_NAME>
```

### 2.2 초기 설정 (Initialization)
`infra/postgres/init.sql` 스크립트를 통해 컨테이너 구동 시 초기 환경이 설정됩니다.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

## 3. 데이터 모델 및 스키마 (Schema & Models)

Source of Truth는 `backend-core/models.py`입니다. 본 섹션은 주요 테이블의 논리적 구조를 설명합니다.

### 3.1 User (사용자)
사용자 인증 및 프로필 정보를 관리합니다.

| 컬럼명 | 타입 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Auto Increment |
| `username` | `VARCHAR` | 로그인 ID | Unique, Index |
| `hashed_password` | `VARCHAR` | 암호화된 비밀번호 | |
| `full_name` | `VARCHAR` | 사용자 실명 | Optional |
| `created_at` | `TIMESTAMP` | 생성 일시 | Default: UTC Now |

### 3.2 InterviewSession (면접 세션)
하나의 면접 진행 단위입니다. 사용자는 여러 번의 면접 세션을 가질 수 있습니다.

| 컬럼명 | 타입 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Auto Increment |
| `user_id` | `INTEGER` | Foreign Key (`user.id`) | Index |
| `user_name` | `VARCHAR` | 면접자 이름 | 세션 당시의 이름 스냅샷 |
| `position` | `VARCHAR` | 지원 직군 | 예: 'Backend Developer' |
| `status` | `VARCHAR` | 진행 상태 | Default: 'started' |
| `emotion_summary` | `JSONB` | 전체 세션 감정 분석 요약 | 상세 구조 하단 참조 |
| `created_at` | `TIMESTAMP` | 세션 시작 일시 | Default: UTC Now |

### 3.3 InterviewRecord (면접 상세 기록)
세션 내의 개별 질문과 그에 대한 답변, 그리고 평가 결과를 저장합니다.

| 컬럼명 | 타입 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | Primary Key | Auto Increment |
| `session_id` | `INTEGER` | Foreign Key (`interviewsession.id`) | Index |
| `question_text` | `VARCHAR` | AI가 생성한 질문 내용 | |
| `order` | `INTEGER` | 질문 순서 | 1부터 시작 |
| `answer_text` | `VARCHAR` | 사용자의 답변 텍스트 | STT 변환 결과 (Optional) |
| `evaluation` | `JSONB` | 답변 평가 결과 | LLM 평가 (Optional) |
| `emotion_summary` | `JSONB` | 답변별 감정 분석 결과 | (Optional) |
| `answered_at` | `TIMESTAMP` | 답변 완료 일시 | |
| `created_at` | `TIMESTAMP` | 질문 생성 일시 | |

## 4. JSONB 데이터 구조 (JSON Schema Definitions)

PostgreSQL의 `JSONB` 타입을 사용하여 유연하게 저장되는 필드들의 상세 구조입니다.

### 4.1 Evaluation (평가 결과)
*   **Table**: `InterviewRecord`
*   **Column**: `evaluation`

```json
{
  "score": 85,
  "feedback": "구체적인 경험을 예시로 든 점이 좋습니다. 다만 기술적인 깊이가 조금 더 보강되면 좋겠습니다.",
  "keywords": ["REST API", "Async", "Optimization"],
  "strengths": ["Clear communication", "Practical example"],
  "improvements": ["Need deeper technical explanation"]
}
```

### 4.2 Emotion Summary (감정 분석)
*   **Table**: `InterviewSession`, `InterviewRecord`
*   **Column**: `emotion_summary`

```json
{
  "dominant_emotion": "confidence",
  "emotion_scores": {
    "confidence": 0.85,
    "nervousness": 0.10,
    "excitement": 0.05
  },
  "facial_expression_data": {
    // 세부 안면 인식 데이터 (선택적)
  }
}
```

## 5. 연동 방식 및 규칙 (Integration Rules)

1.  **비동기 처리 (Async)**: 모든 DB I/O는 `async`/`await` 패턴을 사용하여 메인 스레드 차단을 방지합니다.
2.  **ORM 사용**: 날(Raw) SQL 쿼리 작성은 지양하고 `SQLModel` 및 `Exec` 객체를 사용합니다.
3.  **트랜잭션 관리**: 데이터 무결성이 필요한 작업(예: 세션 생성과 첫 질문 생성이 동시에 이루어져야 하는 경우)은 트랜잭션 범위 내에서 처리합니다.
4.  **마이그레이션**: 모델 변경 시 `Alembic` 등을 활용하여 스키마 변경 이력을 관리하는 것을 권장합니다 (현재 단계에서는 `table=True` 옵션으로 자동 생성 활용 중).
