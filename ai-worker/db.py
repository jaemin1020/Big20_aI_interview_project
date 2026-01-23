from sqlmodel import SQLModel, create_engine, Session, Field, JSON, Column, select
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict, Any
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:1234@db:5432/interview_db")
engine = create_engine(DATABASE_URL)

# ==================== Models (AI-Worker 버전) ====================

class Interview(SQLModel, table=True):
    __tablename__ = "interviews"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int
    position: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    overall_score: Optional[float] = None
    emotion_summary: Optional[Dict[str, Any]] = Field(
        default=None, 
        sa_column=Column(JSONB)
    )

class Question(SQLModel, table=True):
    __tablename__ = "questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    category: str
    difficulty: str
    rubric_json: Dict[str, Any] = Field(sa_column=Column(JSONB))
    position: Optional[str] = None
    usage_count: int = Field(default=0)

class Transcript(SQLModel, table=True):
    __tablename__ = "transcripts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int
    speaker: str  # "AI" or "User"
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
    details_json: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB)
    )
    evaluator_model: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# ==================== DB Helper Functions ====================

def update_transcript_sentiment(transcript_id: int, sentiment_score: float, emotion: str):
    """Transcript에 감정 분석 결과 업데이트"""
    with Session(engine) as session:
        transcript = session.get(Transcript, transcript_id)
        if transcript:
            transcript.sentiment_score = sentiment_score
            transcript.emotion = emotion
            session.add(transcript)
            session.commit()

def update_interview_emotion(interview_id: int, emotion_summary: dict):
    """Interview에 전체 감정 요약 업데이트"""
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if interview:
            interview.emotion_summary = emotion_summary
            session.add(interview)
            session.commit()

def create_or_update_evaluation_report(
    interview_id: int,
    technical_score: float = None,
    communication_score: float = None,
    cultural_fit_score: float = None,
    summary_text: str = None,
    details_json: dict = None,
    evaluator_model: str = None
):
    """평가 리포트 생성 또는 업데이트"""
    with Session(engine) as session:
        # 기존 리포트 확인
        stmt = select(EvaluationReport).where(
            EvaluationReport.interview_id == interview_id
        )
        report = session.exec(stmt).first()
        
        if report:
            # 업데이트
            if technical_score is not None:
                report.technical_score = technical_score
            if communication_score is not None:
                report.communication_score = communication_score
            if cultural_fit_score is not None:
                report.cultural_fit_score = cultural_fit_score
            if summary_text:
                report.summary_text = summary_text
            if details_json:
                report.details_json = details_json
            if evaluator_model:
                report.evaluator_model = evaluator_model
            
            report.updated_at = datetime.utcnow()
        else:
            # 새로 생성
            report = EvaluationReport(
                interview_id=interview_id,
                technical_score=technical_score,
                communication_score=communication_score,
                cultural_fit_score=cultural_fit_score,
                summary_text=summary_text,
                details_json=details_json,
                evaluator_model=evaluator_model
            )
        
        session.add(report)
        session.commit()
        session.refresh(report)
        return report

def get_interview_transcripts(interview_id: int):
    """면접의 모든 대화 기록 조회"""
    with Session(engine) as session:
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id
        ).order_by(Transcript.timestamp)
        return session.exec(stmt).all()

def get_user_answers(interview_id: int):
    """사용자 답변만 조회"""
    with Session(engine) as session:
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id,
            Transcript.speaker == "User"
        ).order_by(Transcript.timestamp)
        return session.exec(stmt).all()

def update_interview_overall_score(interview_id: int, overall_score: float):
    """Interview의 overall_score 업데이트"""
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if interview:
            interview.overall_score = overall_score
            session.add(interview)
            session.commit()