
import logging
import os
import json
from celery import shared_task, current_app
from sqlmodel import Session
from db import engine
from models import Resume
from .parse_resume import parse_resume_final

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="parse_resume_pdf", queue='cpu_queue')
def parse_resume_pdf(self, resume_id: int, file_path: str):
    """
    이력서 PDF 파일을 파싱하여 구조화된 데이터를 DB에 저장하고, 임베딩 생성을 요청합니다.
    """
    logger.info(f"Starting resume parsing for ID: {resume_id}, File: {file_path}")
    
    try:
        # 1. 파일 존재 확인
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            _update_status(resume_id, "failed")
            return
            
        # 2. 파싱 실행
        parsed_data = parse_resume_final(file_path)
        logger.info(f"Parsed data header: {parsed_data.get('header')}")
        
        # 3. DB 업데이트
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if not resume:
                logger.error(f"Resume {resume_id} not found in DB")
                return

            resume.structured_data = parsed_data
            
            # Position 추출 및 저장
            target_pos = parsed_data.get("header", {}).get("target_role")
            if target_pos:
                resume.target_position = target_pos
                
            # 텍스트 추출 (임베딩을 위해 단순화된 텍스트 저장)
            # 실제로는 parse_resume_final에서 원본 텍스트를 반환받는 게 좋지만,
            # 현재 구조상 JSON 덤프를 텍스트로 사용하거나, 추후 개선 필요.
            resume.extracted_text = json.dumps(parsed_data, ensure_ascii=False)
            
            # 상태 업데이트: 파싱 완료 -> 임베딩 대기
            resume.processing_status = "processing" 
            session.add(resume)
            session.commit()
            
        # 4. 임베딩 태스크 호출
        current_app.send_task(
            "generate_resume_embeddings",
            args=[resume_id],
            queue='gpu_queue'
        )
        logger.info(f"Sent embedding generation task for resume {resume_id}")

    except Exception as e:
        logger.error(f"Error parsing resume {resume_id}: {e}", exc_info=True)
        _update_status(resume_id, "failed")

def _update_status(resume_id: int, status: str):
    with Session(engine) as session:
        resume = session.get(Resume, resume_id)
        if resume:
            resume.processing_status = status
            session.add(resume)
            session.commit()
