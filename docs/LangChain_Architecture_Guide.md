# 🦜 LangChain 기반 AI 인터페이스 설계 및 활용 가이드

본 문서는 **Big20 AI 면접 프로젝트**의 `ai-worker` 모듈에서 **LangChain**이 어떻게 활용되고 있는지, 그 구조와 핵심 문법, 그리고 도입 이유를 상세히 설명합니다.

---

## 1. LangChain 도입 배경 및 이유

### 🌟 랭체인(LangChain)을 사용하면 무엇이 좋은가? (핵심 장점)

개발자가 LLM을 직접 호출(Raw API)하지 않고 랭체인을 거쳐서 사용하는 이유는 **"단순한 호출기 이상의 프레임워크"**이기 때문입니다.

1.  **모델 교체 및 확장성 (Model Agnosticity)**: 
    *   OpenAI, Claude 같은 유료 API부터 Llama, EXAONE 같은 로컬 모델까지 **코드 한 줄만 바꾸면** 바로 교체할 수 있습니다. 특정 모델에 종속되지 않는 유연한 아키텍처를 제공합니다.
2.  **레고 블록 같은 모듈화 (Modular Design)**:
    *   프롬프트(Prompt), 모델(LLM), 데이터 가공(Output Parser)을 각각 독립된 블록으로 만듭니다. 이를 조립만 하면 되므로 로직이 섞이지 않아 유지보수가 훨씬 쉽습니다.
3.  **복잡한 로직의 단순화 (LCEL)**:
    *   기존에는 "입력 -> 프롬프트 생성 -> 모델 호출 -> 데이터 파싱 -> 결과 반환" 과정을 복잡한 함수로 짜야 했으나, 랭체인의 **LCEL(파이프 연산자 `|`)**을 쓰면 한 줄의 선언만으로 모든 파이프라인이 완성됩니다.
4.  **RAG 인프라의 완성도**:
    *   검색 증강 생성(RAG)을 구현하려면 문서를 자르고, 벡터화하고, DB에 저장하고 검색하는 복잡한 과정이 필요한데, 랭체인은 이를 위해 이미 검증된 수백 개의 도구(Retriever, VectorStore 등)를 기본 제공합니다.
5.  **강력한 디버깅 (LangSmith)**:
    *   AI가 왜 이런 답변을 했는지, 중간 과정에서 프롬프트가 어떻게 전달되었는지 모든 트레이싱(Tracing)을 자동으로 기록해주어 **블랙박스인 AI 내부를 투명하게** 볼 수 있습니다.

### 도입 이유 요약
*   **표준화된 인터페이스**: 다양한 LLM을 동일한 방식으로 관리.
*   **개발 생산성**: 복잡한 체인 구성을 코드가 아닌 선언적 구조로 설계.
*   **RAG 구현 최적화**: 이력서 기반 면접 질문 생성을 위한 최적의 도구 모음 제공.

---

## 2. 모듈별 활용 현황 및 상세 분석

### 2.1. [LLM 엔진 코어] `utils/exaone_llm.py`
이 모듈은 프로젝트의 두뇌 역할을 하는 로컬 LLM(EXAONE)을 LangChain 생태계에 통합하는 가장 핵심적인 지점입니다.

*   **사용된 랭체인 클래스**: 
    *   `langchain_core.language_models.llms.LLM`: 커스텀 LLM 구현을 위한 베이스 클래스.
    *   `langchain_core.callbacks.manager.CallbackManagerForLLMRun`: 실행 중 콜백 관리를 위한 객체.
*   **활용 코드 분석**:
    ```python
    class ExaoneLLM(LLM):
        # 랭체인의 추상 메서드 _call을 오버라이딩하여 
        # 로컬 GGUF 모델(llama-cpp-python) 호출 로직을 구현합니다.
        def _call(self, prompt, stop=None, run_manager=None, **kwargs):
            output = self.llm(prompt, ...)
            return output['choices'][0']['text']
    ```
*   **도입 이유**: 랭체인의 `LLM` 클래스를 상속받음으로써, 이후에 등장하는 모든 `PromptTemplate`나 `LCEL Chain` 구문에서 이 모델을 마치 OpenAI 모델인 것처럼 똑같이 사용할 수 있게 됩니다.

