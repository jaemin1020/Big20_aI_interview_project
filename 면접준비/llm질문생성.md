# LLM 꼬리질문 생성 시 잘못된 인용 문제 분석

작성일: 2026-02-24

---

## 발생한 문제

### 지원자 실제 답변 (원문)
```
네, 해당 과정들을 통해 데이터 파이프라인부터 AI 서비스 구현까지 전반적인 실무 역량을 체계적으로 습득했습니다.

먼저 AWS 기반 빅데이터 분석 및 AI 모델링 과정에서는 S3, EC2, RDS 환경에서 데이터 수집·저장·처리 파이프라인을 구축했고,
Python을 활용한 전처리와 머신러닝 모델 학습 및 배포까지 경험했습니다.
특히 대용량 로그 데이터를 기반으로 피처 엔지니어링과 모델 성능 개선을 수행한 것이 핵심 성과였습니다.

또한 RAG 아키텍처 분석가 과정에서는 벡터DB 구축, 임베딩 기반 검색, cross-encoder re-ranking 등
LLM 기반 검색 증강 생성 구조를 설계하고 튜닝하는 실무 기술을 익혔습니다.
이를 통해 질의 정합도와 응답 일관성을 개선하는 방법을 체득했습니다.

운전면허 1종은 프로젝트 수행 시 현장 대응과 외부 협업 업무의 기동성을 확보하는 데 도움이 된다고 생각합니다.
이러한 경험을 바탕으로 데이터 분석부터 AI 서비스 구현까지 엔드투엔드로 기여할 수 있는 역량을 갖추게 되었습니다.
```

### AI가 생성한 꼬리질문 (잘못된 인용 포함)
```
RAG 아키텍처 구축 경험을 통해 특히 어떤 기법을 사용하여 질의 정합도와 응답 일관성을 개선하셨는지,
그 구체적인 과정과 결과를 자세히 설명해 주세요.
```

### 문제의 핵심
- 지원자 원문: **"RAG 아키텍처 분석가 과정"**
- AI 인용구: **"RAG 아키텍처 구축 경험"**
- `분석가 과정` → `구축 경험` 으로 **의미가 다른 단어로 바뀌어 버림**

---

## 근본 원인: LLM에게 "직접 인용"이 아닌 "요약"을 시켰기 때문

### 현재 `PROMPT_TEMPLATE` 규칙 7번 (ai-worker/tasks/question_generator.py, line 42)

```
7. **꼬리질문(Follow-up) 규칙**: 지원자의 답변 중 핵심적인 구절을 골라 
   작은따옴표(' ') 안에 넣어 "...라고 하셨는데,"로 요약하며 시작하십시오.
   (예: 'RAG 아키텍처'라고 말씀하셨는데,)
```

**"요약하며 시작하십시오"** 라고 지시한 것이 핵심 문제다.

LLM은 "요약"이라는 지시를 받으면 **원문을 그대로 가져오지 않고 자기 언어로 재구성**한다.
이 과정에서 지원자가 쓰지 않은 단어와 표현이 끼어든다.

```
지원자 실제 답변:  "RAG 아키텍처 분석가 과정에서는 벡터DB 구축..."
                            ↓ LLM이 "요약" 처리
꼬리질문 인용구:  "RAG 아키텍처 구축 경험을 통해..."  ← 의역 + 환각 발생
```

---

## 현재 꼬리질문 생성 흐름 (코드 레벨)

### 1. 컨텍스트 구성 (question_generator.py, line 359~365)

```python
if next_stage.get("type") == "followup":
    # 꼬리질문: RAG/질문은행 모두 스킵하고 오직 '질문-답변' 맥락만 사용
    logger.info("🎯 Follow-up mode: RAG & Question Bank disabled.")
    context_text = f"이전 질문: {last_ai_transcript.text if last_ai_transcript else '없음'}\n"
    if last_user_transcript:
        context_text += f"[지원자의 최근 답변]: {last_user_transcript.text}"
    rag_results = []
```

### 2. LLM 프롬프트로 전달 (question_generator.py, line 416~420)

```python
for chunk in chain.stream({
    "context": context_text,           # ← 질문 + 답변 텍스트
    "stage_name": next_stage['display_name'],
    "guide": next_stage.get('guide', ''),
    "target_role": interview.position or "지원 직무"
}):
```

