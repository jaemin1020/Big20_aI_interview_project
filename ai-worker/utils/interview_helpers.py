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
    기준: 지원 직무의 핵심 키워드가 전공명에 포함되어 있지 않으면 전환자로 간주합니다.
    """
    if not major or not target_role:
        return True # 정보가 없으면 보수적으로 전환자 시나리오 적용
        
    # 직무별 핵심 키워드 맵핑 (직무에 이 단어가 있으면 전공에도 관련 단어가 있어야 함)
    role_to_major_keywords = {
        "보안": ["보안", "정보보호", "해킹", ],
        "데이터": ["데이터", "통계", "수학", "계산",],
        "개발": ["컴퓨터", "소프트웨어", "공학", "전산", "IT", "정보", "웹", "앱", "SW", "프로그래밍"],
        "분석": ["데이터", "통계", "수학",],
        "AI": ["인공지능", "컴퓨터", "소프트웨어", "지능"],
        "엔지니어": ["컴퓨터", "소프트웨어", "시스템", "IT"]
    }

    # 1. 현재 지원 직무에서 어떤 핵심 키워드군에 속하는지 확인
    relevant_major_keywords = set()
    for role_key, major_keys in role_to_major_keywords.items():
        if role_key.lower() in target_role.lower():
            relevant_major_keywords.update(major_keys)

    # 2. 만약 직무 키워드를 찾았다면, 전공에 해당 관련 단어가 있는지 확인
    if relevant_major_keywords:
        is_major_match = any(mk.lower() in major.lower() for mk in relevant_major_keywords)
        if not is_major_match:
            logger.info(f"Transition Detected: Role '{target_role}' requires keywords {relevant_major_keywords}, but Major is '{major}'")
            return True
        else:
            logger.info(f"Major Match: '{major}' is considered relevant for Role '{target_role}'")
            return False

    # 3. 매칭되는 직무 키워드가 없는 경우 (기본 기술직군 체크)
    tech_keywords = ["컴퓨터", "소프트웨어", "전산", "IT", "플랫폼", "인공지능", "정보"]
    is_tech_major = any(kw.lower() in major.lower() for kw in tech_keywords)
    
    if not is_tech_major:
        return True
        
    return False
