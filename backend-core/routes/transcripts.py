from fastapi import APIRouter, Depends
from sqlmodel import Session
from celery import Celery
import logging

from database import get_session
from db_models import User, Transcript, TranscriptCreate, Speaker, Question
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/transcripts", tags=["transcripts"])
logger = logging.getLogger("Transcript-Router")

from celery_app import celery_app

# 대화 기록 저장
@router.post("")
async def create_transcript(
    transcript_data: TranscriptCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    대화 기록 저장
    실시간 대화 기록 저장 (STT 결과)
    
    Args:
        transcript_data (TranscriptCreate): 대화 기록 데이터
        db (Session): 데이터베이스 세션
        current_user (User): 현재 사용자
        
    Returns:
        dict: 대화 기록 저장 결과
    
    생성자: ejm
    생성일자: 2026-02-06
    """
    try:
        transcript = Transcript(
            interview_id=transcript_data.interview_id,
            speaker=transcript_data.speaker,
            text=transcript_data.text,
            question_id=transcript_data.question_id
        )
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        logger.info(f"Transcript saved: Interview={transcript.interview_id}, Speaker={transcript.speaker}")
        
        # 사용자 답변인 경우 AI 평가 요청 (비동기)
        if transcript.speaker == Speaker.USER:
            question = db.get(Question, transcript.question_id)
            if question:
                # 1. 다음 질문 생성 태스크 즉시 트리거 (실시간성 확보가 최우선)
                celery_app.send_task(
                    "tasks.question_generation.generate_next_question",
                    args=[transcript.interview_id],
                    queue="gpu_queue"
                )

                # 2. 답변 분석 및 평가 요청 (gpu_queue: EXAONE LLM 필요 → GPU 워커 필수)
                # [성능 최적화] 다음 질문 생성을 방해하지 않도록 120초 지연 후 시작 (GPU Solo Pool 블로킹 방지)
                celery_app.send_task(
                    "tasks.evaluator.analyze_answer",
                    args=[
                        transcript.id,
                        question.content,
                        transcript.text,
                        question.rubric_json,
                        question.id,
                        question.question_type  # 9~14번 스테이지(협업/가치관/성장) 판별용
                    ],
                    queue="gpu_queue",
                    countdown=10
                )
                logger.info(f"Triggered Next Question first, then Evaluation for transcript {transcript.id}")
    except Exception as e:
        logger.error(f"Failed to save transcript: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save transcript")
    return {"id": transcript.id, "status": "saved"}