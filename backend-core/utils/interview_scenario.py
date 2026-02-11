# -*- coding: utf-8 -*-
"""
면접 시나리오 설정 파일
실시간 대화형 면접의 전체 흐름을 정의합니다.
"""

INTERVIEW_STAGES = [
    # 1. 자기소개 (템플릿 - 즉시)
    {
        "stage": "intro",
        "type": "template",
        "template": "{candidate_name} 지원자님, 간단히 자기소개 부탁드립니다.",
        "variables": ["candidate_name"],
        "order": 1
    },
    
    # 2. 지원동기 (템플릿 - 즉시)
    {
        "stage": "motivation",
        "type": "template",
        "template": "{candidate_name} 지원자님, 지원하신 직무인 '{target_role}'에 지원하게 된 동기는 무엇입니까?",
        "variables": ["candidate_name", "target_role"],
        "order": 2
    },
    
    # 3. 직무 지식 평가 (AI 생성)
    {
        "stage": "skill",
        "type": "ai",
        "category": "certification",
        "query_template": "{target_role} 기술 스킬 도구 활용 능력",
        "guide": "지원자가 사용한 기술의 구체적인 설정법이나 기술적 원리를 물어볼 것.",
        "order": 3
    },
    
    # 4. 직무 지식 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "skill_followup",
        "type": "followup",
        "parent": "skill",
        "guide": "이전 답변에서 부족하거나 모호한 부분을 구체적으로 파고들 것.",
        "order": 4
    },
    
    # 5. 직무 경험 평가 (AI 생성)
    {
        "stage": "experience",
        "type": "ai",
        "category": "project",
        "query_template": "프로젝트 성과 달성 경험 결과",
        "guide": "프로젝트에서 달성한 구체적인 역할과 기여도를 물어볼 것.",
        "order": 5
    },
    
    # 6. 직무 경험 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "experience_followup",
        "type": "followup",
        "parent": "experience",
        "guide": "프로젝트 경험에서 구체적인 수치나 기술적 디테일을 추가로 물어볼 것.",
        "order": 6
    },
    
    # 7. 문제 해결 능력 평가 (AI 생성)
    {
        "stage": "problem_solving",
        "type": "ai",
        "category": None,  # 전체 검색
        "query_template": "문제 해결 기술적 난관 극복",
        "guide": "어려운 상황을 만났을 때 어떤 논리적 단계를 거쳐 해결했는지 물어볼 것.",
        "order": 7
    },
    
    # 8. 문제 해결 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "problem_solving_followup",
        "type": "followup",
        "parent": "problem_solving",
        "guide": "문제 해결 과정에서의 의사결정 근거나 대안 검토 과정을 물어볼 것.",
        "order": 8
    },
    
    # 9. 의사소통 및 협업 평가 (AI 생성)
    {
        "stage": "communication",
        "type": "ai",
        "category": "narrative",
        "query_template": "협업 갈등 해결 설득",
        "guide": "팀 내 의견 대립 시 어떻게 조율하고 성과를 냈는지 물어볼 것.",
        "order": 9
    },
    
    # 10. 의사소통 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "communication_followup",
        "type": "followup",
        "parent": "communication",
        "guide": "협업 과정에서 사용한 구체적인 커뮤니케이션 기법이나 도구를 물어볼 것.",
        "order": 10
    },
    
    # 11. 책임감 및 가치관 평가 (AI 생성)
    {
        "stage": "responsibility",
        "type": "ai",
        "category": "narrative",
        "query_template": "직업 윤리 목표 가치관",
        "guide": "전문가로서의 윤리 의식과 책임감 있는 태도를 물어볼 것.",
        "order": 11
    },
    
    # 12. 책임감 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "responsibility_followup",
        "type": "followup",
        "parent": "responsibility",
        "guide": "가치관이 실제 업무에서 어떻게 구현되었는지 구체적 사례를 물어볼 것.",
        "order": 12
    },
    
    # 13. 성장의지 평가 (AI 생성)
    {
        "stage": "growth",
        "type": "ai",
        "category": "narrative",
        "query_template": "성장 계획 자기계발 미래",
        "guide": "현재 기술 트렌드 변화에 맞춰 구체적으로 어떤 학습을 하고 있는지 물어볼 것.",
        "order": 13
    },
    
    # 14. 성장의지 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "growth_followup",
        "type": "followup",
        "parent": "growth",
        "guide": "학습 계획의 구체적인 실행 방법이나 타임라인을 물어볼 것.",
        "order": 14
    },
    
    # 15. 최종 발언 (템플릿 - 즉시)
    {
        "stage": "final_statement",
        "type": "template",
        "template": "{candidate_name} 지원자님, 마지막으로 하고 싶으신 말씀이 있으신가요?",
        "variables": ["candidate_name"],
        "order": 15
    }
]


def get_stage_by_name(stage_name: str):
    """
    단계 이름으로 설정 조회
    """
    for stage in INTERVIEW_STAGES:
        if stage["stage"] == stage_name:
            return stage
    return None


def get_next_stage(current_stage: str):
    """
    현재 단계의 다음 단계 반환
    """
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
    """
    면접 시작 시 즉시 제공할 템플릿 질문들 (자기소개, 지원동기)
    """
    return [stage for stage in INTERVIEW_STAGES if stage["type"] == "template" and stage["order"] <= 2]
