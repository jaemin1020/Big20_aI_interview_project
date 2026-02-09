
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
        UserRole, InterviewStatus, QuestionCategory, QuestionDifficulty, Speaker, ResumeSectionType,
        User, Resume, ResumeChunk, ResumeSectionEmbedding, Interview, Question, Transcript, EvaluationReport, AnswerBank, Company
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
    """
    직무별로 가장 좋은 질문을 가져옴
    
    Args:
        position: 직무
        limit: 가져올 질문 수
        
    Returns:
        List[Question]: 직무별로 가장 좋은 질문
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        stmt = select(Question).where(
            Question.position == position,
            Question.avg_score >= 3.0,
            Question.usage_count < 100
        ).order_by(Question.avg_score.desc()).limit(limit)
        return session.exec(stmt).all()

def increment_question_usage(question_id: int):
    """
    질문 사용 횟수 증가
    
    Args:
        question_id: 질문 ID
        
    Returns:
        None
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        question = session.get(Question, question_id)
        if question:
            question.usage_count += 1
            session.add(question)
            session.commit()

def update_question_avg_score(question_id: int, new_score: float):
    """
    질문 평균 점수 업데이트
    
    Args:
        question_id: 질문 ID
        new_score: 새로운 점수
        
    Returns:
        None
    
    생성자: ejm
    생성일자: 2026-02-04
    """
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
    """
    면접 스크립트 감성 분석 업데이트
    
    Args:
        transcript_id: 면접 스크립트 ID
        sentiment_score: 감성 점수
        emotion: 감정
        
    Returns:
        None
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        transcript = session.get(Transcript, transcript_id)
        if transcript:
            transcript.sentiment_score = sentiment_score
            transcript.emotion = emotion
            session.add(transcript)
            session.commit()

def create_or_update_evaluation_report(interview_id: int, **kwargs):
    """
    면접 평가 보고서 생성 또는 업데이트
    
    Args:
        interview_id: 면접 ID
        **kwargs: 평가 보고서 데이터
        
    Returns:
        EvaluationReport: 평가 보고서
    
    생성자: ejm
    생성일자: 2026-02-04
    """
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
    """
    면접 스크립트 가져오기
    
    Args:
        interview_id: 면접 ID
        
    Returns:
        List[Transcript]: 면접 스크립트
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        stmt = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.order)
        return session.exec(stmt).all()

def get_user_answers(interview_id: int):
    """
    사용자 답변 가져오기
    
    Args:
        interview_id: 면접 ID
        
    Returns:
        List[Transcript]: 사용자 답변
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id,
            Transcript.speaker != Speaker.AI
        )
        return session.exec(stmt).all()

def update_interview_overall_score(interview_id: int, score: float):
    """
    면접 전체 점수 업데이트
    
    Args:
        interview_id: 면접 ID
        score: 전체 점수
        
    Returns:
        None
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if interview:
            interview.overall_score = score
            session.add(interview)
            session.commit()

# ==================== Company Helper Functions ====================

def create_company(company_id: str, company_name: str, ideal: str = None, description: str = None, embedding: List[float] = None):
    """
    회사 정보 생성
    
    Args:
        company_id: 회사 ID
        company_name: 회사 이름
        ideal: 이상적인 인재상
        description: 회사 설명
        embedding: 회사 특성 벡터
        
    Returns:
        Company: 회사 정보
    
    생성자: ejm
    생성일자: 2026-02-04
    """
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
    """
    회사 ID로 조회
    
    Args:
        company_id: 회사 ID
        
    Returns:
        Company: 회사 정보
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        return session.get(Company, company_id)

def update_company_embedding(company_id: str, embedding: List[float]):
    """
    회사 특성 벡터 업데이트
    
    Args:
        company_id: 회사 ID
        embedding: 회사 특성 벡터
        
    Returns:
        None
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        company = session.get(Company, company_id)
        if company:
            company.embedding = embedding
            company.updated_at = datetime.utcnow()
            session.add(company)
            session.commit()

def find_similar_companies(embedding: List[float], limit: int = 5):
    """
    벡터 유사도 기반 유사 회사 검색
    
    Args:
        embedding: 회사 특성 벡터
        limit: 가져올 회사 수
        
    Returns:
        List[Company]: 유사 회사
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        stmt = select(Company).where(
            Company.embedding.isnot(None)
        ).order_by(
            Company.embedding.cosine_distance(embedding)
        ).limit(limit)
        
        return session.exec(stmt).all()

def update_session_emotion(interview_id: int, emotion_data: Dict[str, Any]):
    """
    면접 세션의 감정 분석 결과 업데이트
    
    Args:
        interview_id: 면접 ID
        emotion_data: 감정 분석 데이터
        
    Returns:
        None
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if interview:
            current_summary = interview.emotion_summary or {}
            
            # 이력 관리를 위해 history 리스트에 추가
            if "history" not in current_summary:
                current_summary["history"] = []
            
            # 타임스탬프 추가
            emotion_data["timestamp"] = datetime.utcnow().isoformat()
            current_summary["history"].append(emotion_data)
            
            # 최신 상태 업데이트
            current_summary["latest"] = emotion_data
            
            # SQLModel에서 JSON 필드 변경 감지를 위해 재할당
            interview.emotion_summary = dict(current_summary)
            
            session.add(interview)
            session.commit()
