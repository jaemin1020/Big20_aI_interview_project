# 📑 AI-워커 엔진 상세 진행 보고서 (통합본)

---

## 📄 [01-파싱.md] PDF 파싱 엔진 기술 분석 및 이력서 구조화 시스템 종합 보고서

# 📑 PDF 파싱 엔진 기술 분석 및 이력서 구조화 시스템 종합 보고서

---

## 1. 시스템 개요

본 문서는 **pdfplumber 기반 이력서 자동 파싱 시스템**의 기술적 구조와 동작 원리를 설명하는 종합 보고서입니다.

본 시스템은 다음 두 가지를 동시에 수행합니다.

1. PDF 내부 객체(Object) 기반 텍스트·표 추출
2. 추출 데이터를 구조화된 JSON 형태로 변환

핵심 목표는 다음과 같습니다.

* 이력서의 **정형 데이터(학력, 경력, 수상 등)**를 정확히 매핑
* 표 기반 레이아웃을 최대한 보존
* 비정형 자기소개서까지 구조적으로 분리

---

# 2. PDF 파싱 엔진 핵심 원리

## 2-1. 객체 기반 추출 (Object-Based Extraction)

본 시스템은 pdfplumber를 사용합니다.

pdfplumber는 OCR 방식이 아닙니다.

즉,

❌ 이미지를 보고 글자를 추측하지 않음
✅ PDF 내부 객체 데이터 직접 분석

PDF 내부에는 다음 정보가 저장되어 있습니다.

* 문자(Char)

  * x0, x1, top, bottom 좌표
  * 폰트
  * 크기
* 선(Line)
* 사각형(Rect)
* 기타 그래픽 객체

이 정보를 조합하여 문서 구조를 재구성합니다.

---

## 2-2. 좌표 시스템 기반 구조 인식

pdfplumber는 페이지를 하나의 좌표 평면으로 간주합니다.

### 텍스트 문장 인식

* 같은 y축에 일정 간격으로 배열 → 하나의 문장
* x좌표 간격 → 띄어쓰기 판단

### 표(Table) 인식

* 선(Line) 객체 감지
* 선이 교차하는 지점 → 셀(Cell) 생성
* 행(Row), 열(Column) 구성

이 원리 덕분에 이력서처럼 표가 많은 문서에 매우 강력합니다.

---

# 3. 전체 파싱 아키텍처

시스템 흐름은 다음과 같습니다.

```
PDF 입력
   ↓
pdfplumber 객체 추출
   ↓
텍스트 + 표 데이터 분리 수집
   ↓
섹션 상태 전환(State Machine)
   ↓
카테고리별 구조화
   ↓
JSON 출력
```

---

# 4. 코드 상세 분석

아래 코드를 기준으로 매우 상세히 설명합니다.

---

# 4-1. 유틸리티 함수 분석

---

## ① clean_text(text)

### 목적

* 불필요한 공백 제거
* 줄바꿈 통합
* 정규식 매칭 정확도 향상

### 코드 핵심

```python
return re.sub(r'\s+', ' ', text).strip()
```

### 동작 원리

* `\s+` → 하나 이상의 공백
* 모든 공백을 단일 스페이스로 변환
* 앞뒤 공백 제거

### 입력 / 출력 예시

입력:

```
"  홍길동   \n  백엔드   개발자  "
```

출력:

```
"홍길동 백엔드 개발자"
```

---

## ② get_row_text(row)

### 목적

* 표 한 줄을 하나의 문자열로 결합
* 섹션 키워드 탐지용

### 예시

입력:

```
["학력", "", ""]
```

출력:

```
"학력"
```

입력:

```
["2020.03", "서울대학교", "컴퓨터공학과"]
```

출력:

```
"2020.03서울대학교컴퓨터공학과"
```

공백 제거 후 붙입니다.

---

## ③ is_date(text)

### 목적

* 날짜 또는 연도 포함 여부 확인

정규식:

```
\d{4}
```

### 예시

입력:

```
"2023.03 ~ 2024.02"
```

출력:

```
True
```

입력:

```
"컴퓨터공학과"
```

출력:

```
False
```

---

# 4-2. 메인 함수: parse_resume_final()

---

## 1단계: 기본 데이터 구조 생성

```python
data = {
    "header": { "name": "", "target_company": "", "target_role": "" },
    "education": [],
    "activities": [],
    "awards": [],
    "projects": [],
    "certifications": [],
    "self_intro": []
}
```

### 출력 형태 예시

```json
{
  "header": {
    "name": "홍길동",
    "target_company": "삼성전자",
    "target_role": "백엔드 개발"
  },
  "education": [],
  ...
}
```

---

## 2단계: 입력 소스 판별

```python
is_file_path = False
```

조건:

* 문자열이 .pdf로 끝남
* 실제 파일 존재

→ 파일로 판단

아니면 텍스트로 판단

---

## 3단계: PDF에서 데이터 추출

### 텍스트 추출

```python
text = page.extract_text()
```

### 예시 출력

```
이름 : 홍길동
지원직무 : 백엔드 개발
```

---

### 표 추출

```python
tables.extend(page.extract_tables())
```

### 예시 출력 구조

```
[
  [
    ["이름", "홍길동"],
    ["지원직무", "백엔드 개발"]
  ],
  [
    ["학력"],
    ["2020.03~2024.02", "서울대학교", "컴퓨터공학과", "3.8/4.5"]
  ]
]
```

---

# 5. 헤더(Header) 파싱 로직

## 로직 설명

1. "이름" 찾음
2. 오른쪽 칸(i+1) 값 가져옴
3. 없으면 i+2 확인

### 예시 표 입력

```
["이름", "홍길동"]
```

출력:

```json
"header": {
  "name": "홍길동"
}
```

---

## 폴백 로직 (정규식)

표에 이름이 없으면:

```
이\s*름\s*[:：\-\s]+([가-힣]{2,4})
```

입력:

```
이름 : 홍길동
```

출력:

```
홍길동
```

---

# 6. 섹션 상태 관리 (State Machine)

변수:

```python
current_section
```

동작 방식:

| 발견 키워드 | 상태 변경      |
| ----------- | -------------- |
| 학력        | education      |
| 경력/활동   | activities     |
| 수상        | awards         |
| 자격증      | certifications |
| 프로젝트    | projects       |

---

# 7. 학력 파싱 상세 분석

입력 예시:

