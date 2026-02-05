# 🏗️ 프로젝트 종합 품질 감사 보고서 (Project Quality Audit Report)

**진단 일시**: 2026-02-05  
**진단 대상**: Big20 AI Interview Project (Backend, Frontend, AI-Worker, Media-Server)

---

## 1. 📊 종합 요약 (Executive Summary)

전반적으로 프로젝트는 **기능 구현 중심의 MVP 단계**로 보입니다. 핵심적인 AI 기능(면접 질문 생성, 평가, STT)과 실시간 통신(WebRTC)은 잘 구현되어 있으나, **유지보수성**과 **배포 안정성** 측면에서 개선이 필요합니다.

| 영역 | 점수 | 상태 | 주요 이슈 |
|------|------|------|-----------|
| **아키텍처** | 4.0/5 | 🟢 양호 | 마이크로서비스 구조 분리 잘됨 (Core, Worker, Media) |
| **코드 품질** | 3.5/5 | 🟡 보통 | 일부 파일의 비대화 (`App.jsx`, `main.py`), 하드코딩된 값 |
| **보안** | 3.0/5 | 🟡 주의 | 프론트엔드 API 키 노출 관리 필요, 기본 Secret Key 사용 |
| **테스트** | 2.0/5 | 🔴 미흡 | 백엔드 기본 테스트 존재하나 커버리지 낮음, 프론트엔드 테스트 부재 |
| **인프라** | 4.0/5 | 🟢 양호 | Docker Compose 기반 실행 환경 잘 구성됨 |

---

## 2. 🔍 상세 진단 결과

### 2.1 코드 복잡도 및 구조 (Maintainability)

**🚩 식별된 대형 파일 (Refactoring Targets)**
다음 파일들은 단일 책임 원칙(SRP) 위배 가능성이 높으므로 분할이 권장됩니다.
1.  **`frontend/src/App.jsx` (498 lines)**: 라우팅, 전역 상태, 웹소켓 로직이 혼재됨. → `Context API` 및 `Router` 설정 분리 필요.
2.  **`backend-core/main.py` (481 lines)**: 모든 API 엔드포인트가 하나에 모여 있음. → `APIRouter`를 사용해 도메인별(Auth, Interview, Users)로 분리 필요.
3.  **`backend-core/utils/rubric_generator.py` (409 lines)**: 프롬프트 관리와 로직을 분리 권장.

**🚩 기술 부채 (Technical Debt)**
- `ai-worker/tasks/answer_collector.py`: "벡터 유사도로 중복 체크" 로직이 `TODO`로 남겨져 있어, 답변 중복 저장 이슈 가능성 있음.

### 2.2 보안 (Security)

**✅ 양호한 점**
- `.env` 파일이 Git에 포함되지 않음 (로컬 관리).
- JWT 기반 인증 방식 사용.

**⚠️ 개선 필요 사항**
1.  **Deepgram API Key 노출**: 프론트엔드(`App.jsx`)에서 `import.meta.env.VITE_DEEPGRAM_API_KEY`를 직접 사용 중.
    - **위험**: 브라우저 개발자 도구에서 키 탈취 가능성.
    - **권장**: 백엔드에서 일회용/임시 토큰을 발급받아 프론트엔드에 전달하는 방식(Proxy)으로 변경해야 함.
2.  **Fallback Secret Key**: `auth.py`에서 환경변수 누락 시 사용하는 기본 키(`your-secret-key...`)가 코드에 하드코딩됨. 프로덕션 배포 시 사고 위험.

### 2.3 테스트 현황 (Test Coverage)

- **Backend**: `backend-core/tests`에 `test_auth.py`, `test_interview.py`가 존재하지만 커버리지가 제한적임.
- **Frontend**: `frontend/test/` 디렉토리가 존재하지만 내용이 비어있음 (**Test Void**).
- **CI/CD**: 현재 자동화된 테스트 파이프라인 설정 파일(GitHub Workflows 등) 부재.

### 2.4 의존성 관리 (Dependency Hygiene)

- `backend-core`와 `ai-worker`는 `sqlmodel`, `pydantic`, `celery` 등의 버전이 잘 일치함.
- **주의**: `media-server`는 `celery==5.4.0` (고정)을 사용하고, 다른 서비스는 `>=5.3.6`을 사용함. 마이너 버전 차이로 인한 메시지 직렬화 호환성 문제 가능성 미미하지만 존재.

---

## 3. 📅 우선순위 기반 개선 로드맵

### 🚀 Phase 1: 안정성 및 보안 (이번 주 권장)
- [ ] **보안 패치**: Deepgram API Key 프론트엔드 직접 호출 제거 → 백엔드 Proxy 엔드포인트 구현.
- [ ] **구조 개선**: `backend-core/main.py`를 `routes/` 패키지로 라우터 분리.
- [ ] **구조 개선**: `frontend/src/App.jsx`의 비즈니스 로직을 Custom Hooks(`useInterview`, `useAuth`)로 분리.

### 🛠️ Phase 2: 품질 향상 (다음 주)
- [ ] **테스트**: 백엔드 핵심 비즈니스 로직(면접 생성, 평가) 단위 테스트 보강.
- [ ] **기능 완성**: `ai-worker`의 답변 중복 체크(TODO) 구현.
- [ ] **문서화**: API 명세(Swagger)를 기반으로 한 연동 문서 최신화.

### 🏗️ Phase 3: 운영 고도화 (추후)
- [ ] **모니터링**: Prometheus/Grafana 도입으로 컨테이너 상태 시각화.
- [ ] **CI**: GitHub Actions를 통한 PR 시 테스트 자동 실행 설정.

---

**작성자**: AI Agent (Antigravity)
