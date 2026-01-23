import logging
import time
import json
from celery import shared_task
from langchain_community.llms import LlamaCpp
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from db import (
    update_transcript_sentiment,
    create_or_update_evaluation_report,
    get_interview_transcripts,
    get_user_answers,
    update_interview_overall_score
)

logger = logging.getLogger("AI-Worker-Evaluator")

# ==================== Output Schema ====================

class SingleAnswerEvaluation(BaseModel):
    """개별 답변 평가 스키마"""
    technical_score: int = Field(description="기술적 정확성 (1-5)")
    communication_score: int = Field(description="의사소통 능력 (1-5)")
    strengths: str = Field(description="강점")
    weaknesses: str = Field(description="개선점")
    feedback: str = Field(description="상세 피드백")

class FinalReportSchema(BaseModel):
    """최종 평가 리포트 스키마"""
    technical_score: float = Field(description="기술 점수 (0-100)")
    communication_score: float = Field(description="소통 점수 (0-100)")
    cultural_fit_score: float = Field(description="문화 적합성 (0-100)")
    overall_score: float = Field(description="종합 점수 (0-100)")
    summary_text: str = Field(description="종합 평가 요약")
    strengths: str = Field(description="전체 강점")
    areas_for_improvement: str = Field(description="개선이 필요한 영역")
    recommendation: str = Field(description="채용 추천 의견")

# ==================== Model Setup ====================

MODEL_PATH = "/app/models/solar-10.7b-instruct-v1.0.Q8_0.gguf"
single_parser = JsonOutputParser(pydantic_object=SingleAnswerEvaluation)
final_parser = JsonOutputParser(pydantic_object=FinalReportSchema)

logger.info(f"Loading Solar-10.7B model: {MODEL_PATH}")

try:
    eval_llm = LlamaCpp(
        model_path=MODEL_PATH,
        n_ctx=4096,
        n_threads=8,
        n_gpu_layers=0,
        temperature=0.1,
        verbose=False
    )
    logger.info("✅ Solar-10.7B model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load Solar model: {e}")
    raise

# ==================== Tasks ====================

@shared_task(name="tasks.evaluator.analyze_answer")
def analyze_answer(transcript_id: int, question: str, user_answer: str, rubric: dict):
    """
    개별 답변 평가 (Transcript 기반)
    """
    logger.info(f"[Transcript {transcript_id}] 답변 평가 시작")
    start_time = time.time()
    
    format_instructions = single_parser.get_format_instructions()
    
    prompt = f"""### System:
당신은 IT 전문 기술 면접관입니다. 아래 질문에 대한 사용자의 답변을 평가하세요.
반드시 JSON 포맷으로만 응답하세요.

### User:
질문: {question}
답변: {user_answer}
평가 기준: {json.dumps(rubric, ensure_ascii=False)}

{format_instructions}

### Assistant:
"""
    
    try:
        raw_output = eval_llm.invoke(prompt)
        parsed_data = single_parser.parse(raw_output)
        
        # 감정 점수 계산 (간단한 휴리스틱)
        sentiment_score = (parsed_data["technical_score"] + parsed_data["communication_score"]) / 10 - 0.5
        
        # DB 업데이트
        update_transcript_sentiment(
            transcript_id=transcript_id,
            sentiment_score=sentiment_score,
            emotion="positive" if sentiment_score > 0 else "negative"
        )
        
        duration = time.time() - start_time
        logger.info(f"[Transcript {transcript_id}] 평가 완료 ({duration:.2f}초)")
        
        return {
            "transcript_id": transcript_id,
            "evaluation": parsed_data,
            "sentiment_score": sentiment_score
        }
        
    except Exception as e:
        logger.error(f"[Transcript {transcript_id}] 평가 실패: {e}")
        return {"error": str(e)}

@shared_task(name="tasks.evaluator.generate_final_report")
def generate_final_report(interview_id: int):
    """
    면접 종료 후 최종 평가 리포트 생성
    """
    logger.info(f"[Interview {interview_id}] 최종 리포트 생성 시작")
    start_time = time.time()
    
    try:
        # 1. 모든 대화 기록 조회
        transcripts = get_interview_transcripts(interview_id)
        user_answers = get_user_answers(interview_id)
        
        if not user_answers:
            logger.warning(f"[Interview {interview_id}] 답변이 없어 리포트 생성 불가")
            return {"error": "No user answers found"}
        
        # 2. 전체 대화 컨텍스트 구성
        conversation_text = "\n".join([
            f"{'면접관' if t.speaker == 'AI' else '지원자'}: {t.text}"
            for t in transcripts
        ])
        
        # 3. 개별 평가 점수 집계
        avg_sentiment = sum([t.sentiment_score or 0 for t in user_answers]) / len(user_answers)
        
        # 4. 최종 리포트 생성 프롬프트
        format_instructions = final_parser.get_format_instructions()
        
        prompt = f"""### System:
당신은 최종 면접 평가 리포트를 작성하는 HR 전문가입니다.
아래 면접 전체 대화를 바탕으로 종합 평가를 작성하세요.

### User:
전체 대화 내용:
{conversation_text}

답변 개수: {len(user_answers)}개
평균 감정 점수: {avg_sentiment:.2f}

{format_instructions}

### Assistant:
"""
        
        raw_output = eval_llm.invoke(prompt)
        parsed_report = final_parser.parse(raw_output)
        
        # 5. DB에 저장
        report = create_or_update_evaluation_report(
            interview_id=interview_id,
            technical_score=parsed_report["technical_score"],
            communication_score=parsed_report["communication_score"],
            cultural_fit_score=parsed_report["cultural_fit_score"],
            summary_text=parsed_report["summary_text"],
            details_json={
                "strengths": parsed_report["strengths"],
                "areas_for_improvement": parsed_report["areas_for_improvement"],
                "recommendation": parsed_report["recommendation"],
                "total_answers": len(user_answers),
                "avg_sentiment": avg_sentiment
            },
            evaluator_model="Solar-10.7B-Q8"
        )
        
        # 6. Interview의 overall_score 업데이트
        update_interview_overall_score(interview_id, parsed_report["overall_score"])
        
        duration = time.time() - start_time
        logger.info(f"[Interview {interview_id}] 최종 리포트 생성 완료 ({duration:.2f}초)")
        
        return {
            "interview_id": interview_id,
            "report_id": report.id,
            "overall_score": parsed_report["overall_score"]
        }
        
    except Exception as e:
        logger.error(f"[Interview {interview_id}] 리포트 생성 실패: {e}", exc_info=True)
        return {"error": str(e)}