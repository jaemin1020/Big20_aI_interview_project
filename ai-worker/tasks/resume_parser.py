
import logging
import os
import json
from celery import shared_task, current_app
from sqlmodel import Session

logger = logging.getLogger(__name__)

try:
    from db_models import Resume
    from db import engine
except ImportError as e:
    logger.error(f"❌ Critical Import Error in resume_parser: {e}")
    
from .parse_resume import parse_resume_final

logger.info("✅ Task Module 'tasks.resume_pipeline' is being loaded.")

@shared_task(bind=True, name="tasks.resume_pipeline.process_resume_pipeline", queue='gpu_queue')
def parse_resume_pdf(self, resume_id: int, file_path: str):
    """
    이력서 PDF 파일을 파싱하여 구조화된 데이터를 DB에 저장하고, 임베딩 생성을 요청합니다.
    """
    # 1. 파일 경로 정규화 (컨테이너 환경에 맞게 조정)
    # 백엔드에서 온 로컬 경로나 상대 경로를 컨테이너 내부의 /app/uploads 경로로 강제 변환
    filename = os.path.basename(file_path)
    # /app/uploads는 docker-compose에서 마운트된 경로
    normalized_path = os.path.join("/app/uploads", filename)
    
    logger.info(f"🚀 [START] Resume parsing ID: {resume_id}")
    logger.info(f"Original path: {file_path}")
    logger.info(f"Normalized path: {normalized_path}")
    
    try:
        # 파일 존재 확인
        if not os.path.exists(normalized_path):
            logger.error(f"❌ File not found at normalized path: {normalized_path}")
            # 폴백: 원래 경로로 한 번 더 시도
            if os.path.exists(file_path):
                normalized_path = file_path
            else:
                _update_status(resume_id, "failed")
                return
            
        # 2. 파싱 실행
        logger.info(f"🔍 Parsing PDF...")
        parsed_data = parse_resume_final(normalized_path)
        logger.info(f"✅ Parsing Success: {parsed_data.get('header', {}).get('name')} detected")
        
        # 3. DB 업데이트
        with Session(engine) as session:
            resume = session.get(Resume, resume_id)
            if not resume:
                logger.error(f"❌ Resume {resume_id} not found in DB")
                return

            resume.structured_data = parsed_data
            target_pos = parsed_data.get("header", {}).get("target_role")
            if target_pos:
                resume.target_position = target_pos
                
            resume.extracted_text = json.dumps(parsed_data, ensure_ascii=False)
            resume.processing_status = "processing" 
            session.add(resume)
            session.commit()
            logger.info(f"💾 DB Updated for Resume {resume_id}")
            
        # 4. 임베딩 태스크 호출 (이름 명확화)
        current_app.send_task(
            "tasks.resume_embedding.generate_resume_embeddings",
            args=[resume_id],
            queue='gpu_queue'
        )
        logger.info(f"➡️ [NEXT] Sent embedding task for Resume {resume_id}")

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
