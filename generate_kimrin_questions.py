from sqlmodel import SQLModel, create_engine, Session, Field, select
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import os
import logging

# Configure logging
logger = logging.getLogger("AI-Worker-DB")

# Database Connection
# 환경 변수에 따라 DB 주소를 유연하게 설정 (도커 내부: db:5432 / 로컬: localhost:15432)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")

engine = create_engine(DATABASE_URL)

# Enums & Models (Imported from Backend Core)
import sys

# backend-core 경로 추가 (db_models 임포트를 위함)
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend-core"))
if backend_path not in sys.path:
    sys.path.append(backend_path)

# DB 테이블 모듈 임포트
try:
    from db_models import (
        User, UserRole, InterviewStatus, QuestionCategory, QuestionDifficulty, Speaker,
        Company, Resume, Interview, Question, Transcript, EvaluationReport, AnswerBank
    )
except ImportError as e:
    logger.error(f"❌ Failed to import models from {backend_path}: {e}")
    raise

# -----------------------------------------------------------
# Helper Functions (시스템 운영에 필수적인 함수들)
# -----------------------------------------------------------

def save_generated_question(interview_id: int, content: str, category: str, stage: str, guide: str = None, session: Session = None):
    """생성된 질문을 Question 및 Transcript 테이블에 저장"""
    if session is None:
        with Session(engine) as new_session:
            return _save_generated_question_logic(new_session, interview_id, content, category, stage, guide)
    else:
        return _save_generated_question_logic(session, interview_id, content, category, stage, guide)

def _save_generated_question_logic(session: Session, interview_id: int, content: str, category: str, stage: str, guide: str = None):
    # 1. Question 테이블 저장
    question = Question(
        content=content,
        category=category,
        difficulty=QuestionDifficulty.MEDIUM,
        question_type=stage,
        rubric_json={"guide": guide},
        is_active=True
    )
    session.add(question)
    session.flush() 
    
    # 2. Transcript 테이블에 AI 질문으로 저장
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
    logger.info(f"✅ [DB_SAVE] Question(id={question.id}) & Transcript saved.")
    return question.id

def update_transcript_sentiment(transcript_id: int, sentiment_score: float, emotion: str):
    """면접 답변의 감성(점수) 분석 결과 업데이트"""
    with Session(engine) as session:
        transcript = session.get(Transcript, transcript_id)
        if transcript:
            transcript.sentiment_score = sentiment_score
            transcript.emotion = emotion
            session.add(transcript)
            session.commit()

def update_question_avg_score(question_id: int, new_score: float):
    """질문 데이터베이스의 질문 평균 점수 업데이트 (통계용)"""
    with Session(engine) as session:
        question = session.get(Question, question_id)
        if question:
            if question.avg_score is None:
                question.avg_score = new_score
            else:
                # 간단한 이동 평균 적용 (가중치 0.1)
                question.avg_score = (question.avg_score * 0.9) + (new_score * 0.1)
            session.add(question)
            session.commit()

def get_interview_transcripts(interview_id: int) -> List[Transcript]:
    """특정 면접의 모든 대화 기록 조회"""
    with Session(engine) as session:
        stmt = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.order)
        return session.exec(stmt).all()

def get_user_answers(interview_id: int) -> List[Transcript]:
    """지원자(User)의 답변만 필터링해서 조회"""
    with Session(engine) as session:
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id,
            Transcript.speaker == Speaker.USER
        ).order_by(Transcript.order)
        return session.exec(stmt).all()

def create_or_update_evaluation_report(interview_id: int, **kwargs):
    """면접 완료 후 평가 리포트 생성 또는 수정"""
    with Session(engine) as session:
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
    """면접 세션의 전체 점수 업데이트"""
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if interview:
            interview.overall_score = score
            session.add(interview)
            session.commit()