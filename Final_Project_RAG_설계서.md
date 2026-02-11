# 산출물 2 : Final_Project_RAG_설계서 (심화 상세 버전)

## 1. 문서 개요
### 1.1 문서 목적
본 문서는 멀티모달 생성형 AI 면접 시스템의 핵심 로직인 **RAG(Retrieval-Augmented Generation)** 아키텍처를 정의한다. 특히 `ai-worker/tasks` 내의 각 모듈이 이력서 업로드 이후 데이터를 어떻게 파싱, 임베딩, 저장하여 생성형 AI의 근거 자료로 활용하는지 상세 설계 수치를 포함하여 기술한다.

### 1.2 적용 범위
• **데이터 전처리**: 업로드된 PDF 이력서의 구조적 분석 및 벡터라이징
• **지식 저장소**: PostgreSQL + pgvector를 활용한 하이브리드 지식 베이스 구축
• **질문 및 평가**: RAG 컨텍스트 기반의 실시간 질문 생성 및 답변 검증

---

## 2. 모듈별 상세 역할 분석 (`ai-worker/tasks`)

| 파일명 | 핵심 역할 | 상세 기능 |
| :--- | :--- | :--- |
| **`parse_resume.py`** | **구조적 텍스트 추출** | `pdfplumber`를 활용한 표(Table) 인식 및 Regex 기반의 섹션 분류 (헤더, 학력, 프로젝트 등) |
| **`save_structured.py`** | **정형 데이터 영속화** | 파싱된 JSON 데이터를 `resumes` 테이블의 `structured_data` (JSONB) 필드에 저장 |
| **`chunking.py`** | **의미 단위 분할** | 추출된 데이터를 검색 최적화 단위(Chunk)로 분할 및 카테고리 메타데이터 부여 |
| **`embedding.py`** | **고차원 벡터 변환** | `nlpai-lab/KURE-v1` 모델을 사용하여 텍스트를 고차원 밀집 벡터로 변환 |
| **`pgvector_store.py`** | **벡터 데이터베이스 관리** | `pgvector` 확장을 사용해 벡터와 메타데이터를 통합 저장 및 인덱싱 |
| **`rag_retrieval.py`** | **하이브리드 검색 엔진** | 벡터 유사도 검색과 SQL 메타데이터 필터링을 결합한 컨텍스트 추출 |
| **`question_generation.py`** | **LLM 질문 생성** | 면접관 페르소나와 추출된 컨텍스트를 결합하여 맞춤형 질문 생성 |
| **`evaluator.py`** | **답변 분석 및 리포트** | 지원자 답변의 논리성 평가 및 실시간 다음 질문 생성 트리거 |
| **`resume_pipeline.py`** | **워크플로우 오케스트레이션** | 위 모듈들을 순차적으로 실행하는 Celery 비동기 파이프라인 관리 |

---

## 3. 데이터 파이프라인 상세 설계 (Upload to Search)

### 3.1 Step 1: 구조적 파싱 (Parsing Logic)
`parse_resume.py`는 단순 텍스트 추출을 필터링하여 다음의 **7대 핵심 도메인**으로 정형화한다.
- **데이터 구조**: `header`, `education`, `activities`, `awards`, `projects`, `certifications`, `self_intro`
- **특이사항**: 자기소개서의 경우 질문(`question`)과 답변(`answer`)을 1:1 매핑하여 저장함으로써 검색 시 질문의 의도까지 컨텍스트에 포함되도록 설계함.

### 3.2 Step 2: 의미 기반 청킹 (Semantic Chunking Strategy)
`chunking.py`는 LLM의 컨텍스트 윈도우 효율성과 검색 정확도를 위해 다음 전략을 적용한다.
- **전략**: 섹션별 고정 가중치 부여 및 `RecursiveCharacterTextSplitter` 적용
- **설정값**: `Chunk Size 200`, `Overlap 70`
- **메타데이터 구조**: 
  - `category`: 검색 필터링용 태그 (ex: `project`, `activity`, `narrative` 등)
  - `subtype`: 세부 분류 (ex: `narrative_q`, `narrative_a`)

### 3.3 Step 3: 고성능 임베딩 (Embedding)
- **모델**: **`nlpai-lab/KURE-v1`** (한국어 지식 추출 최적화 모델)
- **차원**: 1024차원 (고차원 벡터를 통한 정밀한 유사도 측정)

### 3.4 Step 4: 벡터 저장 및 인덱싱 (Storage)
- **테이블**: `resume_embeddings`
- **인덱싱**: `embedding vector(1024)`와 `metadata JSONB`를 결합하여 저장.

---

## 4. RAG 검색 최적화: 시나리오 기반 메타데이터 필터링

### 4.1 하이브리드 Retrieval 설계 (정밀도 향상)
본 시스템은 단순히 전체 이력서에서 유사한 문장을 찾는 것이 아니라, **면접 단계에 최적화된 하이브리드 검색**을 수행한다.

- **원격 제어**: `interview_scenario.py`에 정의된 `category` 설정값을 활용.
- **필터링 메커니즘**:
  1. 질문 생성 태스크(`question_generation.py`)가 현재 면접 단계의 `category` 정보(예: `project`)를 읽어옴.
  2. 검색 엔진(`rag_retrieval.py`)에 해당 카테고리를 `filter_category`로 전달.
  3. DB 레벨에서 `metadata->>'category' = :filter_category` 조건을 통해 검색 범위를 1차 축소.
  4. 축소된 범위 내에서만 벡터 유사도 정렬(`ORDER BY embedding <=> :qv`)을 수행.

### 4.2 기대 효과
1. **검색 노이즈 제거**: 기술 면접 단계에서 자기소개서 내용이 섞여 나오는 등의 간섭 현상을 완벽히 차단.
2. **질문의 날카로움 증대**: LLM이 지원자의 특정 프로젝트나 특정 활동에만 집중하여 질문할 수 있는 환경 제공.
3. **DB 성능 최적화**: 검색 대상 데이터 군을 미리 필터링함으로써 검색 속도 및 인덱스 활용 효율 향상.

---

## 5. 결론 및 기대 효과
본 RAG 설계는 **'시나리오 → 메타데이터 필터링 → 벡터 검색'**으로 이어지는 3단계 정밀 프로세스를 통해 할루시네이션을 최소화하고 면접의 전문성을 극대화한다. 이를 통해 AI 면접관은 단순한 키워드 매칭을 넘어, 지원자의 상세 프로젝트 경험을 속속들이 파악하고 질문하는 **초개인화 면접 서비스**를 제공한다.
