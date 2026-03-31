# 🧠 AI Core System (LLM & Precision RAG)

본 프로젝트의 지성(Intelligence)을 담당하는 **EXAONE-3.5** 엔진과 **pgvector** 기반 고정밀 RAG 시스템의 기술적 실장을 상세히 기술합니다.

---

## 1. LLM 서빙: EXAONE-3.5 (State-of-the-Art)

LG AI Research의 **EXAONE-3.5-7.8B-Instruct** 모델을 온프레미스 GPU 워커에서 최적화된 상태로 구동합니다.

### ⚙️ 고성능 추론 설계
-   **양자화 서빙**: 4-bit (Q4_K_M) GGUF 포맷을 사용하여 VRAM 점유율을 6GB 내외로 억제하면서도 추론 속도를 극대화했습니다.
-   **모델 싱글톤(Singleton)**: `gpu_queue` 워커 기동 시 모델을 메모리에 상주시켜, 매 호출 시 발생하는 로딩 오버헤드(Cold Start)를 0으로 만들었습니다.
-   **스트리밍 인터페이스**: `llama-cpp-python`의 Generator를 활용하여 Redis Pub/Sub 채널로 토큰을 실시간 스트리밍, 프론트엔드에 즉각적인 타이핑 UX를 제공합니다.

---

## 2. 하이브리드 RAG (Retrieval-Augmented Generation)

단순한 문서 검색을 넘어, **PostgreSQL + pgvector**를 활용한 고효율 검색 아키텍처를 채택했습니다.

### 🔍 Search Pipeline
-   **KURE-v1 Embedding**: 한국어 문맥 이해도가 가장 높은 모델 중 하나인 KURE-v1을 통해 이력서와 기업 정보를 1024차원 고밀도 벡터로 변환합니다.
-   **원스톱 하이브리드 쿼리**: 별도의 Vector DB(Milvus 등)를 운영하는 대신, PostgreSQL 내부에서 `L2 Distance (<->)` 혹은 `Cosine Similarity (<=>)` 연산자를 SQL에 직접 포함하여 관계형 데이터와 의미론적 검색을 단일 트랜잭션으로 처리합니다.
-   **섹션 기반 청킹(Chunking)**: 이력서를 학력, 경력, 보유기술 단위로 논리적 분할하여 검색 정합성을 높였습니다.

---

## 3. 맞춤형 질문 생성 알고리즘

-   **Dynamic Context Fusion**: 지원자의 특정 경험(Vector) + 지원 직무(SQL Meta) + 기업 인재상(Vector)을 실시간으로 결합하여 "A 프로젝트에서 B 기술을 사용했는데, C 상황에서는 어떻게 대처했나요?" 식의 **초개인화 질문**을 생성합니다.
-   **Scenario Branching**: `check_if_transition()` 로직을 통해 신입, 경력, 직무 전환자 여부를 데이터 레벨에서 자동 판별하고 최적화된 질문 세트를 주입합니다.
-   **실시간 꼬리질문 (Follow-up)**: 이전 발화의 STT 결과를 컨텍스트에 덧붙여 실시간으로 질문의 깊이를 더합니다.

---

## 4. 다차원 평가 루브릭 및 리포트

-   **Structured Evaluation**: 질문 생성 단계에서 미리 생성된 평가 기준(JSON)을 바탕으로 LLM이 답변의 논리성, 기술적 전문성을 채점합니다.
-   **멀티모달 통합**: 텍스트 분석 결과에 Media-Server에서 수집된 비언어적 지표(시선, 자세, 미세 표정 점수)를 통합하여 "신뢰도 높은 전문성"을 수치화합니다.
-   **데이터 영속성**: 최종 평가 결과는 `evaluation_reports` 테이블에 JSONB 타입으로 저장되어 데이터 유실을 방지하고 빠른 통계 추출을 지원합니다.

---
*문서 위치: `docs/readmelist/AI_CORE_SYSTEM.md`*

