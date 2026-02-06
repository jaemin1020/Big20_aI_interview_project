🎯 최적의 면접 질문 생성 전략: RAG 기반 Context 융합 방식
단순히 LLM에게 질문을 맡기는 것이 아니라, DB에 저장된 **기업 정보(인재상/JD)**와 표준 질문 세트를 이력서와 정교하게 매칭하는 것이 핵심입니다.

1. 데이터 파이프라인 구조질문 생성은 아래 3가지 소스를 결합하여 이루어집니다.
   데이터 소스저장 방식 (PostgreSQL)활용 목적
   기업 정보company_info (인재상, JD)
   채용 적합성(Cultural Fit) 기준 수립
   질문 은행question_db (산업/직무별)검증된 양질의 질문 템플릿 제공
   이력서resume_embeddings (Vector)후보자의 개별 경험 및 역량 파악
2. 질문 생성 프로세스 (Workflow)
   단계 1: 시맨틱 검색 (Semantic Retrieval)pgvector를 사용하여 이력서의 각 문단과 가장 유사한 산업/직무별 질문을 검색합니다.
   예: 이력서에 "React 성능 최적화" 언급 → 질문 DB에서 "프론트엔드 성능 저하 해결 사례" 질문 추출.
   단계 2: 인재상 정렬 (Alignment)추출된 질문들을 회사의 인재상 및 JD와 대조하여 필터링합니다.우리 회사가 '협업'을 중시한다면,
   기술 질문 중에서도 '협업 과정에서의 기술적 소통'에 관한 질문에 가중치를 둡니다.
   단계 3: Solar 10.7B를 이용한 맞춤형 생성검색된 문맥(Context)들을 Solar 모델에게 전달하여, 이력서의 고유한 수치나 프로젝트명이 포함된 개인 맞춤형 질문으로 재구성합니다.
3. 추천 프롬프트 엔지니어링 (Chain-of-Thought)Solar 10.7B에 전달할 최적의 프롬프트 구조입니다.
   Markdown

### Role

너는 대기업의 전문 면접관이야. 아래 제공된 정보를 바탕으로 지원자를 날카롭게 검증할 수 있는 질문을 생성해.

### Context

1. 회사의 인재상: {target_values}
2. 직무 및 산업군: {job_description}
3. 지원자 이력서 핵심 내용: {resume_context}
4. 참고용 표준 질문: {retrieved_questions}

### Task

- 표준 질문의 논리를 유지하되, 이력서의 구체적인 프로젝트 경험을 결합할 것.
- 인재상 중 '{value_A}'를 확인할 수 있는 압박 질문 1개를 포함할 것.
- 답변 시나리오를 고려하여 '꼬리 질문(Follow-up)'까지 설계할 것.

### Constraint

- 전문 용어를 적절히 섞어 전문성을 보여줄 것.
- 질문은 3개 이내로 생성할 것.

4. 아키텍처 상의 구현 로직
   FE (React): 사용자가 이력서 업로드.
   BE (FastAPI): 이력서 텍스트 추출 및 임베딩 생성.
   DB (pgvector): ```sql-- 이력서와 가장 유사한 직무 질문 3개 찾기
   SELECT question_textFROM question_dbORDER BY embedding <=> l2_normalize(resume_vector)LIMIT 3;
   AW (Celery): 검색된 결과와 인재상을 프롬프트에 담아 Solar 10.7B 호출.
   Result: 생성된 질문을 DB에 저장하고 WebSocket/Axios를 통해 프론트엔드에 전달.
