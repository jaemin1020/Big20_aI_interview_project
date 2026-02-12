# -*- coding: utf-8 -*-
"""
면접 관련 헬퍼 함수들
"""
import json
import logging
from sqlalchemy.orm import Session
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_candidate_info(db: Session, resume_id: int) -> Dict[str, str]:
    """
    이력서 DB에서 지원자 정보 추출
    
    Args:
        db: 데이터베이스 세션
        resume_id: 이력서 ID
    
    Returns:
        {
            "candidate_name": "최승우",
            "target_role": "보안엔지니어",
            "email": "...",
            "phone": "..."
        }
    """
    try:
        # Resume 모델 임포트 (순환 참조 방지를 위해 함수 내부에서 임포트)
<<<<<<< HEAD
        from db_models import Resume
=======
        from models import Resume
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
        
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if not resume or not resume.structured_data:
            logger.warning(f"Resume {resume_id} not found or has no structured_data")
            return {
                "candidate_name": "지원자",
                "target_role": "해당 직무",
                "email": "",
                "phone": ""
            }
        
        # structured_data가 JSON 문자열인 경우 파싱
        if isinstance(resume.structured_data, str):
            try:
                data = json.loads(resume.structured_data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse structured_data for resume {resume_id}: {e}")
                return {
                    "candidate_name": "지원자",
                    "target_role": "해당 직무",
                    "email": "",
                    "phone": ""
                }
        else:
            data = resume.structured_data
        
        header = data.get("header", {})
        
        return {
            "candidate_name": header.get("name", "지원자"),
            "target_role": header.get("target_role", "해당 직무"),
            "email": header.get("email", ""),
            "phone": header.get("phone", "")
        }
        
    except Exception as e:
        logger.error(f"Error getting candidate info for resume {resume_id}: {e}")
        return {
            "candidate_name": "지원자",
            "target_role": "해당 직무",
            "email": "",
            "phone": ""
        }


def generate_template_question(template: str, variables: Dict[str, str]) -> str:
    """
    템플릿 문자열에 변수 삽입
    
    Args:
        template: "{candidate_name} 지원자님, ..."
        variables: {"candidate_name": "최승우", "target_role": "보안엔지니어"}
    
    Returns:
        "최승우 지원자님, ..."
    """
    try:
        return template.format(**variables)
    except KeyError as e:
        logger.error(f"Missing variable in template: {e}")
        return template
    except Exception as e:
        logger.error(f"Error formatting template: {e}")
        return template


def get_next_stage_name(current_stage: str) -> Optional[str]:
    """
    현재 단계의 다음 단계 이름 반환
    
    Args:
        current_stage: 현재 단계 이름 (예: "intro", "skill", ...)
    
    Returns:
        다음 단계 이름 또는 None (마지막 단계인 경우)
    """
    try:
        # 시나리오 파일에서 임포트
        import sys
        import os
        
        # ai-worker/config 경로 추가
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "ai-worker", "config")
        if config_path not in sys.path:
            sys.path.append(config_path)
        
        from interview_scenario import get_next_stage
        
        next_stage = get_next_stage(current_stage)
        return next_stage["stage"] if next_stage else None
        
    except Exception as e:
        logger.error(f"Error getting next stage for {current_stage}: {e}")
        return None
