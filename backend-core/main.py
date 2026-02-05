from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from database import init_db
# 라우터 임포트
from routes.auth import router as auth_router
from routes.companies import router as companies_router
from routes.interviews import router as interviews_router
from routes.transcripts import router as transcripts_router
from routes.resumes import router as resumes_router
from routes.users import router as users_router

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backend-Core")

app = FastAPI(title="AI Interview Backend v2.0")

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

# Health Check
@app.get("/")
async def root():
    return {
        "service": "AI Interview Backend v2.0",
        "status": "running",
        "doc": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)