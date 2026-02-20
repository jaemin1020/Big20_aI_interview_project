# 🤖 AI-Worker Tasks 핵심 모듈 상세 가이드

이 문서는 `ai-worker/tasks` 디렉토리에 있는 핵심 로직들을 누구나 이해할 수 있도록 **매우 상세하고 친절하게** 설명합니다. 이 모듈들은 우리 AI 면접 시스템의 '두뇌' 역할을 하는 가장 중요한 부분입니다.

---

## 📂 전체 구조 요약
이 가이드는 파일별로 어떤 역할을 수행하고, 코드가 내부적으로 어떻게 돌아가는지 설명합니다.

1.  **입력 & 파싱**: `parse_resume.py`, `resume_parser.py` (이력서 읽기)
2.  **지식 저장 (RAG)**: `chunking.py`, `embedding.py`, `pgvector_store.py`, `resume_embedding.py` (이력서 데이터 벡터화)
3.  **면접 진행**: `question_generator.py`, `rag_retrieval.py` (질문 만들기)
4.  **미디어 처리**: `stt.py`, `tts.py`, `vision.py` (듣고, 말하고, 보기)
5.  **평가**: `evaluator.py` (면접 결과 분석)

---

## 1. 🎤 듣기 (Speech-To-Text) - `stt.py`
지원자가 말한 음성을 텍스트로 바꾸는 모듈입니다.

*   **주요 기술**: `Faster-Whisper` (매우 빠르고 정확한 STT 모델)
*   **핵심 로직**:
    *   **In-Memory 처리**: 오디오 파일을 디스크에 저장하지 않고 메모리(PCM) 상에서 직접 처리하여 **응답 속도를 극대화**했습니다.
    *   **환각(Hallucination) 필터**: 고요한 상태에서 STT 모델이 "감사합니다", "시청해주셔서 감사합니다"와 같은 헛소리를 만들어내는 현상을 방지하는 필터가 들어있습니다.

---

## 2. 🗣️ 말하기 (Text-To-Speech) - `tts.py`
AI 면접관의 질문을 부드러운 목소리로 들려주는 모듈입니다.

*   **주요 기술**: `Supertonic 2` 엔진
*   **핵심 로직**:
    *   **남성 음성(M1)**: 신뢰감을 주는 남성 면접관 목소리를 기본으로 설정했습니다.
    *   **Base64 반환**: 생성된 음성 파일을 브라우저가 바로 재생할 수 있도록 `Base64` 문자열로 인코딩하여 전달합니다.

---

## 3. 📄 이력서 파싱 (Parsing) - `parse_resume.py` & `resume_parser.py`
PDF 형태의 이력서를 분석하여 구조화된 데이터(JSON)로 바꾸는 과정입니다.

*   **`parse_resume.py`**: 실제 분석가
    *   **표(Table) 분석**: `pdfplumber`를 사용해 이력서 내의 격자 구조를 파악하고, 학력/경력/수상을 정확히 발라냅니다.
    *   **Regex(정규표현식)**: 표가 없는 이력서도 분석할 수 있도록 패턴 기반으로 이름과 직무를 찾아냅니다.
*   **`resume_parser.py`**: 작업 관리자
    *   Celery 태스크로 동작하며, 파일이 업로드되면 `parse_resume.py`를 실행하고 결과를 DB에 저장한 뒤, 다음 단계인 '임베딩' 작업을 트리거합니다.

---

## 4. 🧠 지식 구축 (Vectorization) - `chunking.py`, `embedding.py`, `pgvector_store.py`, `resume_embedding.py`
이력서 내용을 AI가 검색하기 쉬운 '수학적 벡터' 형태로 저장하는 과정입니다.

*   **`chunking.py` (쪼개기)**:
    *   이력서 전체를 한꺼번에 AI에게 주면 context 부족으로 헷갈려 합니다. 그래서 학력, 프로젝트, 자기소개서 문항 등 **의미 있는 단위**로 잘게 쪼갭니다.
*   **`embedding.py` (변환하기)**:
    *   `nlpai-lab/KURE-v1` 이라는 최신 한국어 임베딩 모델을 사용합니다. 텍스트를 **1024차원의 숫자 리스트**로 바꿉니다.
*   **`pgvector_store.py` (저장하기)**:
    *   숫자로 변환된 데이터를 PostgreSQL의 벡터 확장 기능(`pgvector`)을 통해 저장합니다.
*   **`resume_embedding.py` (오케스트레이터)**:
    *   이 모듈은 **임베딩 프로세스의 총괄 지휘자**입니다. `chunking`과 `embedding`, `pgvector_store`를 순서대로 호출하여 전체적인 지식 구축 흐름을 관리합니다. 작업이 완료되면 DB의 상태를 `completed`로 변경하여 면접 준비가 끝났음을 알립니다.

---

## 5. ❓ 질문 생성 및 검색 (RAG) - `question_generator.py` & `rag_retrieval.py`
이 시스템의 **가장 핵심적인 모듈**들입니다.

*   **`question_generator.py` (질문 생성기)**:
    *   `EXAONE 3.5` 모델과 `LangChain`을 사용하여 지원자 맞춤형 질문을 생성합니다.
    *   **시나리오 기반**: 전공자와 직무 전환자를 구분하여 상황에 맞는 질문 시나리오를 적용합니다.
*   **`rag_retrieval.py` (지식 검색기)**:
    *   이 모듈은 AI가 똑똑하게 질문할 수 있도록 **필요한 정보만 쏙쏙 뽑아주는 도서관 사서**와 같습니다.
    *   질문 생성 전, 이력서 벡터 DB에서 지금 질문과 가장 관련 있는 내용을 찾아 `question_generator`에게 전달합니다. 이를 통해 "이력서에 적힌 'A 프로젝트'에서 어떤 역할을 하셨나요?"와 같은 구체적인 질문이 가능해집니다.

---

## 6. 📝 평가 및 리포트 (Evaluation) - `evaluator.py`
면접이 끝나면 종합 성적표를 만드는 모듈입니다.

*   **다각도 평가**: Technical, Communication, Problem Solving 등 6가지 지표를 분석합니다.
*   **상세 피드백**: 지원자의 강점과 개선점을 시니어 면접관의 시각에서 정리하여 리포트로 생성합니다.

---

## 7. 👀 시각 분석 (Vision) - `vision.py`
지원자의 표정과 눈 움직임을 분석합니다.

*   **감정 분석**: `DeepFace`를 사용해 지원자의 실시간 감정 상태를 분석합니다.
*   **시선 추적**: OpenCV를 통해 지원자가 화면(면접관)을 얼마나 집중해서 바라보고 있는지 파악합니다.

---

## 💡 요약하자면
1.  **지원자**가 이력서를 올리면 → `resume_parser`가 실행되어 `parse_resume`, `chunking`, `embedding`, `pgvector_store`를 거쳐 지식이 저장됩니다. (전체 과정은 `resume_embedding`이 관리합니다.)
2.  **면접**이 시작되면 → AI가 `rag_retrieval`로 필요한 정보를 실시간 검색하고 → `question_generator`로 질문을 하며 → `stt/tts`로 끊김 없이 대화합니다.
3.  **종료**되면 → `evaluator`가 모든 기록을 종합하여 최종 결과 리포트를 출력합니다.

이 모든 과정이 Celery 태스크를 통해 병렬로 처리되어, 사용자는 실제 면접관과 대화하는 듯한 매끄러운 경험을 하게 됩니다. 🚀