```
["2020.03~2024.02", "서울대학교-컴퓨터공학과", "3.8/4.5"]
```

### 분해 과정

1. period → 첫 칸
2. 학교명 → parts[0]
3. 전공 → parts[1]
4. 학점 → GPA 패턴 검색

### 출력 예시

```json
{
  "period": "2020.03~2024.02",
  "school_name": "서울대학교",
  "major": "컴퓨터공학과",
  "gpa": "3.8/4.5"
}
```

---

# 8. 활동(Activities) 파싱

입력:

```
["2023.01~2023.06", "AI 프로젝트 - 1등 (2023)", "팀장", "하이브본사"]
```

### 처리 단계

1. 괄호 안 날짜 추출
2. * 기준 분리
3. 역할 보강

출력:

```json
{
  "period": "2023",
  "title": "AI 프로젝트",
  "role": "팀장",
  "organization": "하이브본사"
}
```

---

# 9. 수상(Awards) 파싱

입력:

```
["2023", "AI 경진대회 - 최우수상", "한국정보원"]
```

출력:

```json
{
  "date": "2023",
  "title": "AI 경진대회",
  "organization": "한국정보원"
}
```

---

# 10. 프로젝트 파싱

입력:

```
["2024.01", "RAG 기반 챗봇 개발", "FastAPI"]
```

출력:

```json
{
  "period": "2024.01",
  "title": "RAG 기반 챗봇 개발",
  "organization": "FastAPI"
}
```

---

# 11. 자기소개서(Self Introduction) 분리

정규식:

```
(\[질문\d+\].*?(?:주십시오|세요))
```

### 입력 예시

```
[질문1] 지원 동기를 작성하세요
저는 백엔드 개발자가 되고 싶습니다.

[질문2] 협업 경험을 작성하세요
...
```

### 출력

```json
[
  {
    "question": "[질문1] 지원 동기를 작성하세요",
    "answer": "저는 백엔드 개발자가 되고 싶습니다."
  }
]
```

---

# 12. 라이브러리 비교 분석

| 라이브러리   | 특징                  | 강점                | 한계                     |
| ------------ | --------------------- | ------------------- | ------------------------ |
| pdfplumber   | 객체 기반 고수준 추출 | 표 인식 강력        | 대용량 문서 느릴 수 있음 |
| PyPDF2       | 저수준 조작           | 병합/분할 빠름      | 표 인식 거의 없음        |
| pdfminer.six | 상세 로우데이터       | 폰트/좌표 완전 제어 | 복잡                     |
| Camelot      | 표 특화               | 격자 표 강력        | 텍스트 추출 약함         |
| Tesseract    | OCR 엔진              | 스캔 PDF 가능       | 느리고 오타 발생         |

---

# 13. 결론

본 시스템은 다음 이유로 pdfplumber를 채택하였습니다.

1. 이력서의 대부분은 표 기반
2. 좌표 기반 매칭 가능
3. 항목-값 매칭 정확도 우수
4. 상태 전환 기반 구조화 가능

단, 스캔 PDF 대응 시에는 OCR 엔진(Tesseract)와의 하이브리드 구성이 필요합니다.

---

# 🔥 최종 결과 예시 (전체 출력)

```json
{
  "header": {
    "name": "홍길동",
    "target_company": "삼성전자",
    "target_role": "백엔드 개발"
  },
  "education": [
    {
      "period": "2020.03~2024.02",
      "school_name": "서울대학교",
      "major": "컴퓨터공학과",
      "gpa": "3.8/4.5"
    }
  ],
  "activities": [],
  "awards": [],
  "projects": [],
  "certifications": [],
  "self_intro": []
}
```

---

# 📌 종합 평가

본 코드는 단순 텍스트 추출이 아닌,

* 객체 기반 분석
* 표 구조 인식
* 상태 머신 기반 분류
* 정규식 보강 로직
* 예외 대응 처리

까지 포함한 **준-프로덕션 수준 이력서 파싱 엔진**입니다.

---

## 📄 [02-청킹.md] 이력서 AI 분석 시스템: 파싱 및 청킹 엔진 심층 분석

# 📑 [기술 명세서] 이력서 AI 분석 시스템: 파싱 및 청킹 엔진 심층 분석

본 문서는 PDF에서 추출된 비정형 데이터를 AI가 가장 효율적으로 이해할 수 있는 형태인 **'의미 단위의 조각(Chunk)'**으로 재구성하는 기술적 매커니즘을 상세히 다룹니다.

---

## 1. 텍스트 분할 전략: `RecursiveCharacterTextSplitter`

가장 먼저 살펴볼 부분은 데이터를 자르는 **'도구'**의 설정입니다. 단순히 글자 수로 자르는 것은 AI에게 문맥이 잘린 쓰레기 데이터를 주는 것과 같습니다.

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " ", ""]
)

```

### 🔍 깊이 있는 분석

* **재귀적 분할 (Recursive Splitting)**: 이 분할기는 `separators` 리스트의 순서대로 자를 지점을 찾습니다.

1. 가장 먼저 **문단(`\n\n`)**을 찾습니다. 문단이 통째로 600자 이내라면 그대로 한 조각이 됩니다.
2. 문단이 너무 길면 **줄바꿈(`\n`)**을 찾고, 그다음은 **마침표(`.`)**을 찾습니다.
3. 결과적으로 문장 중간이 툭 끊기지 않고, 최대한 의미가 완결되는 지점에서 조각이 나뉩니다.

* **청크 오버랩 (100자)**: 조각 A의 끝 100자와 조각 B의 앞 100자를 겹치게 만듭니다. 이는 AI가 검색된 조각만 읽었을 때 앞뒤 문맥을 몰라 발생하는 **'할루시네이션(환각)'**을 방지하는 아주 중요한 장치입니다.

---

## 2. 항목별 데이터 처리 로직 및 문법 분석

코드는 각 항목의 특성에 맞춰 데이터를 **'시맨틱(Semantic) 문장'**으로 가공합니다.

### ① 안전한 데이터 접근 (`.get()` 문법)

```python
header = parsed_data.get("header", {})
educations = parsed_data.get("education", [])

```

* **분석**: `parsed_data["header"]`라고 직접 접근하면 해당 키가 없을 때 프로그램이 즉시 종료됩니다. `.get("key", default)`를 사용하여 데이터가 누락된 이력서라도 에러 없이 유연하게 넘어가도록 설계되었습니다.

### ② 정형 데이터의 자연어 변환 (Feature Engineering)

```python
text = f"[학력] {school} {major} ({status})"
if period: text += f" - {period}"
if gpa: text += f", 학점: {gpa}"

