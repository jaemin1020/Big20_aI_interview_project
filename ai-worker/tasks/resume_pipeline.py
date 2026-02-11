import logging
import os
from celery import shared_task
from sqlalchemy import text as sql_text
from .parse_resume import parse_resume_final
from .save_structured import save_structured
from .chunking import chunk_resume
from .embedding import embed_chunks
from .pgvector_store import store_embeddings

# DB 연결을 위해 추가
try:
    from db import engine
except ImportError:
    engine = None

logger = logging.getLogger("AI-Worker-ResumePipeline")

@shared_task(name="tasks.resume_pipeline.process_resume_pipeline")
def process_resume_pipeline(resume_id, file_path):
    """
    사용자가 작성한 원본 로직(Step 2~6)을 순서대로 실행하는 통합 태스크
    """
    logger.info(f"Starting resume processing pipeline for resume_id: {resume_id}")
    
    try:
        # 0. Candidate ID 조회
        candidate_id = 1
        if engine:
            with engine.connect() as conn:
                res = conn.execute(
                    sql_text("SELECT candidate_id FROM resumes WHERE id = :rid"),
                    {"rid": resume_id}
                ).fetchone()
                if res:
                    candidate_id = res[0]

        # Step 1/5: 원본 파싱 로직 (parse_resume_final)
        logger.info(f"[Step 1/5] Parsing resume: {file_path}")
        parsed_data = parse_resume_final(file_path)
        if not parsed_data:
            raise ValueError("Failed to parse resume data.")

        # Step 2/5: 원본 DB 저장 로직 (save_structured)
        file_name = os.path.basename(file_path)
        logger.info(f"[Step 2/5] Saving structured data")
        save_structured(resume_id=resume_id, candidate_id=candidate_id, parsed_data=parsed_data, file_name=file_name)

        # Step 3/5: 원본 청킹 로직 (chunk_resume)
        logger.info(f"[Step 3/5] Chunking data")
        chunks = chunk_resume(parsed_data)
        if not chunks:
            raise ValueError("No chunks generated.")

        # Step 4/5: 원본 임베딩 로직 (embed_chunks)
        logger.info(f"[Step 4/5] Generating embeddings")
        embedded_result = embed_chunks(chunks)
        if not embedded_result:
            raise ValueError("Failed to generate embeddings.")

        # Step 5/5: 원본 벡터 저장 로직 (store_embeddings)
        logger.info(f"[Step 5/5] Storing in pgvector")
        store_embeddings(resume_id=resume_id, embedded_chunks=embedded_result)

        # 상태 업데이트
        if engine:
            with engine.begin() as conn:
                conn.execute(
                    sql_text("UPDATE resumes SET processing_status = 'completed', processed_at = CURRENT_TIMESTAMP WHERE id = :rid"),
                    {"rid": resume_id}
                )

        logger.info(f"✅ Pipeline completed for resume_id: {resume_id}")
        return {"status": "success", "resume_id": resume_id}

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        if engine:
            try:
                with engine.begin() as conn:
                    conn.execute(
                        sql_text("UPDATE resumes SET processing_status = 'failed' WHERE id = :rid"),
                        {"rid": resume_id}
                    )
            except: pass
        return {"status": "error", "message": str(e)}
