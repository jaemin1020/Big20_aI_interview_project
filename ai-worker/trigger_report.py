import os
import sys
from sqlmodel import Session, select

# Adjust path if needed
sys.path.append("/app")

from main import app
from tasks.evaluator import generate_final_report
from ai_worker.db import engine
from db_models import Interview

def trigger():
    with Session(engine) as session:
        interview = session.exec(select(Interview).order_by(Interview.id.desc())).first()
        if interview:
            print(f"Triggering report for Interview ID: {interview.id}")
            # Run the task function directly to avoid queue issues for this manual trigger
            generate_final_report(interview.id)
            print("Successfully triggered and finished analysis.")
        else:
            print("No interview found.")

if __name__ == "__main__":
    trigger()
