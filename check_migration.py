import os
import sys
from sqlmodel import Session, create_engine, select, text
from dotenv import load_dotenv

# backend-core 경로 추가
sys.path.append(os.path.join(os.getcwd(), "backend-core"))
from models import Resume, ResumeChunk

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
LOCAL_DATABASE_URL = DATABASE_URL.replace("db:5432", "localhost:15432")

engine = create_engine(LOCAL_DATABASE_URL)

with Session(engine) as session:
    resumes = session.exec(select(Resume)).all()
    print(f"Total Resumes: {len(resumes)}")
    for r in resumes:
        chunks = session.exec(select(ResumeChunk).where(ResumeChunk.resume_id == r.id)).all()
        print(f"Resume ID {r.id}: {len(chunks)} chunks")
