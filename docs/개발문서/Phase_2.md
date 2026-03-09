# 🔍 Phase 2: 지능형 면접 RAG 시스템 구축 설계서

> **작성일**: 2026-02-05
> **상태**: 🔄 **구현 진행 중 (Step 4 완료)**
> **목적**: 기업 인재상(Ideal)과 이력서 섹션별 데이터를 결합한 단계별 RAG 면접 시스템 구축

---

## 🚀 실행 과정 기록 (Current Progress)

### ✅ **Step 1: PostgreSQL HNSW 인덱스 생성 (완료)**

- **내용**: `resume_chunks.embedding`에 HNSW 기반 코사인 유사도 인덱스 적용.
- **효과**: 수만 개의 질문 및 이력서 조각 중 0.1초 내외로 유사 데이터 검색 가능.

### ✅ **Step 2: 검색 헬퍼 Task 구현 (완료)**

- **내용**: `ai-worker`에 쿼리 임베딩 생성 전용 Celery Task (`generate_query_embedding`) 등록.
- **모델**: KURE-v1 (1024차원) 사용하여 한국어 맥락 이해도 극대화.

### ✅ **Step 3: 기본 벡터 검색 API 구현 (완료)**

- **내용**: `/test/resumes/search` 엔드포인트 구축 완료.
- **현황**: 단순 벡터 검색 작동 확인됨.

### ✅ **Step 4: 이력서 섹션 라벨링 시스템 구축 (완료)**

**실행 일시**: 2026-02-05 16:15

#### **4-1. DB 스키마 수정**

**A. SectionType Enum 추가**
**파일**: `backend-core/models.py` (32-40줄)

```python
class SectionType(str, Enum):
    """이력서 섹션 타입 (RAG 검색 정확도 향상용)"""
    SKILL_CERT = "skill_cert"  # 기술 스택 + 자격증
    CAREER_PROJECT = "career_project"  # 경력 + 프로젝트
    COVER_LETTER = "cover_letter"  # 자기소개서
```

**B. ResumeChunk 모델에 section_type 필드 추가**
**파일**: `backend-core/models.py` (112-117줄)

```python
# 섹션 타입 (Phase 2: RAG 검색 정확도 향상)
section_type: Optional[SectionType] = Field(
    default=None,
    description="이력서 섹션 분류 (기술/경력/자소서)"
)
```

#### **4-2. 섹션 분류기 구현**

**파일**: `ai-worker/utils/section_classifier.py` (신규 생성)

**핵심 로직**:

```python
class ResumeSectionClassifier:
    SKILL_KEYWORDS = ["기술", "자격증", "프로그래밍", ...]
    CAREER_KEYWORDS = ["경력", "프로젝트", "인턴", ...]
    COVER_KEYWORDS = ["자기소개", "지원동기", "성격", ...]
  
    @classmethod
    def classify_chunk(cls, text: str, chunk_index: int = 0) -> str:
        # 키워드 매칭 점수 계산
        skill_score = sum(1 for kw in cls.SKILL_KEYWORDS if kw in text.lower())
        career_score = sum(1 for kw in cls.CAREER_KEYWORDS if kw in text.lower())
        cover_score = sum(1 for kw in cls.COVER_KEYWORDS if kw in text.lower())
      
        # 최고 점수 섹션 반환
        return max_score_section
```

#### **4-3. 파싱 파이프라인 통합**

**파일**: `ai-worker/tasks/resume_parser.py`

**수정 내용** (116-120줄):

```python
# Phase 2: 섹션 타입 자동 분류
section_type = ResumeSectionClassifier.classify_chunk(chunk_text, idx)

chunk_record = ResumeChunk(
    resume_id=resume_id,
    content=chunk_text,
    chunk_index=idx,
    section_type=section_type,  # 섹션 타입 추가!
    embedding=chunk_embedding
)
```

**로그 출력 예시**:

```
[Resume 9] 청크 0: skill_cert (길이: 245자)
[Resume 9] 청크 1: career_project (길이: 512자)
[Resume 9] 청크 2: cover_letter (길이: 1024자)
```

#### **4-4. 테스트 방법**

**A. 새 이력서 업로드**

1. `/test/resumes/upload` 엔드포인트 사용
2. Backend 로그에서 섹션 분류 확인

**B. DB 확인**

```sql
SELECT chunk_index, section_type, LEFT(content, 50)
FROM resume_chunks
WHERE resume_id = 10
ORDER BY chunk_index;
```

---

### ✅ **Step 5: 면접 컨텍스트 및 하이브리드 검색 API 구현 (완료)**

**실행 일시**: 2026-02-05 16:20

