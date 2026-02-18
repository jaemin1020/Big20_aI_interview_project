import json
import os
import sys
from datetime import datetime
from enum import Enum

# ai-worker 경로 추가
ai_worker_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ai-worker"))
if ai_worker_path not in sys.path:
    sys.path.append(ai_worker_path)

# backend-core 경로 추가 (db_models 임포트를 위함)
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend-core"))
if backend_path not in sys.path:
    sys.path.append(backend_path)

# 환경 변수 설정 (로콜 실행 시 db:5432 -> localhost:15432)
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:1234@localhost:15432/interview_db"

from db import engine, select, Session, Question

class DateTimeEnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

def export_questions_to_json():
    print("🚀 questions 테이블 데이터 내보내기를 시작합니다...")
    
    try:
        with Session(engine) as session:
            stmt = select(Question)
            questions = session.exec(stmt).all()
            
            print(f"📊 총 {len(questions)}개의 질문을 찾았습니다.")
            
            # 모델 객체를 딕셔너리로 변환
            data = []
            for q in questions:
                q_dict = q.model_dump()
                # embedding 필드는 이미 리스트이거나 None일 것이므로 별도 처리가 필요할 수 있음
                # pgvector의 Vector 타입은 조회 시 보통 list로 반환됩니다.
                data.append(q_dict)
            
            # JSON 파일로 저장
            output_file = "questions_export.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4, cls=DateTimeEnumEncoder)
            
            print(f"✅ 내보내기 완료: {os.path.abspath(output_file)}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    export_questions_to_json()
