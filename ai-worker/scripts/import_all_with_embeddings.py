
import json
import os
import sys
from pathlib import Path

# ai-worker 및 backend-core 경로 설정
# 이를 통해 backend-core의 models_db.py를 직접 임포트하여 스키마 중복 정의를 방지합니다.
current_dir = Path(__file__).parent
backend_core_path = current_dir.parent.parent / "backend-core"
ai_worker_path = current_dir.parent

sys.path.append(str(backend_core_path))
sys.path.append(str(ai_worker_path))

from abc import ABC
from sqlmodel import Session, create_engine, select
# backend-core/db_models.py 에서 임포트
from db_models import Question, AnswerBank, QuestionCategory, QuestionDifficulty, Company
# vector_utils에서 중앙 관리형 EmbeddingGenerator 사용
from utils.vector_utils import get_embedding_generator
from datetime import datetime

# 실행 예시
# docker exec -it interview_worker python scripts/import_all_with_embeddings.py

# ==========================================
# 데이터 구조 (Data Structure)
# ==========================================
# 
# 입력 JSON 형식:
# [
#     {
#         "question": "질문 내용",
#         "answer": "답변 내용",
#         "subcategory": "소분류 (예: 머신러닝, 딥러닝)",  # Optional
#         "industry": "산업 (예: IT/소프트웨어, AI/데이터)",  # Optional
#         "company": "회사명 (예: 삼성전자, 카카오)",  # Optional
#         "position": "직무 (예: Backend 개발자)"  # Optional
#     }
# ]
#
# DB 저장 매핑:
# - subcategory → question_type (질문 세부 분류)
# - industry → Question.industry (산업 분야, NULL 허용)
# - company → Question.company (회사명, NULL 허용)
# - position → Question.position (직무, NULL 허용)
# - 소분류 정보를 기반으로 QuestionCategory 자동 분류
# - NULL 값은 그대로 유지 (기본값 없음)
#
# ==========================================

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
    """설명:
        주어진 파일명을 가능한 데이터 디렉토리에서 찾음

        Args:
        filename: 찾을 파일명

        Returns:
        

        생성자: ejm
        생성일자: 2026-02-04
    """
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
    """설명:
        데이터베이스 엔진을 생성하고 테스트

        Returns:
        

        생성자: ejm
        생성일자: 2026-02-04
    """
    try:
        engine = create_engine(DATABASE_URL)
        with Session(engine) as session:
            pass
        return engine
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def import_questions(session, file_path, source_name, generator):
    """설명:
        JSON 파일에서 질문을 읽고 데이터베이스에 저장

        Args:
        session: 데이터베이스세션
        file_path: 파일위치
        source_name: 데이터소스명
        generator: 임베딩 생성기

        Returns:
        

        생성자: ejm
        생성일자: 2026-02-04
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

    def classify_question(text):
        """
        키워드 기반 간단한 분류 (데이터에 카테고리가 없을 경우 사용)
        
        Args:
            text (str): 분류할 텍스트
        
        Returns:
            tuple: (카테고리, 분류명)
        
        Raises:
            ValueError: 텍스트가 비어있을 경우

        생성자: ejm
        생성일자: 2026-02-04
        """
        text = text.lower()
        
        # 1. 인성/문화 적합성 (CULTURAL_FIT)
        if any(w in text for w in ["지원동기", "입사", "포부", "장점", "단점", "갈등", "협업", "소통", "팀워크", "실패", "성공", "존경", "문화", "why"]):
            return QuestionCategory.CULTURAL_FIT, "인성면접"
            
        # 2. 직무/경험 (BEHAVIORAL)
        if any(w in text for w in ["프로젝트", "경험", "역량", "기여", "해결", "직무", "커리어", "어떻게"]):
            return QuestionCategory.BEHAVIORAL, "직무경험"
            
        # 3. 기술 (TECHNICAL) - Default
        return QuestionCategory.TECHNICAL, "직무지식"
    
    def auto_classify_by_subcategory(subcategory, text):
        """소분류 정보를 기반으로 카테고리 자동 분류
        
        Args:
            subcategory (str): 소분류
            text (str): 분류할 텍스트
        
        Returns:
            QuestionCategory: 카테고리
        
        Raises:
            ValueError: 텍스트가 비어있을 경우
        
        생성자: ejm
        생성일자: 2026-02-04
        """
        subcategory_lower = subcategory.lower()
        
        # 인성/문화 관련 소분류
        cultural_keywords = ["인성", "문화", "가치관", "태도", "성격", "협업", "소통"]
        if any(keyword in subcategory_lower for keyword in cultural_keywords):
            return QuestionCategory.CULTURAL_FIT
        
        # 경험/행동 관련 소분류
        behavioral_keywords = ["경험", "프로젝트", "실무", "사례", "상황", "문제해결"]
        if any(keyword in subcategory_lower for keyword in behavioral_keywords):
            return QuestionCategory.BEHAVIORAL
        
        # 기술 관련 소분류 (기본값)
        # 머신러닝, 딥러닝, 프로그래밍, 알고리즘 등
        return QuestionCategory.TECHNICAL

    for item in data:
        q_text = item.get("question") or item.get("질문")
        # answer_cleaned 우선, 없으면 answer/답변 사용
        a_text = item.get("answer_cleaned") or item.get("answer") or item.get("답변")
        
        # 메타데이터 추출 (NULL 값 그대로 유지)
        subcategory = item.get("subcategory") or item.get("소분류")  # 기본값 없음
        industry_value = item.get("industry") or item.get("산업")  # 기본값 없음
        company_value = item.get("company") or item.get("회사")  # 기본값 없음
        position_value = item.get("position") or item.get("직무")  # 기본값 없음

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
        # 소분류 정보를 활용하여 카테고리 자동 분류
        category_str = item.get("QuestionCategory", "").lower()
        try:
            category = QuestionCategory(category_str)
        except ValueError:
            # 소분류 기반 자동 분류 (소분류가 있을 때만)
            if subcategory:
                category = auto_classify_by_subcategory(subcategory, q_text)
            else:
                category, _ = classify_question(q_text)

        # 2. Difficulty Parsing
        difficulty_str = item.get("QuestionDifficulty", "").lower()
        try:
            difficulty = QuestionDifficulty(difficulty_str)
        except ValueError:
            difficulty = QuestionDifficulty.MEDIUM

        # 3. Question Type Parsing
        # 소분류를 question_type으로 사용 (없으면 자동 분류)
        q_type = item.get("QUESTION_TYPE") or subcategory
        if not q_type:
            _, q_type = classify_question(q_text)

        # Embedding 생성 (Query 모드 사용 권장? Question 자체는 DB에 저장되어 검색됨(Passage 성격도 있음)
        # 하지만 질문-질문 유사도 검색 시에는 둘 다 Query 또는 둘 다 Passage로 맞춰야 함.
        # 벡터 DB 검색 시 유저 쿼리는 "query:", DB 문서는 "passage:"를 붙여 저장하는 비대칭 방식이 일반적.
        # 여기서는 Question을 '검색 대상'으로 저장하므로 "passage:" 접두어를 사용하여 저장.
        # 나중에 유저가 질문을 검색할 때 "query:"를 붙여서 검색.
        q_embedding = generator.encode_passage(q_text)

        # Create Question
        # DB 필드에 직접 저장 (NULL 값 그대로 유지)
        question = Question(
            content=q_text,
            category=category,
            difficulty=difficulty,
            rubric_json={"keywords": []},  # 기본 rubric만 저장
            question_type=q_type, 
            usage_count=0,
            is_active=True,
            embedding=q_embedding,  # 임베딩 저장
            company=company_value,  # None이면 NULL로 저장
            industry=industry_value,  # None이면 NULL로 저장
            position=position_value  # None이면 NULL로 저장
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
            embedding=a_embedding,  # 임베딩 저장
            company=company_value,
            industry=industry_value,
            position=position_value
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
    """설명:
        회사정보를 DB에 저장하는 함수

        Args:
        session: DB 세션
        file_path: JSON 파일 경로
        generator: 임베딩 생성기

        Returns:
        

        생성자: ejm
        생성일자: 2026-02-04
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
    """설명:
        전체 임베딩 데이터 임포트 스크립트의 진입점.
        KURE-v1 모델 로드, DB 연결 확인 후 질문 및 회사 데이터를 순차적으로 처리.

    Returns:
        None

    생성자: ejm
    생성일자: 2026-02-04
    """
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