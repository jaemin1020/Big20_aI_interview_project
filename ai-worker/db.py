from sqlmodel import SQLModel, create_engine, Session, Field, select
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import os

# Database Connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@db:5432/interview_db")
engine = create_engine(DATABASE_URL)

# Enums (Matching Backend)
class UserRole(str, Enum):
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"
    ADMIN = "admin"

class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class QuestionCategory(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"
    CULTURAL_FIT = "cultural_fit"

class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Speaker(str, Enum):
    AI = "AI"
    USER = "User"

# Models (Matching Backend)
class Company(SQLModel, table=True):
    """회사 정보 테이블 (벡터 검색 지원)"""
    __tablename__ = "companies"
    
    id: str = Field(primary_key=True, max_length=50)
    company_name: str
    ideal: Optional[str] = None
    description: Optional[str] = None
    embedding: Any = Field(default=None, sa_column=Column(Vector(1024)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Resume(SQLModel, table=True):
    """이력서 테이블"""
    __tablename__ = "resumes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int
    file_name: str
    file_path: str
    file_size: int
    extracted_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    embedding: Any = Field(default=None, sa_column=Column(Vector(1024)))
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
    processing_status: str = Field(default="pending")

class Interview(SQLModel, table=True):
    __tablename__ = "interviews"
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int
    company_id: Optional[str] = None
    resume_id: Optional[int] = None
    position: str
    status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED)
    scheduled_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    overall_score: Optional[float] = None
    emotion_summary: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))

class Question(SQLModel, table=True):
    __tablename__ = "questions"
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    category: QuestionCategory
    difficulty: QuestionDifficulty
    question_type: Optional[str] = None
    is_follow_up: bool = Field(default=False)
    parent_question_id: Optional[int] = None
    rubric_json: Dict[str, Any] = Field(sa_column=Column(JSONB))
    # Using Any for embedding to bypass SQLModel type inference bug with List[float]
    embedding: Any = Field(default=None, sa_column=Column(Vector(1024)))
    company: Optional[str] = None
    industry: Optional[str] = None
    position: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    usage_count: int = Field(default=0)
    avg_score: Optional[float] = None


class Transcript(SQLModel, table=True):
    __tablename__ = "transcripts"
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int
    speaker: Speaker
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sentiment_score: Optional[float] = None
    emotion: Optional[str] = None
    question_id: Optional[int] = None
    order: Optional[int] = None

class EvaluationReport(SQLModel, table=True):
    __tablename__ = "evaluation_reports"
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int
    technical_score: Optional[float] = None
    communication_score: Optional[float] = None
    cultural_fit_score: Optional[float] = None
    summary_text: Optional[str] = None
    details_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluator_model: Optional[str] = None

class AnswerBank(SQLModel, table=True):
    __tablename__ = "answer_bank"
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int
    answer_text: str
    embedding: Any = Field(default=None, sa_column=Column(Vector(1024)))
    score: float
    evaluator_feedback: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    position: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    reference_count: int = Field(default=0)

# Helper Functions
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
