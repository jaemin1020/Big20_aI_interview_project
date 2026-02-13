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
        "category": None,
        "query_template": "{target_role} 기술 스킬 도구 활용 능력",
        "guide": "이력서 기술 키워드 1개 인용. 실무 적용 원리 검증.",
        "order": 3
    },
    
    # 4. 직무 지식 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "skill_followup",
        "type": "followup",
        "parent": "skill",
        "guide": "이전 답변 기술의 한계 및 예외 상황 검증.",
        "order": 4
    },
    
    # 5. 직무 경험 평가 (AI 생성)
    {
        "stage": "experience",
        "type": "ai",
        "category": None,
        "query_template": "프로젝트 성과 달성 경험 결과 활동 인턴 교육",
        "guide": "이력서 활동 2개 연결. 활동 간 인과관계 및 성장 분석.",
        "order": 5
    },
    
    # 6. 직무 경험 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "experience_followup",
        "type": "followup",
        "parent": "experience",
        "guide": "의사결정 근거 및 해결 논리 파악.",
        "order": 6
    },
    
    # 7. 문제 해결 능력 평가 (AI 생성)
    {
        "stage": "problem_solving",
        "type": "ai",
        "category": None,
        "query_template": "문제 해결 기술적 난관 극복",
        "guide": "고난도 프로젝트 인용. 제약 조건 및 극복 Action 질문.",
        "order": 7
    },
    
    # 8. 문제 해결 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "problem_solving_followup",
        "type": "followup",
        "parent": "problem_solving",
        "guide": "실패/돌발 변수 대처 및 사후 학습 확인.",
        "order": 8
    },
    
    # 9. 의사소통 및 협업 평가 (AI 생성)
    {
        "stage": "communication",
        "type": "ai",
        "category": "narrative",
        "query_template": "자기소개서 3번 의사소통 협업 갈등 해결 사례",
        "guide": "자소서 3번 인용. 조율 근거 및 객관적 데이터 확인.",
        "order": 9
    },
    
    # 10. 의사소통 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "communication_followup",
        "type": "followup",
        "parent": "communication",
        "guide": "반대 의견 설득 원칙 및 커뮤니케이션 스타일.",
        "order": 10
    },
    
    # 11. 책임감 및 가치관 평가 (AI 생성)
    {
        "stage": "responsibility",
        "type": "ai",
        "category": "narrative",
        "query_template": "자기소개서 1번 지원동기 보안 전문가 윤리의식 사명감",
        "guide": "자소서 1번 동기 인용. 윤리적 딜레마 상황 대처 질문.",
        "order": 11
    },
    
    # 12. 책임감 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "responsibility_followup",
        "type": "followup",
        "parent": "responsibility",
        "guide": "개인 신념과 조직 문화 충돌 시 조화 방안.",
        "order": 12
    },
    
    # 13. 성장의지 평가 (AI 생성)
    {
        "stage": "growth",
        "type": "ai",
        "category": "narrative",
        "query_template": "자기소개서 2번 기술 습득 과정 IDS 구축 시각화 자동화",
        "guide": "자소서 2번 문항 인용. 기술 트렌드 시너지 및 학습 계획.",
        "order": 13
    },
    
    # 14. 성장의지 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "growth_followup",
        "type": "followup",
        "parent": "growth",
        "guide": "최근 기술 한계 극복 시도 및 구체적 학습 활동.",
        "order": 14
    },
    
    # 15. 최종 발언 (템플릿 - 즉시)
    {
        "stage": "final_statement",
        "type": "template",
        "template": "{candidate_name} 지원자님, 지금까지 많은 답변 감사드립니다. 마지막으로 하고 싶으신 말씀이나 궁금한 점이 있으신가요?",
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
