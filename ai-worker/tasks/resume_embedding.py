
import logging
import json
from datetime import datetime
from celery import shared_task
from sqlmodel import Session
from db import engine
<<<<<<< HEAD
from db_models import Resume
from .embedding import embed_chunks
from .chunking import chunk_resume
from .pgvector_store import store_embeddings

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="tasks.resume_embedding.generate_resume_embeddings", queue='gpu_queue')
=======
from models import Resume
from .embedding import embed_chunks
from .chunking import chunk_resume

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="generate_resume_embeddings", queue='gpu_queue')
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
def generate_resume_embeddings(self, resume_id: int):
    """
    구조화된 이력서 데이터를 기반으로 청킹 및 임베딩을 생성하여 DB에 저장합니다.
    """
    logger.info(f"Starting resume embedding generation for ID: {resume_id}")
    
    try:
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if not resume:
                logger.error(f"Resume {resume_id} not found in DB")
                return

            if not resume.structured_data:
                logger.error(f"Structured data is missing for resume {resume_id}")
                # Fallback: extracted_text 사용 시도?
                if resume.extracted_text:
                     # 텍스트라도 있으면 그걸로 청킹 시도 가능하지만,
                     # 현재 chunking.py가 structured_data를 기대할 것임.
                     pass 
                
                # 데이터 없음 -> 실패 처리
                resume.processing_status = "failed"
                session.add(resume)
                session.commit()
                return
            
            # 1. 청킹
            chunks = chunk_resume(resume.structured_data)
            logger.info(f"Created {len(chunks)} chunks for resume {resume_id}")
            
            # 2. 임베딩 생성 (벡터 변환)
            # embed_chunks는 [{"text":..., "vector":...}, ...] 리스트 반환
            embedded_data = embed_chunks(chunks)
            
            if not embedded_data:
                logger.error(f"Failed to generate embeddings for resume {resume_id}")
                resume.processing_status = "failed"
                session.add(resume)
                session.commit()
                return

            # 3. 결과 저장
            # 대표 벡터(첫 번째 청크 - 보통 Summary/Header)를 저장
            # pgvector 컬럼(Vector(1024))에 맞게 저장
            if embedded_data and 'vector' in embedded_data[0]:
                 resume.embedding = embedded_data[0]['vector']
<<<<<<< HEAD
                 logger.info(f"Saved representative embedding vector (dim: {len(resume.embedding)})")
            
            # 3. 벡터 DB(resume_embeddings 테이블)에 전체 청크 저장
            try:
                store_embeddings(resume_id, embedded_data)
                logger.info(f"Successfully stored {len(embedded_data)} chunks to vector DB")
            except Exception as e:
                logger.error(f"Failed to store chunks to vector DB: {e}")
                # 전체 저장은 실패해도 개별 상태는 completed로 감 (최소한 요약 벡터는 저장됨)
=======
                 logger.info(f"Saved embedding vector (dim: {len(resume.embedding)})")
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
            
            # 완료 처리
            resume.processing_status = "completed"
            resume.processed_at = datetime.utcnow()
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