### 2.2. 기타 파이썬 유틸리티 (`utils` 폴더 내 다른 모듈)
분석 결과, `utils` 폴더의 다른 모듈(`resume_embedder.py`, `vector_utils.py` 등)은 랭체인의 추상화 계층을 사용하지 않고 **Native 라이브러리**를 직접 사용하여 성능과 제어권을 확보했습니다.

*   **`vector_utils.py`**: 랭체인의 `HuggingFaceEmbeddings` 대신 `sentence_transformers`를 직접 사용합니다. 이는 로컬 환경에서의 임베딩 생성 속도를 최적화하고 모델 로딩 방식을 더 세밀하게 제어하기 위함입니다.
*   **`section_classifier.py` / `validation.py`**: 순수 파이썬 로직과 정규식(Regex)을 사용하여 AI 모델을 호출하지 않고도 빠른 규칙 기반 처리를 수행합니다.

### 2.3. [질문 생성 파이프라인] `tasks/question_generator.py` (핵심)
이 모듈은 면접 상황에 맞는 질문을 실시간으로 생성하는 핵심 파이프라인입니다.

*   **사용된 문법 (LCEL)**:
    ```python
    # 4. LCEL 체인 정의 (Prompt | LLM | Parser)
    prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
    llm = get_exaone_llm()
    output_parser = StrOutputParser()

    chain = prompt | llm | output_parser
    
    # 실행
    content = chain.invoke({
        "position": target_role,
        "name": candidate_name,
        "stage": stage_name,
        "context": rag_context
    })
    ```
*   **도입 효과**: 프롬프트 로직과 모델 로직을 분리하여 유지보수성이 극대화되었습니다.

### 2.3. [RAG 검색 시스템] `tasks/rag_retrieval.py` & `pgvector_store.py`
지원자의 이력서 정보를 기반으로 질문을 던지기 위해 RAG 기술이 사용되었습니다.

*   **기술 스택**: `HuggingFaceEmbeddings` + `PGVector` (PostgreSQL)
*   **핵심 로직**:
    1.  이력서 텍스트를 `RecursiveCharacterTextSplitter`로 분 분할.
    2.  HuggingFace 모델로 벡터화(Embedding) 후 DB 저장.
    3.  질문 생성 시 관련 이력서 문맥을 **Similarity Search**로 검색하여 LLM에 전달.

### 2.4. [답변 분석 및 결과 추출] `tasks/evaluator.py`
사용자의 답변을 분석하여 정형화된 JSON 데이터를 추출할 때 사용됩니다.

*   **핵심 도구**: `JsonOutputParser`
*   **이유**: LLM의 자유로운 출력을 서비스에서 바로 사용할 수 있는 JSON 객체로 강제 변형하기 위함입니다.

---

## 3. 핵심 랭체인 개념 및 문법 가이드

### ① LCEL (LangChain Expression Language)
체인을 만드는 선언적 언어입니다.
*   **문법**: `chain = prompt | model | output_parser`
*   **장점**: 비동기 실행, 트레싱, 배치 처리 등이 자동으로 지원됩니다.

### ② PromptTemplate
LLM에게 전달할 명령을 구조화합니다.
*   **변수 사용**: `{name}`, `{position}` 처럼 플레이스홀더를 사용하여 동적인 프롬프트 생성이 가능합니다.

### ③ Retriever
RAG의 핵심인 '검색기'입니다.
*   **작동 원리**: "이력서 중 보안 관련 내용만 가져와"라는 요청에 대해 벡터 거리가 가까운 문서를 반환합니다.

---

## 4. 향후 발전 방향

*   **LangSmith 연동**: 모든 AI 호출 로그를 추적하여 질문의 질을 지속적으로 개선할 예정입니다.
*   **Agent 구조**: 단순 질문 생성에서 벗어나, 면접자의 답변에 따라 유동적으로 단계를 결정하는 **상태 기반 에이전트**로 고도화가 가능합니다.

---
**문서 작성 완료.** 본 프로젝트의 AI 아키텍처는 LangChain을 통해 표준화되어 관리됩니다.
