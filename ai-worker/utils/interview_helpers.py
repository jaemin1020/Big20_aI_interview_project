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