```

* **분석**: 흩어져 있는 학교, 전공, 학점 데이터를 하나의 완성된 문장으로 합칩니다.
* **이유**: AI 모델(LLM)은 키-값 형태의 데이터보다 **"지원자는 한국대학교에서 컴퓨터공학을 전공하고 졸업했습니다."**와 같은 자연어 형태에서 훨씬 더 높은 검색 정확도를 보이기 때문입니다.

### ③ 프로젝트 및 자기소개서의 지능적 분할

이 부분은 이력서에서 가장 긴 텍스트가 발생하는 구간입니다.

```python
if len(text) > 400:
    split_texts = text_splitter.split_text(text)
    for i, st in enumerate(split_texts):
        chunks.append({
            "text": f"(부분 {i+1}) {st}",
            "metadata": { ..., "title": title }
        })

```

* **로직**: 텍스트가 400자를 초과하면 위에서 정의한 `text_splitter`를 가동합니다.
* **`enumerate`의 활용**: 조각난 텍스트에 `(부분 1)`, `(부분 2)`와 같은 인덱스를 붙여, 나중에 AI가 "이 내용은 프로젝트의 앞부분이구나"라고 인지할 수 있게 돕습니다.

---

## 3. EXAONE 3.5 (32k) 모델 환경에서 이 코드가 빛나는 이유

"EXAONE 3.5는 한 번에 32,000 토큰을 읽는데, 왜 600자씩 자르나요?"라는 의문에 대한 기술적 답변입니다.

### 3.1 "Lost in the Middle" 현상 원천 차단

아무리 컨텍스트 창이 넓어도 모델은 입력된 텍스트의 **중간 부분에 있는 정보**를 가장 잘 놓칩니다. 600자 단위의 명확한 조각을 주면 모델은 그 정보에 100% 집중할 수 있습니다.

### 3.2 수천 명의 데이터 확장성 (Vector Search)

질문이 들어왔을 때 이력서 1,000장을 한꺼번에 모델에 넣으면 비용과 시간이 엄청나게 소모됩니다.

* **해결**: 청킹된 데이터는 벡터 DB에 저장됩니다. 사용자가 "Python 경험자 찾아줘"라고 하면, 이 코드에서 만든 `category: experience`인 조각 중 Python이 언급된 **핀포인트 조각 5개만** 골라 EXAONE 모델에게 전달합니다. 이것이 바로 고효율 RAG의 핵심입니다.

---

## 4. 메타데이터(Metadata) 설계 명세

이 코드는 텍스트만 저장하는 것이 아니라, 각 조각에 **'디지털 이름표'**를 붙입니다.

| 필드명                     | 데이터 예시              | 역할                                                    |
| -------------------------- | ------------------------ | ------------------------------------------------------- |
| **`source`**       | "resume"                 | 데이터의 출처가 이력서임을 명시                         |
| **`category`**     | "narrative", "education" | 특정 항목(예: 학력만, 자소서만)에 대한 필터링 검색 지원 |
| **`subtype`**      | "answer", "question"     | 자기소개서의 질문과 답변을 구분하여 맥락 파악력 향상    |
| **`question_ref`** | "지원동기를 쓰시오..."   | 조각난 답변이 어떤 질문에 대한 것인지 연결고리 제공     |

---

## 💡 최종 결론

본 시스템의 `chunk_resume` 함수는 단순히 텍스트를 자르는 기능적 역할을 넘어, **비정형 이력서 데이터를 AI가 가장 선호하는 '고품질 지식 조각'으로 승화시키는 전처리 공정**입니다.

특히 **EXAONE 3.5**와 같은 대형 모델과 결합될 때, 이 정교한 청킹 전략은 모델의 추론 속도를 높이고, 비용을 절감하며, 무엇보다 **정보 검색의 정확도를 비약적으로 상승**시키는 핵심 엔진 역할을 수행합니다.

---

## 📄 [03.엑사원모델.md] EXAONE-3.5 모델 성능 및 기술 상세

### 컨텍스트 길이 확장 및 성능 유지 (5page)

- **단계적 컨텍스트 확장**: K-EXAONE은 기본적으로 8K 토큰까지 프리트레이닝된 후, 두 단계에 걸쳐 컨텍스트 길이를 32K, 256K로 확장함. 각 단계에서 데이터 샘플링 비율을 조정하여 장문맥 학습 신호와 안정성을 균형 있게 반영함.
- **Rehearsal Dataset**: 장문맥 특화 학습 시 단기(짧은 문맥) 성능 저하를 방지하기 위해, 프리트레이닝 분포 및 기타 단기 데이터에서 고품질 샘플을 재사용하는 Rehearsal Dataset을 도입. 이 데이터셋은 8K→32K, 32K→256K 확장 단계 모두에 포함되며, 각 단계별로 비율을 조정하여 장문맥 신호와 단기 신호가 모두 반영되도록 설계됨. 이를 통해 컨텍스트 확장 후에도 단기 벤치마크 및 내부 검증 지표에서 성능 저하가 없음을 확인함.
- **Synthetic Reasoning Dataset**: 수학, 과학, 경쟁 프로그래밍 등 고난도 문제와 중간 추론(Intermediate Reasoning)을 포함하는 합성 데이터셋을 추가로 학습. 이 데이터셋은 최종 답뿐 아니라 중간 추론 패턴까지 학습하도록 설계되어, 다단계 추론력과 일관성, 복잡한 문제 해결력을 강화함. 장문맥 학습 단계 전체에 걸쳐 이 데이터셋을 통합하여, 긴 입력에서도 추론 품질이 유지되도록 함.
- **Long-Document Dataset**: 장기 의존성 학습을 위해, 전체 문서 단위의 시퀀스를 한 번에 입력하는 Long-Document Dataset을 활용. 이 데이터셋은 문서 전체를 잘라내지 않고 통째로 입력하여, 모델이 장기적 토큰 간 관계를 학습하도록 유도함. 8K→32K 단계에서는 32K까지의 안정적 성능에 중점, 32K→256K 단계에서는 장문서 샘플 비중을 높여 256K까지의 장기 의존성 학습을 강화함.
- **Needle-In-A-Haystack(NIAH) 테스트**: 장문맥 정보 보존력 검증을 위해 NIAH 테스트를 반복적으로 실시. 이 테스트는 긴 입력 내에서 특정 정보를 얼마나 잘 기억하고 찾아내는지 평가하는 방식으로, 각 단계별로 모델이 목표 컨텍스트 길이에서 거의 완벽한 NIAH 성능을 달성할 때까지 학습을 반복함(그린라이트 기준).

### 포스트 트레이닝 및 정렬 (5~6page)

- **지도학습(SFT)**: 다양한 사용자 지시(instruction)에 따라 적절한 응답을 생성하도록 대규모 지도학습을 실시. 도메인별로 태스크를 분류하고, 각 도메인에 맞는 데이터 생성 방식 또는 전문가를 활용함. 한국어 특화 성능 강화를 위해 과기정통부, NIA, K-DATA 등에서 제공하는 공공 및 기관 데이터를 적극 활용함.
- **강화학습(RL)**: 수학, 코드, STEM, 지시이행 등 다양한 과제에 대해 verifiable reward(룰 기반+LLM 판정)를 활용해 RL을 수행. 오프폴리시 정책경사(truncated importance sampling), zero-variance filtering(동일 보상 샘플 제거), 그룹/글로벌 어드밴티지 정규화 등 최신 RL 기법을 적용. KL penalty는 제외하여 불필요한 계산을 줄이고 성능을 높임. RL 단계에서는 MoE 라우터를 고정(freeze)하여 안정성을 확보함.
- **Preference Learning**: RL 이후, 모델을 인간 선호에 더 잘 맞추기 위해 Preference Learning을 실시. GROUPER(Group-wise SimPER)라는 개선된 SimPER 변형을 도입, 그룹 단위로 여러 응답을 샘플링하고, 각 응답에 대해 다차원 평가 기준(룰 기반+루브릭 기반 생성 보상)을 결합하여 그룹 내 표준화 및 스케일링을 통해 선호도 정렬을 강화함.
- **실제 활용성 강화**: 에이전트 도구 사용, 웹서치, 요약/압축 서브에이전트 등 실제 환경에서의 활용성을 높이기 위한 다양한 기능을 도입. 예를 들어, 웹서치 시 요약 서브에이전트가 웹페이지를 요약해주고, 도구 호출 이력이 많아지면 트래젝토리 압축 서브에이전트가 전체 상호작용을 JSON 구조로 압축하여 맥락 효율성을 높임. 이 모든 서브에이전트는 K-EXAONE 기반으로 구현됨.

(모든 내용 출처: 5~6page)

### 평가 및 벤치마크 결과 (7~10, 18, 20page)

- **평가 카테고리 및 벤치마크**

  - K-EXAONE은 총 9개 카테고리(세계지식, 수학, 코딩, 에이전트 도구 사용, 지시이행, 장문맥 이해, 한국어, 다국어, 안전성)에서 다양한 공개 및 자체 벤치마크로 평가됨. (7page)
  - 주요 벤치마크: MMLU-PRO(세계지식), AIME/IMO/HMMT(수학), LIVECODEBENCH/TERMINAL-BENCH/SWE-BENCH(Coding), 2-BENCH/BROWSECOMP(Agentic Tool Use), IFBENCH/IFEVAL(Instruction Following), AA-LCR/OPENAI-MRCR(Long Context), KMMLU-PRO/KOBALT/CLICK/HRM8K/KO-LONGBENCH(한국어), MMMLU/WMT24(다국어), KGC-SAFETY/WILDJAILBREAK(안전성) 등. (7page)
- **Reasoning/Non-Reasoning 모드 성능**

  - Reasoning 모드에서 MMLU-PRO 83.8, AIME 92.8, LIVECODEBENCH V6 80.7, KOBALT 61.8, MMMLU 85.7, KGC-SAFETY 96.1 등 동급 오픈웨이트/상용 모델과 유사하거나 우수한 성적을 기록함. (8~10page)
  - Non-Reasoning 모드에서도 MMLU-PRO 81.0, LIVECODEBENCH V6 44.6, KOBALT 49.1, MMMLU 83.8, KGC-SAFETY 88.4 등 경쟁력 있는 결과를 보임. (9page)
  - Reasoning/Non-Reasoning 모드 모두에서 DeepSeek-V3.2, Qwen3-235B, gpt-oss-120b 등과 비교해 전반적으로 상위권 성능을 유지함. (8~10page)
- **한국어 및 다국어 성능**

  - 한국어 벤치마크(KMMLU-PRO, KOBALT, CLICK, HRM8K, KO-LONGBENCH)에서 Reasoning 모드 기준 KMMLU-PRO 67.3, KOBALT 61.8, CLICK 83.9, HRM8K 90.9, KO-LONGBENCH 86.8 등 고른 성적을 보임. (9page)
  - 다국어(MMMLU, WMT24)에서도 MMMLU 85.7, WMT24 90.5로, 언어별 편차 없이 균형 잡힌 성능을 달성함. (10, 20page)
  - 언어별 세부 성능(예: MMMLU KO 85.6, DE 85.1, ES 86.6, JA 85.5 등)도 고르게 나타남. (20page)
- **장문맥 이해 및 실용적 코딩**

  - 장문맥 벤치마크(AA-LCR, OPENAI-MRCR, KO-LONGBENCH)에서 Reasoning 모드 기준 AA-LCR 53.5, OPENAI-MRCR 52.3, KO-LONGBENCH 86.8 등 긴 입력에서도 정보 보존 및 추론력이 우수함을 입증함. (9page)
  - 실용적 코딩 평가(CODEUTILITYBENCH)에서 전작(EXAONE-4.0-32B) 대비 전체 점수 71.9→63.2로 향상, 특히 코드 이해/구현(Understanding/Implementation) 영역에서 큰 개선을 보임. (18page)
  - 다만, 코드 유지보수(Maintenance) 영역에서는 여전히 추가 개선 여지가 있음(66.0점). (18page)
- **안전성**

  - KGC-SAFETY(한국 민감성, 미래 위험 등 포함)에서 Safe Rate 96.1%로, 동급 모델 중 최고 수준의 안전성을 기록함. (22page)
- **요약**

  - K-EXAONE은 다양한 벤치마크에서 Reasoning/Non-Reasoning, 한국어/다국어, 장문맥/단문맥, 실용적 코딩, 안전성 등 모든 측면에서 동급 최고 수준의 성능과 균형 잡힌 결과를 보여줌.

(모든 내용 출처: 7~10, 18, 20, 22page)

---

## 📄 [04.임베딩.md] [기술 보고서] 이력서 임베딩 엔진: 텍스트의 수치화 및 최적화 전략

본 문서는 한국어 문장 유사도에 특화된 `KURE-v1` 모델을 활용하여, 청킹된 이력서 조각들을 고차원 벡터로 변환하는 기술적 매커니즘을 상세히 다룹니다.

---

## 1. 임베딩(Embedding)의 본질: "언어를 숫자로"

인공지능은 텍스트를 직접 읽지 못합니다. 대신 텍스트를 수백 개의 숫자 리스트인 **벡터(Vector)**로 변환하여 **'의미의 공간'**에 점을 찍습니다.

* **원리**: 비슷한 의미를 가진 문장(예: "Python 개발 경험", "파이썬 프로젝트 수행")은 이 공간에서 서로 가까운 거리에 위치하게 됩니다.
* **활용**: 나중에 사용자가 질문을 던지면, 질문의 좌표와 가장 가까운 곳에 있는 이력서 조각을 찾아내는 **시맨틱 검색(Semantic Search)**이 가능해집니다.

---

## 2. 자원 최적화 전략: 싱글톤(Singleton) 패턴

모델 로딩은 메모리를 기가바이트(GB) 단위로 점유하고 수 초 이상의 시간을 소모하는 **'비싼 작업'**입니다.

```python
_embedder = None # 전역 변수

