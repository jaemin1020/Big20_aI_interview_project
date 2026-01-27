from sqlmodel import SQLModel, create_engine, Session, Field, JSON, Column, select
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict, Any
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@db:5432/interview_db")
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
    
    # 계층적 분류
    company: Optional[str] = None
    industry: Optional[str] = None
    position: Optional[str] = None
    
    usage_count: int = Field(default=0)
    avg_score: Optional[float] = None  # 평균 평가 점수

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

# ==================== Question Management Functions ====================

def get_questions_hierarchical(
    position: str, 
    company: str = None, 
    industry: str = None, 
    limit: int = 10
):
    """
    계층적 질문 탐색 (회사 → 산업 → 직무 순)
    
    Args:
        position: 직무명 (필수)
        company: 회사명 (선택)
        industry: 산업명 (선택)
        limit: 최대 조회 개수
    
    Returns:
        list[Question]: 조회된 질문 리스트
    """
    with Session(engine) as session:
        questions = []
        
        # 1단계: 회사 + 산업 + 직무 (가장 구체적)
        if company and industry:
            stmt = select(Question).where(
                Question.company == company,
                Question.industry == industry,
                Question.position == position,
                Question.avg_score.isnot(None),
                Question.is_active == True
            ).order_by(Question.avg_score.desc()).limit(limit)
            
            questions = list(session.exec(stmt).all())
            if questions:
                return questions
        
        # 2단계: 산업 + 직무
        if industry and not questions:
            stmt = select(Question).where(
                Question.industry == industry,
                Question.position == position,
                Question.avg_score.isnot(None),
                Question.is_active == True
            ).order_by(Question.avg_score.desc()).limit(limit)
            
            questions = list(session.exec(stmt).all())
            if questions:
                return questions
        
        # 3단계: 직무만 (가장 일반적)
        if not questions:
            stmt = select(Question).where(
                Question.position == position,
                Question.avg_score.isnot(None),
                Question.is_active == True
            ).order_by(Question.avg_score.desc()).limit(limit)
            
            questions = list(session.exec(stmt).all())
        
        return questions

def get_best_questions_by_position(position: str, limit: int = 10):
    """
    특정 직무의 '우수 질문' 조회 (재활용 후보)
    - 조건: avg_score가 높고, usage_count가 적절한 질문 (너무 많이 쓰인 건 제외)
    """
    with Session(engine) as session:
        # 1. 평균 점수 높은 순 정렬
        # 2. 사용 횟수가 100회 미만인 것만 (너무 흔한 질문 방지)
        stmt = select(Question).where(
            Question.position == position,
            Question.avg_score >= 3.0,  # 5점 만점 기준 3점 이상
            Question.usage_count < 100
        ).order_by(Question.avg_score.desc()).limit(limit)
        
        return session.exec(stmt).all()

def increment_question_usage(question_id: int):
    """질문 사용 횟수 증가"""
    with Session(engine) as session:
        question = session.get(Question, question_id)
        if question:
            question.usage_count += 1
            session.add(question)
            session.commit()

def update_question_avg_score(question_id: int, new_score: float):
    """질문의 평균 점수 업데이트 (이동 평균)"""
    with Session(engine) as session:
        question = session.get(Question, question_id)
        if question:
            if question.avg_score is None:
                question.avg_score = new_score
            else:
                # 이동 평균 계산 (기존 평균과 새 점수의 가중 평균)
                weight = min(question.usage_count, 10) / 10  # 최대 10회까지 가중치
                question.avg_score = question.avg_score * weight + new_score * (1 - weight)
            
            session.add(question)
            session.commit()