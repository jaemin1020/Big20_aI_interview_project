import os
import sys
from sqlmodel import Session, select

# Adjust path if needed
sys.path.append(os.getcwd())
os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:1234@localhost:15432/interview_db"

from ai_worker.db import engine
from db_models import Interview, Company, Resume

def check():
    with Session(engine) as session:
        interview = session.exec(select(Interview).order_by(Interview.id.desc())).first()
        if not interview:
            print("No interview found")
            return
        
        company = session.get(Company, interview.company_id) if interview.company_id else None
        resume = session.get(Resume, interview.resume_id) if interview.resume_id else None
        
        print(f"Interview ID: {interview.id}")
        print(f"Interview Position: {interview.position}")
        print(f"Company Name: {company.company_name if company else 'N/A'}")
        
        if resume:
            print(f"Resume ID: {resume.id}")
            print(f"Resume Filename: {resume.file_name}")
            # Try to see if resume has position info in its structured_data
            sd = resume.structured_data or {}
            print(f"Resume Header: {sd.get('header', {})}")
        else:
            print("No resume linked to this interview")

if __name__ == "__main__":
    check()
