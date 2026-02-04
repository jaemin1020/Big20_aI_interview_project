
from sqlmodel import SQLModel, create_engine, Session, select
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
import sys
from pathlib import Path

# ==========================================
# Path Setup for Shared Models
# ==========================================
# Try to find backend-core to import central models
current_dir = Path(__file__).parent.resolve()

# 1. Docker Path (/backend-core)
backend_core_docker = Path("/backend-core")
# 2. Local Path relative to this file (../backend-core)
backend_core_local = current_dir.parent / "backend-core"

if backend_core_docker.exists():
    sys.path.append(str(backend_core_docker))
elif backend_core_local.exists():
    sys.path.append(str(backend_core_local))
else:
    print("Warning: backend-core not found. Model imports may fail.")

try:
    # Centralized Model Imports
    from models import (
        UserRole, InterviewStatus, QuestionCategory, QuestionDifficulty, Speaker,
        User, Resume, Interview, Question, Transcript, EvaluationReport, AnswerBank, Company
    )
except ImportError as e:
    print(f"Error importing models from backend-core: {e}")
    # Fallback or Exit? For now let it crash to be visible.
    raise e

# ==========================================
# Database Connection
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@db:5432/interview_db")
engine = create_engine(DATABASE_URL)


# ==========================================
# Helper Functions
# ==========================================

def get_best_questions_by_position(position: str, limit: int = 10):
    with Session(engine) as session:
        stmt = select(Question).where(
            Question.position == position,
            Question.avg_score >= 3.0,
            Question.usage_count < 100
        ).order_by(Question.avg_score.desc()).limit(limit)
        return session.exec(stmt).all()

def increment_question_usage(question_id: int):
    with Session(engine) as session:
        question = session.get(Question, question_id)
        if question:
            question.usage_count += 1
            session.add(question)
            session.commit()

def update_question_avg_score(question_id: int, new_score: float):
    with Session(engine) as session:
        question = session.get(Question, question_id)
        if question:
            if question.avg_score is None:
                question.avg_score = new_score
            else:
                weight = min(question.usage_count, 10) / 10
                question.avg_score = question.avg_score * weight + new_score * (1 - weight)
            session.add(question)
            session.commit()

def update_transcript_sentiment(transcript_id: int, sentiment_score: float, emotion: str):
    with Session(engine) as session:
        transcript = session.get(Transcript, transcript_id)
        if transcript:
            transcript.sentiment_score = sentiment_score
            transcript.emotion = emotion
            session.add(transcript)
            session.commit()

def create_or_update_evaluation_report(interview_id: int, **kwargs):
    with Session(engine) as session:
        stmt = select(EvaluationReport).where(EvaluationReport.interview_id == interview_id)
        report = session.exec(stmt).first()
        
        if report:
            for key, value in kwargs.items():
                if hasattr(report, key):
                     setattr(report, key, value)
        else:
            valid_keys = EvaluationReport.__fields__.keys()
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
            report = EvaluationReport(interview_id=interview_id, **filtered_kwargs)
        
        session.add(report)
        session.commit()
        session.refresh(report)
        return report

def get_interview_transcripts(interview_id: int):
    with Session(engine) as session:
        stmt = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.order)
        return session.exec(stmt).all()

def get_user_answers(interview_id: int):
    with Session(engine) as session:
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id,
            Transcript.speaker != Speaker.AI
        )
        return session.exec(stmt).all()

def update_interview_overall_score(interview_id: int, score: float):
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if interview:
            interview.overall_score = score
            session.add(interview)
            session.commit()

# ==================== Company Helper Functions ====================

def create_company(company_id: str, company_name: str, ideal: str = None, description: str = None, embedding: List[float] = None):
    """회사 정보 생성"""
    with Session(engine) as session:
        company = Company(
            id=company_id,
            company_name=company_name,
            ideal=ideal,
            description=description,
            embedding=embedding
        )
        session.add(company)
        session.commit()
        session.refresh(company)
        return company

def get_company_by_id(company_id: str):
    """회사 ID로 조회"""
    with Session(engine) as session:
        return session.get(Company, company_id)

def update_company_embedding(company_id: str, embedding: List[float]):
    """회사 특성 벡터 업데이트"""
    with Session(engine) as session:
        company = session.get(Company, company_id)
        if company:
            company.embedding = embedding
            company.updated_at = datetime.utcnow()
            session.add(company)
            session.commit()

def find_similar_companies(embedding: List[float], limit: int = 5):
    """벡터 유사도 기반 유사 회사 검색"""
    with Session(engine) as session:
        stmt = select(Company).where(
            Company.embedding.isnot(None)
        ).order_by(
            Company.embedding.cosine_distance(embedding)
        ).limit(limit)
        
        return session.exec(stmt).all()
