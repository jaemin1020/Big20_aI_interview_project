from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector  # pgvector 지원
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# ==================== Enums ====================

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

# ==================== Tables ====================

class User(SQLModel, table=True):
    """사용자 테이블 (지원자/채용담당자)"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    role: UserRole = Field(default=UserRole.CANDIDATE)
    password_hash: str
    full_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    interviews: List["Interview"] = Relationship(back_populates="candidate")

class JobPosting(SQLModel, table=True):
    """채용 공고 테이블 (선택적 - 추후 확장용)"""
    __tablename__ = "job_postings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    requirements: str
    position: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    interviews: List["Interview"] = Relationship(back_populates="job_posting")

class Interview(SQLModel, table=True):
    """면접 세션 테이블"""
    __tablename__ = "interviews"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="users.id", index=True)
    job_posting_id: Optional[int] = Field(default=None, foreign_key="job_postings.id")
    
    # 면접 정보
    position: str  # 지원 직무
    status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED)
    
    # 시간 정보
    scheduled_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 전체 점수 (평가 완료 후 업데이트)
    overall_score: Optional[float] = None
    
    # 메타데이터
    emotion_summary: Optional[Dict[str, Any]] = Field(
        default=None, 
        sa_column=Column(JSONB)
    )
    
    # Relationships
    candidate: User = Relationship(back_populates="interviews")
    job_posting: Optional[JobPosting] = Relationship(back_populates="interviews")
    transcripts: List["Transcript"] = Relationship(back_populates="interview")
    evaluation_report: Optional["EvaluationReport"] = Relationship(back_populates="interview")

class Question(SQLModel, table=True):
    """질문 은행 테이블"""
    __tablename__ = "questions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    category: QuestionCategory
    difficulty: QuestionDifficulty
    
    # 평가 기준 (JSON 형식)
    rubric_json: Dict[str, Any] = Field(sa_column=Column(JSONB))
    
    # 벡터 임베딩 (768차원 - 질문 유사도 검색용)
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(768))
    )
    
    # 메타데이터 (계층적 분류)
    company: Optional[str] = Field(default=None, index=True)    # 회사명 (예: "삼성전자", "카카오")
    industry: Optional[str] = Field(default=None, index=True)   # 산업 (예: "IT", "금융", "제조")
    position: Optional[str] = Field(default=None, index=True)   # 직무 (예: "Backend 개발자")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # 통계
    usage_count: int = Field(default=0)
    avg_score: Optional[float] = None

class Transcript(SQLModel, table=True):
    """대화 기록 테이블 (실시간 STT 결과 저장)"""
    __tablename__ = "transcripts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(foreign_key="interviews.id", index=True)
    
    # 대화 정보
    speaker: Speaker
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # 감정 분석 결과
    sentiment_score: Optional[float] = None  # -1.0 ~ 1.0
    emotion: Optional[str] = None  # happy, neutral, sad, angry 등
    
    # 메타데이터
    question_id: Optional[int] = Field(default=None, foreign_key="questions.id")
    order: Optional[int] = None  # 대화 순서
    
    # Relationship
    interview: Interview = Relationship(back_populates="transcripts")

class EvaluationReport(SQLModel, table=True):
    """평가 리포트 테이블"""
    __tablename__ = "evaluation_reports"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    interview_id: int = Field(foreign_key="interviews.id", unique=True, index=True)
    
    # 점수 (0-100 scale)
    technical_score: Optional[float] = None
    communication_score: Optional[float] = None
    cultural_fit_score: Optional[float] = None
    
    # 종합 평가
    summary_text: Optional[str] = None
    
    # 상세 평가 (JSON 형식)
    details_json: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB)
    )
    
    # 메타데이터
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # LLM 평가자 정보
    evaluator_model: Optional[str] = None  # "Solar-10.7B-Q8" 등
    
    # Relationship
    interview: Interview = Relationship(back_populates="evaluation_report")

class AnswerBank(SQLModel, table=True):
    """우수 답변 은행 (벡터 검색용)"""
    __tablename__ = "answer_bank"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="questions.id", index=True)
    
    # 답변 내용
    answer_text: str
    
    # 벡터 임베딩 (768차원 - Question과 동일한 모델 사용)
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(768))
    )
    
    # 평가 점수 및 피드백
    score: float = Field(description="답변 점수 (0-100)")
    evaluator_feedback: Optional[str] = None
    
    # 계층적 분류 (질문과 동일)
    company: Optional[str] = Field(default=None, index=True)
    industry: Optional[str] = Field(default=None, index=True)
    position: Optional[str] = Field(default=None, index=True)
    
    # 메타데이터
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # 통계
    reference_count: int = Field(default=0)  # 참고된 횟수

# ==================== Request/Response Models ====================

class UserCreate(SQLModel):
    """회원가입 요청 모델"""
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.CANDIDATE

class UserLogin(SQLModel):
    """로그인 요청 모델"""
    username: str
    password: str

class InterviewCreate(SQLModel):
    """면접 생성 요청 모델"""
    position: str
    job_posting_id: Optional[int] = None
    scheduled_time: Optional[datetime] = None

class InterviewResponse(SQLModel):
    """면접 응답 모델"""
    id: int
    candidate_id: int
    position: str
    status: InterviewStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    overall_score: Optional[float]

class TranscriptCreate(SQLModel):
    """대화 기록 생성 요청"""
    interview_id: int
    speaker: Speaker
    text: str
    question_id: Optional[int] = None

class EvaluationReportResponse(SQLModel):
    """평가 리포트 응답 모델"""
    id: int
    interview_id: int
    technical_score: Optional[float]
    communication_score: Optional[float]
    cultural_fit_score: Optional[float]
    summary_text: Optional[str]
    details_json: Optional[Dict[str, Any]]
    created_at: datetime