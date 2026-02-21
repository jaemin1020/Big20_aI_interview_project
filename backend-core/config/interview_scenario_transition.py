# -*- coding: utf-8 -*-
"""
직무 전환자 및 비전공자 특화 면접 시나리오 설정 파일
이전 경력/전공과 현재 지원 직무 간의 '공백'과 '연결고리'를 검증하는 데 집중합니다.
"""

INTERVIEW_STAGES = [
    # 1. 자기소개 (템플릿)
    {
        "stage": "intro",
        "display_name": "기본 질문",
        "intro_sentence": "반갑습니다. 면접을 시작하기 위해 먼저 간단히 자기소개 부탁드립니다.",
        "type": "template",
        "template": "{candidate_name} 지원자님, 간단히 자기소개 부탁드립니다.",
        "variables": ["candidate_name", "major", "target_role"],
        "order": 1
    },

    # 2. 지원동기 (템플릿 - 즉시)
    {
        "stage": "motivation",
        "display_name": "기본 질문",
        "intro_sentence": "감사합니다. 이어서 지원하신 동기에 대해 들어보고 싶습니다.",
        "type": "template",
        "template": "{candidate_name} 지원자님, 지원하신 직무인 '{target_role}'에 지원하게 된 동기는 무엇입니까? 또한 {major}을 전공하셨는데 어떤 계기로 {target_role}에 관심을 갖게 되셨나요?",
        "variables": ["candidate_name", "target_role", "major"],
        "order": 2
    },

    # 3. 직무 지식 평가 (자격증/프로젝트 중심 템플릿)
    {
        "stage": "skill",
        "display_name": "직무지식질문",
        "type": "template",
        "template": "감사합니다. 다음은 직무지식관련 질문입니다. 이력서를 보니 프로젝트에 {course_name}을 하셨고 {cert_name}을 취득하셨네요. 이 과정에서 습득한 지식과 기술이 무엇인지 구체적으로 말해주세요.",
        "order": 3
    },

    # 4. 직무 지식 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "skill_followup",
        "display_name": "직무심층질문",
        "intro_sentence": "추가적으로 궁금한 게 있습니다.",
        "type": "followup",
        "parent": "skill",
        "guide": "지원자의 이전 답변을 '~라고 말씀해 주셨군요.'와 같이 한 문장으로 먼저 요약하십시오. 그 후 답변에서 언급된 구체적인 기술이나 방법론 중 하나를 콕 집어 그 이유나 상세 구현 방식을 묻는 심층 질문을 던지십시오.",
        "order": 4
    },

    # 5. 직무 경험 평가 (AI 생성)
    {
        "stage": "experience",
        "display_name": "실무경험질문",
        "intro_sentence": "다음은 실무경험질문입니다.",
        "type": "ai",
        "category": "behavioral",
        "query_template": "프로젝트 성과 달성 경험 결과 활동 인턴 교육",
        "guide": "이력서 활동 2개 연결. 활동 간 인과관계 및 성장 분석.",
        "order": 5
    },

    # 6. 직무 경험 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "experience_followup",
        "display_name": "실무심층질문",
        "intro_sentence": "추가적으로 궁금한 게 있습니다.",
        "type": "followup",
        "parent": "experience",
        "guide": "답변 중 흥미로운 지점을 요약하고, 당시 왜 그런 방식의 해결책을 선택했는지 혹은 더 나은 대안은 없었는지 비판적 사고력을 검증하는 질문을 하십시오.",
        "order": 6
    },

    # 7. 문제 해결 능력 평가 (AI 생성)
    {
        "stage": "problem_solving",
        "display_name": "문제해결질문",
        "intro_sentence": "다음은 문제해결질문입니다.",
        "type": "ai",
        "category": "situational",
        "query_template": "문제 해결 기술적 난관 극복",
        "guide": "고난도 프로젝트 인용. 제약 조건 및 극복 Action 질문.",
        "order": 7
    },

    # 8. 문제 해결 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "problem_solving_followup",
        "display_name": "문제해결심층",
        "intro_sentence": "추가적으로 궁금한 게 있습니다.",
        "type": "followup",
        "parent": "problem_solving",
        "guide": "실패/돌발 변수 대처 및 사후 학습 확인.",
        "order": 8
    },

    # 9. 의사소통 및 협업 평가 (AI 생성)
    {
        "stage": "communication",
        "display_name": "협업소통질문",
        "intro_sentence": "다음은 협업소통질문입니다.",
        "type": "ai",
        "category": "narrative",
        "query_template": "자기소개서 3번 의사소통 협업 갈등 해결 사례",
        "guide": "자소서 3번 인용. 조율 근거 및 객관적 데이터 확인.",
        "order": 9
    },

    # 10. 의사소통 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "communication_followup",
        "display_name": "협업소통심층",
        "intro_sentence": "추가적으로 궁금한 게 있습니다.",
        "type": "followup",
        "parent": "communication",
        "guide": "반대 의견 설득 원칙 및 커뮤니케이션 스타일.",
        "order": 10
    },

    # 11. 책임감 및 가치관 평가 (AI 생성)
    {
        "stage": "responsibility",
        "display_name": "가치관책임질문",
        "intro_sentence": "다음은 가치관책임질문입니다.",
        "type": "ai",
        "category": "narrative",
        "query_template": "자기소개서 1번 지원동기 보안 전문가 윤리의식 사명감",
        "guide": "자소서 1번 동기 인용. 윤리적 딜레마 상황 대처 질문.",
        "order": 11
    },

    # 12. 책임감 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "responsibility_followup",
        "display_name": "가치관책임심층",
        "intro_sentence": "추가적으로 궁금한 게 있습니다.",
        "type": "followup",
        "parent": "responsibility",
        "guide": "개인 신념과 조직 문화 충돌 시 조화 방안.",
        "order": 12
    },

    # 13. 성장의지 평가 (AI 생성)
    {
        "stage": "growth",
        "display_name": "성장가능성질문",
        "intro_sentence": "다음은 성장가능성질문입니다.",
        "type": "ai",
        "category": "narrative",
        "query_template": "자기소개서 2번 기술 습득 과정 IDS 구축 시각화 자동화",
        "guide": "자소서 2번 문항 인용. 기술 트렌드 시너지 및 학습 계획.",
        "order": 13
    },

    # 14. 성장의지 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "growth_followup",
        "display_name": "성장가능성심층",
        "intro_sentence": "추가적으로 궁금한 게 있습니다.",
        "type": "followup",
        "parent": "growth",
        "guide": "최근 기술 한계 극복 시도 및 구체적 학습 활동.",
        "order": 14
    },

    # 15. 최종 발언 (템플릿 - 즉시)
    {
        "stage": "final_statement",
        "display_name": "최종 발언",
        "type": "template",
        "template": "{candidate_name} 지원자님, 지금까지 많은 답변 감사드립니다. 마지막으로 하고 싶으신 말씀이나 궁금한 점이 있으신가요?",
        "variables": ["candidate_name"],
        "order": 15
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
    """면접 시작 시 제공할 초기 단계 (자기소개만 즉시 생성, 지원동기는 task가 template으로 생성)"""
    return [stage for stage in INTERVIEW_STAGES if stage["type"] == "template" and stage["order"] == 1]
