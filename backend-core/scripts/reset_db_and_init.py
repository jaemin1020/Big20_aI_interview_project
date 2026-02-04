
import os
import sys
import logging

# Add parent directory to path to allow imports from sibling modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import SQLModel
from database import engine, init_db
# Explicitly import all models to ensure they are registered in metadata
from models import (
    User, Company, Interview, Question, Transcript,
    EvaluationReport, Resume, AnswerBank
)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_Reset")

def reset_db_tables():
    logger.info("Starting database reset...")

    try:
        # Drop all tables
        logger.info("Dropping all existing tables...")
        SQLModel.metadata.drop_all(engine)
        logger.info("✅ All tables dropped.")

        # Re-initialize DB (Create tables)
        logger.info("Creating new tables...")
        init_db()
        logger.info("✅ Database initialized successfully with new schema.")

    except Exception as e:
        logger.error(f"❌ Error resetting database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Prompt for confirmation if running interactively
    if sys.stdin.isatty():
        response = input("This will DELETE ALL DATA in the database. Are you sure? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            sys.exit(0)

    reset_db_tables()
