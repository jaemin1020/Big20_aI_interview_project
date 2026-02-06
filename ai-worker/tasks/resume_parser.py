"""
이력서 PDF 파싱 Celery Task
"""
from celery import shared_task
from sqlmodel import Session
from db import Resume, engine
from utils.pdf_parser import ResumePDFParser
# from utils.resume_structurer import ResumeStructurer  # 사용 안 함 (LLM 의존성 제거)
from utils.vector_utils import get_embedding_generator
from utils.section_classifier import ResumeSectionClassifier
from datetime import datetime
import logging
import os
import re

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
        
        # 3. 이력서 섹션 분할 (Phase_2.md 매핑 규칙 적용)
        logger.info(f"[Resume {resume_id}] 키워드 기반 섹션 분할 중...")
        try:
            from utils.section_splitter import SectionSplitter
            # LLM 없이 원문을 키워드 기준으로 잘라냅니다. (원본 보존)
            segments = SectionSplitter.split_by_sections(cleaned_text)
            logger.info(f"[Resume {resume_id}] {len(segments)}개 섹션으로 분리 완료")
        except Exception as e:
            logger.error(f"[Resume {resume_id}] 섹션 분할 실패: {e}")
            segments = [{"section_type": "skill_cert", "content": cleaned_text}]
        
        # 4. 각 섹션 내에서 너무 긴 경우 추가 청킹 (500자 단위)
        logger.info(f"[Resume {resume_id}] 최종 청킹 중...")
        final_chunks = []
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            for segment in segments:
                sub_chunks = text_splitter.split_text(segment["content"])
                for sub in sub_chunks:
                    final_chunks.append({
                        "section_type": segment["section_type"],
                        "content": sub
                    })
            logger.info(f"[Resume {resume_id}] 최종 {len(final_chunks)}개 청크 준비 완료")
            
        except Exception as e:
            logger.error(f"[Resume {resume_id}] 청킹 실패: {e}")
            final_chunks = [{"section_type": "skill_cert", "content": cleaned_text}]
        
        # 5. 각 청크를 임베딩하여 ResumeChunk 테이블에 저장 (RAG 검색용)
        logger.info(f"[Resume {resume_id}] 청크 임베딩 생성 및 저장 중...")
        processed_chunks_info = []
        try:
            from db import ResumeChunk
            # 임베딩 생성기 활성화
            generator = get_embedding_generator()
            
            with Session(engine) as session:
                for idx, chunk_data in enumerate(final_chunks):
                    content = chunk_data["content"]
                    stype = chunk_data["section_type"]
                    
                    # 진짜 임베딩 생성 (1024차원)
                    chunk_embedding = generator.encode_passage(content)
                    
                    chunk_record = ResumeChunk(
                        resume_id=resume_id,
                        content=content,
                        chunk_index=idx,
                        section_type=stype,
                        embedding=chunk_embedding
                    )
                    session.add(chunk_record)
                    
                    processed_chunks_info.append({
                        "index": idx,
                        "section_type": stype,
                        "length": len(content)
                    })
                
                session.commit()
            logger.info(f"[Resume {resume_id}] 모든 청크 임베딩 및 저장 완료")
            
        except Exception as e:
            logger.error(f"[Resume {resume_id}] 청크 저장/임베딩 중 에러: {e}", exc_info=True)
        
        # 6. Resume 메타데이터 업데이트 (지원 정보 추출 및 그룹 명세 포함)
        logger.info(f"[Resume {resume_id}] Resume 메타데이터 업데이트 중...")
        
        target_company = "Unknown"
        target_position = "Unknown"
        for seg in segments:
            if seg["section_type"] == "target_info":
                content = seg["content"]
                comp_match = re.search(r'(?:지원\s*회사|회사명|기업명)\s*[:：]\s*([가-힣\w\s]+)', content)
                pos_match = re.search(r'(?:지원\s*직무|직군|포지션)\s*[:：]\s*([가-힣\w\s]+)', content)
                
                if comp_match: target_company = comp_match.group(1).strip()
                if pos_match: target_position = pos_match.group(1).strip()
                break

        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            resume.extracted_text = cleaned_text
            
            # 사용자 요구사항 매핑 명세 저장
            resume.structured_data = {
                "target_company": target_company,
                "target_position": target_position,
                "mapping_rules": {
                    "technical_questions": ["target_info(position)", "skill_cert", "career_project", "education"],
                    "behavioral_questions": ["target_info(company)", "cover_letter"]
                },
                "segments_count": len(segments),
                "note": "Raw content preserved via SectionSplitter"
            }
            resume.processed_at = datetime.utcnow()
            resume.processing_status = "completed"
            session.add(resume)
            session.commit()
            logger.info(f"[Resume {resume_id}] 업데이트 완료: {target_company} / {target_position} 타겟팅됨")
        
        return {
            "status": "success",
            "resume_id": resume_id,
            "text_length": len(cleaned_text),
            "chunks_count": len(final_chunks),
            "chunks_detail": processed_chunks_info
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
        except Exception as db_error:
            logger.error(f"Failed to update resume status to 'failed': {db_error}")
        
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
