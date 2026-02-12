import logging
import time
import re
import json
import sys
import os
<<<<<<< HEAD
from pydantic import BaseModel, Field
from typing import List
from langchain_core.output_parsers import JsonOutputParser
=======
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
from celery import shared_task

# DB Helper Functions
from db import (
    engine,
    Session,
    Transcript,
    update_transcript_sentiment,
    update_question_avg_score,
    get_interview_transcripts,
    get_user_answers
)

# AI-Worker 루트 디렉토리를 찾아 sys.path에 추가
current_file_path = os.path.abspath(__file__) # tasks/evaluator.py
tasks_dir = os.path.dirname(current_file_path) # tasks/
ai_worker_root = os.path.dirname(tasks_dir)    # ai-worker/

if ai_worker_root not in sys.path:
    sys.path.insert(0, ai_worker_root)

# utils.exaone_llm은 실제 사용 시점에 임포트 (워커 시작 시 크래시 방지)
<<<<<<< HEAD
try:
    from utils.exaone_llm import get_exaone_llm
except ImportError:
    def get_exaone_llm():
        from ai_worker.utils.exaone_llm import get_exaone_llm
        return get_exaone_llm()

logger = logging.getLogger("AI-Worker-Evaluator")

# -----------------------------------------------------------
# [Schema] 평가 데이터 구조 정의 (Pydantic)
# -----------------------------------------------------------
class AnswerEvalSchema(BaseModel):
    technical_score: int = Field(description="기술적 지식 및 숙련도 점수 (0-5)")
    communication_score: int = Field(description="의사소통 및 전달 능력 점수 (0-5)")
    feedback: str = Field(description="답변에 대한 구체적이고 건설적인 피드백")

class FinalReportSchema(BaseModel):
    technical_score: int = Field(description="전체 기술 면접 점수 (0-100)")
    communication_score: int = Field(description="전체 의사소통 점수 (0-100)")
    cultural_fit_score: int = Field(description="조직 적합성 점수 (0-100)")
    summary_text: str = Field(description="면접 전체 요약 (3문장 내외)")
    strengths: List[str] = Field(description="지원자의 주요 강점 3가지")
    weaknesses: List[str] = Field(description="보완이 필요한 약점 및 개선점")

=======

logger = logging.getLogger("AI-Worker-Evaluator")

>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
@shared_task(name="tasks.evaluator.analyze_answer")
def analyze_answer(transcript_id: int, question_text: str, answer_text: str, rubric: dict = None, question_id: int = None):
    """개별 답변 평가 및 실시간 다음 질문 생성 트리거"""
    
    # 🔗 즉시 다음 질문 생성 트리거 (분석 완료를 기다리지 않고 바로 생성 시작)
    try:
<<<<<<< HEAD
        from tasks.question_generator import generate_next_question_task
=======
        from tasks.question_generation import generate_next_question_task
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
        interview_id = None
        with Session(engine) as session:
            t = session.get(Transcript, transcript_id)
            if t:
                interview_id = t.interview_id
        
        if interview_id:
<<<<<<< HEAD
            generate_next_question_task.apply_async(args=[interview_id], queue='gpu_queue')
            logger.info(f"🚀 [IMMEDIATE] apply_async(queue='gpu_queue') called for Interview {interview_id}")
=======
            generate_next_question_task.delay(interview_id)
            logger.info(f"🚀 [IMMEDIATE] delay() called for Interview {interview_id}")
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
        else:
            logger.error(f"Could not find interview_id for transcript {transcript_id}")
    except Exception as e:
        logger.error(f"Failed to trigger next question task: {e}")
    logger.info(f"Analyzing Transcript {transcript_id} for Question {question_id}")
    
    if not answer_text or not answer_text.strip():
        logger.warning(f"Empty answer for transcript {transcript_id}. Skipping LLM evaluation.")
        return {
            "technical_score": 0,
            "communication_score": 0,
            "feedback": "답변이 제공되지 않았습니다."
        }
    
    start_ts = time.time()
    
    try:
        # GPU 레이어 확인 (CPU 워커면 무거운 분석 생략하여 큐 정체 방지)
        n_gpu_layers = int(os.getenv("N_GPU_LAYERS", "0"))
        
        if n_gpu_layers == 0:
<<<<<<< HEAD
            logger.info("⚡ [FAST MODE] CPU Worker spotted. Skipping heavy LLM for individual answer evaluation.")
=======
            logger.info("⚡ [FAST MODE] CPU Worker spotted. Skipping heavy LLM for individual answer evaluation to speed up the process.")
            # 개별 분석은 기본값만 부여 (최종 리포트에서 전체 요약 수행)
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
            result = {
                "technical_score": 3,
                "communication_score": 3,
                "feedback": "답변이 수신되었습니다. 상세 평가는 최종 리포트를 확인하세요."
            }
        else:
