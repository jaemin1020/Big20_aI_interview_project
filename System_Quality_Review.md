# 📝 Big20 AI 면접 시스템 - 적합성 검토 및 품질 개선 계획서

본 문서는 `System_Design_Document.md` (시스템 설계서)와 자체 코드 품질 검사 결과(`QUALITY_SUMMARY.md`)를 결합하여, 현재 시스템의 아키텍처 적합성을 평가하고 향후의 개선(Action Plan) 방향을 정리한 리포트입니다.

---

## 1. 아키텍처 적합성 및 주요 강점 (Strengths)

*   **컴포넌트 분리를 통한 확장성 제고**: 
    REST API를 담당하는 `FastAPI(Backend-Core)`, 화상 미디어 스트리밍을 다루는 `aiortc(Media-Server)`, 무거운 AI 추론 작업을 처리하는 `Celery/GPU(AI-Worker)`로 목적과 부하 특성이 명확히 분리된 마이크로서비스(MSA) 형태를 성공적으로 채택했습니다. 이는 향후 AI 노드만 독립적으로 스케일아웃(Scale-out)할 수 있는 유연한 서버 아키텍처를 의미합니다.
*   **최신 기술 스택 통합 구축**: 
    React 18 기반의 비동기 렌더링 환경, FastAPI의 비동기 I/O, PostgreSQL 18.x 기반 스토리지 및 특히 핵심 AI 검색에 해당하는 `pgvector`를 활용한 임베딩 검색 엔진 등 모던 웹 및 AI 생태계 스택을 효과적으로 병합했습니다.

---

## 2. 식별된 문제점 및 취약 사항 (Vulnerabilities)

설계 대비 실제 코드 환경에서 즉시 혹은 단기적으로 보완이 필요한 보안 및 코드 퀄리티 이슈가 식별된 내역입니다. 다음은 전체 코드베이스(`frontend`, `backend-core`, `ai-worker`)를 대상으로 정밀 분석한 상세 취약점 목록입니다.

### 2.1 인증 및 보안 취약점 (Security Risks)
*   **방대한 DB URL 및 패스워드 하드코딩 (Critical)**:
    일반 로컬 설정 파일뿐 아니라, `dump_db.py`, `check_resume_db.py`, `backend-core/check_db.py`, `ai-worker/scripts/insert_companies.py` 등 여러 스크립트 도처에 `postgresql://interview_user:interview_password...` 형태의 하드코딩이 방치되어 있어 크리티컬한 자격 증명 탈취 위험이 있습니다.
*   **Rate Limiting 메커니즘 부재 (High)**: 
    로그인(`routes/auth.py`) 등 인증을 수행하는 핵심 엔드포인트에 요청 제한(Throttling) 제약이 걸려있지 않습니다. 불특정 다수의 무차별 대입 공격(Brute Force)이나 의도적인 봇 트래픽 공격에 서비스 아키텍처가 무방비 노출될 수 있습니다.

### 2.2 클라이언트(Frontend) 배포 결함 (Deployment Blockers)
*   **API 및 WebRTC 통신 URL 하드코딩**:
    `frontend/src/api/interview.js` 내부의 `API_BASE_URL`이 `'http://localhost:8000'` 고정, `App.jsx` 내부 WebRTC 초기화 파트에서 `fetch('http://localhost:8080/offer')`로 명시적 하드코딩을 포함하고 있습니다. 이 상태로 프로덕션 빌드 후 배포 시, 개발자 본인 환경에서만 동작하고 사용자 외부 기기에서는 백엔드에 전혀 접근할 수 없는 **치명적 장애(네트워크 접속 불가)** 가 발생합니다.
*   **운영 콘솔 노출 방치**:
    뷰 컴포넌트(`App.jsx`, `ResultPage.jsx` 등) 내부에 50개 이상의 불필요한 `console.log()`가 혼재되어 있습니다. 이로 인해 운영 브라우저 콘솔에서 서비스의 API 응답 데이터, 사용자 고유 정보가 잠재적으로 노출될 수 있습니다.

