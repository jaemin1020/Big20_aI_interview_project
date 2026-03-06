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
    """설명:
        DB에서 가장 최근 면접 세션을 조회하여 최종 리포트 생성 태스크를 수동으로 실행.
        큐를 우회하여 직접 함수를 호출하므로, 개발/테스트 목적으로 사용.

    Returns:
        None

    생성자: ejm
    생성일자: 2026-02-04
    """
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
