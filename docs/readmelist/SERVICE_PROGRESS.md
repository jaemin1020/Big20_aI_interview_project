
## 🏗️ 2. System Architecture (SA)
-   **MSA 진화**: 단일 모놀리스 구조에서 발생하는 VRAM OOM과 API 블로킹 문제를 해결하기 위해 **7개 마이크로서비스 분산 구조**로 리팩토링 성공.
-   **자원 고립**: `gpu_queue`와 `cpu_queue` 워커의 물리적 격리를 통해 실시간 화상 스트리밍과 무거운 AI 추론의 간섭 없는 병럴 처리망 구축.

## 🗄️ 3. Data Architecture (DA)
-   **Hybrid Vector DB**: PostgreSQL 18과 **pgvector**를 융합하여 RDBMS의 무결성과 벡터 검색의 시맨틱 성능을 단일 포인트에서 확보.
-   **RAG 파이프라인**: KURE-v1 기반 1024차원 임베딩 및 이력서 섹션별 정밀 청킹(pdfplumber 활용) 전략 적용 완료.

## 🧠 4. LLM Architecture (LA)
-   **AI 브레인**: **EXAONE-3.5-7.8B** 모델의 4-bit 양자화 서빙으로 고속 추론 및 토큰 단위 실시간 스트리밍 구현.
-   **지능형 평가**: 면접 질문별 평가 루브릭(JSON) 자동 생성 및 면접 종료 후 종합 역량 채점 알고리즘 탑재.
## 🏗️ 2. System Architecture (SA)
-   **MSA 진화**: 단일 모놀리스 구조에서 발생하는 VRAM OOM과 API 블로킹 문제를 해결하기 위해 **7개 마이크로서비스 분산 구조**로 리팩토링 성공.
-   **자원 고립**: `gpu_queue`와 `cpu_queue` 워커의 물리적 격리를 통해 실시간 화상 스트리밍과 무거운 AI 추론의 간섭 없는 병럴 처리망 구축.

## 🗄️ 3. Data Architecture (DA)
-   **Hybrid Vector DB**: PostgreSQL 18과 **pgvector**를 융합하여 RDBMS의 무결성과 벡터 검색의 시맨틱 성능을 단일 포인트에서 확보.
-   **RAG 파이프라인**: KURE-v1 기반 1024차원 임베딩 및 이력서 섹션별 정밀 청킹(pdfplumber 활용) 전략 적용 완료.

## 🧠 4. LLM Architecture (LA)
-   **AI 브레인**: **EXAONE-3.5-7.8B** 모델의 4-bit 양자화 서빙으로 고속 추론 및 토큰 단위 실시간 스트리밍 구현.
-   **지능형 평가**: 면접 질문별 평가 루브릭(JSON) 자동 생성 및 면접 종료 후 종합 역량 채점 알고리즘 탑재.

## 🤖 5. Model Architecture (MA)
-   **Vision AI**: MediaPipe 기반 **5FPS 샘플링 최적화**를 통해 시선, 자세, 감정을 서버 부하 없이 실시간 추적.
-   **Voice AI**: Faster-Whisper(`large-v3-turbo`)와 Supertonic-2 엔진을 결합한 지능형 음성 인터페이스 구축 및 Redis 분산 락 적용.

## 🛠️ 6. System Development (SD)
-   **품질 혁신**: 8단계 **Git Flow 전략** 도입으로 모노레포 병합 충돌 70% 감소 및 67개 시나리오 검증(18개 자동화 테스트 포함) 전수 통과.
-   **Fault Tolerance**: AI 모델 런타임 오류 시 시스템 중단을 막기 위한 **Smart Fallback** 로직 실장.

---
*참고: 본 문서는 `docs/개발문서/시스템진행보고서초안.md`의 핵심 내용을 요약하고 있습니다.*
