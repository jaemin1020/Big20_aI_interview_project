import os
import sys
import json
import logging
from datetime import datetime
from sqlmodel import Session, select

# 프로젝트 루트 및 backend-core 경로 추가
root_dir = os.path.abspath(os.path.dirname(__file__))
backend_dir = os.path.join(root_dir, "backend-core")
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# 환경 변수 설정 (로컬 실행 시 DB 접속용)
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:1234@localhost:15432/interview_db"

# 모듈 임포트
try:
    from database import engine
    from db_models import Question
except ImportError as e:
    # 만약 위 방식이 실패하면 다른 경로 시도 (예: ai-worker/db)
    logging.error(f"❌ 임포트 실패: {e}. 경로설정을 다시 확인합니다.")
    ai_worker_dir = os.path.join(root_dir, "ai-worker")
    if ai_worker_dir not in sys.path:
        sys.path.append(ai_worker_dir)
    from db import engine
    from db_models import Question

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def export_all_question_data():
    """DB의 Question 테이블 전체(임베딩 포함)를 JSON으로 추출합니다."""
    logger.info("📂 DB 데이터(임베딩 포함) 추출 시작...")
    
    try:
        with Session(engine) as session:
            # 1. 모든 질문 가져오기
            statement = select(Question)
            questions = session.exec(statement).all()
            
            if not questions:
                logger.warning("⚠️ 백업할 질문 데이터가 없습니다.")
                return

            export_data = []
            for q in questions:
                # SQLModel 객체를 dict로 변환
                q_dict = q.model_dump()
                
                # datetime 및 embedding(vector) 처리
                for key, value in q_dict.items():
                    if isinstance(value, datetime):
                        q_dict[key] = value.isoformat()
                    # embedding이 pgvector 객체일 경우 리스트로 변환
                    elif key == "embedding" and value is not None:
                        try:
                            # pgvector 객체면 list(value)로 변환 가능
                            q_dict[key] = [float(x) for x in value]
                        except:
                            try:
                                q_dict[key] = list(value)
                            except:
                                q_dict[key] = str(value)

                export_data.append(q_dict)

            # 파일 저장
            filename = f"db_questions_full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 총 {len(export_data)}개의 질문 데이터(임베딩 포함)가 '{filename}'에 저장되었습니다.")

    except Exception as e:
        logger.error(f"❌ 데이터 추출 중 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    export_all_question_data()
