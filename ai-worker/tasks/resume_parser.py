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

# LangChain for text splitting
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
            structured_data = structurer.structure_with_rules(cleaned_text)
            logger.info(f"[Resume {resume_id}] 구조화 완료")
        except Exception as e:
            logger.error(f"[Resume {resume_id}] 구조화 실패: {e}")
            structured_data = {}
        
        # 4. LangChain을 이용한 텍스트 청킹 (RAG 구조)
        logger.info(f"[Resume {resume_id}] 텍스트 청킹 중...")
        try:
            # RecursiveCharacterTextSplitter 설정
            # chunk_size: 약 1500자 (KURE-v1은 8192 토큰까지 지원하므로 여유있게)
            # chunk_overlap: 300자 (약 20% 중첩으로 문맥 유지)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1500,
                chunk_overlap=300,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            chunks = text_splitter.split_text(cleaned_text)
            logger.info(f"[Resume {resume_id}] 텍스트를 {len(chunks)}개 청크로 분할 완료")
            
        except Exception as e:
            logger.error(f"[Resume {resume_id}] 텍스트 청킹 실패: {e}")
            # 실패 시 전체 텍스트를 하나의 청크로 처리
            chunks = [cleaned_text[:2000]]
        
        # 5. 각 청크를 임베딩하여 ResumeChunk 테이블에 저장
        logger.info(f"[Resume {resume_id}] 청크 임베딩 생성 및 저장 중...")
        try:
            # ResumeChunk 모델 임포트 (동적 임포트로 순환 참조 방지)
            from db import ResumeChunk
            
            generator = get_embedding_generator()
            
            for idx, chunk_text in enumerate(chunks):
                # 각 청크를 임베딩
                chunk_embedding = generator.encode_passage(chunk_text)
                
                # ResumeChunk 레코드 생성
                chunk_record = ResumeChunk(
                    resume_id=resume_id,
                    content=chunk_text,
                    chunk_index=idx,
                    embedding=chunk_embedding
                )
                
                with Session(engine) as session:
                    session.add(chunk_record)
                    session.commit()
                
                logger.info(f"[Resume {resume_id}] 청크 {idx+1}/{len(chunks)} 저장 완료 (길이: {len(chunk_text)}자)")
            
            logger.info(f"[Resume {resume_id}] 모든 청크 임베딩 완료: {len(chunks)}개")
            
        except Exception as e:
            logger.error(f"[Resume {resume_id}] 청크 임베딩 생성 실패: {e}", exc_info=True)
        
        # 6. Resume 메타데이터 업데이트 (embedding은 ResumeChunk에 저장됨)
        logger.info(f"[Resume {resume_id}] Resume 메타데이터 업데이트 중...")
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            resume.extracted_text = cleaned_text
            resume.structured_data = structured_data
            # embedding 필드는 이제 사용하지 않음 (ResumeChunk에 저장)
            resume.embedding = None
            resume.processed_at = datetime.utcnow()
            resume.processing_status = "completed"
            session.add(resume)
            session.commit()
            logger.info(f"[Resume {resume_id}] Resume 메타데이터 업데이트 완료")
        
        return {
            "status": "success",
            "resume_id": resume_id,
            "text_length": len(cleaned_text),
            "structured_fields": list(structured_data.keys()),
            "chunks_count": len(chunks)
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
