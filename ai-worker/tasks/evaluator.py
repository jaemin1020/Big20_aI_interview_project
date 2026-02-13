import logging
import time
import re
import json
import sys
import os
from pydantic import BaseModel, Field
from typing import List
from langchain_core.output_parsers import JsonOutputParser
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
    overall_score: int = Field(description="전체 평균 점수 (0-100)")
    technical_score: int = Field(description="기술 이해도 (0-100)")
    experience_score: int = Field(description="직무 경험 (0-100)")
    problem_solving_score: int = Field(description="문제 해결 (0-100)")
    communication_score: int = Field(description="의사소통 (0-100)")
    responsibility_score: int = Field(description="책임감 (0-100)")
    growth_score: int = Field(description="성장 의지 (0-100)")
    
    technical_feedback: str = Field(description="기술 원리 및 선택 근거에 대한 분석")
    experience_feedback: str = Field(description="직무 경험의 구체성과 실무 연계성에 대한 평가")
    problem_solving_feedback: str = Field(description="STAR 기법에 기반한 논리적 전개 능력 분석")
    communication_feedback: str = Field(description="전문어 사용의 적절성 및 메시지 전달력 평가")
    responsibility_feedback: str = Field(description="답변의 일관성 및 업무에 임하는 책임감 분석")
    growth_feedback: str = Field(description="자기계발 의지 및 향후 발전 가능성에 대한 제언")

    strengths: List[str] = Field(description="지원자의 주요 강점 2-3가지")
    improvements: List[str] = Field(description="보완이 필요한 약점 및 개선점 2-3가지")
    summary_text: str = Field(description="성장을 위한 시니어 위원장의 최종 한마디 (3문장 내외)")

@shared_task(name="tasks.evaluator.analyze_answer")
def analyze_answer(transcript_id: int, question_text: str, answer_text: str, rubric: dict = None, question_id: int = None):
    """개별 답변 평가 및 실시간 다음 질문 생성 트리거"""
    
    # 🔗 즉시 다음 질문 생성 트리거 (분석 완료를 기다리지 않고 바로 생성 시작)
    try:
        from tasks.question_generator import generate_next_question_task
        interview_id = None
        with Session(engine) as session:
            t = session.get(Transcript, transcript_id)
            if t:
                interview_id = t.interview_id
        
        if interview_id:
            generate_next_question_task.apply_async(args=[interview_id], queue='gpu_queue')
            logger.info(f"🚀 [ROUTED] send next question task to gpu_queue for Interview {interview_id}")
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
            logger.info("⚡ [FAST MODE] CPU Worker spotted. Skipping heavy LLM for individual answer evaluation.")
            result = {
                "technical_score": 3,
                "communication_score": 3,
                "feedback": "답변이 수신되었습니다. 상세 평가는 최종 리포트를 확인하세요."
            }
        else:
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

