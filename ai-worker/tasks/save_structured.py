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
            from sqlalchemy import bindparam
            from sqlalchemy.dialects.postgresql import JSONB
            
            # 2. 파싱된 헤더 데이터 추출
            header = parsed_data.get("header", {})
            candidate_name = header.get("name")

            # 3. resumes 테이블 업데이트 (structured_data JSON만 저장)
            conn.execute(
                sql_text("""
                    UPDATE resumes 
                    SET structured_data = CAST(:data AS jsonb),
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = :rid
                """),
                {
                    "data": json.dumps(parsed_data, ensure_ascii=False),
                    "rid": resume_id
                }
            )

            # 4. 이름이 추출되었다면 users 테이블의 full_name 업데이트
            if candidate_name:
                conn.execute(
                    sql_text("""
                        UPDATE users 
                        SET full_name = :name
                        WHERE id = :uid
                    """),
                    {
                        "name": candidate_name,
                        "uid": candidate_id
                    }
                )
            
            logger.info(f"✅ Successfully saved structured data for resume_id: {resume_id} (Name: {candidate_name})")
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to save structured data: {e}")
        return False
