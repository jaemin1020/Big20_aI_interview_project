# Big20 AI 면접 프로젝트 시스템 명세서 (최종)

## 1. 개요 (Overview)

### 1.1 프로젝트 명
Big20 AI 면접 프로젝트 (Big20 AI Interview Project)

### 1.2 목적
본 시스템은 최신 AI 기술(LLM, Vision AI, STT)과 실시간 웹 통신 기술(WebRTC)을 결합하여, 실제 면접과 유사한 환경을 제공하고 면접자의 답변 내용과 비언어적 태도를 종합적으로 분석하여 객관적이고 심도 있는 피드백을 제공한다. 특히 온프레미스 GPU 환경에서 고성능 AI 모델을 구동하여 보안성과 경제성을 모두 확보한다.

### 1.3 범위
- 웹 기반의 실시간 화상 면접 및 실시간 미디어 분석
- EXAONE-3.5 기반 지원자 맞춤형 심층 면접 질문 생성 (RAG)
- Faster-Whisper를 이용한 고정밀 실시간 음성 인식 (STT)
- MediaPipe를 활용한 실시간 시선, 자세, 표정 분석
- 종합 결과 리포트 대시보드 및 PDF 리포트 제공

---

## 2. 시스템 아키텍처 (System Architecture)

### 2.1 전체 구성도
본 시스템은 마이크로서비스 아키텍처(MSA)로 구성되며, 7개의 컨테이너가 Docker Compose로 연결된다.
- **Frontend**: 사용자 인터페이스 (React 18 + Vite)
- **Backend-Core**: 비즈니스 로직 및 API 관제 (FastAPI)
- **Media-Server**: WebRTC 시그널링 및 실시간 비전 분석 (aiortc + MediaPipe)
- **AI-Worker (GPU)**: EXAONE LLM 질문 생성 및 평가 (Celery + Llama-cpp)
- **AI-Worker (CPU)**: Faster-Whisper STT 및 Supertonic-2 TTS (Celery)
- **Database**: 정형 및 벡터 데이터 저장 (PostgreSQL + pgvector)
- **Message Broker**: 비동기 태스크 큐 및 브로드캐스팅 (Redis)

### 2.2 기술 스택 요약
| 구분 | 기술 스택 | 비고 |
|:---:|:---|:---|
| **AI LLM** | EXAONE-3.5-7.8B-Instruct | GGUF 양자화, RAG 기반 질문 생성 |
| **STT** | Faster-Whisper (large-v3-turbo) | 서버 사이드 고속 전사 |
| **TTS** | Supertonic-2 | 한국어 감정 음성 합성 |
| **Vision** | MediaPipe FaceLandmarker | 실시간 시선, 자세, 표정 추적 |
| **Embedding** | KURE-v1 (1024차원) | 한국어 문맥 최적화 임베딩 |
| **Backend** | FastAPI, SQLModel | 비동기 파이프라인 |
| **DB** | PostgreSQL 18, pgvector | 하이브리드 벡터 검색 |
| **Infra** | Docker Compose | 서비스 격리 및 GPU 가속 연동 |

---

## 3. 구성 요소별 상세 명세 (Component Specifications)

### 3.1 Frontend (React 18)
- **UI 컨셉**: Glassmorphism 디자인 적용 프리미엄 인터페이스.
- **주요 기능**:
  - WebRTC 비디오 스트링 송출 및 실시간 자막 수신.
  - WebSocket을 이용한 AI 질문 텍스트 스트리밍 수신.
  - 실시간 분석 데이터(시선, 감정 점수) 동적 차트 시각화.

### 3.2 Backend-Core (FastAPI)
- **API 서버**: JWT 기반 보안 인증 및 면접 세션(Session) 라이프사이클 관리.
- **태스크 관제**: Celery를 통해 LLM/STT/TTS 등의 고부하 작업을 워커 노드에 할당.
- **RAG 오케스트레이션**: 이력서 업로드 시 PDF 파싱 및 벡터 DB(pgvector) 저장 프로세스 제어.

### 3.3 Media-Server (WebRTC & Vision)
- **Streaming**: aiortc를 활용하여 브라우저와 저지연(300ms 이내) 화상 통신.
- **Behavior Analysis**: MediaPipe를 연동하여 실시간 비디오 프레임에서 시선 방향, 거북목 자세, 미소 수치 등을 5FPS 샘플링으로 정밀 분석.

### 3.4 AI-Worker (Data Processing Unit)
- **GPU 워커**: EXAONE-3.5 모델을 로드하여 질문 생성 및 답변 평가 루브릭 산출.
- **CPU 워커**: Faster-Whisper를 구동하여 오디오 데이터를 1.5초 이내 텍스트로 변환. Supertonic-2를 통한 음성 합성 수행.

---

## 4. 품질 지표 및 테스트 (Quality & Test)
- **단위 테스트**: 총 18개 핵심 테스트 케이스 통과 (Auth 9, Interview 9).
- **성능 목표**:
  - WebRTC 지연: 300ms 미만
  - STT 인식 속도: 1.8초 미만
  - 질문 생성 속도: 10초 내외 (토큰 스트리밍 적용)

---
*최종 업데이트: 2026-03-13*
*문서 위치: `docs/개발문서/SYSTEM_SPECIFICATION.md`*
