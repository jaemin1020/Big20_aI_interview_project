
import json
import os
import sys
from pathlib import Path

# ai-worker 및 backend-core 경로 설정
# 이를 통해 backend-core의 models.py를 직접 임포트하여 스키마 중복 정의를 방지합니다.
current_dir = Path(__file__).parent
backend_core_path = current_dir.parent.parent / "backend-core"
ai_worker_path = current_dir.parent

sys.path.append(str(backend_core_path))
sys.path.append(str(ai_worker_path))

from abc import ABC
from sqlmodel import Session, create_engine, select
# backend-core/models.py 에서 임포트
from models import Question, AnswerBank, QuestionCategory, QuestionDifficulty, Company
# vector_utils에서 중앙 관리형 EmbeddingGenerator 사용
from utils.vector_utils import get_embedding_generator
from datetime import datetime

# 실행 예시
# docker exec -it interview_worker //bin/bash python import_data.py

# ==========================================
# Configuration
# ==========================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@interview_db:5432/interview_db")

# 데이터 파일 경로 (backend-core의 data 디렉토리 참조)
# Docker 컨테이너 내에서 경로가 다를 수 있으므로 volume mount 확인 필요
# 여기서는 상대 경로로 접근 시도. 실패 시 절대 경로 확인 필요.

POSSIBLE_DATA_DIRS = [
    "../backend-core/data", 
    "/backend-core/data",
    "c:/big20/git/Big20_aI_interview_project/backend-core/data",
    "/app/data", # Maybe mounted here
    "/data"
]

DATA_FILE_NAME_OLD = "preprocessed_data.json"
DATA_FILE_NAME_CORP = "corp_data.json"

def find_file(filename):
    for directory in POSSIBLE_DATA_DIRS:
        filepath = os.path.join(directory, filename)
        if os.path.exists(filepath):
            return filepath
    return None

DATA_FILE_OLD = find_file(DATA_FILE_NAME_OLD) or "preprocessed_data.json"
DATA_FILE_CORP = find_file(DATA_FILE_NAME_CORP) or "corp_data.json"


# ==========================================
# Script
# ==========================================

def get_engine():
    try:
        engine = create_engine(DATABASE_URL)
        with Session(engine) as session:
            pass
        return engine
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def import_questions(session, file_path, source_name, generator):
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

    def classify_question(text):
        """키워드 기반 간단한 분류 (데이터에 카테고리가 없을 경우 사용)"""
        text = text.lower()
        
        # 1. 인성/문화 적합성 (CULTURAL_FIT)
        if any(w in text for w in ["지원동기", "입사", "포부", "장점", "단점", "갈등", "협업", "소통", "팀워크", "실패", "성공", "존경", "문화", "why"]):
            return QuestionCategory.CULTURAL_FIT, "인성면접"
            
        # 2. 직무/경험 (BEHAVIORAL)
        if any(w in text for w in ["프로젝트", "경험", "역량", "기여", "해결", "직무", "커리어", "어떻게"]):
            return QuestionCategory.BEHAVIORAL, "직무경험"
            
        # 3. 기술 (TECHNICAL) - Default
        return QuestionCategory.TECHNICAL, "직무지식"

    for item in data:
        q_text = item.get("question") or item.get("질문")
        # answer_cleaned 우선, 없으면 answer/답변 사용
        a_text = item.get("answer_cleaned") or item.get("answer") or item.get("답변")

        if not q_text or not a_text:
            skipped += 1
            continue

        # Check for duplicates
        statement = select(Question).where(Question.content == q_text)
        existing_q = session.exec(statement).first()
        
        if existing_q:
            duplicates += 1
            # 이미 있으면 스킵
            continue

        # 1. Category Parsing
        category_str = item.get("QuestionCategory", "").lower()
        try:
            category = QuestionCategory(category_str)
        except ValueError:
            # Fallback
            category, _ = classify_question(q_text)

        # 2. Difficulty Parsing
        difficulty_str = item.get("QuestionDifficulty", "").lower()
        try:
            difficulty = QuestionDifficulty(difficulty_str)
        except ValueError:
            difficulty = QuestionDifficulty.MEDIUM

        # 3. Question Type Parsing
        q_type = item.get("QUESTION_TYPE")
        if not q_type:
            _, q_type = classify_question(q_text)

        # Embedding 생성 (Query 모드 사용 권장? Question 자체는 DB에 저장되어 검색됨(Passage 성격도 있음)
        # 하지만 질문-질문 유사도 검색 시에는 둘 다 Query 또는 둘 다 Passage로 맞춰야 함.
        # 벡터 DB 검색 시 유저 쿼리는 "query:", DB 문서는 "passage:"를 붙여 저장하는 비대칭 방식이 일반적.
        # 여기서는 Question을 '검색 대상'으로 저장하므로 "passage:" 접두어를 사용하여 저장.
        # 나중에 유저가 질문을 검색할 때 "query:"를 붙여서 검색.
        q_embedding = generator.encode_passage(q_text)

        # Create Question
        question = Question(
            content=q_text,
            category=category,
            difficulty=difficulty,
            rubric_json={"keywords": []}, 
            question_type=q_type, 
            usage_count=0,
            is_active=True,
            embedding=q_embedding # 임베딩 저장
        )
        session.add(question)
        session.flush() # To get ID

        # Answer Embedding (Passage)
        a_embedding = generator.encode_passage(a_text)

        # Create AnswerBank
        answer = AnswerBank(
            question_id=question.id,
            answer_text=a_text,
            score=100.0,
            reference_count=0,
            is_active=True,
            embedding=a_embedding # 임베딩 저장
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

def import_companies(session, file_path, generator):
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
        code = item.get("code")
        ideal = item.get("ideal") or ""
        desc = item.get("description") or ""

        if not name or not code:
            continue

        code_str = str(code).strip()

        # Check for duplicates
        statement = select(Company).where(Company.id == code_str)
        existing_c = session.exec(statement).first()

        if existing_c:
            duplicates += 1
            # Update existing if needed, or skip
            # 여기서는 스킵
            continue
            
        # Embedding text
        text_for_embedding = f"{ideal} {desc}".strip()
        # Company Info도 검색 대상 -> Passage
        embedding = generator.encode_passage(text_for_embedding)

        company = Company(
            id=code_str,
            company_name=name,
            ideal=ideal,
            description=desc,
            embedding=embedding # 임베딩 저장
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
    print("🚀 Starting Data Import with Embeddings...")
    
    # Init Embedding Generator
    print("📦 Loading embedding model (KURE-v1)...")
    generator = get_embedding_generator()
    print("✅ Model loaded.")

    engine = get_engine()
    if not engine:
        return

    with Session(engine) as session:
        # Import Questions
        if DATA_FILE_OLD:
             import_questions(session, DATA_FILE_OLD, "General Questions", generator)
        else:
            print("⚠️ Questions data file not found.")

        print("-" * 40)

        # Import Companies
        if DATA_FILE_CORP:
            import_companies(session, DATA_FILE_CORP, generator)
        else:
             print("⚠️ Corp data file not found.")

    print("=" * 40)
    print("🎉 All imports completed.")

if __name__ == "__main__":
    main()
