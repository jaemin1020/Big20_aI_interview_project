# ERR-05: AI 환각(Hallucination) - 무의미 답변 처리 오류

- **오류 코드**: ERR-05  
- **카테고리**: LLM / 프롬프트  
- **심각도**: 🔴 HIGH  
- **상태**: ✅ 해결 완료  
- **관련 파일**: `ai-worker/tasks/question_generator.py`

---

## 3.2.1 문제 정의

지원자가 자음/모음 나열, 짧은 무의미 입력("ㅋㅋㅋ", "asdf", "모르겠어요" 등)을 입력했을 때, AI 면접관이 이를 정상 답변으로 인식하여 존재하지 않는 내용을 지어내는(Hallucination) 질문을 생성하는 현상이 발생하였습니다.

- **현상**: `"지원자께서 말씀하신 RAG 파이프라인 최적화 경험에 대해..."` → 지원자가 실제로 RAG 언급을 하지 않았음에도 AI가 지어낸 내용 기반으로 질문
- **재현 조건**: 지원자가 무의미하거나 부정적인 입력("모르겠습니다", "ㄴㄴ") 제출 시

---

## 3.2.2 문제 영향 분석

- **신뢰성 영향**: AI가 허구의 경험을 인용하여 지원자가 당황하는 상황 발생
- **면접 진행 영향**: 존재하지 않는 답변을 기반으로 한 질문이 면접 흐름을 왜곡
- **데이터 품질 영향**: 허구 기반 질문에 대한 답변이 평가 데이터로 저장되는 문제

---

## 3.2.3 문제 파악 과정

**원인**: 컨텍스트 격리 로직 부재

LLM이 이전 `context_text`에 아무 내용이 없거나 노이즈 텍스트가 있을 경우, 프롬프트 템플릿의 `{context}` 변수에 빈 문자열 또는 짧은 노이즈가 주입됩니다. LLM은 이를 채우기 위해 훈련 데이터에서 추론한 "그럴법한" 내용을 생성하는 환각 현상이 발생합니다.

```python
# [문제 상황] 지원자 답변이 "ㄴㅇㄹ" 인 경우
context_text += f"\n[지원자의 최근 답변]: ㄴㅇㄹ"
# → LLM이 이 노이즈를 채우기 위해 존재하지 않는 내용을 생성
```

---

## 3.2.4 해결 접근 전략

- **무의미 입력 탐지 함수** 도입: 자음/모음 나열, 특수문자 반복, 너무 짧은 입력을 사전 분류
- **컨텍스트 격리**: 무의미 입력 감지 시 기존 컨텍스트를 삭제하고 경고 메시지로 교체
- **지시어 전환**: 환각 방지 전용 `mode_task_instruction`으로 전환

---

## 3.2.5 해결 도출 및 실행

**① 무의미 입력 탐지 함수**

```python
# [수정 후] question_generator.py L27-39
def is_meaningless(text: str) -> bool:
    if not text: return True
    text = text.strip()
    if len(text) < 5: return True                          # 너무 짧음
    if re.fullmatch(r'[ㄱ-ㅎㅏ-ㅣ\s]+', text): return True  # 자음/모음 나열
    if re.fullmatch(r'[\.\\,\!\?\-\=\s\d]+', text): return True  # 특수문자 반복
    if re.fullmatch(r'[a-zA-Z]{1,5}', text): return True   # 짧은 영어 노이즈
    return False
```

**② 컨텍스트 격리 및 지시어 전환**

```python
# [수정 후] question_generator.py L394-401
if is_meaningless(last_user_transcript.text):
    context_text = "[주의: 지원자의 이전 답변이 무의미하거나 누락되었습니다. 과거 정보에 의존하지 말고 다시 물어보십시오.]"
    logger.warning("🚫 Meaningless input detected! Isolating context to prevent hallucination.")

# [수정 후] question_generator.py L488-491
if is_meaningless(u_text) or any(kw in u_text for kw in negative_keywords):
    mode_task_instruction = "지원자가 답변을 하지 못하거나 의미 없는 입력을 했습니다. 이전 내용에 대한 요약이나 추측을 100% 생략하고, 정중하게 다시 설명을 요청하거나 다른 주제로 전환하십시오."
    global_constraint = "이전 답변 요약을 **절대** 하지 마십시오. 답변을 지어내지 말고, '알겠습니다. 그렇다면...'과 같이 자연스럽게 대화를 이어가십시오."
```

**③ 부정적 키워드 목록**

```python
negative_keywords = [
    "모르겠습니다", "모르겠어요", "아니요", "없습니다",
    "기억이 안 남", "잘 모름", "몰라요", "몰라", "싫어", "싫음", "싫다"
]
```

---

## 3.2.6 해결 결과

- **Before**: 무의미 입력 시 AI가 존재하지 않는 경험을 인용하여 질문 생성
- **After**: `is_meaningless()` 감지 후 컨텍스트 격리 → 환각 없이 "다시 설명을 요청하거나 주제를 전환"하는 정상 질문 생성
- **교훈**: LLM은 빈 컨텍스트를 허구로 채우는 경향이 있으므로, 입력 품질 검증(Garbage In → Guard Rail)을 프롬프트 수준이 아닌 코드 수준에서 먼저 처리해야 함
