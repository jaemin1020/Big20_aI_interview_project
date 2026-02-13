
from sqlmodel import Session, create_engine, select
from ai_worker.models import Transcript
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:15432/interview_db")
engine = create_engine(DATABASE_URL)

def dump_transcripts():
    with Session(engine) as session:
        stmt = select(Transcript).order_by(Transcript.id.desc()).limit(30)
        results = session.exec(stmt).all()
        print(f"{'ID':<5} | {'Intrv':<5} | {'Speaker':<10} | {'Text'}")
        print("-" * 80)
        for t in results:
            print(f"{t.id:<5} | {t.interview_id:<5} | {t.speaker:<10} | {t.text[:50]}")

if __name__ == "__main__":
    dump_transcripts()