### 2.3 시스템 관측성(Logging) 및 예외 처리 (Observability & Error Handling)
*   **로깅 환경 파편화 및 `print()` 남용**:
    AI 추론을 비동기로 처리하는 코어 워커(`ai-worker/tasks/` 내부의 `rag_retrieval.py`, `pgvector_store.py`, `chunking.py` 등) 전반에 걸쳐 `logging` 모듈 대신 단순 `print()` 문이 도배되어 있습니다.
    이는 분산된 Celery 워커 기반 아키텍처에서 로그 유실을 유발하고 ELK 스택 / Datadog 등과의 모니터링 연동을 전면 불가능하게 합니다.
*   **포괄적 예외 처리 (Bare Excepts) 남용**:
    백엔드/워커 파이프라인에서 무차별적으로 `except Exception as e:`를 캐치하고 있습니다. 이로 인해 일시적인 시스템 문제(DB Time-out 등)와 코드 스크립트 상의 크래시가 구분되지 않아 트러블슈팅 및 사후 디버깅 타임을 크게 낭비시킬 수 있습니다.

### 2.4 테스트 커버리지 및 방어적 코드 부재 (Testing)
*   프로젝트 구성을 지탱하는 3개의 주축(`backend-core`, `ai-worker`, `frontend`) 중 백엔드 코어에만 극히 일부(`test_auth.py`, `test_interview.py`)의 테스트가 존재합니다. RAG 로직(`resumes.py`)이나 AI-Worker 기능 등에 대한 유닛/통합 테스트가 존재하지 않아 코드 변경(Refactoring) 작업의 위험도가 최상 레벨입니다.

---

## 3. 시스템 품질 개선 및 대응 전략 (Action Plan)

안정적인 시스템 고도화 및 서비스 레벨 확보를 위해 다음의 단계적 대응 방향을 설정합니다. 현재 발굴된 치명적인 결함부터 우선적으로 처리합니다.

### Phase 1: 즉시 대응 방어책 및 배포 정상화 (초단기 과제)
*   **프론트엔드 환경변수 분리**: `frontend/src` 전역에 고정된 `http://localhost:*` URL을 `.env` (예: `import.meta.env.VITE_API_URL`) 체계로 분리하여 외부 접근이 가능한 정상적인 배포 빌드 환경을 복구합니다.
*   **민감 암호/키 격리화**: 모든 백엔드 전역 파일 내부에 남아있는 하드코딩된 Secret Text(DB_URL, 패스워드 등)를 전면 제거하고 필수 변수를 캡슐화합니다.
*   **운영 콘솔 클리닝**: 클라이언트 파일상의 모든 민감한 `console.log()` 구문들을 배포 빌드 시점에 제거(설정)하거나 코드에서 걷어냅니다.

### Phase 2: 구조 안정화 및 관측성 확보 (단기 과제)
*   **보안 방파제 구성**: `slowapi` 등의 라이브러리를 FastAPI 미들웨어로 부착하여 로그인/Auth 경로 등에 IP 혹은 세션 별 Rate Limit 정책을 강제 적용합니다.
*   **로깅 표준화 및 예외 세분화**: 
    1. AI Worker 및 Data 파이프라인 상의 무분별한 `print()`문을 제거하고 Python 표준 `logger`로 교체합니다.
    2. `except Exception as e:` 형태로 작성된 방어 코드를 점검하여, `TimeOutError`, `ValueError`, `DBConnectionError` 등으로 구체화(Catch)하여 서비스 에러 추적성을 높입니다.

### Phase 3: 신뢰성 제고 및 CI/CD (장기 과제)
*   **테스트 커뮤니티 주도**: 백엔드 코어 모듈(RAG, STT)을 중심으로 `pytest` 환경을 융합하고, 프론트엔드에는 `Jest` / `React Testing Library`를 부착해 핵심 기능의 BDD(Behavior-Driven) 테스트 케이스를 우선 마련합니다.
*   **배포 파이프라인(CI/CD) 수립**: GitHub Actions 혹은 GitLab CI를 통한 자동화를 통해 PR 발생 전 혹은 병합 직전에 [Lint -> Test -> Build] 검증 루틴이 의무적으로 수행되도록 체계를 구축합니다.

---
**문서 생성일**: 2026년 2월 23일
**참조 문서**: `System_Design_Document.md`, 전체 코드베이스 정밀 스캔 결과

