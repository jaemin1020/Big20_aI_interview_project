from fastapi import APIRouter, Depends
from sqlmodel import Session
from celery import Celery
import logging

from database import get_session
from models import User, Transcript, TranscriptCreate, Speaker, Question
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/transcripts", tags=["transcripts"])
logger = logging.getLogger("Transcript-Router")

celery_app = Celery("ai_worker", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

# 대화 기록 저장
@router.post("")
async def create_transcript(
    transcript_data: TranscriptCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """실시간 대화 기록 저장 (STT 결과)"""
    
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
        # 해당 질문 조회
        question = db.get(Question, transcript.question_id)
        if question:
            celery_app.send_task(
                "tasks.evaluator.analyze_answer",
                args=[
                    transcript.id,
                    question.content,
                    transcript.text,
                    question.rubric_json,
                    question.id
                ]
            )
            logger.info(f"Evaluation task sent for transcript {transcript.id}")
    
    return {"id": transcript.id, "status": "saved"}
