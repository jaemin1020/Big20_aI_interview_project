import logging
import time
from celery import shared_task

# DB Helper Functions
from db import (
    update_transcript_sentiment,
    update_question_avg_score,
    get_interview_transcripts,
    get_user_answers
)

# EXAONE LLM import
from utils.exaone_llm import get_exaone_llm

logger = logging.getLogger("AI-Worker-Evaluator")

@shared_task(name="tasks.evaluator.analyze_answer")
def analyze_answer(transcript_id: int, question_text: str, answer_text: str, rubric: dict = None, question_id: int = None):
    """
    개별 답변 평가 및 점수 반영 (EXAONE-3.5-7.8B-Instruct 사용)
    
    Args:
        transcript_id (int): 트랜스크립트 ID
        question_text (str): 질문 텍스트
        answer_text (str): 답변 텍스트
        rubric (dict, optional): 평가 기준. Defaults to None.
        question_id (int, optional): 질문 ID. Defaults to None.
    
    Returns:
        dict: 평가 결과
    
    Raises:
        ValueError: 답변이 없는 경우
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    logger.info(f"Analyzing Transcript {transcript_id} for Question {question_id}")
    
    # 예외 처리: 답변이 없는 경우 LLM 호출 생략
    if not answer_text or not answer_text.strip():
        logger.warning(f"Empty answer for transcript {transcript_id}. Skipping LLM evaluation.")
        return {
            "technical_score": 0,
            "communication_score": 0,
            "feedback": "답변이 제공되지 않았습니다."
        }
    
    start_ts = time.time()
    
    try:
        # EXAONE LLM으로 평가
        llm = get_exaone_llm()
        result = llm.evaluate_answer(
            question_text=question_text,
            answer_text=answer_text,
            rubric=rubric
        )
        
        tech_score = result.get("technical_score")
        if tech_score is None:
             tech_score = 3
             
        comm_score = result.get("communication_score")
        if comm_score is None:
             comm_score = 3
        
        # 감정/종합 점수 계산 (-1.0 ~ 1.0)
        # (5점 만점 -> -0.5 ~ 0.5 범위로 정규화 + 보정)
        sentiment = ((tech_score + comm_score) / 10.0) - 0.5 
        
        # DB 업데이트 (Transcript)
        update_transcript_sentiment(
            transcript_id, 
            sentiment_score=sentiment, 
            emotion="neutral"  # 감정 분석은 별도 모델 필요하나 일단 점수로 대체
        )
        
        # 질문 평점 업데이트 (선순환 구조)
        # 답변 점수 (0-100)
        answer_quality = (tech_score + comm_score) * 10 
        
        if question_id:
            update_question_avg_score(question_id, answer_quality)
            logger.info(f"Updated Question {question_id} Avg Score with {answer_quality}")

        duration = time.time() - start_ts
        logger.info(f"Evaluation Completed ({duration:.2f}s)")
        
        return result

    except Exception as e:
        logger.error(f"Evaluation Failed: {e}")
        return {"error": str(e)}

@shared_task(name="tasks.evaluator.generate_final_report")
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
    
    # 1. Get all answers
    answers = get_user_answers(interview_id)
    if not answers:
        logger.warning("No answers found for this interview. Generating empty report.")
        # 빈 리포트 생성 (404 방지)
        from db import create_or_update_evaluation_report, update_interview_overall_score
        create_or_update_evaluation_report(
            interview_id,
            technical_score=0,
            communication_score=0,
            cultural_fit_score=0,
            summary_text="면접 데이터가 충분하지 않아 평가를 생성할 수 없습니다. (음성 인식 실패 또는 답변 누락)",
            details_json={"strengths": [], "weaknesses": ["No input detected"]}
        )
        update_interview_overall_score(interview_id, 0)
        return
    
    # 2. Calculate aggregations
    # 실제로는 모든 transcript의 점수를 평균내야 하지만,
    # 여기서는 간단한 Mock 로직 사용
    
    tech_score = 85.0
    comm_score = 88.0
    cult_score = 90.0
    overall_score = (tech_score + comm_score + cult_score) / 3
    
    summary = (
        "지원자는 강력한 기술적 지식과 우수한 의사소통 능력을 보여주었습니다. "
        "직무에 대한 열정이 있으며 회사 문화에 잘 맞을 것으로 판단됩니다."
    )
    
    # 3. Save to DB
    from db import create_or_update_evaluation_report, update_interview_overall_score
    
    create_or_update_evaluation_report(
        interview_id,
        technical_score=tech_score,
        communication_score=comm_score,
        cultural_fit_score=cult_score,
        summary_text=summary,
        details_json={
            "strengths": ["명확한 의사 표현", "관련 경험 풍부"],
            "weaknesses": ["일부 질문에서 더 구체적인 예시 필요"]
        }
    )
    
    update_interview_overall_score(interview_id, overall_score)
    logger.info(f"Final Report Generated for Interview {interview_id}")