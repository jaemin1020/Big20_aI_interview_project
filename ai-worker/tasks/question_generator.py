import sys
import os
import re
import gc 
import logging
import torch
import json
from datetime import datetime
from celery import shared_task

# 1. 초기 설정 및 모델 경로 최적화
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

logger = logging.getLogger("AI-Worker-QuestionGen")

# LangChain 관련 임포트
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ==========================================
# 2. 페르소나 설정 (Prompt Engineering)
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
# 3. 메인 작업: 질문 생성 태스크
# ==========================================

@shared_task(name="tasks.question_generation.generate_next_question")
def generate_next_question_task(interview_id: int):
    """
    [함수의 역할] 인터뷰 진행 상황을 파악하고 다음 단계의 AI 질문을 생성합니다.
    """
    # 순환 참조 방지를 위해 내부 임포트
    from db import (engine, Session, select, Interview, Transcript, Speaker, Question, save_generated_question)
    from utils.exaone_llm import get_exaone_llm
    from tasks.rag_retrieval import retrieve_context
    
    logger.info(f"🚀 [START] Generating next question for Interview {interview_id}")
    
    with Session(engine) as session:
        # 1. 인터뷰 정보 로드
        interview = session.get(Interview, interview_id)
        if not interview: 
            logger.error(f"Interview {interview_id} not found")
            return {"status": "error", "message": "Interview not found"}

        # 2. 대화 내역 조회 (현재 단계 파악용)
        stmt = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.order.desc())
        transcripts = session.exec(stmt).all()
        
        if not transcripts:
            logger.warning(f"No transcripts found for interview {interview_id}. Logic might need initial setup.")
            return {"status": "error", "message": "No transcripts found"}

        last_transcript = transcripts[0]
        
        # 3. 중복 생성 방지 (AI가 질문했는데 10초 이내에 또 요청 오면 무시)
        if last_transcript.speaker == "AI":
            diff = (datetime.utcnow() - last_transcript.timestamp).total_seconds()
            if diff < 10: 
                logger.info(f"Skipping: Last AI message was just {diff:.1f}s ago.")
                return {"status": "skipped", "reason": "too_soon"}

        # 4. 다음 단계 결정 (Scenario Logic)
        from utils.interview_helpers import check_if_transition, get_candidate_info
        cand_info = get_candidate_info(session, interview.resume_id)
        is_transition = check_if_transition(cand_info.get("major", ""), interview.position)
        
        # 시나리오 로드
        if is_transition:
            import config.interview_scenario_transition as scenario
        else:
            import config.interview_scenario as scenario
            
        # 마지막 AI 질문의 단계를 찾고 다음 단계 결정
        last_ai_transcript = next((t for t in transcripts if t.speaker == "AI"), None)
        last_stage_name = "motivation" # 기본값
        if last_ai_transcript and last_ai_transcript.question_id:
            q = session.get(Question, last_ai_transcript.question_id)
            if q: last_stage_name = q.question_type or "motivation"
        
        next_stage_data = scenario.get_next_stage(last_stage_name)
        
        if not next_stage_data:
            logger.info(f"Interview {interview_id} finished (No more stages). Status -> COMPLETED")
            interview.status = "COMPLETED"
            session.add(interview)
            session.commit()
            return {"status": "completed"}

        stage_name = next_stage_data["stage"]
        stage_display = next_stage_data.get("display_name", "심층 면접")
        stage_guide = next_stage_data.get("guide", "지원자의 역량을 검증하십시오.")
        
        logger.info(f"Target Stage: {stage_name} ({stage_display})")

        # 5. RAG 컨텍스트 확보
        # 직무 지식이나 경험 질문인 경우 이력서에서 관련 내용을 뽑아옴
        rag_context = ""
        if next_stage_data.get("type") == "ai" or next_stage_data.get("type") == "followup":
            query = next_stage_data.get("query_template", interview.position).format(target_role=interview.position)
            search_results = retrieve_context(query, resume_id=interview.resume_id, top_k=5)
            rag_context = "\n".join([r['text'] for r in search_results])

        # 6. 최근 대화 요약 (Context for LLM)
        # 최근 3~4개의 대화만 요약하여 전달
        chat_limit = 5
        recent_chats = transcripts[:chat_limit][::-1] # 역순 (오래된 것부터)
        chat_history_str = "\n".join([f"{t.speaker}: {t.text}" for t in recent_chats])

        # 7. LLM 호출 (LangChain LCEL)
        try:
            llm = get_exaone_llm()
            prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
            output_parser = StrOutputParser()
            
            chain = prompt | llm | output_parser
            
            final_content = chain.invoke({
                "position": interview.position,
                "name": cand_info.get("candidate_name", "지원자"),
                "stage_display": stage_display,
                "guide": stage_guide,
                "context": rag_context if rag_context else "이력서 정보가 충분하지 않습니다. 일반적인 직무 지식을 물어보십시오.",
                "chat_history": chat_history_str
            })
            
            # 후처리: [단계] 말머리가 이미 생성된 경우 중복 방지
            if not final_content.startswith('['):
                intro_msg = next_stage_data.get("intro_sentence", "")
                final_content = f"[{stage_display}] {intro_msg} {final_content}" if intro_msg else f"[{stage_display}] {final_content}"

            # 8. 결과 저장
            save_generated_question(
                interview_id=interview_id,
                content=final_content,
                category=next_stage_data.get("category", "general"),
                stage=stage_name,
                guide=stage_guide
            )
            
            logger.info(f"✅ Successfully generated and saved next question for Interview {interview_id}")
            
            # 메모리 정리
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return {"status": "success", "stage": stage_name}

        except Exception as llm_err:
            logger.error(f"❌ LLM generation failed: {llm_err}")
            return {"status": "error", "message": "LLM failed"}