### 3. LLM이 받는 프롬프트 구조

```
[이력서 및 답변 문맥]
이전 질문: [AI 질문 텍스트]
[지원자의 최근 답변]: [지원자 답변 전문]

[현재 면접 단계 정보]
- 단계명: 직무심층질문
- 가이드: 지원자의 이전 답변을 '~라고 하셨는데,'와 같이 한 문장으로 먼저 요약하십시오...

[절대 규칙]
 7. 지원자의 답변 중 핵심적인 구절을 골라 작은따옴표(' ')안에 넣어 "...라고 하셨는데,"로 요약하며 시작하십시오.
```

### 4. 문제 발생 지점

LLM은 위 프롬프트를 받아서 "요약하며 시작"하라는 지시에 따라:
1. 지원자 답변 전체를 읽음
2. **스스로** 핵심 키워드를 선택 및 재구성
3. `RAG 아키텍처 분석가 과정` → `RAG 아키텍처 구축 경험` 으로 **의역**
4. 의역된 문장으로 꼬리질문 생성

이 과정은 LLM의 특성상 **완벽히 막을 수 없다**.  
LLM은 입력 텍스트를 그대로 복사하지 않고 항상 내부적으로 "이해 → 재생성"을 거친다.

---

## 해결 가능한가?

**→ 충분히 가능하다.**

방법 A (Python 사전 추출)와 방법 B (LLM 2-패스) 두 가지가 있다.

---

## 방법 A: Python 사전 추출 (권장)

LLM에게 "어떤 문장을 인용할지 결정"하는 역할을 맡기지 않는다.  
대신 **Python 코드에서 먼저 인용할 문장을 추출**한 뒤, LLM 프롬프트에 `{pre_extracted_quote}`로 주입한다.

### 처리 흐름

```
지원자 답변 텍스트 (last_user_transcript.text)
        ↓
Python: re.split()으로 문장 단위 분리
        ↓
["S1", "S2", "S3", ...]
        ↓
길이 필터 (15자 < len < 80자) + 의미 있는 문장 랭킹
        ↓
가장 핵심적인 1문장 선택 → best_quote
        ↓
LLM 프롬프트에 주입:
"반드시 다음 인용문을 원문 그대로 사용하여 시작하십시오: [{best_quote}]"
```

### 구체적 구현 코드 (의사 코드)

```python
# question_generator.py - followup 분기 내부

if next_stage.get("type") == "followup":
    # 1. 지원자 최근 답변 텍스트
    user_answer_text = last_user_transcript.text if last_user_transcript else ""

    # 2. 문장 단위 분리 (한국어 기준: 다/요. 으로 끝나는 경우)
    raw_sentences = re.split(r'(?<=[다요])\. ?', user_answer_text)
    
    # 3. 후보 문장 필터: 너무 짧거나 너무 긴 문장 제외
    candidates = [s.strip() for s in raw_sentences if 15 < len(s.strip()) < 80]
    
    # 4. 가장 핵심적인 1문장 선택 (가장 긴 문장 = 정보량 많은 문장)
    if candidates:
        best_quote = max(candidates, key=len)
    else:
        # 폴백: 답변 앞 60자
        best_quote = user_answer_text[:60].rstrip()
    
    # 5. 기존 컨텍스트 구성
    context_text = (
        f"이전 질문: {last_ai_transcript.text if last_ai_transcript else '없음'}\n"
        f"[지원자의 최근 답변]: {user_answer_text}"
    )
    
    # 6. guide에 추출된 인용문을 동적으로 주입
    original_guide = next_stage.get('guide', '')
    guide_with_quote = (
        f"[사전 추출된 인용 문구]: {best_quote}\n"
        f"반드시 위 인용 문구를 원문 그대로 작은따옴표(' ')에 넣어 '...라고 하셨는데,'로 시작하십시오. "
        f"절대 의역하거나 다른 단어로 바꾸지 마십시오.\n\n"
        f"{original_guide}"
    )
    
    # 7. 이후 LLM 호출 시 guide 대신 guide_with_quote 사용
```

### PROMPT_TEMPLATE 규칙 7번 변경

