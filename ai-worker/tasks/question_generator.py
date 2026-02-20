import sys
import os
import re
import gc
import logging
import torch
import json
from datetime import datetime
from celery import shared_task  # Celery 비동기 작업 데코레이터

# ==========================================
# 1. Initial setup & path optimization
# ==========================================

# 🔹 sys.path: Python이 모듈을 찾는 경로 리스트
# "/app" 경로가 없으면 맨 앞에 추가
# → 컨테이너 환경에서 로컬 모듈 import 보장
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

# 🔹 logger 생성 (worker 전용 이름)
logger = logging.getLogger("AI-Worker-QuestionGen")

# ==========================================
# LangChain imports
# ==========================================

from langchain_core.prompts import PromptTemplate
# PromptTemplate: LLM에 넣을 프롬프트 템플릿 관리

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
# OutputParser: LLM 출력 후처리

from langchain_core.runnables import RunnablePassthrough
# LCEL에서 데이터 흐름 연결용 (여기서는 미사용)

# ==========================================
# 2. Persona Prompt (Prompt Engineering)
# ==========================================

PROMPT_TEMPLATE = """당신은 20년 경력의 베테랑 면접관이며 전문 채용 위원장입니다. 
지원자의 답변을 바탕으로 날카로우면서도 성취 지향적인 다음 면접 질문을 생성하십시오.

[면접 상황 관제 정보]
- 지원 직무: {position}
- 지원자 성명: {name}
- 현재 단계: {stage_display}
- 핵심 가이드: {guide}

[참고: 지원자 이력서 문맥]
{context}

[이전 대화 요약]
{chat_history}

[질문 생성 지침]
1. 반드시 다음 질문 1개만 텍스트로 출력하십시오.
2. 지원자의 답변 내용에서 기술적 키워드나 경험 수치를 인용하여 구체적으로 질문하십시오.
3. 질문 끝에는 "..." 같은 특수문자를 남발하지 말고 정중한 마침표나 물음표로 끝내십시오.
4. 길이는 150자 이내로 핵심만 찌르십시오.
5. {stage_display} 성격에 맞는 질문이어야 합니다.

질문:"""

# ==========================================
# 3. Main Task: Generate Question
# ==========================================

