
import sys
import os
import json

# ai-worker 경로 추가
ai_worker_path = r"c:\big20\Big20_aI_interview_project\ai-worker"
if ai_worker_path not in sys.path:
    sys.path.insert(0, ai_worker_path)

# backend-core 경로 추가 (db_models 임포트를 위함)
backend_path = r"c:\big20\Big20_aI_interview_project\backend-core"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 로컬에서 실행할 경우 DB 컨테이너 포트 (15432) 접근
os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:1234@localhost:15432/interview_db"

from sqlmodel import Session, select, desc
from db import engine, Question, Transcript, Interview, Speaker

def check_counts():
    with Session(engine) as session:
        # 최근 인터뷰 5개
        stmt = select(Interview).order_by(desc(Interview.id)).limit(5)
        interviews = session.exec(stmt).all()
        
        for inv in interviews:
            # 질문 개수
            stmt_q = select(Question).where(Question.id.in_(
                select(Transcript.question_id).where(Transcript.interview_id == inv.id, Transcript.speaker == Speaker.AI)
            ))
            q_count = len(session.exec(stmt_q).all())
            
            # 마지막 대화
            stmt_last = select(Transcript).where(Transcript.interview_id == inv.id).order_by(desc(Transcript.id))
            last_t = session.exec(stmt_last).first()
            
            print(f"Interview {inv.id}: Status={inv.status}, Q_Count={q_count}")
            if last_t:
                print(f"  Last Transcript: ID={last_t.id}, Speaker={last_t.speaker}, Text[:50]={last_t.text[:50] if last_t.text else 'EMPTY'}")

if __name__ == "__main__":
    check_counts()