def get_embedder(device):
    global _embedder
    if _embedder is None: # 처음 한 번만 실행
        _embedder = HuggingFaceEmbeddings(...)
    return _embedder

```

### 🔍 깊이 있는 분석

* **메모리 보호**: 만약 함수를 호출할 때마다 모델을 새로 로드한다면, 동시 접속자가 많아질 때 서버의 RAM이 즉시 고갈되어 시스템이 붕괴(OOM, Out of Memory)됩니다.
* **지연 시간(Latency) 최소화**: 첫 호출 이후에는 메모리에 상주(Resident) 중인 모델을 즉시 반환하므로, 실제 임베딩 처리 속도가 비약적으로 빨라집니다.

---

## 3. 핵심 로직 상세 분석 (`embed_chunks`)

실제 조각들을 벡터로 바꾸는 과정에서 사용된 기술적 포인트들입니다.

### ① 하드웨어 가속 자동 감지

```python
device = 'cuda' if torch.cuda.is_available() else 'cpu'

```

* **로직**: 시스템에 NVIDIA GPU가 있는지 확인합니다. GPU(`cuda`)가 있다면 수백 개의 문장을 병렬로 처리하여 속도를 수십 배 높이고, 없다면 안정적인 `cpu` 모드로 작동합니다.

### ② 수학적 정규화 (Normalization)

```python
encode_kwargs={'normalize_embeddings': True}