```python
# 변경 전
" 7. **꼬리질문(Follow-up) 규칙**: 지원자의 답변 중 핵심적인 구절을 골라 "
"    작은따옴표(' ') 안에 넣어 \"...라고 하셨는데,\"로 요약하며 시작하십시오."

# 변경 후
" 7. **꼬리질문(Follow-up) 규칙**: [가이드]에 [사전 추출된 인용 문구]가 제공된 경우, "
"    해당 문구를 반드시 원문 그대로 작은따옴표(' ') 안에 넣어 \"...라고 하셨는데,\"로 시작하십시오. "
"    절대 의역, 요약, 단어 변경 금지. 제공된 문구가 없는 경우에만 스스로 핵심 구절을 선택하십시오."
```

---

## 방법 B: LLM 2-패스

1. **1패스**: LLM에게 "이 답변에서 가장 핵심적인 한 문장을 **원문 그대로** 복사해서 출력하라"만 지시
2. **2패스**: 1패스 결과(추출된 문장)를 `{quote}`로 넣어 꼬리질문 생성

```python
# 1패스: 인용문 추출 전용 LLM 호출
extraction_prompt = (
    f"[|system|]당신은 텍스트 추출 전문가입니다. "
    f"아래 답변에서 가장 핵심적인 문장 1개를 원문에서 그대로 복사하여 출력하십시오. "
    f"절대 의역하거나 수정하지 마십시오.[|endofturn|]\n"
    f"[|user|]답변: {user_answer_text}[|endofturn|]\n"
    f"[|assistant|]"
)
extracted_quote = llm.invoke(extraction_prompt, temperature=0.0)

# 2패스: 추출된 문장을 사용해 꼬리질문 생성
guide_with_quote = f"반드시 '{extracted_quote}'라고 하셨는데, 로 시작하십시오. ..."
```

---

## 방법 비교

| 항목 | 현재 방식 | 방법 A (Python 추출) | 방법 B (LLM 2패스) |
|------|----------|---------------------|-------------------|
| **인용 정확도** | ❌ 낮음 (의역/환각) | ✅ 높음 (원문 그대로) | ✅ 높음 |
| **처리 속도** | 빠름 | 빠름 (추가 LLM 호출 없음) | 느림 (LLM 2회 호출) |
| **구현 난이도** | - | 중간 | 낮음 |
| **추가 비용** | 없음 | 없음 | LLM 1회 추가 |
| **한계** | 환각 항상 발생 | 문장 분리 실패 시 폴백 필요 | 1패스도 의역 가능성 있음 |

**→ 방법 A 권장**: 속도 저하 없이 정확도를 높일 수 있음

---

## 수정 대상 파일 및 위치

| 파일 | 위치 | 수정 내용 |
|------|------|-----------|
| `ai-worker/tasks/question_generator.py` | line 32~54 (`PROMPT_TEMPLATE`) | 규칙 7번: "요약" → "사전 추출 인용문 원문 사용" |
| `ai-worker/tasks/question_generator.py` | line 359~365 (followup 분기) | Python 사전 추출 로직 추가, guide에 `{best_quote}` 동적 주입 |

---

## 기대 효과

### 변경 전
```
지원자: "RAG 아키텍처 분석가 과정에서는 벡터DB 구축..."
AI 꼬리질문: "RAG 아키텍처 구축 경험을 통해..."  ← 존재하지 않는 표현
```

### 변경 후 (방법 A 적용)
```
Python 추출: "RAG 아키텍처 분석가 과정에서는 벡터DB 구축, 임베딩 기반 검색..."
AI 꼬리질문: "'RAG 아키텍처 분석가 과정에서는 벡터DB 구축, 임베딩 기반 검색'이라고 
              하셨는데, 그 중 cross-encoder re-ranking을 적용하셨을 때 구체적으로..."
              ← 원문 그대로 인용
```

---

## 참고: 관련 코드 전체 위치

```
ai-worker/
└── tasks/
    └── question_generator.py
        ├── PROMPT_TEMPLATE (line 32~54)  ← 규칙 7번 수정
        └── generate_next_question_task()
            └── followup 분기 (line 357~365)  ← 사전 추출 로직 추가
```
