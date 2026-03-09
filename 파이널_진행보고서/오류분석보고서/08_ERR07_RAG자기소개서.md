# ERR-07: 11번 단계 RAG 자기소개서 인용 실패

- **오류 코드**: ERR-07  
- **카테고리**: RAG / 벡터 검색  
- **심각도**: 🟠 MEDIUM  
- **상태**: ✅ 해결 완료  
- **관련 파일**: `ai-worker/tasks/question_generator.py`

---

## 3.2.1 문제 정의

면접 11번 단계(가치관/책임감 질문)에서 지원자의 자기소개서 [질문1] 내용을 인용하여 질문을 생성해야 하나, 자기소개서 데이터를 정상적으로 불러오지 못하여 일반적인 인재상 질문을 생성하는 오류가 발생하였습니다.

- **현상**: `"자기소개서에 [인용문장]라고 작성하셨습니다."` 형태가 되어야 하나, 실제로는 `"지원자의 가치관을 말씀해 주세요."` 와 같은 일반 질문 생성
- **재현 조건**: 11번(responsibility) 단계 진입 시 발생

---

## 3.2.2 문제 영향 분석

- **면접 품질 영향**: 개인화된 질문이 아닌 범용 질문 생성으로 면접의 차별성 저하
- **지원자 경험 영향**: 자기소개서를 읽지 않은 면접관처럼 느껴질 수 있어 신뢰도 하락

---

## 3.2.3 문제 파악 과정

**원인 A - `self_intro` 데이터 탐색 로직 부재**

자기소개서가 `structured_data.self_intro` 리스트에 저장되어 있으나, [질문1]을 정확히 찾는 로직이 없어 항상 빈 값으로 폴백됨.

```python
# [문제 상황] 수정 전
# self_intro_list를 순회하는 로직 자체가 없었음
# responsibility 단계도 일반 RAG 검색만 수행:
rag_results = retrieve_context("가치관", resume_id=..., top_k=2)
context_text = "\n".join([r['text'] for r in rag_results])
# → 자소서 [질문1]을 인용하지 않음
```

**원인 B - `[질문1]` 식별 키워드 불일치**

DB에 저장된 자기소개서 질문 텍스트가 `"[질문1]"`, `"질문 1"`, `"1."` 등 다양한 형식으로 저장되어 있어 단순 `==` 비교로는 찾을 수 없었습니다.

---

## 3.2.4 해결 접근 전략

- **`responsibility` 단계 전용 분기 추가**: 일반 RAG 대신 `structured_data.self_intro` 직접 탐색
- **유연한 질문 1 탐지**: `"[질문1]"`, `"질문 1"`, `"1."` 키워드 중 하나라도 매칭되면 추출
- **폴백 처리**: 질문 1을 찾지 못한 경우 전체 자기소개서 앞 300자를 컨텍스트로 활용

---

## 3.2.5 해결 도출 및 실행

```python
# [수정 후] question_generator.py L319-353
if next_stage.get("stage") == "responsibility":
    logger.info("✨ Responsibility Stage (11): Prioritizing Self-Intro Q1.")
    
    values_text = ""
    try:
        if interview.resume and interview.resume.structured_data:
            s_data = interview.resume.structured_data
            if isinstance(s_data, str):
                s_data = json.loads(s_data)
            
            self_intro_list = s_data.get("self_intro", [])
            for item in self_intro_list:
                q_text = item.get("question", "")
                # [개선] 다양한 형식으로 [질문1] 탐색
                if "[질문1]" in q_text or "질문 1" in q_text or q_text.startswith("1."):
                    ans = item.get('answer', '')
                    if len(ans) > 20:
                        values_text = f"[지원자 자기소개서 질문1 답변]: {ans}"
                        logger.info("📍 Found Question 1 in Self-Intro.")
                        break
            
            # Fallback: 전체 자소서 앞부분 활용
            if not values_text and self_intro_list:
                all_answers = " ".join([i.get("answer","") for i in self_intro_list])
                values_text = f"[지원자 자기소개서 요약]: {all_answers[:300]}"
    except Exception as e:
        logger.error(f"Failed to extract self_intro values: {e}")
    
    # RAG 결과와 결합
    rag_results = retrieve_context("지원자의 가치관, 직업 윤리, 정직함", resume_id=interview.resume_id, top_k=2)
    rag_context = "\n".join([r['text'] for r in rag_results]) if rag_results else ""
    context_text = f"{values_text}\n\n[추가 참고 정보]:\n{rag_context}".strip()
```

---

## 3.2.6 해결 결과

- **Before**: 11번 단계에서 자소서 인용 없이 `"지원자의 가치관을 말씀해 주세요."` 형태 생성
- **After**: `structured_data.self_intro`에서 [질문1] 답변을 직접 추출하여 `"자기소개서에 [인용문장]라고 작성하셨는데..."` 형태로 개인화된 질문 생성
- **교훈**: RAG(벡터 검색)만으로는 정형화된 구조적 데이터(자소서 특정 질문)를 정확히 찾기 어려울 수 있으므로, 구조화된 DB 데이터와 RAG를 상호 보완적으로 활용해야 함
