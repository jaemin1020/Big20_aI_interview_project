import logging
import json
from sqlalchemy import text as sql_text

# DB 연결을 위해 추가
try:
    from db import engine
except ImportError:
    engine = None

logger = logging.getLogger("AI-Worker-SaveStructured")

def save_structured(resume_id, candidate_id, parsed_data, file_name):
    """
    파싱된 이력서 데이터를 DB에 저장 (JSON 형태 및 기본 정보 업데이트)
    """
    logger.info(f"Saving structured data for resume_id: {resume_id}")
    
    if not engine:
        logger.error("Database engine not initialized. Cannot save structured data.")
        return False

    try:
        # 1. JSON 직렬화 (한글 깨짐 방지)
        structured_json = json.dumps(parsed_data, ensure_ascii=False)
        
        with engine.begin() as conn:
            # 2. resumes 테이블의 structured_data 업데이트
            # processed_at을 현재 시간으로 설정하고, 상태도 업데이트 가능하지만 
            # pipeline에서 나중에 'completed'로 바꾸므로 여기서는 데이터만 저장
            conn.execute(
                sql_text("""
                    UPDATE resumes 
                    SET structured_data = :data,
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = :rid
                """),
                {
                    "data": structured_json,
                    "rid": resume_id
                }
            )
            
            logger.info(f"✅ Successfully saved structured data for resume_id: {resume_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to save structured data: {e}")
        return False
