import json
import os
import sys
from sqlmodel import Session, create_engine, select
from sqlalchemy.exc import IntegrityError
# models.py must be in the same directory
from models import Question, AnswerBank, QuestionCategory, QuestionDifficulty, Company

# ==========================================
# Configuration
# ==========================================

# Database Connection String
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@localhost:5432/interview_db")

# Paths to the data files
DATA_FILE_OLD = os.path.join("data/preprocessed_data.json")
DATA_FILE_CORP = os.path.join("data/corp_data.json")

# ==========================================
# Script
# ==========================================

def get_engine():
    """
    db 삽입을 위한 engine 생성

    사용예: docker exec -it interview_backend //bin/bash
    python import_data.py
    """
    try:
        engine = create_engine(DATABASE_URL)
        # Test connection
        with Session(engine) as session:
            pass
        return engine
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Tip: Make sure the database is running and accessible (e.g. port 5432 exposed).")
        return None

def import_questions(session, file_path, source_name):
    """
    Imports questions from a JSON file.
    Expected format: List of dicts with 'question'/'answer' OR '질문'/'답변' keys.
    """
    if not os.path.exists(file_path):
        print(f"⚠️ Warning: File not found at {file_path}. Skipping {source_name}.")
        return

    print(f"📂 Reading {source_name} from: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading {source_name}: {e}")
        return

    print(f"🚀 Importing {len(data)} items from {source_name}...")

    count = 0
    skipped = 0
    duplicates = 0

    for item in data:
        # Normalize keys
        q_text = item.get("question") or item.get("질문")
        a_text = item.get("answer") or item.get("답변")

        if not q_text or not a_text:
            skipped += 1
            continue

        # Check for duplicates (simple check by content)
        statement = select(Question).where(Question.content == q_text)
        existing_q = session.exec(statement).first()

        if existing_q:
            duplicates += 1
            continue

        # Create Question
        question = Question(
            content=q_text,
            category=QuestionCategory.TECHNICAL,
            difficulty=QuestionDifficulty.MEDIUM,
            rubric_json={"keywords": []},
            question_type="직무지식",
            usage_count=0,
            is_active=True
        )
        session.add(question)
        session.flush() # To get ID

        # Create AnswerBank
        answer = AnswerBank(
            question_id=question.id,
            answer_text=a_text,
            score=100.0,
            reference_count=0,
            is_active=True
        )
        session.add(answer)
        count += 1

        if count % 100 == 0:
            print(f"   - {count} items processed...")

    try:
        session.commit()
        print(f"✅ Finished {source_name}: Imported {count}, Duplicates {duplicates}, Skipped {skipped}")
    except Exception as e:
        session.rollback()
        print(f"❌ Failed to commit {source_name}: {e}")

def import_companies(session, file_path):
    """
    Imports companies from corp_data.json.
    """
    if not os.path.exists(file_path):
        print(f"⚠️ Warning: File not found at {file_path}. Skipping Companies.")
        return

    print(f"📂 Reading Companies from: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading Companies: {e}")
        return

    print(f"🚀 Importing {len(data)} companies...")

    count = 0
    duplicates = 0

    for item in data:
        name = item.get("name")
        code = item.get("code") # Use code for ID
        ideal = item.get("ideal")
        desc = item.get("description")

        if not name or not code:
            continue

        # Ensure code is string (handle int/str variations in JSON)
        code_str = str(code).strip()

        # Check for duplicates by ID (using Code as ID)
        statement = select(Company).where(Company.id == code_str)
        existing_c = session.exec(statement).first()

        if existing_c:
            duplicates += 1
            # Optional: Update existing record? For now, skip.
            continue

        # Check if code is already used (double check)
        # We are using code as primary key, so 'existing_c' check covers it.

        company = Company(
            id=code_str, # Using Company Code as ID
            company_name=name,
            ideal=ideal,
            description=desc
        )
        session.add(company)
        count += 1

        if count % 50 == 0:
            print(f"   - {count} companies processed...")

    try:
        session.commit()
        print(f"✅ Finished Companies: Imported {count}, Duplicates {duplicates}")
    except Exception as e:
        session.rollback()
        print(f"❌ Failed to commit Companies: {e}")


def main():
    engine = get_engine()
    if not engine:
        return

    with Session(engine) as session:
        # 1. Import Old Data (data.json)
        import_questions(session, DATA_FILE_OLD, "General Questions (data.json)")

        print("-" * 40)

        # 3. Import Corporate Data (corp_data.json)
        import_companies(session, DATA_FILE_CORP)

    print("=" * 40)
    print("🎉 All imports completed.")

if __name__ == "__main__":
    main()
