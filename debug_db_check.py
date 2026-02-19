from sqlmodel import Session, create_engine, select
import os
import sys

# 프로젝트 경로 추가
sys.path.append(os.getcwd())

os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:1234@localhost:15432/interview_db"

from ai_worker.db import engine
from db_models import Interview, Transcript, EvaluationReport

def check_latest_interview():
    with Session(engine) as session:
        # 1. 최근 인터뷰 확인
        interview = session.exec(select(Interview).order_by(Interview.id.desc())).first()
        if not interview:
            print("No interviews found.")
            return

        print(f"--- Latest Interview (ID: {interview.id}) ---")
        print(f"Position: {interview.position}")
        print(f"Status: {interview.status}")
        print(f"Score: {interview.overall_score}")

        # 2. 대화 기록 개수 확인
        transcripts = session.exec(select(Transcript).where(Transcript.interview_id == interview.id)).all()
        print(f"Transcripts Count: {len(transcripts)}")
        for t in transcripts:
            print(f"[{t.speaker}] {t.text[:30]}...")

        # 3. 리포트 존재 여부 및 내용 확인
        report = session.exec(select(EvaluationReport).where(EvaluationReport.interview_id == interview.id)).first()
        if report:
            print("--- Evaluation Report Found ---")
            print(f"Summary: {report.summary_text[:50]}...")
            print(f"Details JSON present: {report.details_json is not None}")
        else:
            print("--- No Evaluation Report Found ---")

if __name__ == "__main__":
    check_latest_interview()
