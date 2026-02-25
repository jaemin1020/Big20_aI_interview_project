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
        "type": "template",
        "template": "반갑습니다. 우선 저희 {company_name} {target_role}에 지원해 주셔서 감사합니다. 저는 오늘 면접을 진행할 면접관 VIEW입니다. {candidate_name} 지원자님,면접을 시작하기 위해 먼저 간단히 자기소개 부탁드립니다.",
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
        "rubric": {
            "criteria": ["기술 원리 이해", "선택 근거 명확성", "심층 기술 설명 능력"],
            "focus": "단순 암기가 아닌 원리를 이해하고 왜 그 기술/방법론을 선택했는지 논리적 근거를 제시하는지 평가",
            "scoring": {"technical_score": "기술 원리의 심층 이해도 (0-5)", "communication_score": "기술적 내용을 쉽게 풀어 설명하는 능력 (0-5)"}
        },
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
        "rubric": {
            "criteria": ["기술 선택 근거", "문제 인식 능력", "비판적 사고"],
            "focus": "언급한 기술/방법론이 해당 상황에서 왜 최선이었는지 논리적으로 설명하는지 평가",
            "scoring": {"technical_score": "기술 개념 정확성과 활용 방식 (0-5)", "communication_score": "기술적 선택을 설득력 있게 설명하는 능력 (0-5)"}
        },
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
        "rubric": {
            "criteria": ["대안 검토 능력", "최선 판단 근거", "기술적 비판 사고"],
            "focus": "선택한 해결책 외에 다른 선택지를 고려했는지, 최선이라고 판단한 기준이 기술적으로 타당한지 평가",
            "scoring": {"technical_score": "대안 분석과 최선 선택의 기술적 근거 (0-5)", "communication_score": "판단 이유를 논리적으로 전달하는 능력 (0-5)"}
        },
        "order": 8
    },
    
    # 9. 의사소통 및 협업 평가 (템플릿)
    {
        "stage": "communication",
        "display_name": "협업소통질문",
        "type": "template",
        "template": "{candidate_name} 지원자님, 자기소개서에 팀 프로젝트에 대해 상세히 적어주셨는데요. 해당 프로젝트에서 구체적으로 어떤 직무를 담당하셨고, 협업 과정에서는 본인이 어떤 기여를 하셨는지 말씀해 주시겠어요?",
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
        "rubric": {
            "criteria": ["갈등 해결 구체성", "설득 방식", "의견 조율 능력"],
            "focus": "의견 충돌 상황에서 감정적이 아닌 논리적으로 해결한 경험이 있는지, 타인의 입장을 존중하며 합의점을 찾는지 평가",
            "scoring": {"technical_score": "갈등 해결 과정의 논리성과 구체성 (0-5)", "communication_score": "타인 설득과 합의 도출 능력 (0-5)"}
        },
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
        "rubric": {
            "criteria": ["가치관 일관성", "직업윤리 인식 수준", "직무 연계성"],
            "focus": "지원자가 밝힌 가치관이 지원 직무에서 어떻게 발현될 수 있는지 구체적 근거를 제시했는지 평가",
            "scoring": {"technical_score": "기술적 맥락에서 가치관을 설명한 수준 (0-5)", "communication_score": "가치관을 설득력 있게 전달하는 능력 (0-5)"}
        },
        "order": 11
    },
    
    # 12. 책임감 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "responsibility_followup",
        "display_name": "가치관책임심층",
        "type": "followup",
        "parent": "responsibility",
        "guide": "반드시 '그렇다면,'으로 시작하십시오. 지원자가 방금 답변에서 드러낸 가치관을 바탕으로, 그 신념이 시험받거나 조직의 이익과 충돌할 수 있는 구체적인 가상 상황(딜레마)을 하나 제시하고, 그 상황에서 어떤 선택을 할 것인지 묻는 질문을 하나의 완결된 문장으로 작성하십시오. 반드시 어미는 '~건가요?' 혹은 '~인가요?'로 끝내고 물음표를 포함하십시오.",
        "rubric": {
            "criteria": ["딜레마 판단력", "윤리적 사고", "원칙 견고성"],
            "focus": "가상의 압박 상황에서도 자신의 가치관과 원칙을 일관되게 유지하고 합리적으로 설명하는지 평가",
            "scoring": {"technical_score": "딜레마 상황에서 판단의 논리적 타당성 (0-5)", "communication_score": "본인의 선택과 이유를 명확히 전달하는 능력 (0-5)"}
        },
        "order": 12
    },
    
    # 13. 성장의지 평가 (AI 생성)
    {
        "stage": "growth",
        "display_name": "성장가능성질문",
        "type": "ai",
        "category": "narrative",
        "query_template": "자기소개서 2번 기술 습득 과정 IDS 구축 시각화 자동화",
        "guide": "자소서 2번 문항 인용. 기술 트렌드 시너지 및 학습 계획. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 절대 사용하지 마십시오.",
        "rubric": {
            "criteria": ["학습 계획 구체성", "기술 트렌드 인식", "성장 방향성"],
            "focus": "막연한 의지 표명이 아닌 구체적인 학습 로드맵, 현재 역량과 목표 수준 간의 gap 인식, 실천 가능한 계획이 제시되는지 평가",
            "scoring": {"technical_score": "기술적 목표 달성 계획의 구체성과 현실성 (0-5)", "communication_score": "성장 의지와 계획을 설득력 있게 전달하는 능력 (0-5)"}
        },
        "order": 13
    },
    
    # 14. 성장의지 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "growth_followup",
        "display_name": "성장가능성심층",
        "type": "followup",
        "parent": "growth",
        "guide": "최근 기술 한계 극복 시도 및 구체적 학습 활동. 모든 질문은 반드시 '~주세요.'로 끝내고 물음표를 사용하지 마십시오.",
        "rubric": {
            "criteria": ["실제 학습 사례", "자기계발 실천력", "지속적 성장 증거"],
            "focus": "최근 실제로 실행한 학습 활동이 구체적으로 언급되는지, 성장 의지가 행동으로 이어지고 있는지 평가",
            "scoring": {"technical_score": "학습 활동의 기술적 깊이와 일관성 (0-5)", "communication_score": "자기계발 경험을 구체적으로 전달하는 능력 (0-5)"}
        },
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
