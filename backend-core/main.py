from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from celery import Celery
from datetime import datetime, timedelta
from typing import List
import logging
import os
import shutil
import time
from pathlib import Path

# DB 설정
from database import init_db, get_session
# DB 테이블 모듈 임포트
from db_models import (
    User, UserCreate, UserLogin, Company,
    Interview, InterviewCreate, InterviewResponse, InterviewStatus,
    Question, QuestionCategory, QuestionDifficulty,
    Transcript, TranscriptCreate, Speaker,
    EvaluationReport, EvaluationReportResponse,
    Resume
)
# Imports cleaned up


# 로깅 설정
LOG_DIR = Path("./uploads/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 1. 포맷터 설정
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# 2. 핸들러 설정
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

file_handler = logging.FileHandler(LOG_DIR / "backend.log", encoding='utf-8')
file_handler.setFormatter(log_formatter)

# 3. 로거 설정
logger = logging.getLogger("Backend-Core")
logger.setLevel(logging.INFO)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)

# FastAPI 및 uvicorn 로거에도 추가
logging.getLogger("uvicorn.access").addHandler(file_handler)
logging.getLogger("uvicorn.error").addHandler(file_handler)

app = FastAPI(title="AI Interview Backend v2.0")

# 상세 로깅 미들웨어 (Request/Response Body 및 Latency 기록)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 1. 요청 정보 추출
    method = request.method
    url = str(request.url)
    client_ip = request.client.host if request.client else "unknown"
    
    # 2. 요청 바디 추출 (스트림 소비 주의)
    request_body = b""
    if method in ["POST", "PUT", "PATCH"]:
        request_body = await request.body()
        # 스트림을 다시 채워줘야 다음 핸들러가 읽을 수 있음
        async def receive():
            return {"type": "http.request", "body": request_body}
        request.scope["receive"] = receive

    # 요청 로그 기록 (민감정보 보안 유의)
    body_str = request_body.decode("utf-8", errors="ignore") if request_body else "None"
    if len(body_str) > 500: body_str = body_str[:500] + "... (truncated)"
    logger.info(f"▶️ [REQ] {method} {url} | IP: {client_ip} | Body: {body_str}")

    # 3. 실제 요청 처리
    response = await call_next(request)
    
    # 4. 응답 시간 및 상태 기록
    process_time = time.time() - start_time
    logger.info(f"◀️ [RES] {method} {url} | Status: {response.status_code} | Duration: {process_time:.3f}s")
    
    # 응답 헤더에 요청 처리 시간 추가 (디버깅용)
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

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
    logger.info("✅ Database initialized & Logging Middleware active")

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

# Celery 설정 (중앙화된 설정 로드)
from celery_app import celery_app

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

# TTS 오디오 파일 디렉토리 (ai-worker와 공유 볼륨)
TTS_DIR = Path("./uploads/tts")
TTS_DIR.mkdir(parents=True, exist_ok=True)

# [추가] /uploads/tts 정적 파일 서빙 (프론트엔드에서 audio_url로 직접 접근)
app.mount("/uploads/tts", StaticFiles(directory=str(TTS_DIR)), name="tts_audio")

@app.post("/resumes/upload", tags=["resumes"])
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
            detail="지원하지 않는 파일 형식입니다. PDF, DOC, DOCX 파일만 업로드 가능합니다."
        )

    try:
        # 파일 저장 경로 생성 (날짜 + 사용자ID + 파일명)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{current_user.id}_{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename

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
            args=[new_resume.id, str(file_path)],
            queue='gpu_queue'
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
@app.get("/resumes/{resume_id}", tags=["resumes"])
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
    # 모든 기술 스택 통합
    all_skills = []

    # [수정: 2026-02-10] structured_data 타입 처리 로직 개선
    # 이유: PostgreSQL DB에서 JSONB 컬럼이 간혹 문자열(String) 형태로 반환되는 이슈 발생
    #       (AttributeError: 'str' object has no attribute 'get' 에러 유발).
    # 해결: 데이터 타입이 문자열인 경우 json.loads()로 명시적 파싱을 수행하여
    #       항상 딕셔너리(Dict) 형태로 처리하도록 안전 장치(Fail-safe) 추가.
    import json
    parsed_data = {}

    try:
        if resume.structured_data:
            temp_data = resume.structured_data
            # 문자열인 경우 파싱 (이중 인코딩 대응)
            if isinstance(temp_data, str):
                try:
                    temp_data = json.loads(temp_data)
                    # 한 번 더 파싱했는데도 문자열이면 또 파싱 시도 (이중 인코딩)
                    if isinstance(temp_data, str):
                        temp_data = json.loads(temp_data)
                except Exception as parse_error:
                    print(f"JSON parse error: {parse_error}")

            # 최종 결과가 딕셔너리인지 확인
            if isinstance(temp_data, dict):
                parsed_data = temp_data
            else:
                print(f"Warning: structured_data is not a dict after parsing: {type(temp_data)}")
    except Exception as e:
        print(f"Error processing structured_data: {e}")
        parsed_data = {}

    # 모든 기술 스택 통합
    all_skills = []
    if "skills" in parsed_data:
        skills_data = parsed_data["skills"]
        if isinstance(skills_data, dict):
            for cat, skills_list in skills_data.items():
                if isinstance(skills_list, list):
                    all_skills.extend(skills_list)

    # [수정: 2026-02-10] target_position 타입 안전 처리
    # 이유: target_position이 문자열("Unknown")일 수도 있고 딕셔너리일 수도 있음.
    #       문자열인데 .get()을 호출하면 AttributeError 발생.
    target_pos_data = parsed_data.get("target_position")
    position_value = None
    if isinstance(target_pos_data, dict):
        position_value = target_pos_data.get("position")
    elif isinstance(target_pos_data, str):
        position_value = target_pos_data

    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "processing_status": resume.processing_status,
        "processed_at": resume.processed_at,
        "structured_data": parsed_data,
        "position": position_value,
        "skills": list(set(all_skills))  # 중복 제거
    }

from fastapi.responses import FileResponse

@app.get("/api/resumes/{resume_id}/pdf", tags=["resumes"])
async def get_resume_pdf(
    resume_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """이력서 실제 PDF 파일 다운로드 및 조회"""
    resume = db.get(Resume, resume_id)

    if not resume or not resume.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이력서를 찾을 수 없습니다."
        )

    # 권한 확인 (본인 또는 관리자만)
    if resume.candidate_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다."
        )

    if not os.path.exists(resume.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="이력서 파일을 서버에서 찾을 수 없습니다."
        )

    return FileResponse(
        path=resume.file_path,
        filename=resume.file_name,
        media_type="application/pdf"
    )

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