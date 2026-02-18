import json
import os
import sys
from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, create_engine, Session, select

# backend-core 경로 추가 (db_models 임포트를 위함)
root_dir = os.path.abspath(os.path.dirname(__file__))
backend_path = os.path.join(root_dir, "backend-core")
if backend_path not in sys.path:
    sys.path.append(backend_path)

try:
    from db_models import Question
except ImportError:
    print("❌ db_models를 찾을 수 없습니다. 경로 설정을 확인하세요.")
    sys.exit(1)

# 시도해볼 데이터베이스 URL 목록
DB_URLS = [
    os.getenv("DATABASE_URL"),
    "postgresql+psycopg://postgres:1234@localhost:15432/interview_db",
    "postgresql+psycopg://postgres:1234@localhost:5432/interview_db",
    "postgresql+psycopg://admin:1234@localhost:15432/interview_db",
    "postgresql+psycopg://interview_user:interview_password@localhost:15432/interview_db"
]

class DateTimeEnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

def export_questions():
    print("Starting Question table backup...")
    
    engine = None
    connected = False
    
    for url in DB_URLS:
        if not url: continue
        try:
            print(f"Connecting to: {url}")
            engine = create_engine(url, connect_args={"connect_timeout": 5})
            with Session(engine) as session:
                session.exec(select(Question).limit(1))
            connected = True
            print(f"Connected: {url}")
            break
        except Exception:
            continue
            
    if not connected:
        print("Failed to connect to any DB. Check if DB is running.")
        return

    try:
        with Session(engine) as session:
            stmt = select(Question)
            questions = session.exec(stmt).all()
            
            print(f"Total questions retrieved: {len(questions)}")
            
            export_data = []
            for q in questions:
                q_dict = q.model_dump()
                # embedding 필드가 Vector 객체인 경우 리스트로 변환
                if "embedding" in q_dict and q_dict["embedding"] is not None:
                    try:
                        q_dict["embedding"] = [float(x) for x in q_dict["embedding"]]
                    except:
                        q_dict["embedding"] = list(q_dict["embedding"])
                export_data.append(q_dict)
            
            output_file = f"questions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, cls=DateTimeEnumEncoder)
            
            print(f"Backup complete! Filename: {output_file}")
            print(f"Path: {os.path.abspath(output_file)}")
            
    except Exception as e:
        print(f"Error during extraction: {e}")

if __name__ == "__main__":
    export_questions()