#### **5-1. 면접 컨텍스트 로드 API**

**목적**: 면접 시작 시 회사 인재상, 지원 직무, 이력서 정보를 한 번에 가져오기

**파일**: `backend-core/main.py` (882-940줄)

**엔드포인트**: `GET /interviews/{interview_id}/context`

**구현 코드**:

```python
@app.get("/interviews/{interview_id}/context")
async def get_interview_context(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 1. Interview 조회
    interview = db.get(Interview, interview_id)
  
    # 2. Company 정보 조회 (인재상 포함)
    company_data = None
    if interview.company_id:
        company = db.get(Company, interview.company_id)
        company_data = {
            "company_id": company.id,
            "company_name": company.company_name,
            "company_ideal": company.ideal,  # 핵심!
            "company_description": company.description
        }
  
    # 3. Resume 정보 조회
    resume_data = {...}
  
    return {
        "interview_id": interview.id,
        "position": interview.position,
        "company": company_data,
        "resume": resume_data
    }
```

**응답 예시**:

```json
{
  "interview_id": 1,
  "position": "보안 엔지니어",
  "company": {
    "company_id": "AHNLAB",
    "company_name": "안랩",
    "company_ideal": "정직, 최고, 협력을 추구하는 보안 전문가",
    "company_description": "대한민국 대표 보안 기업"
  },
  "resume": {
    "resume_id": 10,
    "file_name": "최승우_이력서.pdf",
    "processing_status": "completed"
  }
}
```

**활용 방법**:

- 면접 시작 시 이 API를 호출하여 컨텍스트를 로컬 세션에 저장
- 이후 모든 질문 생성 시 `company_ideal`을 LLM System Prompt에 주입

---

### 🎯 이력서 섹션별 청킹 및 매핑 규칙 (Mappings)

AI 면접관이 질문을 생성할 때, 이력서의 특정 부분을 정확히 참조하기 위해 다음과 같은 엄격한 분류 규칙을 따릅니다.

| 면접 단계              | 참조 섹션 (`section_type`) | 이력서 내 추출 대상 (Content)                                                  | 주요 분류 키워드 (AI 가이드)                         |
| :--------------------- | :--------------------------- | :----------------------------------------------------------------------------- | :--------------------------------------------------- |
| **1. 직무 지식** | **`skill_cert`**     | 기술 스택(Python, C++ 등), 자격증(정보보안기사 등), 전문 툴(Wireshark, AWS 등) | 기술, 자격증, 스택, 언어, 프레임워크, 도구, 환경     |
| **2. 직무 경험** | **`career_project`** | 경력 사항(인턴, 정규직 근무지), 프로젝트 명칭, 수행 역할, 구체적 기술적 성과   | 경력, 프로젝트, 인턴, 담당, 수행, 구축, 인프라, 설계 |
| **3. 문제 해결** | **`career_project`** | 위 경력/프로젝트 중 트러블슈팅 사례, 난이도가 높았던 기술적 도전 과제          | (직무 경험 섹션에서 고난도 키워드 중심 추출)         |
| **4. 인성 평가** | **`cover_letter`**   | 자기소개서, 지원동기, 성장과정, 성격의 장단점, 입사 후 포부 및 가치관          | 자기소개, 지원동기, 성격, 가치관, 포부, 배움, 극복   |

---

#### **[상세 추출 로직]**

1. **직무 지식 추출 (`skill_cert`):**

   * **역할**: 지원자의 '전문성 하드웨어' 확인.
   * **추출 예시**: "정보보안기사 취득", "Wireshark를 통한 패킷 분석 가능", "Linux 커널 보안 패치 경험" 등.
   * **질문 생성**: 위 텍스트를 기반으로 "Wireshark를 사용해 실제 탐지했던 가장 위험한 프로토콜은 무엇인가요?"와 같은 이론/실무 질문 생성.
2. **직무 경험 추출 (`career_project`):**

   * **역할**: 실제 실무 환경에서의 '문제 해결력' 확인.
   * **추출 예시**: "KISA 보안관제 인턴 근무 (6개월)", "Snort 기반의 IDS 룰 최적화 프로젝트 수행" 등.
   * **질문 생성**: "IDS 룰 최적화 과정에서 오탐(False Positive)을 줄이기 위해 어떤 데이터셋을 참조하셨나요?"와 같은 고난도 압박 질문 생성.
