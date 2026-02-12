import os
import sys

# 가장 먼저 로그 파일을 생성하여 시작 확인
LOG_FILE = "populate_log.txt"
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("Script started...\n")

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")
    print(msg)

try:
    log("Loading dependencies...")
    import json
    from sqlmodel import Session, create_engine, select, text
    from dotenv import load_dotenv
    log("Dependencies loaded.")
    
    log("Loading models...")
    # models.py import를 위해 현재 디렉토리를 경로에 추가
    sys.path.append(os.getcwd())
    from db_models import Question
    log("Models loaded.")

    # .env 파일 로드
    load_dotenv()

    # 데이터베이스 연결 설정
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
    if "db:5432" in DATABASE_URL:
        # 도커 외부에서 실행할 경우, docker-compose에 설정된 15432 포트 사용
        LOCAL_DATABASE_URL = DATABASE_URL.replace("db:5432", "localhost:15432")
    else:
        LOCAL_DATABASE_URL = DATABASE_URL
    
    log(f"Using DATABASE_URL: {DATABASE_URL}")
    log(f"Trying LOCAL_DATABASE_URL: {LOCAL_DATABASE_URL}")

    # 스크립트 위치 기준 절대 경로 설정
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    JSON_FILE_PATH = os.path.join(BASE_DIR, "data", "preprocessed_data.json")

    def update_questions():
        # 엔진 생성
        try:
            engine = create_engine(LOCAL_DATABASE_URL)
            
            # 1. pgvector 확장 활성화 시도
            log("Enabling pgvector extension...")
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
            
            # 2. 테이블이 없으면 생성
            log("Ensuring database tables exist...")
            from sqlmodel import SQLModel
            SQLModel.metadata.create_all(engine)
            
            with Session(engine) as session:
                session.execute(text("SELECT 1"))
            log(f"Connected to database at {LOCAL_DATABASE_URL}")
        except Exception as e:
            log(f"Failed to connect to {LOCAL_DATABASE_URL}: {e}")
            log(f"Trying original DATABASE_URL: {DATABASE_URL}")
            try:
                engine = create_engine(DATABASE_URL)
                with Session(engine) as session:
                    session.execute(text("SELECT 1"))
                log(f"Connected to database at {DATABASE_URL}")
            except Exception as e2:
                log(f"Failed to connect to database: {e2}")
                return

        # JSON 데이터 로드
        log(f"Loading JSON data from {JSON_FILE_PATH}...")
        if not os.path.exists(JSON_FILE_PATH):
            log(f"Error: {JSON_FILE_PATH} not found.")
            return
            
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        log(f"Loaded {len(data)} items from JSON.")

        # 업데이트할 데이터 정리
        update_map = {}
        for item in data:
            q_text = item.get("question")
            industry = item.get("industry")
            position = item.get("position")
            
            if q_text and (industry or position):
                update_map[q_text] = {"industry": industry, "position": position}

        log(f"Found {len(update_map)} unique questions with industry/position info.")

        # DB 업데이트
        count = 0
        updated_count = 0
        total_to_check = len(update_map)
        
        with Session(engine) as session:
            for q_text, info in update_map.items():
                count += 1
                if count % 1000 == 0:
                    log(f"Processing... {count}/{total_to_check}")
                
                statement = select(Question).where(Question.content == q_text)
                results = session.exec(statement).all()
                
                if results:
                    for db_q in results:
                        db_q.industry = info["industry"]
                        db_q.position = info["position"]
                        session.add(db_q)
                        updated_count += 1
                
                if count % 500 == 0:
                    session.commit()
            
            session.commit()

        log(f"Update complete. Total {updated_count} rows updated in database.")

    if __name__ == "__main__":
        update_questions()

except Exception as e:
    log(f"CRITICAL ERROR: {e}")
    import traceback
    log(traceback.format_exc())
