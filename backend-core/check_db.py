from sqlmodel import Session, create_engine, select
from db_models import Transcript
import os

# Use environment variable or a default that works inside the container
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@db:5432/interview_db")
engine = create_engine(DATABASE_URL)

def check_transcripts():
    with Session(engine) as session:
        statement = select(Transcript).order_by(Transcript.id.desc()).limit(10)
        results = session.exec(statement).all()
        
        print(f"{'ID':<5} | {'Interview':<10} | {'Speaker':<10} | {'Text'}")
        print("-" * 80)
        if not results:
            print("No transcripts found.")
            return

        for t in results:
            text_preview = t.text[:50].replace('\n', ' ') if t.text else "None"
            print(f"{t.id:<5} | {t.interview_id:<10} | {t.speaker:<10} | {text_preview}")

if __name__ == "__main__":
    check_transcripts()
