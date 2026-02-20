
import os
import json
from sqlalchemy import create_engine, text

# Host port is 15432 as per the latest docker-compose change
DATABASE_URL = "postgresql+psycopg://admin:1234@localhost:15432/interview_db"

def check_latest_resume():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Get the latest resume
            result = conn.execute(text("SELECT id, candidate_id, file_name, processing_status, structured_data FROM resumes ORDER BY uploaded_at DESC LIMIT 1"))
            row = result.fetchone()
            
            if row:
                print(f"Resume ID: {row[0]}")
                print(f"Candidate ID: {row[1]}")
                print(f"File Name: {row[2]}")
                print(f"Status: {row[3]}")
                print("Structured Data:")
                if row[4]:
                    print(json.dumps(row[4], ensure_ascii=False, indent=2))
                else:
                    print("None")
            else:
                print("No resumes found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_latest_resume()
