
import os
import sys
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

def debug_full():
    with Session(engine) as session:
        # 가장 최근 인터뷰 1개
        stmt_i = select(Interview).order_by(desc(Interview.id)).limit(1)
        i = session.exec(stmt_i).first()
        if not i:
            print("No interview found.")
            return

        print(f"--- Interview ID: {i.id} (Status: {i.status}) ---")
        
        # 모든 트랜스크립트 가져오기 (시간순)
        stmt_t = select(Transcript).where(Transcript.interview_id == i.id).order_by(Transcript.id)
        ts = session.exec(stmt_t).all()
        
        for t in ts:
            q_info = ""
            if t.question_id:
                q = session.get(Question, t.question_id)
                if q:
                    q_info = f"[Stage: {q.question_type}, Order: {t.order}]"
            
            speaker_label = "AI  " if t.speaker == Speaker.AI else "USER"
            text_preview = t.text[:100].replace("\n", " ") if t.text else "EMPTY"
            print(f"{t.id} | {speaker_label} | {q_info} | {text_preview}")

        # 사용 중인 시나리오 확인
        from utils.interview_helpers import check_if_transition
        major = ""
        if i.resume and i.resume.structured_data:
            sd = i.resume.structured_data
            if isinstance(sd, str): sd = json.loads(sd)
            edu = sd.get("education", [])
            major = next((e.get("major", "") for e in edu if e.get("major", "").strip()), "")
        
        is_transition = check_if_transition(major, i.position)
        print(f"\nScenario: {'TRANSITION' if is_transition else 'STANDARD'}")

if __name__ == "__main__":
    debug_full()
