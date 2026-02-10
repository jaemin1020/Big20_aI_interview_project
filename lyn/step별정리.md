

좋아! 그럼 네가 계획서에 바로 넣을 수 있도록, 단계별 파이프라인을 **Markdown(.md)** 형식으로 정리해줄게. 그대로 복사해서 GitHub, Notion, 또는 문서에 붙여넣기 가능하도록 만들었어.

```markdown
# AI 모의면접 파이프라인 단계별 정리

---

## [1] Resume Input (PDF/TXT)
- **목적:** 사용자가 제출한 이력서를 시스템이 읽을 수 있는 형태로 수집
- **입력:** PDF, TXT 등 다양한 포맷의 이력서
- **출력:** 원본 텍스트
- **주요 포인트:**
  - PDF의 경우 `pdfplumber`, `PyMuPDF` 같은 라이브러리 활용
  - 텍스트 추출 시 문단/표/리스트 구조 보존 고려
  - 전처리 단계에서 불필요한 공백, 특수문자 제거

---

## [2] Resume Parsing (LLM 기반 구조화)
- **목적:** LLM을 활용해 이력서를 JSON 구조로 변환
- **입력:** 원본 이력서 텍스트
- **출력:** 구조화된 JSON
```json
{
  "profile": {...},
  "experience": [...],
  "projects": [...],
  "skills": [...],
  "certs": [...],
  "education": [...]
}
```

* **주요 포인트:**
  * LLM (GPT-4o-mini, EXAONE, LlamaCpp) 활용
  * JSON 형식을 강제하여 후속 단계에서 자동 처리 가능
  * 이력서 내 모든 직무/프로젝트/교육/자격/기술 정보 포함

---

## [3] Resume Structured DB 저장 (PostgreSQL JSONB)

* **목적:** 구조화된 이력서를 DB에 저장하여 재사용, 검색, RAG 대응
* **입력:** Step 2에서 생성된 JSON
* **출력:** `Resume` 테이블 저장
* **주요 포인트:**
  * PostgreSQL `JSONB` 타입으로 저장 → 유연성 확보
  * Resume ID 기반으로 Chunk, Embedding 등 연계 가능
  * 사용자, 회사, 직무 정보와 연동 가능

---

## [4] Semantic Chunking (의미 단위 분리)

* **목적:** 이력서 내용을 의미 단위로 분할하여 LLM/임베딩 효율 향상
* **입력:** Resume JSON
* **출력:** 의미 단위 Chunk (sections/paragraphs)
* **주요 포인트:**
  * 단순 줄 단위 분리가 아니라 의미 기반 분리
  * Chunk 단위 최소 1~2 문장 이상 권장
  * Chunk에 metadata 포함: section_type, source, resume_id

---

## [5] Embedding 생성

* **목적:** 각 Chunk를 벡터화하여 유사도 검색 가능하게 함
* **입력:** Chunk 텍스트
* **출력:** 벡터 (예: 1536차원)
* **주요 포인트:**
  * OpenAI Embedding, Llama/ExaONE 임베딩 모델 활용 가능
  * 텍스트 → 고정 길이 벡터 변환
  * Metadata 포함 (chunk_type, resume_id 등)

---

## [6] pgvector 저장 (resume_embeddings)

* **목적:** Embedding + metadata를 벡터 DB에 저장하여 검색/질문 생성 활용
* **입력:** Chunk + Embedding + Metadata
* **출력:** `resume_embeddings` 테이블

```text
- resume_id
- chunk_type
- chunk_text
- embedding (vector)
- metadata (json)
```

* **주요 포인트:**
  * pgvector 확장 활용 (PostgreSQL)
  * 유사도 기반 검색 (Cosine, Euclidean)
  * RAG/QA 시스템과 직결

---

## [7] Question DB (질문 RAG DB)

* **목적:** 면접 질문을 저장하고 재사용
* **입력:** 사전 수집된 질문 데이터
* **출력:** 질문 테이블 (Question)

```text
- question_id
- question
- domain
- role
- skills
- context_type
- tags
```

* **주요 포인트:**
  * RAG 기반 질문 생성용
  * 직무/레벨/스킬별 분류
  * 통계 기반 질문 난이도/사용량 관리

---

## [8] RAG 기반 질문 생성

* **목적:** Resume 임베딩과 질문 DB를 활용해 맞춤 질문 생성
* **입력:** Resume Embedding, Question DB
* **출력:** Interview Session용 질문 리스트
* **주요 포인트:**
  * 유사도 검색 → 적합한 질문 선별
  * LLM로 context-aware 질문 변환 가능
  * 질문 Intent: 직무 지식 / 경험 / 문제 해결 평가 구분

---

## [9] Interview Engine

* **목적:** 실시간 면접 시나리오 진행
* **입력:** 질문 리스트, 사용자 응답
* **출력:** Transcript, 실시간 로그
* **주요 포인트:**
  * LLM 기반 질문 & 대화 관리
  * Multi-turn 대화 지원
  * Speaker 구분 (AI / Candidate)

---

## [10] Answer Parsing

* **목적:** 사용자 답변을 구조화된 데이터로 변환
* **입력:** Transcript 텍스트
* **출력:** Answer JSON
* **주요 포인트:**
  * LLM 또는 룰 기반 파서 사용
  * 핵심 문장 추출, 키워드 매핑
  * 루브릭 평가 연계 용이

---

## [11] Rubric Evaluation

* **목적:** 답변을 사전에 정의된 평가 기준으로 점수화
* **입력:** Answer JSON
* **출력:** 평가 점수, 코멘트
* **주요 포인트:**
  * LLM 기반 자동 점수 계산 가능
  * 평가 항목: 직무 지식, 경험, 문제 해결 능력, 소통 능력 등
  * 점수와 코멘트를 함께 제공

---

## [12] Score + Feedback + Report

* **목적:** 최종 면접 결과 제공
* **입력:** Rubric Evaluation 결과
* **출력:** 최종 점수, 피드백, 보고서 PDF/JSON
* **주요 포인트:**
  * 총점 + 항목별 점수
  * 피드백 메시지 자동 생성
  * Resume & Interview 기반 Personalized Report 생성
  * HR/채용자, 후보자용 모두 활용 가능

```

---

원하면 내가 **이 Markdown을 기반으로 한 그림 흐름도**도 만들어서 바로 계획서에 넣을 수 있게 시각화해줄 수도 있어.  

혹시 그거 만들어줄까?
```
