# Big20 AI Interview Project Structure

이 프로젝트는 AI 기반 모의 면접 서비스를 제공하기 위한 풀스택 애플리케이션입니다. 크게 Frontend, Backend Core, AI Worker, Media Server로 구성되어 있습니다.

## 📂 전체 디렉토리 구조 요약

- `backend-core/`: 서비스의 핵심 비즈니스 로직과 API를 담당하는 메인 서버 (FastAPI)
- `ai-worker/`: 이력서 분석, 질문 생성, STT 등 무거운 AI 연산을 처리하는 백그라운드 워커
- `frontend/`: 사용자 인터페이스 (React + Vite)
- `media-server/`: 면접 중 실시간 미디어(WebRTC 등) 처리를 담당하는 서버
- `infra/`: 인프라 설정 및 배포 관련 파일
- `docs/`: 프로젝트 관련 문서
- `models/`: 로컬 AI 모델 파일 저장 공간

---

## 🏗️ 각 디렉토리 및 모듈 상세 설명

### 1. `backend-core/` (메인 API 서버)
사용자의 요청을 처리하고 데이터베이스와 상호작용하며, 필요한 경우 AI Worker에 작업을 요청합니다.

- `routes/`: API 엔드포인트 정의
    - `auth.py`: 사용자 인증 (회원가입, 로그인)
    - `interviews.py`: 면접 세션 생성, 진행 상태 관리, 질문 조회 등
    - `resumes.py`: 이력서 업로드 및 관리
    - `companies.py`: 채용 공고 및 기업 정보 관리
    - `stt.py` & `transcripts.py`: 면접 답변의 텍스트 변환 및 기록 관리
- `models.py`: SQLModel을 사용한 데이터베이스 스키마 정의 (User, Interview, Question 등)
- `database.py`: SQLAlchemy 기반 DB 연결 및 세션 관리
- `data/`: 초기 데이터 및 전처리된 데이터 (JSON 형식) 저장

### 2. `ai-worker/` (AI 프로세싱 엔진)
비동기적으로 무거운 AI 작업을 수행합니다. 주로 `tasks/` 폴더 내에 핵심 로직이 위치합니다.

- `tasks/`: 핵심 AI 파이프라인
    - `parse_resume.py`: 업로드된 이력서(PDF 등)에서 텍스트 및 구조적 정보 추출
    - `chunking.py`: 긴 텍스트를 AI 모델이 처리하기 쉬운 단위로 분할
    - `embedding.py`: 텍스트를 벡터로 변환하여 검색 가능하게 만듦
    - `pgvector_store.py`: 벡터 데이터를 DB에 저장하고 검색하는 로직
    - `rag_retrieval.py`: 사용자의 질문에 답변하기 위해 관련 문서를 검색 (RAG)
    - `question_generation.py`: 이력서 및 기업 정보를 바탕으로 맞춤형 면접 질문 생성
    - `stt.py`: 음성 데이터를 텍스트로 변환
    - `vision.py`: 면접 영상의 시각적 요소(표정, 태도 등) 분석
    - `evaluator.py`: 면접 답변에 대한 평가 및 피드백 생성
- `config/interview_scenario.py`: 면접 진행 시나리오 및 프롬프트 템플릿 설정

### 3. `frontend/` (사용자 인터페이스)
React를 기반으로 한 웹 서비스입니다.

- `src/pages/`: 주요 화면 구성 (홈, 면접 대기실, 면접 진행, 결과 리포트 등)
- `src/components/`: 버튼, 모달, 비디오 플레이어 등 재사용 가능한 UI 컴포넌트
- `src/api/`: 백엔드 서버와의 API 통신 로직
- `App.jsx`: 전체 라우팅 및 전역 상태 관리

### 4. `media-server/` (실시간 미디어 서버)
면접 중 발생하는 실시간 스트리밍 데이터를 처리합니다.

- `main.py`: WebRTC 연결 설정 및 실시간 음성/영상 데이터 처리 로직

### 5. 기타 디렉토리
- `docker/`: Dockerfile 및 환경 구성 파일
- `infra/`: 배포 자동화 및 클라우드 인프라 관련 스크립트
- `test/`: 각종 통합 및 단위 테스트 코드

---

## 🔄 시스템 워크플로우

1. **이력서 업로드**: 사용자가 Frontend에서 이력서를 업로드하면 `backend-core`가 이를 수신하고 `ai-worker`에 분석 작업을 보냅니다.
2. **AI 분석**: `ai-worker`가 이력서를 파싱, 임베딩하고 질문을 미리 생성하여 DB에 저장합니다.
3. **면접 진행**: 사용자가 면접을 시작하면 `media-server`를 통해 실시간 영상/음성이 전달되고, `ai-worker`가 실시간 STT 및 시각 분석을 수행합니다.
4. **결과 생성**: 면접 종료 후 `ai-worker`가 전체 답변을 평가하고 피드백을 생성하여 `backend-core`를 통해 사용자에게 제공합니다.
