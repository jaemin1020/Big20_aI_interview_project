from fastapi import APIRouter, Depends, HTTPException
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
        logger.info(f"Received transcript request: Interview={transcript_data.interview_id}, Speaker={transcript_data.speaker}, TextLen={len(transcript_data.text)}")
        
        from sqlmodel import select as sqlmodel_select
        
        # [개선] 순서(order) 계산 로직: 해당 인터뷰의 전체 대화 흐름을 고려하여 순서 부여
        # 이전 화자(same speaker)만 찾는 방식에서 전체 인터뷰의 마지막 order를 찾는 방식으로 변경
        stmt_last = sqlmodel_select(Transcript).where(
            Transcript.interview_id == transcript_data.interview_id
        ).order_by(Transcript.id.desc())
        
        last_transcript = db.exec(stmt_last).first()
        
        if last_transcript and last_transcript.order is not None:
            next_order = last_transcript.order + 1
            logger.info(f"Next order calculated: {next_order} (based on last transcript ID {last_transcript.id})")
        else:
            # 첫 번째 발화인 경우 (보통 AI의 Intro가 먼저 저장되므로 이 상태는 드묾)
            next_order = 1
            logger.info("No previous transcript with order found. Setting next_order to 1.")

        # Speaker Enum 처리 보강: 프론트엔드에서 오는 문자열이 Enum과 정확히 매칭되도록 보장
        speaker_value = transcript_data.speaker
        if hasattr(speaker_value, 'value'):
            speaker_value = speaker_value.value
            
        transcript = Transcript(
            interview_id=transcript_data.interview_id,
            speaker=speaker_value,
            text=transcript_data.text,
            question_id=transcript_data.question_id,
            order=next_order,
            timestamp=get_kst_now()
        )
        
        db.add(transcript)
        db.commit()
        db.refresh(transcript)
        
        logger.info(f"✅ Transcript saved successfully: ID={transcript.id}, Interview={transcript.interview_id}, Speaker={transcript.speaker}")
        
        # 사용자 답변인 경우 AI 다음 질문 생성 요청 (비동기)
        # Enum 비교를 str() 기반으로 안전하게 처리 (DB에서 문자열로 반환될 수도 있음)
        if str(transcript.speaker).lower() in ("user", "speaker.user"):
            logger.info(f"User response detected. Triggering next question generation for Interview {transcript.interview_id}")
            question = db.get(Question, transcript.question_id)
            if question:
                # 1. 다음 질문 생성 태스크 즉시 트리거 (실시간성 확보가 최우선)
                try:
                    celery_app.send_task(
                        "tasks.question_generation.generate_next_question",
                        args=[transcript.interview_id],
                        queue="gpu_queue"
                    )
                    logger.info(f"Celery task 'generate_next_question' sent for Interview {transcript.interview_id}")
                except Exception as celery_err:
                    # Celery 태스크 실패는 DB 저장 성공에 영향 주지 않음
                    logger.warning(f"Celery task failed (non-critical): {celery_err}")
            else:
                logger.warning(f"No associated question found for transcript {transcript.id} (question_id={transcript.question_id})")

        return {"id": transcript.id, "status": "saved"}

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to save transcript: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save transcript: {str(e)}")