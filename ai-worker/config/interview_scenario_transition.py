# -*- coding: utf-8 -*-
"""
직무 전환자 및 비전공자 특화 면접 시나리오 설정 파일
이전 경력/전공과 현재 지원 직무 간의 '공백'과 '연결고리'를 검증하는 데 집중합니다.
"""

INTERVIEW_STAGES = [
    # 1. 자기소개 및 전공-직무 매칭 질문 (템플릿)
    {
        "stage": "intro",
        "type": "template",
        "template": "{candidate_name} 지원자님, {major}를 전공하셨는데 어떤 계기로 {target_role} 분야에 관심을 갖게 되셨는지, 그 시작점을 포함해 자기소개 부탁드립니다.",
        "variables": ["candidate_name", "major", "target_role"],
        "order": 1
    },
    
    # 2. 전공 지식의 활용 가능성 (AI 생성)
    {
        "stage": "major_synergy",
        "type": "ai",
        "category": "narrative",
        "query_template": "전공 지식 직무 활용 시너지 인문학적 관점 기술 결합",
        "guide": "{major}라는 배경이 오히려 {target_role}로서 업무를 수행할 때 가질 수 있는 본인만의 독특한 강점이나 차별화된 시각은 무엇인지 질문하세요.",
        "order": 2
    },
    
    # 3. 전직/전환에 대한 확신 검증 (꼬리질문)
    {
        "stage": "conviction_check",
        "type": "followup",
        "parent": "major_synergy",
        "guide": "전공 분야로 돌아가지 않고 이 직무에서 장기적으로 성장할 수 있다는 확신을 보여준 구체적 증거(프로젝트, 학습량 등)를 요구하세요.",
        "order": 3
    },
    
    # 4. 독학 과정의 기술적 한계 돌파 (AI 생성)
    {
        "stage": "learning_grit",
        "type": "ai",
        "category": "skill",
        "query_template": "비전공자 기술 학습 난관 극복 독학 부트캠프",
        "guide": "비전공자로서 {target_role} 기술을 습득하며 느꼈던 가장 큰 벽은 무엇이었고, 이를 '전공자가 아닌 본인만의 방식'으로 어떻게 극복했는지 질문하세요.",
        "order": 4
    },
    
    # 5. 기술적 깊이 검증 (꼬리질문)
    {
        "stage": "technical_followup",
        "type": "followup",
        "parent": "learning_grit",
        "guide": "방금 답변한 해결책에서 사용한 기술의 원리를 더 깊게(예: CS 기초 지식 등) 파고들어 학습 비전공자의 '학습 깊이'를 테스트하세요.",
        "order": 5
    },
    
    # 6. 협업 및 커뮤니케이션 (AI 생성)
    {
        "stage": "collaboration",
        "type": "ai",
        "category": "narrative",
        "query_template": "협업 방식 갈등 해결 소통 노하우 비전공자 관점",
        "guide": "이전 배경(전공/경력)에서의 협업 스타일과 현재 {target_role} 정체성 사이의 조화 방안을 묻고, 본인만의 독특한 소통 방식이 팀에 줄 수 있는 이점을 검증하세요.",
        "order": 6
    },
    
    # 7. 협업 꼬리질문 (AI 생성)
    {
        "stage": "collaboration_followup",
        "type": "followup",
        "parent": "collaboration",
        "guide": "기술적 이해도가 다른 팀원(예: 전공자 또는 비기술직군)과의 의견 충돌 시 이를 어떻게 논리적으로 설득할 것인지 구체적 상황을 가정해 질문하세요.",
        "order": 7
    },
    
    # 8. 마지막 발언 (템플릿)
    {
        "stage": "final_statement",
        "type": "template",
        "template": "{major}라는 기초 위에 {target_role}이라는 기술을 쌓아 올린 과정이 인상 깊었습니다. 마지막으로 포부 한 말씀 부탁드립니다.",
        "variables": ["candidate_name", "major", "target_role"],
        "order": 8
    }
]

def get_stage_by_name(stage_name: str):
    for stage in INTERVIEW_STAGES:
        if stage["stage"] == stage_name:
            return stage
    return None

def get_next_stage(current_stage: str):
    current_order = None
    for stage in INTERVIEW_STAGES:
        if stage["stage"] == current_stage:
            current_order = stage["order"]
            break
    
    if current_order is None:
        return None
    
    for stage in INTERVIEW_STAGES:
        if stage["order"] == current_order + 1:
            return stage
    return None

def get_initial_stages():
    """면접 시작 시 제공할 초기 단계"""
    return [stage for stage in INTERVIEW_STAGES if stage["type"] == "template" and stage["order"] == 1]