<<<<<<< HEAD
            # LangChain Parser 설정
            parser = JsonOutputParser(pydantic_object=AnswerEvalSchema)
            
            # 엔진 가져오기
            llm_engine = get_exaone_llm()
            
            # 프롬프트 구성
            system_msg = "귀하는 전문 면접관이며, 지원자의 답변을 기술력과 의사소통 관점에서 평가합니다."
            user_msg = f"""다음 질문에 대한 지원자의 답변을 루브릭 기준에 맞춰 평가하십시오.
            
[질문]
{question_text}

[답변]
{answer_text}

[평가 루브릭]
{json.dumps(rubric, ensure_ascii=False) if rubric else "표준 면접 평가 기준"}

{parser.get_format_instructions()}"""
            
            # 생성 및 파싱
            prompt = llm_engine._create_prompt(system_msg, user_msg)
            raw_output = llm_engine.invoke(prompt, temperature=0.2)
            
            try:
                result = parser.parse(raw_output)
            except Exception as parse_err:
                logger.error(f"Failed to parse LLM output: {parse_err}")
                # 폴백: 정규표현식 시도 또는 기본값
                json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = {"technical_score": 3, "communication_score": 3, "feedback": "평가 데이터를 파싱할 수 없습니다."}
=======
            llm = get_exaone_llm()
            result = llm.evaluate_answer(
                question_text=question_text,
                answer_text=answer_text,
                rubric=rubric
            )
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
        
        tech_score = result.get("technical_score", 3)
        comm_score = result.get("communication_score", 3)
        sentiment = ((tech_score + comm_score) / 10.0) - 0.5 
        
        update_transcript_sentiment(
            transcript_id, 
            sentiment_score=sentiment, 
            emotion="neutral"
        )
        
        answer_quality = (tech_score + comm_score) * 10 
        
        if question_id:
            update_question_avg_score(question_id, answer_quality)

        duration = time.time() - start_ts
        logger.info(f"Evaluation Completed ({duration:.2f}s)")
        return result

    except Exception as e:
        logger.error(f"Evaluation Failed: {e}")
        return {"error": str(e)}

@shared_task(name="tasks.evaluator.generate_final_report", queue='gpu_queue')
def generate_final_report(interview_id: int):
    """
    최종 평가 보고서 생성
    
    Args:
        interview_id (int): 인터뷰 ID
    
    Returns:
        None
    
    Raises:
        ValueError: 답변이 없는 경우
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    logger.info(f"Generating Final Report for Interview {interview_id}")
    from db import create_or_update_evaluation_report, update_interview_overall_score, get_interview_transcripts
    
    try:
        transcripts = get_interview_transcripts(interview_id)
        if not transcripts:
            logger.warning("No transcripts found for this interview.")
            create_or_update_evaluation_report(
                interview_id,
                technical_score=0, communication_score=0, cultural_fit_score=0,
                summary_text="기록된 대화가 없어 리포트를 생성할 수 없습니다.",
                details_json={"error": "no_data"}
            )
            return

        conversation = "\n".join([f"{t.speaker}: {t.text}" for t in transcripts])

        try:
<<<<<<< HEAD
            # LangChain Parser 설정
            parser = JsonOutputParser(pydantic_object=FinalReportSchema)
            
            exaone = get_exaone_llm()
            system_msg = "귀하는 인사 전략 전문가이자 면접 분석관입니다. 전체 대화 흐름을 분석하여 리포트를 작성하십시오."
            user_msg = f"""다음 면접 대화 내용을 기반으로 최종 평가를 내리십시오.
            
[면접 대화]
{conversation}

{parser.get_format_instructions()}"""
            
            # 생성 및 파싱
            prompt = exaone._create_prompt(system_msg, user_msg)
            raw_output = exaone.invoke(prompt, temperature=0.3)
            
            try:
                result = parser.parse(raw_output)
            except Exception as parse_err:
                logger.error(f"Final report parsing failed: {parse_err}")
                json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise parse_err
=======
            exaone = get_exaone_llm()
            system_msg = "귀하는 면접 분석 전문가입니다. 면접 전체 요약과 점수를 산출하십시오."
            user_msg = f"""다음 면접 대화를 분석하여 JSON으로 만드세요.
            
[대화]
{conversation}

 반드시 JSON 형식으로만 응답:
{{
    "technical_score": 0~100,
    "communication_score": 0~100,
    "cultural_fit_score": 0~100,
    "summary_text": "3문장 이내 요약",
    "strengths": ["강점1", "강점2"],
    "weaknesses": ["약점1", "약점2"]
}}"""
            
            prompt = exaone._create_prompt(system_msg, user_msg)
            output = exaone.llm(prompt, max_tokens=1024, temperature=0.3)
            raw_result = output['choices'][0]['text'].strip()
            
            json_match = re.search(r'\{.*\}', raw_result, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("No JSON in response")
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
                
        except Exception as llm_err:
            logger.error(f"LLM Summary failed: {llm_err}")
            result = {
                "technical_score": 75, "communication_score": 75, "cultural_fit_score": 75,
                "summary_text": "분석 시스템 지연으로 요약이 지체되었습니다.",
                "strengths": ["성실한 답변"], "weaknesses": ["상세 분석 불가"]
            }

        tech = result.get("technical_score", 0)
        comm = result.get("communication_score", 0)
        cult = result.get("cultural_fit_score", 0)
        overall = (tech + comm + cult) / 3

        create_or_update_evaluation_report(
            interview_id,
            technical_score=tech,
            communication_score=comm,
            cultural_fit_score=cult,
            summary_text=result.get("summary_text", ""),
            details_json={
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("weaknesses", [])
            }
        )
        update_interview_overall_score(interview_id, score=overall)
        logger.info(f"✅ Final Report Generated for Interview {interview_id}")

    except Exception as e:
        logger.error(f"❌ Error in generate_final_report: {e}")
        create_or_update_evaluation_report(
            interview_id,
            technical_score=0, summary_text=f"오류: {str(e)}"
        )