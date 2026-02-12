from sqlmodel import Session, create_engine, select
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
from db_models import ResumeChunk, Resume
import os

DATABASE_URL = "postgresql://interview_user:interview_password@interview_postgres:15432/interview_db"
<<<<<<< HEAD
=======
from models import ResumeChunk, Resume
import os

DATABASE_URL = "postgresql://interview_user:interview_password@interview_postgres:5432/interview_db"
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
engine = create_engine(DATABASE_URL)

def save_chunks_to_file():
    with Session(engine) as session:
        statement = select(ResumeChunk, Resume).join(Resume).order_by(ResumeChunk.id.desc()).limit(20)
        results = session.exec(statement).all()
        
        with open("chunk_verification.txt", "w", encoding="utf-8") as f:
            if not results:
                f.write("No chunks found.")
                return

            f.write(f"{'File Name':<25} | {'Idx':<3} | {'Type':<15} | {'Content Preview'}\n")
            f.write("-" * 100 + "\n")
            for chunk, resume in results:
                section = chunk.section_type if chunk.section_type else "None"
                preview = chunk.content[:60].replace('\n', ' ')
                f.write(f"{resume.file_name[:25]:<25} | {chunk.chunk_index:<3} | {section:<15} | {preview}...\n")

if __name__ == "__main__":
    save_chunks_to_file()
