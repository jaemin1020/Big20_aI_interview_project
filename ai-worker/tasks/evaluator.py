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
    technical_score: int = Field(description="전체 기술 면접 점수 (0-100)")
    communication_score: int = Field(description="전체 의사소통 점수 (0-100)")
    cultural_fit_score: int = Field(description="조직 적합성 점수 (0-100)")
    summary_text: str = Field(description="면접 전체 요약 (3문장 내외)")
    strengths: List[str] = Field(description="지원자의 주요 강점 3가지")
    weaknesses: List[str] = Field(description="보완이 필요한 약점 및 개선점")

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
            logger.info(f"🚀 [IMMEDIATE] apply_async(queue='gpu_queue') called for Interview {interview_id}")
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
    
    # [수정: 2026-02-12] 비전 데이터(Vision Analysis) 조회 및 통합
    vision_data = None
    with Session(engine) as session:
        t = session.get(Transcript, transcript_id)
        if t and t.vision_analysis:
            vision_data = t.vision_analysis

    vision_summary = "비전 분석 데이터 없음"
    vision_score_breakdown = {}
    
    if vision_data:
        # [POC 점수 로직 구현]
        # 참고: ai-worker/poc/cv_poc/CV-V2-TASK.py
        
        # 1. 상수 및 가중치 설정
        WEIGHT_CONFIDENCE = 0.3   # 자신감 (미소)
        WEIGHT_FOCUS      = 0.3   # 시선 집중 (정면 응시)
        WEIGHT_POSTURE    = 0.2   # 자세 안정 (고개 흔들림 없음)
        WEIGHT_EMOTION    = 0.2   # 정서 안정 (불안/찌푸림 없음)
        
        # 2. 원본 데이터 추출 및 정규화
        total_frames = vision_data.get('duration_frames', 1)
        if total_frames == 0: total_frames = 1
        
        # 시선 비율 (이미 퍼센트 단위)
        gaze_ratio = vision_data.get('gaze_center_pct', 0) 
        
        # 미소 점수 (0.0-1.0 -> 0-100 환산)
        avg_smile = vision_data.get('avg_smile_score', 0) * 100
        
        # 불안 점수 (0.0-1.0 -> 0-100 환산)
        avg_anxiety = vision_data.get('avg_anxiety_score', 0) * 100
        
        # 자세 안정 비율 (프론트엔드에서 수집한 'posture_stable_pct' 사용)
        posture_ratio = vision_data.get('posture_stable_pct', 80.0) # 없으면 기본 80
        
        # 3. 가중치 점수 계산 (PoC 가중치 적용)
        score_conf = avg_smile * WEIGHT_CONFIDENCE
        score_focus = gaze_ratio * WEIGHT_FOCUS
        score_posture = posture_ratio * WEIGHT_POSTURE
        score_emotion = (100 - avg_anxiety) * WEIGHT_EMOTION
        
        overall_vision_score = score_conf + score_focus + score_posture + score_emotion
        
        vision_score_breakdown = {
            "confidence": round(score_conf, 1),
            "focus": round(score_focus, 1),
            "posture": round(score_posture, 1),
            "emotion": round(score_emotion, 1),
            "total": round(overall_vision_score, 1)
        }
        
        logger.info(f"📊 [Vision Score Breakdown] Transcript={transcript_id} | Total={overall_vision_score} | Breakdown={vision_score_breakdown}")
        
        vision_summary = f"""
[비언어적 태도 채점 결과 (총점: {overall_vision_score:.1f}/100)]
1. 자신감(미소): {score_conf:.1f}점 (배점 30점) - 평균 미소: {avg_smile:.1f}%
2. 시선집중: {score_focus:.1f}점 (배점 30점) - 정면 응시: {gaze_ratio}%
3. 자세안정: {score_posture:.1f}점 (배점 20점) - 안정 유지: {posture_ratio}% (추정치)
4. 정서안정: {score_emotion:.1f}점 (배점 20점) - 불안 지수: {avg_anxiety:.1f}% (낮을수록 좋음)

* 이 점수는 POC(V4.5) 알고리즘에 기반하여 산출되었습니다.
"""
    # [수정: 2026-02-12] 도커 로그에 비전 점수 출력 (User Request - Critical)
    logger.info(f"📊 [Vision Score Breakdown] {vision_summary}")

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
                # 폴백: 정규표현식 시도
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