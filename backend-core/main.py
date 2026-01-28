from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from celery import Celery
from datetime import datetime, timedelta
from typing import List
import logging
import os

from database import init_db, get_session
from models import (
    User, UserCreate, UserLogin,
    Interview, InterviewCreate, InterviewResponse, InterviewStatus,
    Question, QuestionCategory, QuestionDifficulty,
    Transcript, TranscriptCreate, Speaker,
    EvaluationReport, EvaluationReportResponse
)
from auth import get_password_hash, verify_password, create_access_token, get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backend-Core")

app = FastAPI(title="AI Interview Backend v2.0")

@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("✅ Database initialized with new schema")

# CORS 설정
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Celery 설정
celery_app = Celery("ai_worker", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

# ==================== Auth Endpoints ====================

@app.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_session)):
    # 중복 확인
    stmt = select(User).where(
        (User.username == user_data.username) | (User.email == user_data.email)
    )
    existing_user = db.exec(stmt).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    # 새 사용자 생성
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        role=user_data.role,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.username} ({new_user.role})")
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    stmt = select(User).where(User.username == form_data.username)
    user = db.exec(stmt).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== Interview Endpoints ====================

@app.post("/interviews", response_model=InterviewResponse)
async def create_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """면접 세션 생성 및 질문 생성"""
    
    # 1. Interview 레코드 생성 (상태: SCHEDULED)
    new_interview = Interview(
        candidate_id=current_user.id,
        position=interview_data.position,
        job_posting_id=interview_data.job_posting_id,
        status=InterviewStatus.SCHEDULED,
        scheduled_time=interview_data.scheduled_time,
        start_time=datetime.utcnow()
    )
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)
    
    logger.info(f"Interview created: ID={new_interview.id}, Position={new_interview.position}")
    
    # 2. AI 질문 생성 (AI-Worker에 위임)
    # Backend가 직접 LLM을 돌리지 않으므로, Celery Task를 호출합니다.
    generated_questions = []
    
    try:
        logger.info("Requesting question generation from AI-Worker...")
        # Celery 태스크 호출 (최대 90초 대기 - 모델 로딩 시간 고려)
        task = celery_app.send_task(
            "tasks.question_generator.generate_questions",
            args=[interview_data.position, 5]
        )
        # 동기적으로 결과를 기다림 (UX상 질문이 바로 필요함)
        generated_questions = task.get(timeout=90)
        logger.info(f"Received {len(generated_questions)} questions from AI-Worker")
        
    except Exception as e:
        logger.warning(f"AI-Worker question generation failed ({e}). Using fallback questions.")
        # 실패 시 폴백 질문 생성
        generated_questions = [
            f"{interview_data.position} 직무에 지원하게 된 동기를 구체적으로 말씀해주세요.",
            "가장 도전적이었던 프로젝트 경험과 그 과정에서 얻은 교훈은 무엇인가요?",
            f"{interview_data.position}로서 본인의 가장 큰 강점과 보완하고 싶은 점은 무엇인가요?",
            "갈등 상황을 해결했던 구체적인 사례가 있다면 설명해주세요.",
            "향후 5년 뒤의 커리어 목표는 무엇인가요?"
        ]

    # 3. Questions 및 Transcript 테이블에 저장
    try:
        for i, q_text in enumerate(generated_questions):
            # 3-1. 질문 은행에 저장
            question = Question(
                content=q_text,
                category=QuestionCategory.TECHNICAL if i < 3 else QuestionCategory.BEHAVIORAL,
                difficulty=QuestionDifficulty.MEDIUM,
                rubric_json={
                    "criteria": ["구체성", "직무 적합성", "논리력"], 
                    "weight": {"content": 0.5, "communication": 0.5}
                },
                position=interview_data.position
            )
            db.add(question)
            db.commit()
            db.refresh(question)
            
            # 3-2. Transcript에 AI 발화로 기록
            transcript = Transcript(
                interview_id=new_interview.id,
                speaker=Speaker.AI,
                text=q_text,
                question_id=question.id,
                order=i
            )
            db.add(transcript)
        
        # 면접 상태 업데이트: LIVE
        new_interview.status = InterviewStatus.LIVE
        db.add(new_interview)
        db.commit()
        db.refresh(new_interview)
        
    except Exception as e:
        logger.error(f"Failed to save questions: {e}")
        # 에러 발생 시에도 면접 세션은 반환 (빈 질문 목록일 수 있음)
    
    return InterviewResponse(
        id=new_interview.id,
        candidate_id=new_interview.candidate_id,
        position=new_interview.position,
        status=new_interview.status,
        start_time=new_interview.start_time,
        end_time=new_interview.end_time,
        overall_score=new_interview.overall_score
    )

