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

class SectionType(str, Enum):
    """이력서 섹션 타입 (RAG 검색 정확도 향상용)"""
    SKILL_CERT = "skill_cert"  # 기술 스택 + 자격증
    CAREER_PROJECT = "career_project"  # 경력 + 프로젝트
    COVER_LETTER = "cover_letter"  # 자기소개서 (지원동기, 성격, 포부 등)
    TARGET_INFO = "target_info"  # 지원 정보 (희망 회사, 직무 등)
    EDUCATION = "education"  # 학력 사항

class ResumeSectionType(str, Enum):
    """멀티 섹션 임베딩 타입 (구조화된 이력서 섹션)"""
    PROFILE = "profile"  # 프로필 (이름, 연락처, 지원 정보)
    EXPERIENCE = "experience"  # 경력
    PROJECT = "project"  # 프로젝트
    EDUCATION = "education"  # 학력
    SELF_INTRODUCTION = "self_introduction"  # 자기소개서
    CERTIFICATION = "certification"  # 자격증
    LANGUAGE = "language"  # 어학
    SKILL = "skill"  # 기술 스택
    AWARD = "award"  # 수상 경력
    ACTIVITY = "activity"  # 대외활동


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
    resumes: List["Resume"] = Relationship(back_populates="candidate")

class Resume(SQLModel, table=True):
    """이력서 테이블"""
    __tablename__ = "resumes"

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="users.id", index=True)

    # 파일 정보
    file_name: str = Field(description="원본 파일명")
    file_path: str = Field(description="저장 경로 (S3 또는 로컬)")
    file_size: int = Field(description="파일 크기 (bytes)")

    # 추출된 텍스트 (PDF → Text)
    extracted_text: Optional[str] = Field(default=None, description="PDF에서 추출한 전체 텍스트")

    # 구조화된 정보 (JSON)
    structured_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="경력, 학력, 기술스택 등 구조화된 데이터"
    )

    # 메타데이터
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = Field(default=None, description="파싱 완료 시각")
    is_active: bool = Field(default=True)
    processing_status: str = Field(default="pending", description="pending, processing, completed, failed")

    # Relationships
    candidate: User = Relationship(back_populates="resumes")
    interviews: List["Interview"] = Relationship(back_populates="resume")
    chunks: List["ResumeChunk"] = Relationship(back_populates="resume")
    section_embeddings: List["ResumeSectionEmbedding"] = Relationship(back_populates="resume")


class ResumeChunk(SQLModel, table=True):
    """이력서 청크 테이블 (RAG용 - 문맥 기반 검색)"""
    __tablename__ = "resume_chunks"

    id: Optional[int] = Field(default=None, primary_key=True)
    resume_id: int = Field(foreign_key="resumes.id", index=True)

    # 청크 내용
    content: str = Field(description="잘게 쪼개진 이력서 텍스트 조각")
    chunk_index: int = Field(description="청크 순서 (0부터 시작)")

    # 섹션 타입 (Phase 2: RAG 검색 정확도 향상)
    section_type: Optional[str] = Field(
        default=None,
        index=True,
        description="이력서 섹션 분류 (직무/인성 질문 그룹화용)"
    )

    # 벡터 임베딩 (1024차원 - KURE-v1)
    embedding: Any = Field(
        default=None,
        sa_column=Column(Vector(1024)),
        description="청크의 벡터 임베딩 (유사도 검색용)"
    )

    # 메타데이터
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    resume: Resume = Relationship(back_populates="chunks")


class ResumeSectionEmbedding(SQLModel, table=True):
    """이력서 섹션별 임베딩 테이블 (구조화된 멀티 섹션 RAG용)"""
    __tablename__ = "resume_section_embeddings"

    id: Optional[int] = Field(default=None, primary_key=True)
    resume_id: int = Field(foreign_key="resumes.id", index=True)

    # 섹션 정보
    section_type: ResumeSectionType = Field(
        index=True,
        description="섹션 타입 (profile, experience, project 등)"
    )
    section_index: int = Field(
        default=0,
        description="같은 타입 내 순서 (예: 경력 1, 경력 2)"
    )
    section_id: Optional[str] = Field(
        default=None,
        description="섹션 고유 ID (예: exp_1, proj_2)"
    )

    # 섹션 내용
    content: str = Field(description="섹션의 텍스트 내용")

    # 구조화된 데이터 (JSON)
    section_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSONB),
        description="섹션별 메타데이터 (회사명, 기간, 기술스택 등)"
    )

    # 벡터 임베딩 (1024차원 - KURE-v1)
    embedding: Any = Field(
        default=None,
        sa_column=Column(Vector(1024)),
        description="섹션의 벡터 임베딩 (의미 기반 검색용)"
    )

    # 자기소개서 타입 분류 (self_introduction인 경우)
    si_type: Optional[str] = Field(
        default=None,
        description="자기소개서 질문 타입 (지원동기, 협업경험 등)"
    )

    # 메타데이터
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    resume: Resume = Relationship(back_populates="section_embeddings")


class Company(SQLModel, table=True):
    """회사 정보 테이블 (벡터 검색 지원)"""
    __tablename__ = "companies"

    # Primary Key (문자열 - 직접 삽입)
    id: str = Field(primary_key=True, max_length=50, description="회사 고유 ID (예: KAKAO, NAVER)")

    # 기본 정보
    company_name: str = Field(index=True, description="회사명")

    # 회사 특성 (벡터화 대상)
    ideal: Optional[str] = Field(default=None, description="회사가 추구하는 인재상 및 가치관")
    description: Optional[str] = Field(default=None, description="회사 소개 및 비전")

    # 벡터 임베딩 (768차원 - ideal + description 통합 임베딩)
    embedding: Any = Field(
        default=None,
        sa_column=Column(Vector(1024)),
        description="회사 특성 벡터 (유사 회사 검색 및 문화 적합성 평가용)"
    )

    # 시스템 필드
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # Relationships
    interviews: List["Interview"] = Relationship(back_populates="company")


class Interview(SQLModel, table=True):
    """면접 세션 테이블"""
    __tablename__ = "interviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="users.id", index=True)
    company_id: Optional[str] = Field(default=None, foreign_key="companies.id", index=True)
    resume_id: Optional[int] = Field(default=None, foreign_key="resumes.id", index=True)

    # 면접 정보
    position: str = Field(description="지원 직무 (예: Backend Engineer)")
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
    company: Optional[Company] = Relationship(back_populates="interviews")
    resume: Optional[Resume] = Relationship(back_populates="interviews")
    transcripts: List["Transcript"] = Relationship(back_populates="interview")
    evaluation_report: Optional["EvaluationReport"] = Relationship(back_populates="interview")

class Question(SQLModel, table=True):
    """질문 은행 테이블"""
    __tablename__ = "questions"

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    category: QuestionCategory
    difficulty: QuestionDifficulty

    # 질문 유형 및 추가 질문 여부
    question_type: Optional[str] = Field(default=None, description="자기소개, 지원동기, 직무지식, 직무경험, 문제해결, 협업, 책임감, 성장가능성")
    is_follow_up: bool = Field(default=False, description="추가 질문(1-1, 2-1, 3-1) 여부")
    parent_question_id: Optional[int] = Field(default=None, foreign_key="questions.id", description="원 질문 ID (추가 질문인 경우)")

    # 평가 기준 (JSON 형식)
    rubric_json: Dict[str, Any] = Field(sa_column=Column(JSONB))

    # 벡터 임베딩 (768차원 - 질문 유사도 검색용)
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(1024))
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
        sa_column=Column(Vector(1024))
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
    company_id: Optional[str] = None
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