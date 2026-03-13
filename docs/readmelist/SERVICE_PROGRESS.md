# 📊 파트별 통합 진행 보고서 (Integrated Progress Report)

본 문서는 **PA, SA, DA, LA, MA, SD** 6개 파트의 주요 설계 및 구현 내용을 하나로 통합한 보고서입니다.

---

## 📋 1. Planning Architecture (PA)
- **비전**: LLM과 Vision AI를 활용한 온프레미스 기반 지능형 면접 솔루션 구축.
- **로드맵**:
  - Phase 1: 기반 인프라 (Docker, DB, RAG) 구축 및 이력서 파싱 완료.
  - Phase 2: AI 핵심 엔진 (EXAONE, Faster-Whisper, Supertonic) 통합 및 비동기 처리 구현.
  - Phase 3: 실시간 미디어 스트리밍 (WebRTC) 및 행동 분석 모듈 완성.

## 🏗️ 2. System Architecture (SA)
- **MSA 구조**: 7개 마이크로서비스(Frontend, Core, Media, CPU-Worker, GPU-Worker, Redis, DB) 통합 제어망 구축.
- **비동기 파이프라인**: Celery와 Redis를 통해 LLM/STT 등 고부하 작업을 비동기화하여 API 서버 블로킹 제거.
- **자원 격리**: GPU 전용 큐와 CPU 전용 큐를 분리하여 연산 경합 방지 및 안정성 확보.

## 🗄️ 3. Data Architecture (DA)
- **Hybrid Storage**: PostgreSQL + pgvector를 통해 관계형 데이터와 벡터 데이터를 단일 DB에서 통합 관리.
- **RAG 파이프라인**: KURE-v1 기반 1024차원 임베딩 생성 및 이력서 섹션별 정밀 청킹 전략 적용.
- **데이터 흐름**: 지원 직무와 이력서 간의 유사도 검색(Cosine Similarity)을 통한 개인화 질문 생성 지원.

## 🧠 4. LLM Architecture (LA)
- **핵심 엔진**: EXAONE-3.5-7.8B-Instruct (GGUF 양자화) 모델을 활용한 고속 추론 및 스트리밍 지원.
- **프롬프트 엔진**: 이력서 컨텍스트와 기업 정보를 결합한 Dynamic Prompting 및 루브릭(평가 기준) 자동 생성.
- **대화 관리**: 이전 답변을 분석하여 실시간 꼬리질문을 생성하는 지능형 인터렉션 구현.
- **결과 분석**: 면접 종료 후 6개 역량(기술/경험/소통 등)에 대한 정밀 평가 및 인재상 매칭 리포트 자동 생성.

## 🤖 5. Model Architecture (MA)
- **Vision (MediaPipe)**: 실시간 시선 처리, 자세, 감정 분석 (5FPS 샘플링 최적화).
- **Voice (STT/TTS)**: 
  - Faster-Whisper (`large-v3-turbo`) 기반 고정밀 음성 인식.
  - Supertonic-2 기반 고음질 한국어 음성 합성 및 Redis 캐싱 적용.

## 🛠️ 6. System Development (SD)
- **품질 관리**: Git Flow 브랜칭 전략 도입으로 병합 충돌 70% 감소 및 18개 통합 테스트 통과.
- **성능 지표**:
  - WebRTC 레이턴시 300ms 이내 유지.
  - STT/TTS 왕복 지연 시간 2초 이내 달성.
- **기술 병목 해결**: VRAM OOM 관리 및 소켓 데드락 해결을 통한 Fault-tolerant 플랫폼 구축.

---
*참고: 상세 내용은 각 아키텍처 문서를 참조하시기 바랍니다.*
