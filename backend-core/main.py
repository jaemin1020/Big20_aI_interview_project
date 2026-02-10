from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from celery import Celery
from datetime import datetime, timedelta
from typing import List
import logging
import os
import shutil
from pathlib import Path

# DB 설정
from database import init_db, get_session
# DB 테이블 모듈 임포트
from models import (
    User, UserCreate, UserLogin, Company,
    Interview, InterviewCreate, InterviewResponse, InterviewStatus,
    Question, QuestionCategory, QuestionDifficulty,
    Transcript, TranscriptCreate, Speaker,
    EvaluationReport, EvaluationReportResponse,
    Resume
)
# Imports cleaned up


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backend-Core")

app = FastAPI(title="AI Interview Backend v2.0")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    import json
    try:
        body = await request.json()
    except:
        body = "Could not parse body"
    logger.error(f"Validation Error: {exc}")
    logger.error(f"Request Body: {body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": body},
    )

# DB 초기화
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

# Company Router 등록
from routes.companies import router as companies_router
app.include_router(companies_router)

# Celery 설정
celery_app = Celery("ai_worker", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

# Router Imports
from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.interviews import router as interviews_router
from routes.transcripts import router as transcripts_router
from routes.stt import router as stt_router
# from routes.companies import router as companies_router # Already imported below

# Auth Utils for Resume endpoints
from utils.auth_utils import get_current_user

# Router Registration
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(interviews_router)
app.include_router(transcripts_router)
app.include_router(stt_router)
# companies_router is included below (or above in original code)

# ==================== Resume Endpoints ====================

# 업로드 디렉토리 설정
UPLOAD_DIR = Path("./uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """이력서 파일 업로드 (PDF, DOC, DOCX)"""
    
    # 파일 확장자 검증
    allowed_extensions = [".pdf", ".doc", ".docx"]
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # 파일 저장 경로 생성 (candidate_id_timestamp_filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # 파일 저장
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Resume 레코드 생성
        new_resume = Resume(
            candidate_id=current_user.id,
            file_name=file.filename,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            processing_status="pending"
        )
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        
        logger.info(f"Resume uploaded: ID={new_resume.id}, User={current_user.username}, File={file.filename}")
        
        # Celery 태스크로 이력서 파싱 및 구조화 작업 전달
        celery_app.send_task(
            "parse_resume_pdf",
            args=[new_resume.id, str(file_path)]
        )
        logger.info(f"Resume parsing task sent for ID={new_resume.id}")
        
        return {
            "id": new_resume.id,
            "file_name": new_resume.file_name,
            "file_size": new_resume.file_size,
            "status": "uploaded",
            "message": "Resume uploaded successfully. Processing will begin shortly."
        }
        
    except Exception as e:
        logger.error(f"Resume upload failed: {e}")
        # 실패 시 파일 삭제
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail="File upload failed")

# 이력서 조회 (상태 및 분석 결과)
@app.get("/resumes/{resume_id}")
async def get_resume(
    resume_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """이력서 조회 및 파싱 결과 확인"""
    resume = db.get(Resume, resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    # 권한 체크: 본인 또는 관리자만 접근 가능
    if resume.candidate_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this resume")
        
    # 모든 기술 스택 통합
    all_skills = []
    if resume.structured_data and "skills" in resume.structured_data:
        for cat, skills_list in resume.structured_data["skills"].items():
            if isinstance(skills_list, list):
                all_skills.extend(skills_list)
                
    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "processing_status": resume.processing_status,
        "processed_at": resume.processed_at,
        "structured_data": resume.structured_data,
        "position": resume.structured_data.get("target_position") if resume.structured_data else None,
        "skills": list(set(all_skills))  # 중복 제거
    }

# ==================== Health Check ====================

# 서버 상태 확인
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