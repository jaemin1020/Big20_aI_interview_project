from fastapi import APIRouter, Depends
from sqlmodel import Session
from celery import Celery
import logging

from database import get_session
from db_models import User, Transcript, TranscriptCreate, Speaker, Question
from utils.auth_utils import get_current_user
from datetime import datetime, timezone, timedelta

# KST (Korea Standard Time) 설정
KST = timezone(timedelta(hours=9))

def get_kst_now():
    return datetime.now(KST).replace(tzinfo=None)

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
        from sqlmodel import select as sqlmodel_select
        # User 답변의 order: 이전 User 발화 기준으로 다음 순서 계산
        stmt_last = sqlmodel_select(Transcript).where(
            Transcript.interview_id == transcript_data.interview_id,
            Transcript.speaker == transcript_data.speaker
        ).order_by(Transcript.id.desc())
        last_same_speaker = db.exec(stmt_last).first()
        next_order = (last_same_speaker.order + 1) if (last_same_speaker and last_same_speaker.order is not None) else None

        transcript = Transcript(
            interview_id=transcript_data.interview_id,
            speaker=transcript_data.speaker,
            text=transcript_data.text,
            question_id=transcript_data.question_id,
            order=next_order,
            timestamp=get_kst_now()
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

                # 2. 답변 분석 및 평가 요청 (이제 최종 리포트 생성 단계에서 한꺼번에 처리하도록 변경)
                # logger.info(f"Answer analysis deferred to final report: transcript {transcript.id}")
                # celery_app.send_task(
                #     "tasks.evaluator.analyze_answer",
                #     args=[
                #         transcript.id,
                #         question.content,
                #         transcript.text,
                #         question.rubric_json,
                #         question.id,
                #         question.question_type 
                #     ],
                #     queue="gpu_queue",
                #     countdown=5
                # )
                # logger.info(f"Triggered Next Question first, Evaluation will be done in final report.")
    except Exception as e:
        logger.error(f"Failed to save transcript: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save transcript")
    return {"id": transcript.id, "status": "saved"}