@shared_task(name="tasks.evaluator.generate_final_report")
def generate_final_report(interview_id: int):
    """
    최종 평가 보고서 생성 (시니어 면접관 페르소나 적용)
    """
    logger.info(f"Generating Final Report for Interview {interview_id}")
    from db import create_or_update_evaluation_report, update_interview_overall_score, get_interview_transcripts
    
    try:
        transcripts = get_interview_transcripts(interview_id)
        logger.info(f"📊 Found {len(transcripts)} transcripts for Interview {interview_id}")
        
        if not transcripts:
            logger.warning(f"⚠️ No transcripts found for Interview {interview_id}. Returning early.")
            create_or_update_evaluation_report(
                interview_id,
                technical_score=0, communication_score=0, cultural_fit_score=0,
                summary_text="기록된 대화가 없어 리포트를 생성할 수 없습니다.",
                details_json={"error": "no_data"}
            )
            return

        conversation = "\n".join([f"{t.speaker}: {t.text}" for t in transcripts])
        logger.info(f"🤖 Starting LLM analysis for Interview {interview_id}...")

        try:
            # LangChain Parser 설정
            parser = JsonOutputParser(pydantic_object=FinalReportSchema)
            
            exaone = get_exaone_llm()
            system_msg = """당신은 대한민국 최고의 기술 기업에서 수천 명의 지원자를 검증해온 '시니어 면접관 위원회'의 위원장입니다. 
당신의 임무는 제공된 면접 로그를 바탕으로 지원자의 역량을 6개 핵심 지표로 정밀 평가하는 것입니다.

[평가 방법론: STAR & Consistency]
1. STAR 분석: 지원자가 답변에서 구체적인 상황(S), 과업(T), 행동(A), 결과(R)를 논리적으로 설명했는지 분석하십시오.
2. 기술적 정합성: 선택한 기술의 이유와 원리를 명확히 알고 있는지 체크하십시오.
3. 태도 일관성: 면접 전체 과정에서 용어 사용의 적절성과 가치관의 일관성을 확인하십시오.
4. 유연한 평가: 만약 면접이 중간에 종료되어 데이터가 부족하더라도, 제공된 답변 범위 내에서 최선의 분석을 제공하고 부족한 부분은 '추후 확인 필요' 등으로 명시하십시오. 중도 종료 자체만으로 점수를 낮게 평가하지 마십시오. """

            user_msg = f"""다음 면접 대화 내용을 기반으로 최종 평가를 내리십시오.
            
[면접 대화]
{conversation}

[제약 사항]
- 결과는 반드시 시스템 연동을 위해 지정된 JSON 포맷으로만 출력하십시오.
- 각 피드백은 지원자의 성장을 돕는 '시니어의 조언' 톤을 유지하십시오.
- strengths와 improvements는 반드시 문자열 배열([])로 작성하십시오.

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
                
        except Exception as llm_err:
            logger.error(f"LLM Summary failed: {llm_err}")
            result = {
                "overall_score": 70,
                "technical_score": 70, "experience_score": 70, "problem_solving_score": 70,
                "communication_score": 70, "responsibility_score": 70, "growth_score": 70,
                "summary_text": "분석 시스템 지연으로 요약이 지체되었습니다.",
                "strengths": ["성실한 답변"], "improvements": ["상세 분석 불가"]
            }

        # DB 저장을 위해 점수 추출
        tech = result.get("technical_score", 0)
        comm = result.get("communication_score", 0)
        # cultural_fit은 responsibility와 growth의 평균으로 임시 계산 (DB 컬럼 호환성)
        cult = (result.get("responsibility_score", 0) + result.get("growth_score", 0)) / 2
        overall = result.get("overall_score", (tech + comm + cult) / 3)

        # 모든 상세 필드를 details_json에 저장 (프론트엔드 연동)
        details = {
            "experience_score": result.get("experience_score", 0),
            "problem_solving_score": result.get("problem_solving_score", 0),
            "responsibility_score": result.get("responsibility_score", 0),
            "growth_score": result.get("growth_score", 0),
            "technical_feedback": result.get("technical_feedback", ""),
            "experience_feedback": result.get("experience_feedback", ""),
            "problem_solving_feedback": result.get("problem_solving_feedback", ""),
            "communication_feedback": result.get("communication_feedback", ""),
            "responsibility_feedback": result.get("responsibility_feedback", ""),
            "growth_feedback": result.get("growth_feedback", ""),
            "strengths": result.get("strengths", []),
            "improvements": result.get("improvements", [])
        }

        create_or_update_evaluation_report(
            interview_id,
            technical_score=tech,
            communication_score=comm,
            cultural_fit_score=cult,
            summary_text=result.get("summary_text", ""),
            details_json=details
        )
        update_interview_overall_score(interview_id, score=overall)
        logger.info(f"✅ Final Report Generated for Interview {interview_id} with Senior Persona")

    except Exception as e:
        logger.error(f"❌ Error in generate_final_report: {e}")
        create_or_update_evaluation_report(
            interview_id,
            technical_score=0, summary_text=f"오류: {str(e)}"
        )
