# -*- coding: utf-8 -*-
"""
면접 시나리오 설정 파일
실시간 대화형 면접의 전체 흐름을 정의합니다.
"""

INTERVIEW_STAGES = [
    # 1. 자기소개 (템플릿 - 즉시)
    {
        "stage": "intro",
        "display_name": "기본 질문",
        "intro_sentence": "면접을 시작하겠습니다.",
        "type": "template",
        "template": "반갑습니다. 우선 저희 {company_name} {target_role}에 지원해 주셔서 감사합니다. 저는 오늘 면접을 진행할 면접관 VIEW입니다. 면접을 시작하기 위해 먼저 간단히 자기소개 부탁드립니다. {candidate_name} 지원자님, 자기소개 부탁드립니다.",
        "variables": ["candidate_name", "target_role", "company_name"],
        "order": 1
    },
    
    # 2. 지원동기 (템플릿 - 즉시)
    {
        "stage": "motivation",
        "display_name": "기본 질문",
        "intro_sentence": "감사합니다. 이어서 지원하신 동기에 대해 들어보고 싶습니다.",
        "type": "template",
        "template": "{candidate_name} 지원자님, 지원하신 직무인 '{target_role}'에 지원하게 된 동기는 무엇입니까?",
        "variables": ["candidate_name", "target_role"],
        "order": 2
    },
    
    # 3. 직무 지식 평가 (자격증 중심 템플릿)
    {
        "stage": "skill",
        "display_name": "직무지식질문",
        "type": "template",
        "template": "이력서를 보니 {cert_list} 자격증을 취득하셨네요. 이 과정에서 습득한 지식과 기술이 무엇인지 구체적으로 말씀해 주세요.",
        "variables": ["cert_list"],
        "order": 3
    },
    
    # 4. 직무 지식 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "skill_followup",
        "display_name": "직무심층질문",
        "type": "followup",
        "parent": "skill",
        "guide": "지원자의 이전 답변을 '~라고 말씀해 주셨군요.'와 같이 한 문장으로 먼저 요약하십시오. 그 후 답변에서 언급된 구체적인 기술이나 수치, 방법론 중 하나를 콕 집어 그 이유나 상세 구현 방식을 묻는 심층 질문을 던지십시오. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 사용하지 마십시오.",
        "order": 4
    },
    
    # 5. 직무 경험 평가 (템플릿)
    {
        "stage": "experience",
        "display_name": "실무경험질문",
        "type": "template",
        "template": " 경력사항에 {act_org}에서 {act_role}일을 하셨고, {proj_org}에서 {proj_name} 관련 프로젝트를 하셨네요. 각 분야에서 구체적으로 어떤 일을 하셨는지 설명해 주세요.",
        "variables": ["act_org", "act_role", "proj_org", "proj_name"],
        "order": 5
    },
    
    # 6. 직무 경험 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "experience_followup",
        "display_name": "실무심층질문",
        "type": "followup",
        "parent": "experience",
        "guide": "지원자의 이전 답변 중 핵심 기술이나 방법론을 하나 요약하며 '~라고 하셨는데,'와 같이 인용하십시오. 그 후, 당시 내린 의사결정의 기술적 근거나 혹은 다른 대안 대신 그 방법을 선택한 구체적인 이유를 질문하십시오. 이 단계에서는 반드시 '~인가요?' 혹은 '~무엇인가요?' 어조를 사용하고 물음표를 포함하십시오.",
        "order": 6
    },
    
    # 7. 문제 해결 능력 평가 (템플릿)
    {
        "stage": "problem_solving",
        "display_name": "문제해결질문",
        "type": "template",
        "template": "{proj_name}를 하실 때 경험했던 기술적 문제가 있었나요? 만약 있었다면 어떤 문제였고 또 그것을 어떤 방식으로 해결하셨는지 구체적으로 말씀해 주세요.",
        "variables": ["proj_name"],
        "order": 7
    },
    
    # 8. 문제 해결 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "problem_solving_followup",
        "display_name": "문제해결심층",
        "type": "followup",
        "parent": "problem_solving",
        "guide": "지원자의 이전 답변을 '~라고 하셨는데,'와 같이 한 줄 요약하며 인용하십시오. 그 후, 해당 해결책을 선택한 기술적 근거가 무엇인지, 혹은 예상치 못한 변수나 한계점은 없었는지 질문하십시오. 이 단계에서는 반드시 '~인가요?' 혹은 '~무엇인가요?' 어조를 사용하고 물음표를 포함하십시오.",
        "order": 8
    },
    
    # 9. 의사소통 및 협업 평가 (AI 생성 - 인재상 기반)
    {
        "stage": "communication",
        "display_name": "협업소통질문",
        "type": "ai",
        "category": "narrative",
        "guide": "회사의 인재상인 '{company_ideal}'의 핵심 가치를 바탕으로, 지원자가 일상이나 조직 생활에서 타인과 협력할 때 가장 중요하게 생각하는 태도가 무엇인지 묻는 질문을 생성하십시오. 직무 전문성보다는 인재상의 정신을 어떻게 실천하는지 확인하십시오. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 사용하지 마십시오.",
        "order": 9
    },
    
    # 10. 의사소통 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "communication_followup",
        "display_name": "협업소통심층",
        "type": "followup",
        "parent": "communication",
        "guide": "지원자의 이전 답변에서 협업과 소통에 대한 본인만의 철학이 드러난 대목을 짧게 요약하며 시작하십시오. 그 후, 만약 동료와 의견이 강하게 충돌하거나 이해관계가 상충하는 현실적인 상황이 발생한다면 어떻게 대처할 것인지 1개의 단일 질문을 던지십시오. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 사용하지 마십시오.",
        "order": 10
    },
    
    # 11. 책임감 및 가치관 평가 (AI 생성 - 인재상 기반)
    {
        "stage": "responsibility",
        "display_name": "가치관책임질문",
        "type": "ai",
        "category": "narrative",
        "guide": "제공된 [지원자 자기소개서 질문1 답변]에서 지원자의 핵심 가치관이 드러난 문장을 반드시 그대로 혹은 가깝게 인용하며 (~라고 작성하셨는데,)로 질문을 시작하십시오. 이때 백엔드나 프로젝트 같은 직무 세부 사항은 절대 언급하지 마십시오. 오직 인용된 가치관과 회사의 인재상인 '{company_ideal}'을 연결하여, 지원자가 어떤 직업 윤리로 업무에 임할 것인지 묻는 1개의 단일 질문을 생성하십시오. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 절대 사용하지 마십시오.",
        "order": 11
    },
    
    # 12. 책임감 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "responsibility_followup",
        "display_name": "가치관책임심층",
        "type": "followup",
        "parent": "responsibility",
        "guide": "지원자의 이전 답변 중에서 책임감과 정직함이 가장 잘 드러난 문장을 짧게 요약하며 시작하십시오. 그 후, 만약 자신의 신념을 지키기 위해 개인적인 불이익을 감수해야 하는 딜레마 상황이 온다면 어떻게 본인의 가치를 지켜낼 것인지 1개의 단일 질문을 던지십시오. 모든 질문은 반드시 '~기 위해 ...할 것인가요?'와 같이 '~인가요?'로 끝맺음하고 물음표를 포함하십시오.",
        "order": 12
    },
    
    # 13. 성장의지 및 창의성 평가 (AI 생성 - 인재상 기반)
    {
        "stage": "growth",
        "display_name": "성장가능성질문",
        "type": "ai",
        "category": "narrative",
        "guide": "회사의 인재상인 '{company_ideal}'의 관점에서, 지원자가 평소 자신의 삶을 변화시키거나 새로운 것에 도전할 때 어떤 원칙을 가지고 있는지 묻는 질문을 생성하십시오. 직무 역량이 아닌, 인재상에 부합하는 성장 마인드와 실천 의지를 확인하십시오. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 절대 사용하지 마십시오.",
        "order": 13
    },
    
    # 14. 성장의지 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "growth_followup",
        "display_name": "성장가능성심층",
        "type": "followup",
        "parent": "growth",
        "guide": "지원자의 이전 답변에서 성장에 대한 의지나 새로운 시도가 드러난 부분을 짧게 요약하며 시작하십시오. 그 후, 만약 주변 동료들이 현상 유지를 선호하며 지원자의 변화 노력을 의심한다면 어떻게 설득하여 꾸준히 성장을 이어갈 것인지 1개의 단일 질문을 던지십시오. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 사용하지 마십시오.",
        "order": 14
    },
    
    # 15. 최종 발언 (템플릿 - 즉시)
    {
        "stage": "final_statement",
        "display_name": "최종 발언",
        "type": "template",
        "template": "{candidate_name} 지원자님, 마지막으로 하고 싶으신 말씀이나 궁금한 점이 있으면 말씀해 주세요.",
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
    면접 시작 시 즉시 제공할 템플릿 질문들 (자기소개, 지원동기, 직무지식)
    """
    return [stage for stage in INTERVIEW_STAGES if stage["type"] == "template" and stage["order"] <= 3]
