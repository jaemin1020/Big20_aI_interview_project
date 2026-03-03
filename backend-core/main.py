from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
from pathlib import Path

# DB 설정
from database import init_db
# DB 테이블 모듈 임포트 (초기화용으로 유지)
from db_models import (
    User, Company, Interview, Question, Transcript, EvaluationReport, Resume
)

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

# TTS 오디오 파일 디렉토리 설정 (프론트엔드 직접 접근 허용)
TTS_DIR = Path("./uploads/tts")
TTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/tts", StaticFiles(directory=str(TTS_DIR)), name="tts_audio")

# ==================== Router Imports & Registration ====================
# 각 실무 부서(라우터)들을 임포트합니다.
from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.companies import router as companies_router
from routes.interviews import router as interviews_router
from routes.transcripts import router as transcripts_router
from routes.stt import router as stt_router
from routes.resumes import router as resumes_router # ✨ 이력서 전담 부서 추가!

# 관제탑(app)에 각 부서들을 연결해 줍니다.
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(companies_router)
app.include_router(interviews_router)
app.include_router(transcripts_router)
app.include_router(stt_router)
app.include_router(resumes_router) # ✨ 이력서 부서 연결 완료!

# (기존에 길게 있던 이력서 관련 엔드포인트들은 모두 routes/resumes.py로 이사 갔으므로 삭제되었습니다!)

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