```

* **수학적 의미**: 생성된 벡터의 길이를 모두 **1**로 맞추는 작업입니다.
* **이유**: 검색 시 사용하는 **코사인 유사도(Cosine Similarity)** 계산을 단순화하고 정확도를 높이기 위해서입니다. 벡터의 길이와 상관없이 '방향'만으로 유사도를 판별하게 하여, 문장의 길이에 의한 왜곡을 방지합니다.

$$
\text{Similarity} = \cos(\theta) = \frac{A \cdot B}{\|A\| \|B\|}
$$

### ③ 데이터 결합 (Mapping)

```python
embedded_result.append({
    "text": c["text"],
    "vector": vectors[i] # AI가 계산한 좌표값
})

```

* **분석**: 벡터 자체는 숫자 덩어리일 뿐이라 사람이 읽을 수 없습니다. 따라서 **"이 숫자가 어떤 글자에서 나왔는지"**를 알 수 있도록 원본 텍스트 및 메타데이터와 한 세트로 묶어주는 과정이 필수적입니다.

---

## 4. `KURE-v1` 모델의 특성 분석

본 시스템에서 채택한 `nlpai-lab/KURE-v1`은 한국어 검색 및 문장 유사도 성능이 매우 뛰어난 모델입니다.

| 특징                     | 설명                                   | 효과                                               |
| ------------------------ | -------------------------------------- | -------------------------------------------------- |
| **한국어 특화**    | 한국어의 구어체와 문어체를 모두 학습   | 이력서 특유의 딱딱한 말투도 정확히 이해함          |
| **Pure Embedding** | 접두어(Instruction) 없이도 고성능 발휘 | 데이터 전처리 복잡도를 낮추고 원문의 의미를 보존함 |
| **고차원 벡터**    | 문장을 수백 개의 숫자로 정밀하게 묘사  | 미세한 의미 차이(예: '팀원'과 '팀장')를 구분해냄   |

---

## 5. 결론 및 RAG 시스템에서의 역할

이 코드가 완성됨으로써, 앞서 수행한 **파싱(추출)**과 **청킹(분할)** 데이터는 비로소 **'기계가 읽을 수 있는 지식'**으로 탈바꿈했습니다. 이제 이 데이터는 벡터 데이터베이스(ChromaDB, Pinecone 등)에 저장되어, **EXAONE 3.5** 모델이 답변을 생성할 때 가장 신뢰할 수 있는 근거 자료로 활용될 준비를 마쳤습니다.

---

## 📄 [05.pgvector.md] [기술 보고서] 벡터 데이터 저장 엔진: PGVector 기반 영구 저장 매커니즘

본 문서는 임베딩된 이력서 데이터를 PostgreSQL의 벡터 확장 기능(`pgvector`)을 활용하여 영구 저장하고, 멀티 테넌트(Multi-tenant) 검색을 위해 메타데이터를 관리하는 기술적 과정을 상세히 기술합니다.

---

## 1. 환경 유연성 확보: 동적 경로 설정 (Dynamic Pathing)

가장 먼저 코드는 실행 환경(Docker vs Local)에 상관없이 서버의 핵심 로직을 참조할 수 있도록 설계되었습니다.

```python
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_core_docker = "/backend-core"
backend_core_local = os.path.join(current_dir, "backend-core")

if os.path.exists(backend_core_docker):
    sys.path.append(backend_core_docker)

