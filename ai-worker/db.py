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
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@db:5432/interview_db")
# db ➔ localhost
# 5432 ➔ 1543 (Main branch uses 15432, but keeping local default 5432)

engine = create_engine(DATABASE_URL)

# Enums & Models (Imported from Backend Core)
import sys
import os

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

# Helper Functions
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
            company.updated_at = datetime.now()
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
            emotion_data["timestamp"] = datetime.now().isoformat()
            current_summary["history"].append(emotion_data)
            
            # 최신 상태 업데이트
            current_summary["latest"] = emotion_data
            
            # SQLModel에서 JSON 필드 변경 감지를 위해 재할당
            interview.emotion_summary = dict(current_summary)
            
            session.add(interview)
            session.commit()

def save_generated_question(interview_id: int, content: str, category: str, stage: str, guide: str = None, session: Session = None):
    """생성된 질문을 Question 및 Transcript 테이블에 저장하여 프론트엔드가 즉시 인식하게 함"""
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
    session.flush() # ID 생성을 위해 즉시 플러시
    
    # 2. Transcript 테이블에 AI 질문으로 저장
    # [수정] AI transcript 기준으로만 다음 order 계산 (User transcript는 order=NULL이라 리셋 버그 발생)
    stmt = select(Transcript).where(
        Transcript.interview_id == interview_id,
        Transcript.speaker == Speaker.AI
    ).order_by(Transcript.order.desc())
    last_ai = session.exec(stmt).first()
    next_order = (last_ai.order + 1) if last_ai and last_ai.order is not None else 1

    new_transcript = Transcript(
        interview_id=interview_id,
        speaker=Speaker.AI,
        text=content,
        question_id=question.id,
        order=next_order,
        timestamp=datetime.now()
    )
    session.add(new_transcript)
    session.commit() # 전체 확정
    
    logger.info(f"✅ [DB_SAVE] Question(id={question.id}) & Transcript(id={new_transcript.id}) saved for Interview {interview_id}")
    return question.id