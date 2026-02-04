"""
이력서 PDF 파싱 Celery Task
"""
from celery import shared_task
from sqlmodel import Session
from db import Resume, engine
from utils.pdf_parser import ResumePDFParser
from utils.resume_structurer import ResumeStructurer
from utils.vector_utils import get_embedding_generator
from datetime import datetime
import logging
import os

logger = logging.getLogger("ResumeParserTask")


@shared_task(bind=True, name="parse_resume_pdf")
def parse_resume_pdf_task(self, resume_id: int, file_path: str):
    """
    이력서 PDF 파싱 및 구조화 Task
    
    Args:
        resume_id: Resume ID
        file_path: PDF 파일 경로
        
    Returns:
        dict: 파싱 결과
    """
    logger.info(f"[Task {self.request.id}] Resume {resume_id} 파싱 시작")
    
    try:
        # 1. Resume 레코드 조회
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if not resume:
                logger.error(f"Resume {resume_id} not found")
                return {"status": "error", "message": "Resume not found"}
            
            # 상태 업데이트: processing
            resume.processing_status = "processing"
            session.add(resume)
            session.commit()
        
        # 2. PDF 텍스트 추출
        logger.info(f"[Resume {resume_id}] PDF 텍스트 추출 중...")
        try:
            extracted_text = ResumePDFParser.extract_text(file_path)
            cleaned_text = ResumePDFParser.clean_text(extracted_text)
            logger.info(f"[Resume {resume_id}] 텍스트 추출 완료: {len(cleaned_text)} 글자")
        except Exception as e:
            logger.error(f"[Resume {resume_id}] PDF 추출 실패: {e}")
            with Session(engine) as session:
                resume = session.get(Resume, resume_id)
                resume.processing_status = "failed"
                session.add(resume)
                session.commit()
            return {"status": "error", "message": f"PDF extraction failed: {e}"}
        
        # 3. 이력서 구조화
        logger.info(f"[Resume {resume_id}] 이력서 구조화 중...")
        try:
            structurer = ResumeStructurer()  # LLM 없이 규칙 기반
            structured_data = structurer.structure_resume(cleaned_text)
            logger.info(f"[Resume {resume_id}] 구조화 완료")
        except Exception as e:
            logger.error(f"[Resume {resume_id}] 구조화 실패: {e}")
            structured_data = {}
        
        # 4. 임베딩 생성 (이력서 전체 내용)
        logger.info(f"[Resume {resume_id}] 임베딩 생성 중...")
        try:
            # 텍스트가 너무 길면 앞부분만 사용
            text_for_embedding = cleaned_text[:2000]
            
            # vector_utils의 싱글톤 생성기 사용 (KURE-v1, passage 모드)
            generator = get_embedding_generator()
            # 이력서는 검색 대상(Passage)이므로 encode_passage 사용 ("passage: " 접두어)
            embedding = generator.encode_passage(text_for_embedding)
            
            logger.info(f"[Resume {resume_id}] 임베딩 생성 완료: {len(embedding)} 차원")
        except Exception as e:
            logger.error(f"[Resume {resume_id}] 임베딩 생성 실패: {e}")
            embedding = None
        
        # 5. DB 업데이트
        logger.info(f"[Resume {resume_id}] DB 업데이트 중...")
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            resume.extracted_text = cleaned_text
            resume.structured_data = structured_data
            resume.embedding = embedding
            resume.processed_at = datetime.utcnow()
            resume.processing_status = "completed"
            session.add(resume)
            session.commit()
            logger.info(f"[Resume {resume_id}] DB 업데이트 완료")
        
        return {
            "status": "success",
            "resume_id": resume_id,
            "text_length": len(cleaned_text),
            "structured_fields": list(structured_data.keys()),
            "has_embedding": embedding is not None
        }
        
    except Exception as e:
        logger.error(f"[Resume {resume_id}] 치명적 에러: {e}", exc_info=True)
        
        # 상태 업데이트: failed
        try:
            with Session(engine) as session:
                resume = session.get(Resume, resume_id)
                if resume:
                    resume.processing_status = "failed"
                    session.add(resume)
                    session.commit()
        except:
            pass
        
        return {"status": "error", "message": str(e)}


@shared_task(name="reprocess_resume")
def reprocess_resume_task(resume_id: int):
    """
    이력서 재처리 Task
    
    Args:
        resume_id: Resume ID
    """
    logger.info(f"Resume {resume_id} 재처리 시작")
    
    with Session(engine) as session:
        resume = session.get(Resume, resume_id)
        if not resume:
            logger.error(f"Resume {resume_id} not found")
            return {"status": "error", "message": "Resume not found"}
        
        file_path = resume.file_path
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {"status": "error", "message": "File not found"}
    
    # 파싱 Task 실행
    return parse_resume_pdf_task(resume_id, file_path)


# 사용 예시
if __name__ == "__main__":
    # 테스트
    result = parse_resume_pdf_task(1, "path/to/resume.pdf")
    print(result)
