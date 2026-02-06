import os
from sqlmodel import create_engine, text, Session
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
LOCAL_DATABASE_URL = DATABASE_URL.replace("db:5432", "localhost:15432")

print(f"Testing connection to {LOCAL_DATABASE_URL}...")
try:
    engine = create_engine(LOCAL_DATABASE_URL)
    with Session(engine) as session:
        session.execute(text("SELECT 1"))
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
