from sqlmodel import SQLModel, create_engine, Session, Field, select
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import os
import logging
import sys

# Configure logging
logger = logging.getLogger("AI-Worker-DB")

# Database Connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
engine = create_engine(DATABASE_URL)

# backend-core 경로 추가 (db_models 임포트를 위함)
# 이 부분을 함수화하거나 더 상단에서 처리하여 순환 참조 방지
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend-core"))
if backend_path not in sys.path:
    sys.path.append(backend_path)

# -----------------------------------------------------------
# Helper Functions (순환 참조 방지를 위해 모델 임포트 전에 정의)
# -----------------------------------------------------------

def update_transcript_sentiment(transcript_id: int, sentiment_score: float, emotion: str):
    """면접 답변의 감성 분석 결과 업데이트"""
    with Session(engine) as session:
        # Transcript 모델은 함수 내에서 지연 임포트 (순환 참조 방지)
        from db_models import Transcript
        transcript = session.get(Transcript, transcript_id)
        if transcript:
            transcript.sentiment_score = sentiment_score
            transcript.emotion = emotion
            session.add(transcript)
            session.commit()

def update_question_avg_score(question_id: int, new_score: float):
    """질문 평균 점수 업데이트"""
    with Session(engine) as session:
        from db_models import Question
        question = session.get(Question, question_id)
        if question:
            if question.avg_score is None:
                question.avg_score = new_score
            else:
                question.avg_score = (question.avg_score * 0.9) + (new_score * 0.1)
            session.add(question)
            session.commit()

def get_interview_transcripts(interview_id: int):
    with Session(engine) as session:
        from db_models import Transcript
        stmt = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.order)
        return session.exec(stmt).all()

def get_user_answers(interview_id: int):
    with Session(engine) as session:
        from db_models import Transcript, Speaker
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id,
            Transcript.speaker == Speaker.USER
        ).order_by(Transcript.order)
        return session.exec(stmt).all()

def create_or_update_evaluation_report(interview_id: int, **kwargs):
    with Session(engine) as session:
        from db_models import EvaluationReport
        stmt = select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
        report = session.exec(stmt).first()
        if not report:
            report = EvaluationReport(interview_id=interview_id)
        for key, value in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, value)
        session.add(report)
        session.commit()
        return report

def update_interview_overall_score(interview_id: int, score: float):
    with Session(engine) as session:
        from db_models import Interview
        interview = session.get(Interview, interview_id)
        if interview:
            interview.overall_score = score
            session.add(interview)
            session.commit()

def save_generated_question(interview_id: int, content: str, category: str, stage: str, guide: str = None, session: Session = None):
    from db_models import Question, Transcript, QuestionDifficulty, Speaker
    if session is None:
        with Session(engine) as new_session:
            return _save_generated_question_logic(new_session, interview_id, content, category, stage, guide)
    else:
        return _save_generated_question_logic(session, interview_id, content, category, stage, guide)

def _save_generated_question_logic(session, interview_id, content, category, stage, guide):
    from db_models import Question, Transcript, QuestionDifficulty, Speaker
    # 임베딩 생성을 위한 유틸리티 지연 임포트
    try:
        from utils.vector_utils import generate_question_embedding
        embedding = generate_question_embedding(content)
    except Exception as e:
        logger.error(f"⚠️ Failed to generate embedding for saved question: {e}")
        embedding = None

    question = Question(
        content=content,
        category=category,
        difficulty=QuestionDifficulty.MEDIUM,
        question_type=stage,
        rubric_json={"guide": guide},
        embedding=embedding,
        is_active=True
    )
    session.add(question)
    session.flush()
    
    stmt = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.order.desc())
    last_transcript = session.exec(stmt).first()
    next_order = (last_transcript.order + 1) if last_transcript and last_transcript.order is not None else 1

    new_transcript = Transcript(
        interview_id=interview_id,
        speaker=Speaker.AI,
        text=content,
        question_id=question.id,
        order=next_order,
        timestamp=datetime.utcnow()
    )
    session.add(new_transcript)
    session.commit()
    logger.info(f"✅ [DB_SAVE] Question & Transcript saved.")
    return question.id

# -----------------------------------------------------------
# 모델 임포트 (하단 배치로 순환 참조 완전 차단)
# -----------------------------------------------------------
try:
    from db_models import (
        User, UserRole, InterviewStatus, QuestionCategory, QuestionDifficulty, Speaker,
        Company, Resume, Interview, Question, Transcript, EvaluationReport, AnswerBank
    )
except ImportError as e:
    logger.error(f"❌ Failed to import models: {e}")