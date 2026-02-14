import json
import os
import sys

# 프로젝트 경로 추가 (backend-core 내부에서 실행한다고 가정)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select, create_engine
from db_models import Question, QuestionCategory, QuestionDifficulty

# 환경변수에서 DATABASE_URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@localhost:15432/interview_db")

def import_questions(json_path: str):
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    # 엔진 생성
    print(f"Connecting to: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)

    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

    print(f"Loaded {len(data)} items from {json_path}")

    with Session(engine) as session:
        # 성능 최적화: 기존 질문 내용을 Set으로 가져옴 (메모리 효율적 비교)
        print("Fetching existing questions for deduplication...")
        existing_contents = set(session.exec(select(Question.content)).all())
        print(f"Found {len(existing_contents)} existing questions in DB.")

        count = 0
        skipped = 0
        total = len(data)
        
        for idx, item in enumerate(data):
            question_text = item.get("question")
            if not question_text:
                continue
            
            # 중복 체크 (메모리 내 Set 활용으로 DB 접근 최소화)
            if question_text in existing_contents:
                skipped += 1
                continue

            # 2. 필드 매핑 및 변환
            category_val = item.get("QuestionCategory", "TECHNICAL")
            difficulty_val = item.get("QuestionDifficulty", "MEDIUM")
            
            try:
                category = QuestionCategory(category_val)
            except ValueError:
                category = QuestionCategory.TECHNICAL
                
            try:
                difficulty = QuestionDifficulty(difficulty_val)
            except ValueError:
                difficulty = QuestionDifficulty.MEDIUM

            # Question 객체 생성
            new_question = Question(
                content=question_text,
                category=category,
                difficulty=difficulty,
                question_type=item.get("QUESTION_TYPE") or item.get("question_type") or "직무지식",
                position=item.get("position"),
                industry=item.get("industry"),
                rubric_json={}
            )
            session.add(new_question)
            count += 1
            existing_contents.add(question_text) # 메모리 상의 Set도 업데이트
            
            # 1000개 단위로 커밋 (성능 향상)
            if count % 1000 == 0:
                session.commit()
                print(f"Processed {idx+1}/{total}... (Imported: {count}, Skipped: {skipped})")

        session.commit()
        print(f"Finished! Total: {total}, Imported: {count}, Skipped: {skipped}")

if __name__ == "__main__":
    # 인자로 받은 경로가 있으면 사용, 없으면 기본값
    if len(sys.argv) > 1:
        target_json = sys.argv[1]
    else:
        # 스크립트 위치 기준 상대 경로 (루트의 data.json)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_json = os.path.join(project_root, "data.json")
    
    import_questions(target_json)
