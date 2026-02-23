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
            "major": "컴퓨터공학",
            "email": "...",
            "phone": "..."
        }
    """
    try:
        # Resume 모델 임포트 (순환 참조 방지를 위해 함수 내부에서 임포트)
        from db_models import Resume
        
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        
        if not resume or not resume.structured_data:
            logger.warning(f"Resume {resume_id} not found or has no structured_data")
            return {
                "candidate_name": "지원자",
                "target_role": "해당 직무",
                "major": "",
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
        
        # 교육 정보에서 전공 추출
        major = ""
        education = data.get("education", [])
        if education and isinstance(education, list):
            # [수정] education[0]은 PDF 표의 헤더 행일 수 있으므로
            # major가 실제로 채워진 첫 번째 항목을 찾습니다.
            major = next((e.get("major", "") for e in education if e.get("major", "").strip()), "")
        
        # [추가] 3, 5, 7번 템플릿을 위한 상세 정보 추출
        certs = data.get("certifications", [])
        cert_names = [c.get("title") or c.get("name") for c in certs if (c.get("title") or c.get("name"))]
        cert_list = ", ".join(cert_names) if cert_names else "관련 자격"

        act_org, act_role = "관련 기관", "담당 업무"
        acts = data.get("activities", [])
        act_header_kws = ["기간", "역할", "기관", "소속", "장소", "제목", "내용"]
        for act in acts:
            tmp_org = act.get("organization") or act.get("name") or ""
            tmp_role = act.get("role") or act.get("position") or ""
            if not any(kw in tmp_org for kw in act_header_kws) and not any(kw in tmp_role for kw in act_header_kws):
                act_org = tmp_org or act_org
                act_role = tmp_role or act_role
                break

        proj_org, proj_name = "해당 기관", "수행한 프로젝트"
        projs = data.get("projects", [])
        proj_header_kws = ["기간", "제목", "과정명", "기관", "설명", "내용"]
        for proj in projs:
            tmp_name = proj.get("title") or proj.get("name") or ""
            tmp_org = proj.get("organization") or ""
            if not any(kw in tmp_name for kw in proj_header_kws) and not any(kw in tmp_org for kw in proj_header_kws):
                proj_name = tmp_name or proj_name
                proj_org = tmp_org or proj_org
                break

        return {
            "candidate_name": header.get("name", "지원자"),
            "target_role": header.get("target_role", "해당 직무"),
            "company_name": header.get("target_company") or header.get("company") or "저희 회사",
            "major": major,
            "email": header.get("email", ""),
            "phone": header.get("phone", ""),
            "cert_list": cert_list,
            "act_org": act_org,
            "act_role": act_role,
            "proj_org": proj_org,
            "proj_name": proj_name
        }
        
    except Exception as e:
        logger.error(f"Error getting candidate info for resume {resume_id}: {e}")
        return {
            "candidate_name": "지원자",
            "target_role": "해당 직무",
            "major": "",
            "email": "",
            "phone": ""
        }


def check_if_transition(major: str, target_role: str) -> bool:
    """
    지원 직무와 전공을 비교하여 '직무 전환자/비전공자' 여부를 판단합니다.
    """
    if not major or not target_role:
        return False
    
    # 1. 기술(IT) 직무 키워드
    tech_role_keywords = ['개발', '엔지니어', '프로그래머', 'IT', 'SW', '소프트웨어', '데이터', '인공지능', 'AI', '보안', '시스템']
    # 2. 기술(IT) 전공 키워드 (이공계 핵심)
    tech_major_keywords = ['컴퓨터', '소프트웨어', '정보통신', '전기', '전자', 'IT', '데이터', '인공지능', 'AI', '수학', '통계', '산업공학']
    
    # 지원 직무가 IT 관련인지 확인
    is_tech_role = any(kw in target_role for kw in tech_role_keywords)
    # 전공이 IT 관련인지 확인
    is_tech_major = any(kw in major for kw in tech_major_keywords)
    
    # [결론] 직무는 IT인데, 전공이 IT가 아니라면 '전환자'로 판단!
    if is_tech_role and not is_tech_major:
        return True
        
    return False


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