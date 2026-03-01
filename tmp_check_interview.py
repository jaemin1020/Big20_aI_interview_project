
import sys
import os

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
from db import engine, Interview, Transcript, Speaker, Question

def check_status():
    with Session(engine) as session:
        # 최근 인터뷰 1개 가져오기
        stmt = select(Interview).order_by(desc(Interview.id)).limit(1)
        interview = session.exec(stmt).first()
        
        if not interview:
            print("No interviews found.")
            return

        print(f"--- Latest Interview (ID: {interview.id}) ---")
        print(f"Status: {interview.status}")
        print(f"Position: {interview.position}")
        print(f"Created At: {interview.created_at}")

        # 해당 인터뷰의 트랜스크립트(질문/답변) 가져오기
        stmt_transcripts = select(Transcript).where(Transcript.interview_id == interview.id).order_by(Transcript.id)
        transcripts = session.exec(stmt_transcripts).all()

        print("\n--- Transcripts ---")
        for t in transcripts:
            speaker_tag = "[AI]" if t.speaker == Speaker.AI else "[User]"
            content_preview = (t.text[:50] + "...") if t.text and len(t.text) > 50 else (t.text or "EMPTY")
            print(f"[{t.id}] {speaker_tag} (Q_ID: {t.question_id}, Order: {t.order}): {content_preview}")

if __name__ == "__main__":
    check_status()
