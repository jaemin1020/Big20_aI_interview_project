# Question Generator Task 모듈 (question_generator.py)

인터뷰 시나리오와 지원자의 데이터를 바탕으로 최적의 질문을 실시간으로 생성하는 핵심 모듈입니다.

## 주요 기능

### 1. `tasks.question_generation.generate_next_question`
- **설명**: 현재 면접 단계(Intro, Tech, Behavioral 등)를 판별하고, 다음에 던질 AI 질문을 생성합니다.
- **매개변수**:
    - `interview_id`: 인터뷰 ID
- **주요 로직**:
    - **시나리오 판별**: 지원자의 전공/직무를 분석하여 '전공 일치' 또는 '비전공(전환자)' 시나리오를 자동 선택
    - **RAG(검색) 연동**: 이력서 데이터에서 질문 주제에 맞는 컨텍스트를 실시간으로 검색하여 LLM에 제공
    - **LLM 생성**: EXAONE-3.5 모델을 사용하여 예리하고 자연스러운 꼬리질문 생성
    - **정제 시스템**: 출력물에서 마크다운, 레이블, 중복 질문 등을 제거하는 후처리 수행
    - **연쇄 호출**: 질문 생성 직후 `tasks.tts.synthesize`를 호출하여 음성 파일을 미리 생성
- **큐(Queue)**: `gpu_queue` (EXAONE LLM 및 RAG 검색 가속)
