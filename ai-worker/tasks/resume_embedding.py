
import logging
import json
from datetime import datetime
from celery import shared_task
from sqlmodel import Session
from db import engine
from db_models import Resume
from .embedding import embed_chunks
from .chunking import chunk_resume
from .pgvector_store import store_embeddings

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="tasks.resume_pipeline.generate_embeddings", queue='gpu_queue')
def generate_resume_embeddings(self, resume_id: int):
    """
    구조화된 이력서 데이터를 기반으로 청킹 및 임베딩을 생성하여 DB에 저장합니다.
    """
    logger.info(f"Starting resume embedding generation for ID: {resume_id}")
    
    try:
        # 1. 데이터 조회 (짧은 세션)
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if not resume:
                logger.error(f"Resume {resume_id} not found in DB")
                return
            structured_data = resume.structured_data
            
        if not structured_data:
            logger.error(f"Structured data is missing for resume {resume_id}")
            with Session(engine) as session:
                resume = session.get(Resume, resume_id)
                if resume:
                    resume.processing_status = "failed"
                    session.add(resume)
                    session.commit()
            return
        
        # 2. 청킹 및 임베딩 (세션 외부에서 수행 - 시간 소요 큼)
        # 이 과정이 진행되는 동안 DB 세션을 잡고 있으면 트랜잭션 충돌 발생 가능
        chunks = chunk_resume(structured_data)
        logger.info(f"Created {len(chunks)} chunks for resume {resume_id}")
        
        embedded_data = embed_chunks(chunks)
        
        if not embedded_data:
            logger.error(f"Failed to generate embeddings for resume {resume_id}")
            with Session(engine) as session:
                resume = session.get(Resume, resume_id)
                if resume:
                    resume.processing_status = "failed"
                    session.add(resume)
                    session.commit()
            return

        # 3. 결과 저장 (새로운 짧은 세션)
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if not resume: return

            # 대표 벡터 저장
            if embedded_data and 'vector' in embedded_data[0]:
                 resume.embedding = embedded_data[0]['vector']
            
            # 벡터 DB(PGVector)에 전체 청크 저장
            try:
                # store_embeddings 내부에서도 별도 연결을 사용하므로 세션 외부 호출과 동일 효과
                store_embeddings(resume_id, embedded_data)
                logger.info(f"Successfully stored {len(embedded_data)} chunks to vector DB")
            except Exception as e:
                logger.error(f"Failed to store chunks to vector DB: {e}")
            
            # 상태 업데이트
            resume.processing_status = "completed"
            resume.processed_at = datetime.now()
            session.add(resume)
            session.commit()
            
        logger.info(f"Resume {resume_id} processing completed successfully.")

    except Exception as e:
        logger.error(f"Error generating embeddings for resume {resume_id}: {e}", exc_info=True)
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if resume:
                resume.processing_status = "failed"
                session.add(resume)
                session.commit()
