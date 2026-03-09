# Chat Conversation

Note: _This is purely the output of the chat conversation and does not contain any raw data, codebase snippets, etc. used to generate the output._

### User Input

C:\big20\Big20_aI_interview_project\backend-core\config\interview_scenario_transition.py 여기서  "type": "template"은 생성 즉 llm을 거치지 않으니 RAG라고 할수 없는건가

*Viewed [interview_scenario_transition.py](file:///c:/big20/Big20_aI_interview_project/backend-core/config/interview_scenario_transition.py) *

### Planner Response

네, 사용자의 지적이 정확합니다. `type: "template"`으로 정의된 부분은 **엄격한 의미에서의 RAG(Retrieval-Augmented Generation)라고 보기 어렵습니다.**

그 이유는 다음과 같습니다.

### 1. "Generation" 과정의 부재 (LLM 미사용)
RAG의 핵심은 **검색(Retrieval)**된 정보를 바탕으로 LLM이 상황에 맞는 문장을 **생성(Generation)**하는 것입니다. 하지만 `type: "template"`은:
*   미리 정해진 문장 구조(Template)가 있고,
*   단순히 `{candidate_name}`, `{target_role}` 같은 변수만 치환(String Interpolation)하여 출력합니다.
*   이 과정에서 LLM의 "추론"이나 "문장 구성 능력"이 개입하지 않기 때문에 이는 **'룰 기반(Rule-based) 템플릿 방식'**에 해당합니다.

### 2. 변수 데이터의 출처 (Retrieval의 관점)
다만, 이 템플릿에 들어가는 **변수들의 값**(`cert_list`, `proj_name` 등)이 어디서 왔는지가 중요합니다.
*   만약 이 변수들이 사전에 단순히 DB에서 읽어온 데이터라면 완전히 RAG가 아닙니다.
*   하지만 만약 AI가 이력서 수천 페이지 중 관련 내용을 **검색(Retrieval)**해서 추출해둔 데이터라면, "검색" 단계가 포함된 시스템의 일부라고 볼 수는 있습니다. 그럼에도 불구하고 이 특정 시나리오 단계 자체는 "템플릿 출력"일 뿐입니다.

### 3. 이 파일 내의 진짜 RAG/AI 단계
기술적으로 **RAG 또는 다이나믹 AI 생성**에 해당하는 부분은 동일 파일 내의 다른 `type`들입니다.
*   **`type: "followup"` (예: 54번 라인, 85번 라인 등):** 지원자의 답변(데이터)을 바탕으로 AI가 실시간으로 분석하여 질문을 생성하므로 AI Generation 영역입니다.
*   **`type: "ai"` (예: 130번 라인):** `{company_ideal}` 같은 외부 정보(기업 인재상)를 가져와서(Retrieval) 그에 맞는 질문을 생성(Generation)하도록 가이드를 주고 있으므로, 이 단계가 전형적인 **RAG 또는 컨텍스트 기반 생성** 방식입니다.

### 요약하자면:
`"type": "template"`은 면접의 **일관성**과 **안정성**을 위해 도입된 **정적(Static) 방식**입니다. 
따라서 이 부분만 떼어놓고 본다면 **RAG가 아니며**, 전체 시스템은 [안정적인 템플릿] + [유동적인 RAG/AI 생성]이 혼합된 **하이브리드 구조**라고 이해하시는 것이 가장 정확합니다.