```

### 🔍 깊이 있는 분석

* **존재 이유**: 개발자의 로컬 PC 폴더 구조와 Docker 컨테이너 내부의 구조는 완전히 다릅니다.
* **해결**: `sys.path.append`를 통해 파이썬의 모듈 탐색 경로에 동적으로 길을 터줌으로써, 어느 환경에서든 `db.py`나 `embedding.py` 같은 공통 모듈을 에러 없이 불러올 수 있는 **환경 독립성(Environmental Independence)**을 확보했습니다.

---

## 2. 데이터 표준화: `Document` 객체 생성

AI 도구(LangChain)가 DB와 소통하기 위해서는 텍스트를 전용 포장지인 **`Document`** 객체에 담아야 합니다.

```python
for item in embedded_chunks:
    metadata = item.get("metadata", {})
    metadata["resume_id"] = resume_id # 핵심 견출지
    metadata["chunk_type"] = item.get("type", "unknown")
  
    doc = Document(
        page_content=item["text"],
        metadata=metadata
    )

```

### 🔍 상세 로직 분석

* **`page_content`**: AI가 실제로 읽고 질문을 생성할 **원본 텍스트**입니다.
* **메타데이터(Metadata)의 전략적 활용**: 수만 명의 이력서 조각이 하나의 DB 테이블(`collection`)에 섞여 저장됩니다. 이때 `resume_id`를 메타데이터로 심어두지 않으면, 나중에 특정 사용자의 데이터만 골라내는 것이 불가능합니다. 이는 DB의 **인덱싱(Indexing)**과 **필터링** 속도를 결정짓는 결정적인 설계입니다.

---

## 3. 벡터 저장소의 핵심: `PGVector` 연동

이 코드는 단순한 DB 저장을 넘어, PostgreSQL을 **고차원 좌표 검색 엔진**으로 변환시킵니다.

```python
vector_store = PGVector.from_documents(
    embedding=embeddings,
    documents=documents,
    collection_name="resume_all_embeddings",
    connection_string=connection_string,
    pre_delete_collection=False,
)

```

### 🔍 기술적 메커니즘

1. **`from_documents`**: 이 함수는 내부적으로 **[텍스트 추출 → 임베딩 모델 실행 → 벡터 생성 → DB Insert]**라는 복잡한 과정을 단 한 번에 수행하는 고수준 API입니다.
2. **`collection_name`**: DB 내에서 논리적인 그룹을 나눕니다. "이력서 전용 창고"라고 이름을 붙여주는 것과 같습니다.
3. **보안 관리 (`os.getenv`)**: `DATABASE_URL`을 환경 변수에서 가져옴으로써, 코드 내에 비밀번호가 노출되는 보안 사고를 원천 차단합니다.

---

## 4. 전체 파이프라인에서의 역할 (Workflow)

이 코드가 완료됨으로써 사용자의 이력서는 다음과 같은 상태가 됩니다.

1. **텍스트**: 사람이 읽을 수 있는 형태 (`page_content`)
2. **벡터**: AI가 의미로 검색할 수 있는 수치 형태 (`vector`)
3. **식별자**: 누구의 데이터인지 알 수 있는 정보 (`metadata: resume_id`)

이 세 가지가 결합되어 DB에 저장되면, 이후 **EXAONE 3.5** 모델은 사용자의 질문이 들어왔을 때 DB에서 가장 유사한 조각을 **초고속으로 검색(Semantic Retrieval)**하여 답변을 생성하게 됩니다.

---

## 💡 요약 및 기술 총평

| 단계                  | 적용 기술                 | 목적                                               |
| --------------------- | ------------------------- | -------------------------------------------------- |
| **환경 적응**   | `sys.path` 동적 제어    | 로컬/도커 환경 구분 없는 코드 실행                 |
| **데이터 포장** | `LangChain Document`    | AI 프레임워크 표준 규격 준수                       |
| **검색 최적화** | `Metadata Injection`    | 수만 명 중 특정 지원자 데이터만 즉시 필터링        |
| **영구 저장**   | `PGVector (PostgreSQL)` | 고차원 벡터의 안정적 저장 및 유사도 검색 엔진 구축 |

**최종 결론:**
이 코드는 이력서 분석 시스템의 **'지식 창고'**를 구축하는 마지막 퍼즐 조각입니다. 단순히 데이터를 쌓는 것이 아니라, **나중에 AI 면접관이 가장 정확한 근거를 신속하게 찾을 수 있도록 최적화된 상태로 저장**하는 고도의 설계가 반영되어 있습니다.

---

## 📄 [07.resume-embedding-orcas.md] [기술 보고서] AI 면접 시스템: RAG 기반 지능형 질문 생성 엔진

**일시:** 2026년 3월 1일
**대상:** AI 시스템 아키텍처 및 백엔드 개발 검토용
**주요 기술:** Python, LangChain, Celery, PostgreSQL(pgvector), EXAONE-3.5 LLM

---

# 1. 시스템 아키텍처 개요 (System Architecture)

본 시스템은 지원자의 이력서를 분석하여 벡터화하고, 이를 바탕으로 면접 단계에 맞는 최적의 질문을 실시간으로 생성하는 **오케스트레이션(Orchestration) 구조**를 가집니다.

## ✅ 핵심 구조

* **비동기 파이프라인**

  * Celery를 활용하여 무거운 GPU 연산(임베딩, LLM 추론)을 백그라운드에서 처리
  * API 응답 지연 최소화
* **RAG (Retrieval-Augmented Generation)**

  * 이력서 데이터를 의미 단위(Chunk)로 분할
  * 벡터 DB에 저장
  * 질문 생성 시 관련 정보를 즉시 검색하여 정확도 향상

---

# 2. 데이터 인입 파이프라인: 이력서 벡터화 (Resume Indexing)

이력서 데이터를 AI가 검색 가능한 형태로 변환하는 단계입니다.

---

## 2.1 주요 코드 분석 (`generate_resume_embeddings`)

```python
@shared_task(bind=True, name="tasks.resume_pipeline.generate_embeddings", queue='gpu_queue')
def generate_resume_embeddings(self, resume_id: int):
    # 1. 청킹(Chunking): 구조화된 데이터를 의미 단위로 분할
    chunks = chunk_resume(resume.structured_data)
  
    # 2. 임베딩(Embedding): 텍스트를 1024차원의 수치 벡터로 변환
    embedded_data = embed_chunks(chunks)
  
    # 3. 벡터 DB 저장: pgvector를 사용하여 검색 가능한 형태로 인덱싱
    store_embeddings(resume_id, embedded_data)