# 🔹 Celery task 등록
# → 비동기 워커에서 실행됨
@shared_task(name="tasks.question_generation.generate_next_question")
def generate_next_question_task(interview_id: int):
    """
    [Role]
    Determine interview progress and generate the next AI question.
    """

    # 🔹 내부 import (circular import 방지 + worker startup 속도 개선)
    from db import (
        engine,
        Session,
        select,
        Interview,
        Transcript,
        Speaker,
        Question,
        save_generated_question
    )
    from utils.exaone_llm import get_exaone_llm
    from tasks.rag_retrieval import retrieve_context

    logger.info(f"🚀 [START] Generating next question for Interview {interview_id}")

    # 🔹 DB 세션 컨텍스트 매니저
    # with 블록 종료 시 자동 close
    with Session(engine) as session:

        # ======================================
        # 1. Load interview
        # ======================================

        # session.get(Model, pk)
        interview = session.get(Interview, interview_id)

        if not interview:
            logger.error(f"Interview {interview_id} not found")
            return {"status": "error", "message": "Interview not found"}

        # ======================================
        # 2. Load transcripts (latest first)
        # ======================================

        # 🔹 SQLModel select
        stmt = (
            select(Transcript)
            .where(Transcript.interview_id == interview_id)
            .order_by(Transcript.order.desc())  # 최신순
        )

        transcripts = session.exec(stmt).all()

        if not transcripts:
            logger.warning(
                f"No transcripts found for interview {interview_id}. "
                "Logic might need initial setup."
            )
            return {"status": "error", "message": "No transcripts found"}

        last_transcript = transcripts[0]

        # ======================================
        # 3. Duplicate generation guard
        # ======================================

        # 🔹 마지막 화자가 AI면
        if last_transcript.speaker == "AI":
            diff = (datetime.utcnow() - last_transcript.timestamp).total_seconds()

            # 🔹 10초 이내 재요청 차단
            if diff < 10:
                logger.info(f"Skipping: Last AI message was just {diff:.1f}s ago.")
                return {"status": "skipped", "reason": "too_soon"}

        # ======================================
        # 4. Decide next stage (Scenario logic)
        # ======================================

        from utils.interview_helpers import check_if_transition, get_candidate_info

        # 🔹 지원자 정보 조회
        cand_info = get_candidate_info(session, interview.resume_id)

        # 🔹 직무 전환자 여부 판단
        is_transition = check_if_transition(
            cand_info.get("major", ""),
            interview.position
        )

        # 🔹 시나리오 분기
        if is_transition:
            import config.interview_scenario_transition as scenario
        else:
            import config.interview_scenario as scenario

        # ======================================
        # Find last AI stage
        # ======================================

        # 🔹 generator expression + next()
        # 조건 맞는 첫 요소 반환
        last_ai_transcript = next(
            (t for t in transcripts if t.speaker == "AI"),
            None
        )

        # 기본 단계
        last_stage_name = "motivation"

        # 🔹 마지막 AI 질문의 stage 추적
        if last_ai_transcript and last_ai_transcript.question_id:
            q = session.get(Question, last_ai_transcript.question_id)
            if q:
                last_stage_name = q.question_type or "motivation"

        # 🔹 다음 단계 계산
        next_stage_data = scenario.get_next_stage(last_stage_name)

        # ======================================
        # Interview finished
        # ======================================

        if not next_stage_data:
            logger.info(
                f"Interview {interview_id} finished (No more stages). "
                "Status -> COMPLETED"
            )
            interview.status = "COMPLETED"
            session.add(interview)
            session.commit()
            return {"status": "completed"}

        stage_name = next_stage_data["stage"]
        stage_display = next_stage_data.get("display_name", "심층 면접")
        stage_guide = next_stage_data.get("guide", "지원자의 역량을 검증하십시오.")

        logger.info(f"Target Stage: {stage_name} ({stage_display})")

        # ======================================
        # 5. RAG context retrieval
        # ======================================

        rag_context = ""

        # 🔹 특정 타입일 때만 RAG 수행
        if next_stage_data.get("type") in ("ai", "followup"):

            # query_template.format(...)
            query = next_stage_data.get(
                "query_template",
                interview.position
            ).format(target_role=interview.position)

            # 🔹 벡터 검색
            search_results = retrieve_context(
                query,
                resume_id=interview.resume_id,
                top_k=5
            )

            # 🔹 리스트 → 문자열 결합
            rag_context = "\n".join([r['text'] for r in search_results])

        # ======================================
        # 6. Recent chat summary
        # ======================================

        chat_limit = 5

        # transcripts[:chat_limit] → 최신 5개
        # [::-1] → 시간 순 정렬
        recent_chats = transcripts[:chat_limit][::-1]

        chat_history_str = "\n".join(
            [f"{t.speaker}: {t.text}" for t in recent_chats]
        )

        # ======================================
        # 7. LLM call (LCEL)
        # ======================================

        try:
            llm = get_exaone_llm()

            prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)

            output_parser = StrOutputParser()

            # 🔹 LCEL chain 구성
            # prompt → llm → parser
            chain = prompt | llm | output_parser

            # 🔹 체인 실행
            final_content = chain.invoke({
                "position": interview.position,
                "name": cand_info.get("candidate_name", "지원자"),
                "stage_display": stage_display,
                "guide": stage_guide,
                "context": (
                    rag_context
                    if rag_context
                    else "이력서 정보가 충분하지 않습니다. 일반적인 직무 지식을 물어보십시오."
                ),
                "chat_history": chat_history_str
            })

            # ======================================
            # Post-processing
            # ======================================

            # 🔹 이미 [Stage] 붙어 있으면 중복 방지
            if not final_content.startswith('['):
                intro_msg = next_stage_data.get("intro_sentence", "")

                final_content = (
                    f"[{stage_display}] {intro_msg} {final_content}"
                    if intro_msg
                    else f"[{stage_display}] {final_content}"
                )

            # ======================================
            # 8. Save result
            # ======================================

            save_generated_question(
                interview_id=interview_id,
                content=final_content,
                category=next_stage_data.get("category", "general"),
                stage=stage_name,
                guide=stage_guide
            )

            logger.info(
                f"✅ Successfully generated and saved next question "
                f"for Interview {interview_id}"
            )

            # ======================================
            # Memory cleanup
            # ======================================

            gc.collect()

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            return {"status": "success", "stage": stage_name}

        except Exception as llm_err:
            logger.error(f"❌ LLM generation failed: {llm_err}")
            return {"status": "error", "message": "LLM failed"}
