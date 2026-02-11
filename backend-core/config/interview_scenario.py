
# 면접 단계 정의 및 가이드라인
# 이 파일은 질문 생성 및 단계 관리를 위한 핵심 설정을 담고 있습니다.

INTERVIEW_STAGES = [
    {
        "order": 1,
        "stage": "intro",
        "type": "template",
        "template": "{candidate_name}님, 반갑습니다. 먼저 간단하게 자기소개 부탁드립니다.",
        "guide": "지원자의 전반적인 인상과 자신감을 파악합니다."
    },
    {
        "order": 2,
        "stage": "motivation",
        "type": "template",
        "template": "본 직무({target_role})에 지원하시게 된 동기는 무엇인가요?",
        "guide": "지원자의 지원 동기와 직무에 대한 관심도를 확인합니다."
    },
    {
        "order": 3,
        "stage": "skill",
        "type": "ai",
        "category": "technical",
        "query_template": "{target_role} 기술 역량 및 보유 스킬",
        "guide": "공고 및 이력서에 명시된 기술적 역량을 검증합니다."
    },
    {
        "order": 4,
        "stage": "experience",
        "type": "ai",
        "category": "project",
        "query_template": "주요 프로젝트 성과 및 경험",
        "guide": "실제 프로젝트 경험을 통해 문제 해결 능력을 확인합니다."
    },
    {
        "order": 5,
        "stage": "problem_solving",
        "type": "ai",
        "category": "problem_solving",
        "query_template": "어려움 극복 사례 및 협업 경험",
        "guide": "위기 상황 대처 능력과 소프트 스킬을 평가합니다."
    },
    {
        "order": 6,
        "stage": "final",
        "type": "template",
        "template": "마지막으로 하시고 싶은 말씀이나 궁금한 점이 있으신가요?",
        "guide": "면접을 마무리하며 추가적인 정보를 얻습니다."
    }
]

def get_initial_stages():
    """면접 시작 시 생성할 템플릿 스테이지 반환 (1, 2단계)"""
    return [s for s in INTERVIEW_STAGES if s["order"] <= 2]

def get_stage_by_name(stage_name):
    """스테이지 이름으로 설정 조회"""
    for s in INTERVIEW_STAGES:
        if s["stage"] == stage_name:
            return s
    return None

def get_next_stage(current_stage_name):
    """현재 단계의 다음 단계 정보 반환"""
    current_stage = get_stage_by_name(current_stage_name)
    if not current_stage:
        return INTERVIEW_STAGES[0]
    
    next_order = current_stage["order"] + 1
    for s in INTERVIEW_STAGES:
        if s["order"] == next_order:
            return s
    return None
