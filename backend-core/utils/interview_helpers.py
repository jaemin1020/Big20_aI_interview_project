# -*- coding: utf-8 -*-
"""
면접 관련 헬퍼 함수들 (Backend-Core & AI-Worker 공유)
"""
import json
import logging
import os
import sys
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

def get_candidate_info(db_or_data, resume_id: Optional[int] = None) -> Dict[str, Any]:
    """
    지원자 정보 추출 (DB 세션 또는 구조화된 JSON 데이터 대응)
    """
    if resume_id is not None:
        # DB에서 조회하는 방식 (Backend-Core용)
        try:
            from sqlalchemy.orm import Session
            if isinstance(db_or_data, Session):
                # Resume 모델 임포트 (순환 참조 방지 및 경로 호환성)
                try:
                    from db_models import Resume
                except ImportError:
                    # ai-worker 환경에서 호출 시 backend-core 경로 추가
                    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend-core"))
                    if backend_path not in sys.path:
                        sys.path.append(backend_path)
                    from db_models import Resume
                
                resume = db_or_data.query(Resume).filter(Resume.id == resume_id).first()
                if not resume or not resume.structured_data:
                    return _get_default_info()
                
                data = resume.structured_data
                if isinstance(data, str):
                    data = json.loads(data)
                return _extract_from_dict(data)
        except Exception as e:
            logger.error(f"Error getting candidate info from DB: {e}")
            return _get_default_info()
    
    # 구조화된 데이터(dict)에서 직접 추출하는 방식 (AI-Worker용)
    return _extract_from_dict(db_or_data)

def _get_default_info():
    return {
        "candidate_name": "지원자",
        "target_role": "해당 직무",
        "major": "",
        "email": "",
        "phone": "",
        "cert_list": "관련 자격",
        "act_org": "관련 기관",
        "act_role": "담당 업무",
        "proj_org": "해당 기관",
        "proj_name": "수행한 프로젝트"
    }

def _extract_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return _get_default_info()
        
    header = data.get("header", {})
    
    # 교육 정보에서 전공 추출
    major = ""
    education = data.get("education", [])
    if education and isinstance(education, list):
        major = next((e.get("major", "") for e in education if e.get("major", "").strip()), "")
    
    # 상세 정보 추출
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
        "candidate_name": header.get("name") or header.get("candidate_name") or "지원자",
        "target_role": header.get("target_role") or header.get("target_position") or data.get("position") or "해당 직무",
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

def check_if_transition(major: str, target_role: str) -> bool:
    """
    지원자의 전공과 지원 직무를 비교하여 '직무 전환(비전공자)' 여부를 판별합니다.
    기준: 지원 직무의 핵심 카테고리에 해당하는 관련 전공 키워드가 전공명에 포함되어 있지 않으면 전환자로 간주합니다.
    """
    if not major or not target_role:
        return False
        
    # 지원 직무 키워드군
    role_keywords = {
        "sw_dev": ['개발', '프로그래머', '소프트웨어', 'SW', '웹', '앱', '인터페이스', '프론트엔드', '백엔드', '플랫폼'],
        "ai_data": ['데이터', '인공지능', 'AI', '머신러닝', '딥러닝', '분석', '통계'],
        "security": ['보안', '해킹', '정보보호', '네트워크', '인프라'],
        "generic_tech": ['엔지니어', 'IT', '시스템', '기술']
    }
    
    # 해당 직무에 대응하는 '관련 전공' 키워드군 (전자/전기/산공 등은 SW직군에서는 전환자로 분류되도록 조정)
    major_keywords = {
        "sw_dev": ['컴퓨터', '소프트웨어', '전산', '정보통신', 'IT', '컴공'],
        "ai_data": ['컴퓨터', '데이터', '인공지능', 'AI', '통계', '수학', '소프트웨어'],
        "security": ['보안', '정보보호', '컴퓨터', '네트워크', '해킹'],
        "generic_tech": ['컴퓨터', '소프트웨어', '전산', 'IT', '정보통신', '전기', '전자', '제어', '시스템', '공학']
    }
    
    target_role_lower = target_role.lower()
    major_lower = major.lower()
    
    # 1. 지원 직무가 어느 카테고리에 속하는지 파악
    relevant_categories = []
    for cat, keywords in role_keywords.items():
        if any(kw in target_role_lower for kw in keywords):
            relevant_categories.append(cat)
            
    if not relevant_categories:
        # 매칭되는 직무가 없으면 기본 기술 전공 체크 (보수적)
        tech_major = ['컴퓨터', '소프트웨어', '전산', 'IT', '정보통신']
        return not any(kw in major_lower for kw in tech_major)

    # 2. 관련 카테고리의 전공 키워드가 전공명에 포함되는지 확인
    for cat in relevant_categories:
        if any(mk in major_lower for mk in major_keywords[cat]):
            logger.info(f"✅ Major Match: '{major}' is relevant for Role '{target_role}' (Category: {cat})")
            return False # 하나라도 매칭되면 전공자로 인정
            
    logger.info(f"✨ Transition Detected: Role '{target_role}' vs Major '{major}'")
    return True # 매칭되는 관련 전공 키워드가 없으면 전환자로 판단

def generate_template_question(template: str, variables: Dict[str, Any]) -> str:
    """
    템플릿 문자열에 변수 삽입
    """
    try:
        return template.format(**variables)
    except KeyError as e:
        logger.error(f"Missing variable in template: {e}")
        return template
    except Exception as e:
        logger.error(f"Error formatting template: {e}")
        return template

def get_next_stage_name(current_stage: str, is_transition: bool = False) -> Optional[str]:
    """
    현재 단계의 다음 단계 이름 반환
    """
    try:
        # 시나리오 파일 경로 동적 파악
        base_dir = os.path.dirname(__file__)
        config_dirs = [
            os.path.abspath(os.path.join(base_dir, "..", "config")),
            os.path.abspath(os.path.join(base_dir, "..", "..", "ai-worker", "config")),
            os.path.abspath(os.path.join(base_dir, "..", "..", "backend-core", "config"))
        ]
        
        for cdir in config_dirs:
            if cdir not in sys.path:
                sys.path.append(cdir)
        
        if is_transition:
            from interview_scenario_transition import get_next_stage
        else:
            from interview_scenario import get_next_stage
        
        next_stage = get_next_stage(current_stage)
        return next_stage["stage"] if next_stage else None
        
    except Exception as e:
        logger.error(f"Error getting next stage for {current_stage}: {e}")
        return None