@app.get("/interviews/{interview_id}/questions")
async def get_interview_questions(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """면접의 질문 목록 조회 (Transcript에서 AI 발화만 필터링)"""
    stmt = select(Transcript).where(
        Transcript.interview_id == interview_id,
        Transcript.speaker == Speaker.AI
    ).order_by(Transcript.order)
    
    transcripts = db.exec(stmt).all()
    
    return [
        {
            "id": t.question_id,
            "content": t.text,
            "order": t.order,
            "timestamp": t.timestamp
        }
        for t in transcripts
    ]

# ==================== Transcript Endpoints ====================

@app.post("/transcripts")
async def create_transcript(
    transcript_data: TranscriptCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """실시간 대화 기록 저장 (STT 결과)"""
    
    transcript = Transcript(
        interview_id=transcript_data.interview_id,
        speaker=transcript_data.speaker,
        text=transcript_data.text,
        question_id=transcript_data.question_id
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    
    logger.info(f"Transcript saved: Interview={transcript.interview_id}, Speaker={transcript.speaker}")
    
    # 사용자 답변인 경우 AI 평가 요청
    if transcript.speaker == Speaker.USER:
        # 해당 질문 조회
        question = db.get(Question, transcript.question_id)
        if question:
            celery_app.send_task(
                "tasks.evaluator.analyze_answer",
                args=[
                    transcript.id,
                    question.content,
                    transcript.text,
                    question.rubric_json,
                    question.id  # 질문 ID 추가 (평균 점수 업데이트용)
                ]
            )
            logger.info(f"Evaluation task sent for transcript {transcript.id}")
    
    return {"id": transcript.id, "status": "saved"}

@app.get("/interviews/{interview_id}/transcripts")
async def get_interview_transcripts(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """면접의 전체 대화 기록 조회"""
    stmt = select(Transcript).where(
        Transcript.interview_id == interview_id
    ).order_by(Transcript.timestamp)
    
    transcripts = db.exec(stmt).all()
    
    return [
        {
            "id": t.id,
            "speaker": t.speaker,
            "text": t.text,
            "timestamp": t.timestamp,
            "sentiment_score": t.sentiment_score,
            "emotion": t.emotion
        }
        for t in transcripts
    ]

# ==================== Evaluation Endpoints ====================

@app.post("/interviews/{interview_id}/complete")
async def complete_interview(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """면접 종료 및 최종 평가 리포트 생성"""
    
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # 면접 종료 처리
    interview.status = InterviewStatus.COMPLETED
    interview.end_time = datetime.utcnow()
    db.add(interview)
    db.commit()
    
    # 평가 리포트 생성 태스크 전달
    celery_app.send_task(
        "tasks.evaluator.generate_final_report",
        args=[interview_id]
    )
    
    logger.info(f"Interview {interview_id} completed. Report generation started.")
    return {"status": "completed", "interview_id": interview_id}

@app.get("/interviews/{interview_id}/report", response_model=EvaluationReportResponse)
async def get_evaluation_report(
    interview_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """평가 리포트 조회"""
    stmt = select(EvaluationReport).where(
        EvaluationReport.interview_id == interview_id
    )
    report = db.exec(stmt).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not yet available")
    
    return report

# ==================== Health Check ====================

@app.get("/")
async def root():
    return {
        "service": "AI Interview Backend v2.0",
        "status": "running",
        "database": "PostgreSQL with pgvector",
        "features": ["real-time STT", "emotion analysis", "AI evaluation"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)