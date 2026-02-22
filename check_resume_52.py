
import os
from sqlmodel import Session, create_url, create_engine, select
from db_models import Resume
from database import engine

def check_resume_status(resume_id: int):
    with Session(engine) as session:
        statement = select(Resume).where(Resume.id == resume_id)
        resume = session.exec(statement).first()
        
        if resume:
            print(f"--- Resume {resume_id} Status ---")
            print(f"ID: {resume.id}")
            print(f"File Name: {resume.file_name}")
            print(f"Status: {resume.processing_status}")
            print(f"Uploaded At: {resume.uploaded_at}")
            print(f"Processed At: {resume.processed_at}")
            print(f"Has Structured Data: {resume.structured_data is not None}")
            if resume.structured_data:
                print(f"Structured Data Keys: {list(resume.structured_data.keys())}")
        else:
            print(f"Resume {resume_id} not found.")

if __name__ == "__main__":
    check_resume_status(52)
