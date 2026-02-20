import json
import logging

logger = logging.getLogger("Interview-Helpers")

def get_candidate_info(structured_data):
    """
    이력서 분석 데이터(JSON)에서 성함과 지원 직무를 추출
    """
    if isinstance(structured_data, str):
        try:
            structured_data = json.loads(structured_data)
        except:
            structured_data = {}
            
    header = structured_data.get("header", {})
    
    # 1. 성함 추출
    candidate_name = header.get("name") or header.get("candidate_name") or "지원자"
    
    # 2. 직무 추출
    target_role = header.get("target_role") or header.get("target_position") or structured_data.get("position") or "보안 전문가"
    
    return {
        "candidate_name": candidate_name,
        "target_role": target_role
    }

def check_if_transition(major: str, target_role: str) -> bool:
    """
    지원자의 전공과 지원 직무를 비교하여 '직무 전환(비전공자)' 여부를 판별합니다.
    - major: 지원자 전공 (예: 국어국문학)
    - target_role: 지원 직무 (예: AI 개발자)
    """
    if not major:
        return False
        
    # IT/공학 계열 전공 키워드
    tech_keywords = [
        "컴퓨터", "소프트웨어", "공학", "전산", "IT", "플랫폼", "데이터", "통계", "수학", 
        "인공지능", "AI", "정보", "보안", "시스템", "전자", "전기", "통신", "임베디드",
        "디지털", "웹", "네트워크"
    ]
    
    # 전공에 기술 키워드가 포함되어 있는지 확인
    is_tech_major = any(kw.lower() in major.lower() for kw in tech_keywords)
    
    # 지원 직무가 기술직군인지 확인
    tech_roles = ["개발", "데이터", "분석", "AI", "보안", "엔지니어", "프로그래머", "기획", "디렉터", "운영"]
    is_tech_role = any(kw.lower() in target_role.lower() for kw in tech_roles)
    
    # 기술직군에 지원했는데 전공이 비전공이라면 '전환(Transition)' 시나리오 적용
    if is_tech_role and not is_tech_major:
        logger.info(f"Transition scenario detected: Major={major}, Role={target_role}")
        return True
        
    return False