```

---

## 2.2 기술적 강점

### 🔹 리소스 최적화

* `gpu_queue` 전용 큐 사용
* CPU와 GPU 작업 분리
* 동시 처리량 증가 및 병목 현상 감소

### 🔹 데이터 정합성 관리

* `processing_status` 상태 추적

  * `processing → completed / failed`
* 실패 시 재처리 가능
* 시스템 안정성 확보

---

# 3. 지능형 질문 생성 엔진 (Question Generation)

면접의 흐름과 지원자의 특성(비전공자, 직무 전환자 등)을 고려하여 동적으로 질문을 생성합니다.

---

## 3.1 워크플로우 제어 로직

면접 단계는 `INTERVIEW_STAGES` 설정을 참조하여 동적으로 판별됩니다.

```python
# 비전공자/직무 전환자 여부에 따른 시나리오 분기
is_transition = check_if_transition(major, interview.position)
get_next_stage_func = get_next_stage_transition if is_transition else get_next_stage_normal
```

### ✔ 특징

* 지원자 특성 기반 분기 처리
* 면접 흐름의 유연성 확보
* 고정 질문 트리 구조 탈피

---

## 3.2 LangChain 기반 추론 체인 (LCEL)

단순 텍스트 생성이 아니라, 단계별 지침과 페르소나를 결합한 추론 체인을 구성했습니다.

```python
# LCEL(LangChain Expression Language) 문법 활용
prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
chain = prompt | llm | StrOutputParser()

# 실시간 지시사항 주입
final_content = chain.invoke({
    "context": context_text,
    "mode_instruction": "자기소개서 문장을 인용하여 질문을 시작하십시오.",
    "company_ideal": company_ideal
})
```

### ✔ 설계 포인트

* 실시간 Instruction Injection
* 회사 인재상 반영 가능
* 특정 단계(예: 가치관 질문)에서 자소서 인용 강제

---

## 3.3 응답 정제 및 가공 (Post-Processing)

LLM 출력의 불필요한 메타 문구 제거 및 UI 전달 포맷 정리

### 🔹 정규표현식 기반 패턴 제거

예:

* "질문은 다음과 같습니다"
* "아래와 같이 질문드립니다"

→ 자동 삭제

### 🔹 UI 전달 형식 구조화

```
[심층면접]
질문 내용
```

* 면접관 톤 유지
* 일관된 사용자 경험 제공

---

# 4. 안정성 및 성능 최적화 (Reliability & Performance)

---

## 4.1 메모리 관리 (Memory Management)

대규모 LLM 워커의 메모리 누수 방지를 위한 명시적 정리 수행

```python
gc.collect()  # 파이썬 가비지 컬렉션 강제 실행
if torch.cuda.is_available():
    torch.cuda.empty_cache()  # GPU 캐시 비우기
```

### ✔ 효과

* 장시간 실행 시 OOM 방지
* GPU 메모리 파편화 완화
* 워커 안정성 향상

---

## 4.2 장애 복구 로직 (Fallback Mechanism)

면접이 중단되지 않도록 설계된 이중 안전 장치

### 🔹 Retry 메커니즘

* 최대 3회 재시도 (`self.retry`)

### 🔹 Fallback 질문 자동 생성

* 모델 오류 발생 시
* 사전 정의된 시스템 공통 질문으로 대체

예:

```
"최근 수행한 프로젝트 중 가장 도전적이었던 경험을 말씀해 주세요."
```

→ 사용자 경험 단절 방지

---

# 5. 결론 및 향후 전망

본 시스템은 다음 기술을 결합하여 설계되었습니다.

* RAG 기반 정밀 검색
* 비동기 큐 시스템
* 동적 면접 시나리오 제어
* LLM 후처리 및 안정화 구조

## 🎯 현재 성과

* 비전공자 특화 질문 생성
* 자소서 기반 맞춤형 질문 생성
* 면접 단계별 동적 분기 구현 완료

## 🚀 향후 확장 가능성

* 실시간 감성 분석 레이어 추가

  * 답변 속도 분석
  * 음성 톤 분석
  * 감정 변화 감지
* 질문 난이도 및 압박 강도 조절
* 개인화된 피드백 자동 생성

---

# 📌 종합 평가

본 시스템은 단순 LLM 질의응답 구조를 넘어,

* **비동기 고성능 처리**
* **정교한 RAG 검색 구조**
* **면접 흐름 제어 오케스트레이션**
* **안정성 및 장애 복구 설계**

를 모두 포함한 **실서비스 수준의 AI 면접 플랫폼 백엔드 아키텍처**입니다.

---

## 📄 [08-질문생성.md] 기술 상세 분석 보고서: BIGTERVIEW 지능형 면접 추론 엔진

## BIGTERVIEW 지능형 면접 추론 엔진

본 보고서는 실시간 AI 면접 시스템의 핵심 로직인 `generate_next_question_task`를 중심으로,
**입력 검증 → 문맥 검색 → 동적 추론 → 출력 정제 → 시스템 복원력**에 이르는 전 과정을 코드 수준에서 정밀 분석합니다.

---

## 1️⃣ 전처리 레이어: 입력 유효성 검증 (Input Guardrail)

AI가 엉뚱한 답변(환각)을 생성하지 않도록, 지원자의 입력을 사전에 필터링합니다.

```python
def is_meaningless(text: str) -> bool:
    """지원자의 답변이 무의미한지(자음 나열, 너무 짧음 등) 체크합니다."""
    if not text: return True
    # 1. 길이 및 자음 나열 체크
    if len(text) < 5: return True
    if re.fullmatch(r'[ㄱ-ㅎㅏ-ㅣ\s]+', text): return True
    # 2. 단순 특수문자/숫자 반복 (...., 123123 등)
    if re.fullmatch(r'[\.\,\!\?\-\=\s\d]+', text): return True
```

### 🔎 코드 분석

* `re.fullmatch()`를 사용해 **자음 나열, 특수문자 반복, 숫자 반복 패턴**을 정규식으로 차단
* 길이 기반 1차 필터링 + 패턴 기반 2차 필터링의 이중 구조

### 🎯 기술적 의도

* `"ㅋㅋㅋ"`, `"...."`, `"123123"` 같은 입력이 LLM으로 전달될 경우
  → “웃음이 많으시군요?” 같은 **맥락 왜곡 대화 흐름** 발생 가능
* 이를 사전 차단하여 **면접의 긴장감과 전문성 유지**

---

## 2️⃣ 전략 수립 레이어: 적응형 시나리오 판별

지원자의 전공/직무 배경에 따라 면접 난이도와 방향성을 동적으로 조정하는 로직입니다.

```python
# 전공/직무 기반 시나리오 결정
is_transition = check_if_transition(major, interview.position)
get_next_stage_func = get_next_stage_transition if is_transition else get_next_stage_normal

