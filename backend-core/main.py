from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery
import logging
import os
from fastapi.staticfiles import StaticFiles

# Ensure uploads directory structure exists
os.makedirs("uploads/audio", exist_ok=True)


from database import init_db
# 라우터 임포트
from routes.auth import router as auth_router
from routes.companies import router as companies_router
from routes.interviews import router as interviews_router
from routes.transcripts import router as transcripts_router
from routes.resumes import router as resumes_router
from routes.users import router as users_router
from routes.stt import router as stt_router

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backend-Core")

app = FastAPI(title="AI Interview Backend v2.0")

# Mount static files
app.mount("/static", StaticFiles(directory="uploads"), name="static")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    import json
    try:
        body = await request.json()
    except:
        body = "Could not parse body"
    logger.error(f"Validation Error: {exc}")
    # logger.error(f"Request Body: {body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}, # Body logging optional
    )


# DB 초기화
@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("✅ Database initialized with new schema")

# CORS 설정
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)       # /auth
app.include_router(companies_router)  # /companies
app.include_router(interviews_router) # /interviews
app.include_router(transcripts_router)# /transcripts
app.include_router(resumes_router)    # /api/resumes
app.include_router(users_router)      # /users
app.include_router(stt_router)        # /stt

# Celery 설정
celery_app = Celery("ai_worker", broker="redis://redis:6379/0", backend="redis://redis:6379/0")

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Interview Backend v2.0"}

# Health Check
@app.get("/health")
def health_check():
    return {"status": "ok"}