3. **인성/가치관 추출 (`cover_letter`):**

   * **역할**: 기업의 인재상(Ideal)과의 '문화적 적합성' 확인.
   * **추출 예시**: "저는 어떤 상황에서도 원칙을 지키는 정직함을 최고 가치로 생각합니다", "안랩의 보안 사명감에 깊이 감동하여..." 등.
   * **질문 생성**: "정직함을 중시하신다고 했는데, 보안 사고 보고와 기한 엄수 중 하나를 선택해야 하는 압박 상황이라면 어떻게 하시겠습니까?"와 같은 상황 질문 생성.

---

#### **5-3. 수정된 파일 목록**

| 파일                     | 수정 내용                     | 라인     |
| ------------------------ | ----------------------------- | -------- |
| `backend-core/main.py` | 면접 컨텍스트 로드 API 추가   | 882-940  |
| `backend-core/main.py` | HybridSearchRequest 모델 정의 | 943-950  |
| `backend-core/main.py` | 하이브리드 검색 API 구현      | 952-1060 |

---

#### **5-4. 다음 단계 활용 시나리오**

**직무 지식 질문 생성 흐름**:

1. `GET /interviews/1/context` → 안랩 인재상 로드
2. `POST /search/hybrid` (section_type=`skill_cert`) → 기술 스택 청크 검색
3. LLM에게 전달: `[안랩 인재상] + [기술 스택 청크] + [질문 은행]` → 맞춤형 질문 생성

**직무 경험 질문 생성 흐름**:

1. 동일한 컨텍스트 사용
2. `POST /search/hybrid` (section_type=`career_project`) → 프로젝트 경험 검색
3. LLM 생성

---

## 🏗️ Phase 2 고도화 설계 (Strategy)

### 1. 데이터 구조화 전략 (Indexing Strategy)

#### **A. 이력서 구조화 (Resume Chunking)**

- **테이블**: `resume_chunks`
- **추가 칼럼**: `section_type` (Enum)
  - `SKILL_CERT`: 기술 스택 + 자격증
  - `CAREER_PROJECT`: 경력 + 프로젝트
  - `COVER_LETTER`: 자기소개서

#### **B. 질문 은행 구조화 (Question Categorization)**

- **테이블**: `questions`
- **분류**: `직무지식`, `직무경험`, `인성`

#### **C. 기업 인재상 연동 (Company Ideal)**

- **테이블**: `companies`
- **역할**: LLM System Prompt에 주입

---

### 2. 단계별 RAG 검색 및 생성 프로세스

| 면접 단계              | 이력서 소스        | DB 질문 타겟             | LLM 생성 전략        |
| :--------------------- | :----------------- | :----------------------- | :------------------- |
| **0. 준비**      | 지원 회사 ID       | `Companies` (Ideal)    | 기업 가치관 로드     |
| **1. 직무 지식** | `SKILL_CERT`     | `Questions` (직무지식) | [기술] + [인재상]    |
| **2. 직무 경험** | `CAREER_PROJECT` | `Questions` (직무경험) | [경험] + [인재상]    |
| **3. 문제 해결** | `CAREER_PROJECT` | (Direct Generation)      | [프로젝트] + [Ideal] |
| **4. 인성 평가** | `COVER_LETTER`   | `Questions` (인성)     | [자소서] + [Ideal]   |

---

## 📝 향후 구현 (Next Steps)

### **Step 5: 섹션 기반 검색 API 고도화**

- `section_type` 필터를 사용하는 하이브리드 검색 구현
- 기업 인재상 주입 프롬프트 템플릿 개발

### **Step 6: 질문 및 모범답안 일괄 임베딩**

- `questions`와 `answer_bank` 데이터 벡터화

---

## 📊 기대 효과

**보안 엔지니어 최승우 지원자 + 안랩(인재상: 정직/최고/협력)**:

1. "방화벽 운영" 기술에서 **정직함**을 묻는 질문
2. "IDS 프로젝트"에서 **최고의 성과** 검증
3. 전 과정에서 **안랩맨** 적합성 평가

---

## ✅ 완료 체크리스트

- [X] PostgreSQL HNSW 인덱스 생성
- [X] 쿼리 임베딩 생성 Task 등록
- [X] 기본 벡터 검색 API 구축
- [X] **ResumeChunk 테이블 내 라벨(`section_type`) 추가**
- [X] **키워드 기반 이력서 섹션 분류기 구현**
- [X] **파싱 파이프라인에 섹션 분류 로직 통합**
- [X] **면접 컨텍스트 로드 API 구현**
- [X] **섹션 기반 하이브리드 검색 API 구현**
- [ ] **질문 은행 데이터 임베딩 및 DB 동기화**
- [ ] **기업 인재상 주입 프롬프트 엔진 개발**
- [ ] **LLM 기반 섹션 분류 고도화** (향후)
