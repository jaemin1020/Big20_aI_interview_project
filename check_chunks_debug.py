from sqlmodel import Session, create_engine, select
from models import ResumeChunk, Resume
import os

DATABASE_URL = "postgresql://interview_user:interview_password@localhost:5432/interview_db"
engine = create_engine(DATABASE_URL)

def check_chunks():
    with Session(engine) as session:
        # 최근 10개의 청크 확인
        statement = select(ResumeChunk, Resume).join(Resume).order_by(ResumeChunk.id.desc()).limit(15)
        results = session.exec(statement).all()
        
        if not results:
            print("❌ No chunks found in database.")
            return

        print(f"{'File Name':<20} | {'Idx':<3} | {'Section Type':<15} | {'Content Preview'}")
        print("-" * 80)
        for chunk, resume in results:
            section = chunk.section_type if chunk.section_type else "None"
            preview = chunk.content[:50].replace('\n', ' ')
            print(f"{resume.file_name[:20]:<20} | {chunk.chunk_index:<3} | {section:<15} | {preview}...")

if __name__ == "__main__":
    check_chunks()
