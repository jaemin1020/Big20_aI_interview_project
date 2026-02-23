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
        "type": "template",
        "template": "반갑습니다. 우선 저희 {company_name} {target_role} 직무에 지원해 주셔서 감사합니다. 저는 오늘 면접을 진행할 면접관 VIEW 입니다. {candidate_name} 지원자님, 면접을 시작하기 위해 먼저 간단히 자기소개 부탁드립니다.",
        "variables": ["candidate_name", "major", "target_role", "company_name"],
        "order": 1
    },

    # 2. 지원동기 (템플릿 - 즉시)
    {
        "stage": "motivation",
        "display_name": "기본 질문",
        "intro_sentence": "감사합니다. 이어서 지원하신 동기에 대해 들어보고 싶습니다.",
        "type": "template",
        "template": "{candidate_name} 지원자님, '{target_role}'에 지원하게 된 동기는 무엇입니까? 또한 {major}을 전공하셨는데 어떤 계기로 {target_role}에 관심을 갖게 되셨나요?",
        "variables": ["candidate_name", "target_role", "major"],
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
        "intro_sentence": "추가적으로 궁금한게 있습니다",
        "type": "followup",
        "parent": "skill",
        "guide": "지원자의 이전 답변을 '~라고 하셨는데,'와 같이 한 문장으로 먼저 요약하십시오. 그 후 답변에서 언급된 구체적인 기술이나 방법론 중 하나를 콕 집어 그 이유나 상세 구현 방식을 묻는 심층 질문을 던지십시오. 모든 질문은 반드시 '주세요.'로 끝내고 물음표를 사용하지 마십시오.",
        "order": 4
    },

    # 5. 직무 경험 평가 (템플릿)
    {
        "stage": "experience",
        "display_name": "실무경험질문",
        "type": "template",
        "template": " 경력사항 부분을 보니 {act_org}에서 {act_role}을 하셨고, {proj_org}에서 {proj_name} 관련 프로젝트를 하셨네요. 각 분야에서 구체적으로 어떤 일을 하셨는지 설명해 주세요.",
        "variables": ["act_org", "act_role", "proj_org", "proj_name"],
        "order": 5
    },

    # 6. 직무 경험 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "experience_followup",
        "display_name": "실무심층질문",
        "type": "followup",
        "parent": "experience",
        "guide": "이전 답변에서 가장 핵심적인 기술 키워드(예: 특정 기술 명칭, 방법론 등)를 하나 찾아내십시오. 그 후, '실행하신 프로젝트에서 {키워드}에 대해 말씀해 주셨는데, {키워드}라는 개념은 무엇이고 그 과정에서 어떻게 활용하셨나요?'와 같은 형식으로 완성된 한 문장의 질문을 작성하십시오. 반드시 어미는 '~인가요?' 혹은 '~무엇인가요?'로 끝내고 물음표를 포함하십시오. 문장이 도중에 끊기지 않도록 최종 확인 후 출력하십시오.",
        "order": 6
    },

    # 7. 문제 해결 능력 평가 (템플릿)
    {
        "stage": "problem_solving",
        "display_name": "문제해결질문",
        "type": "template",
        "template": "그렇다면, 언급하신 '{proj_name}' 프로젝트를 진행하며 겪었던 기술적인 어려움이 있었나요? 어떤 상황이었고, 그걸 어떻게 해결하셨는지 구체적으로 말씀해 주세요.",
        "variables": ["proj_name"],
        "order": 7
    },

    # 8. 문제 해결 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "problem_solving_followup",
        "display_name": "문제해결심층",
        "type": "followup",
        "parent": "problem_solving",
        "guide": "지원자의 이전 답변을 '~라고 하셨는데,'와 같이 한 줄 요약하며 인용하십시오. 그 후, 해결 과정에서 고려했던 다른 대안은 없었는지, 혹은 그 해결책이 최선이었다고 판단한 기술적 근거가 무엇인지 구체적으로 질문하십시오. 이 단계에서는 반드시 '~인가요?' 혹은 '~무엇인가요?' 어조를 사용하고 물음표를 포함하십시오.",
        "order": 8
    },

    # 9. 의사소통 및 협업 평가 (템플릿)
    {
        "stage": "communication",
        "display_name": "협업소통질문",
        "type": "template",
        "template": "{candidate_name} 지원자님, 자기소개서에 팀 프로젝트에 대해 상세히 적어주셨는데요. 해당 프로젝트에서 구체적으로 어떤 직무를 담당하셨고, 협업 과정에서는 본인이 어떤 기여를 하셨는지 말씀해 주세요.",
        "variables": ["candidate_name"],
        "order": 9
    },

    # 10. 의사소통 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "communication_followup",
        "display_name": "협업소통심층",
        "type": "followup",
        "parent": "communication",
        "guide": "지원자의 이전 답변에서 언급된 '구체적인 기여 내용'을 '~라고 하셨는데,' 와 같이 요약하며 시작하십시오. 그 후 다음 문구를 반드시 포함하여 질문하십시오: '팀 프로젝트 당시 겪었던 의견 충돌이 있으셨나요? 만약 있었다면 어떻게 의견 충돌을 해결하셨는지도 구체적으로 말씀해 주세요.' 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 사용하지 마십시오.",
        "order": 10
    },

    # 11. 책임감 및 가치관 평가 (AI 생성)
    {
        "stage": "responsibility",
        "display_name": "가치관책임질문",
        "type": "ai",
        "category": "narrative",
        "query_template": "자기소개서 가치관 직업윤리 사명감 생활신조",
        "guide": "지원자의 자기소개서(특히 1번 문항)에서 '가치관', '직업윤리', '사명감', '생활신조'와 관련된 핵심 문장을 찾아 인용하십시오. 그 후, '{candidate_name} 지원자님, 자기소개서에 \"{찾아낸 구절}\"이라고 하셨는데, {target_role}로서 이는 어떤 가치관을 의미하는 것인지 구체적으로 말씀해 주세요.'라는 형식으로 질문하십시오. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 절대 사용하지 마십시오.",
        "order": 11
    },

    # 12. 책임감 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "responsibility_followup",
        "display_name": "가치관책임심층",
        "type": "followup",
        "parent": "responsibility",
        "guide": "지원자가 11번에서 언급한 가치관을 바탕으로, 그 신념이 시험받거나 조직의 이익과 충돌하는 구체적인 가상 상황(딜레마)을 제시하십시오. 그 후, '만약 {가상 상황}이라면 어떠한 선택을 하실 건가요?'와 같은 형식으로 질문하십시오. 반드시 어미는 '~건가요?' 혹은 '~인가요?'로 끝내고 물음표를 포함하십시오.",
        "order": 12
    },

    # 13. 성장의지 평가 (AI 생성)
    {
        "stage": "growth",
        "display_name": "성장가능성질문",
        "type": "ai",
        "category": "narrative",
        "query_template": "자기소개서 2번 기술 습득 과정 IDS 구축 시각화 자동화",
        "guide": "자소서 2번 문항 인용. 기술 트렌드 시너지 및 학습 계획. 질문은 반드시 '~주세요.'로 끝맺음하고 물음표를 사용하지 마십시오.",
        "order": 13
    },

    # 14. 성장의지 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "growth_followup",
        "display_name": "성장가능성심층",
        "type": "followup",
        "parent": "growth",
        "guide": "최근 기술 한계 극복 시도 및 구체적 학습 활동. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 사용하지 마십시오.",
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
    """면접 시작 시 즉시 제공할 템플릿 질문들 (자기소개, 지원동기, 직무지식)"""
    return [stage for stage in INTERVIEW_STAGES if stage["type"] == "template" and stage["order"] <= 3]
