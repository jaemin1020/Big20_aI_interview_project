import logging
import time
import json
from celery import shared_task
from langchain_community.llms import LlamaCpp
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# DB Helper Functions
from db import (
    update_transcript_sentiment,
    update_question_avg_score,  # 질문 평점 업데이트
    get_interview_transcripts,
    get_user_answers
)

logger = logging.getLogger("AI-Worker-Evaluator")

# --- Schemas ---

class SingleAnswerEvaluation(BaseModel):
    # 기술적 정확성 (1-5)
    technical_score: int = Field(description="기술 점수 (1-5)")
    # 의사소통 능력 (1-5)
    communication_score: int = Field(description="소통 점수 (1-5)")
    feedback: str = Field(description="상세 평가 의견")
    
# --- Model Setup ---
# Solar, Mistral 등 가벼운 모델 활용
MODEL_PATH = "/app/models/solar-10.7b-instruct-v1.0.Q8_0.gguf"

try:
    eval_llm = LlamaCpp(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_threads=6, # 적절한 스레드 할당
        n_gpu_layers=0, # CPU 모드
        temperature=0.0, # 일관성 확보
        verbose=False
    )
    logger.info("✅ Evaluator Model Loaded")
except Exception as e:
    logger.error(f"Failed to Load Model: {e}")
    eval_llm = None

@shared_task(name="tasks.evaluator.analyze_answer")
def analyze_answer(transcript_id: int, question_text: str, answer_text: str, rubric: dict = None, question_id: int = None):
    """
    개별 답변 평가 및 점수 반영
    """
    if not eval_llm:
        logger.error("Model unavailable")
        return {"error": "Model not loaded"}

    logger.info(f"Analyzing Transcript {transcript_id} for Question {question_id}")
    
    start_ts = time.time()
    
    # 1. 평가 수행
    prompt = f"""### System:
You are an expert interviewer. Evaluate the candidate's answer based on the question.
Provide the evaluation in JSON format ONLY.

### Question:
{question_text}

### Answer:
{answer_text}

### Rubric (Reference):
Technical accuracy, Logic, Communication skills.

### Output Format (JSON Only):
{{
    "technical_score": (int 1-5),
    "communication_score": (int 1-5),
    "feedback": (string)
}}

### Evaluation:
"""
    try:
        raw_output = eval_llm.invoke(prompt)
        
        # JSON 파싱 (간단한 파서 사용)
        parser = JsonOutputParser(pydantic_object=SingleAnswerEvaluation)
        result = parser.parse(raw_output)
        
        tech_score = result.get("technical_score", 3)
        comm_score = result.get("communication_score", 3)
        
        # 2. 감정/종합 점수 계산 (-1.0 ~ 1.0)
        # (5점 만점 -> -0.5 ~ 0.5 범위로 정규화 + 보정)
        sentiment = ((tech_score + comm_score) / 10.0) - 0.5 
        
        # 3. DB 업데이트 (Transcript)
        update_transcript_sentiment(
            transcript_id, 
            sentiment_score=sentiment, 
            emotion="neutral" # 감정 분석은 별도 모델 필요하나 일단 점수로 대체
        )
        
        # 4. 질문 평점 업데이트 (선순환 구조)
        # 이 질문에 대한 평균 답변 품질이 높다면 -> 좋은 질문일 가능성이 높음 (변별력 있음)
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
    logger.info(f"Generating Final Report for Interview {interview_id}")
    
    # 1. Get all answers
    answers = get_user_answers(interview_id)
    if not answers:
        logger.warning("No answers found for this interview.")
        return
    
    # 2. Calculate aggregations (Mock Logic for now)
    # In a real scenario, we would average the scores from transcripts or re-evaluate the full conversation
    # For now, we generate a positive result to ensure the flow completes.
    
    tech_score = 85.0
    comm_score = 88.0
    cult_score = 90.0
    overall_score = (tech_score + comm_score + cult_score) / 3
    
    summary = (
        "The candidate has demonstrated strong technical knowledge and good communication skills. "
        "They showed enthusiasm for the role and fit well with the company culture."
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
            "strengths": ["Clear articulation", "Relevant experience"],
            "weaknesses": ["Could provide more specific examples in some areas"]
        }
    )
    
    update_interview_overall_score(interview_id, overall_score)
    logger.info(f"Final Report Generated for Interview {interview_id}")