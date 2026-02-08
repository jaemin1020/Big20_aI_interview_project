from sqlmodel import Session, create_engine, select
from models import Resume, ResumeChunk, SectionType
from utils.section_classifier import ResumeSectionClassifier
import os
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Reprocessor")

DATABASE_URL = "postgresql://interview_user:interview_password@interview_postgres:5432/interview_db"
engine = create_engine(DATABASE_URL)

def reprocess_existing_chunks():
    """기존 청크들에 section_type을 부여함"""
    with Session(engine) as session:
        statement = select(ResumeChunk)
        chunks = session.exec(statement).all()
        
        logger.info(f"🔄 총 {len(chunks)}개의 청크를 재분류합니다...")
        
        updated_count = 0
        for chunk in chunks:
            if not chunk.section_type:
                new_type = ResumeSectionClassifier.classify_chunk(chunk.content, chunk.chunk_index)
                chunk.section_type = new_type
                session.add(chunk)
                updated_count += 1
        
        session.commit()
        logger.info(f"✅ {updated_count}개의 청크가 성공적으로 재분류되었습니다.")

if __name__ == "__main__":
    reprocess_existing_chunks()
