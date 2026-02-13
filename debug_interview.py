import os
import sys
# backend-core 경로 추가
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend-core"))
if backend_path not in sys.path:
    sys.path.append(backend_path)

from sqlmodel import Session, create_engine, select
from db_models import Transcript, Question, Interview

DATABASE_URL = "postgresql+psycopg://admin:1234@localhost:15432/interview_db"
engine = create_engine(DATABASE_URL)

def check_interview(interview_id):
    with Session(engine) as session:
        interview = session.get(Interview, interview_id)
        if not interview:
            print(f"Interview {interview_id} not found.")
            return
        
        print(f"--- Interview {interview_id} Status: {interview.status} ---")

        print("\n[Questions]")
        # Transcript through Join is how the frontend gets questions
        stmt = select(Transcript, Question).join(Question, Transcript.question_id == Question.id).where(
            Transcript.interview_id == interview_id,
        ).order_by(Transcript.id)
        results = session.exec(stmt).all()
        for t, q in results:
            print(f"T_ID:{t.id} | Q_ID:{q.id} | Speaker:{t.speaker} | Text:{t.text}")

        print("\n[All Transcripts]")
        stmt = select(Transcript).where(Transcript.interview_id == interview_id).order_by(Transcript.id)
        results = session.exec(stmt).all()
        for t in results:
            print(f"ID:{t.id} | Speaker:{t.speaker} | Text:{t.text[:50]}")

def check_question_155():
    with Session(engine) as session:
        print("\n[Inspecting Question 155]")
        stmt = select(Transcript).where(Transcript.question_id == 155)
        results = session.exec(stmt).all()
        if not results:
            print("No transcripts found for Question 155.")
            return
        
        print(f"{'ID':<5} | {'Intrv':<6} | {'Speaker':<10} | {'Text'}")
        print("-" * 80)
        for t in results:
            print(f"{t.id:<5} | {t.interview_id:<6} | {t.speaker:<10} | {t.text}")

if __name__ == "__main__":
    check_question_155()