# 마지막 AI 발화의 question_type으로 현재 stage 판별
if last_ai_transcript and last_ai_transcript.question_id:
    last_stage_name = last_question.question_type if last_question else "intro"
```

### 🔎 코드 분석

* `is_transition` 변수로 **비전공자 여부 판별**
* 함수를 변수에 할당하여 동적으로 시나리오 호출 (전략 패턴과 유사)
* 이전 질문의 `question_type`을 기반으로 현재 단계 추론

### 🎯 기술적 의도

* 동일 직무라도 전공자/비전공자에 따라 질문 난이도 차별화
* 개인화된 면접 경험 제공
* 면접의 흐름이 단계적으로 이어지도록 상태 기반 설계

---

## 3️⃣ 문맥 엔진 레이어: 단계별 타겟 RAG

(Retrieval-Augmented Generation)

면접 목적에 따라 검색 쿼리를 실시간으로 생성하는 지능형 문맥 검색 구조입니다.

```python
behavioral_keywords = {
    "communication": "협업 사례, 팀 프로젝트 중 갈등 조율, 팀워크 발휘, 소통 능력",
    "growth": "자기계발 노력, 새로운 기술 학습 태도, 실패 극복 및 성장 사례",
    "responsibility": "직업 윤리, 약속 이행, 정직함과 관련된 경험"
}
target_query = behavioral_keywords.get(s_name, "본인의 강점, 성취감, 도전적인 경험 사례")
rag_results = retrieve_context(target_query, resume_id=interview.resume_id, top_k=2)
```

### 🔎 코드 분석

* `dict.get()`을 활용한 단계별 키워드 동적 선택
* `resume_id` 기반 벡터 DB 검색 수행
* `top_k=2`로 핵심 문맥만 추출

### 🎯 기술적 의도

* 단순한 일반 질문 방지
* 이력서 기반 **증거 중심 질문 생성**
* “성격이 어떤가요?” 대신
  → “A 프로젝트 협업 사례에서 갈등을 어떻게 조율하셨나요?”

---

## 4️⃣ 추론 제어 레이어: 하이퍼-프롬프트 엔지니어링

LLM의 행동을 강력한 제약 조건으로 통제합니다.

```python
if is_narrative:
    global_constraint = "인성 단계입니다. 코드, 설계, 개발과 같은 직무 단어를 사용하지 말고, 태도와 가치관을 인용하여 짧게 질문하십시오."

elif s_name == 'responsibility':
    mode_task_instruction = "자기소개서에서 나타난 지원자의 핵심 가치관을 파악하여... 80자 이내로 물으십시오."
```

### 🔎 코드 분석

* `global_constraint`와 `mode_task_instruction`을 동적 조립
* 질문 길이, 어휘 범위, 주제 영역을 명시적으로 제한

### 🎯 기술적 의도

* 인성 단계에서 기술 질문으로 탈선하는 현상 방지
* 질문 길이 과다 생성 방지
* 단계별 일관성 유지

---

## 5️⃣ 사후 정제 레이어: AI 말투 제거 (Sanitization)

LLM이 생성한 메타 발화 및 시스템 문구 제거

```python
meta_patterns = [
    r'(이\s*질문은|의도는|~라고\s*답변했다면|검증합니다|의도함|확인합니다|요구하여).*', 
    r'지원자가\s*.*라고\s*말했다면.*'
]
for pattern in meta_patterns:
    final_content = re.sub(pattern, '', final_content, flags=re.IGNORECASE | re.DOTALL)

quote_match = re.search(r'["\'“]([^"\'”]*\?+)["\'”]', final_content)
if quote_match:
    final_content = quote_match.group(1)
```

### 🔎 코드 분석

* `re.sub()`로 메타 문장 제거
* 따옴표 안 질문만 추출하는 정교한 패턴 매칭
* 불필요한 시스템 메시지 제거

### 🎯 기술적 의도

* “이 질문의 의도는…” 같은 시스템 노출 방지
* 실제 면접관과 대화하는 자연스러운 UX 유지

---

## 6️⃣ 시스템 회복력: 폴백(Fallback) 설계

LLM 추론 실패 시 면접이 중단되지 않도록 설계된 복원 전략입니다.

```python
except Exception as e:
    if self.request.retries >= 3:
        fallback_text = "[시스템 질문] AI 응답 지연으로 인해 기본 질문으로 대체합니다. ..."
        q_id = save_generated_question(content=fallback_text, stage="fallback", ...)
```

### 🔎 코드 분석

* Celery `retries` 횟수 체크
* 임계치 도달 시 하드코딩된 안전 질문 출력
* 질문 저장 로직까지 정상 플로우 유지

### 🎯 기술적 의도

* GPU 장애, 모델 지연 상황에서도 면접 지속 가능
* 사용자 경험 단절 방지
* 시스템 신뢰도 확보

---

# 🧠 종합 구조 요약

| 레이어      | 역할               | 핵심 기술           |
| ----------- | ------------------ | ------------------- |
| 입력 검증   | 무의미 답변 차단   | 정규식 필터링       |
| 전략 판별   | 전공 기반 시나리오 | 동적 함수 할당      |
| 문맥 엔진   | 단계별 RAG         | 벡터 검색           |
| 추론 제어   | LLM 행동 통제      | 제약 기반 프롬프트  |
| 사후 정제   | 메타 발화 제거     | 정규식 Sanitization |
| 시스템 복원 | 장애 대응          | Retry + Fallback    |

---

# 🚀 결론

BIGTERVIEW 추론 엔진은 단순한 질문 생성 시스템이 아니라,

> **입력 통제 → 전략 설계 → 문맥 강화 → 행동 제약 → 출력 정제 → 장애 복구**

까지 이어지는 **다층 방어형 지능 면접 아키텍처**입니다.

이는 LLM 기반 서비스에서 가장 중요한
✔ 환각 방지
✔ 맥락 유지
✔ 사용자 경험 안정성
✔ 시스템 신뢰성

을 동시에 달성하기 위한 정교한 설계라고 평가할 수 있습니다.
