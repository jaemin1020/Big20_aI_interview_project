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
        "template": "반갑습니다. 우선 저희 {company_name} {target_role} 직무에 지원해 주셔서 감사합니다. 저는 오늘 면접을 진행할 면접관 BIG-VIEW 입니다. {candidate_name} 지원자님, 면접을 시작하기 위해 먼저 간단히 자기소개 부탁드립니다.",
        "variables": ["candidate_name", "major", "target_role", "company_name"],
        "rubric": {
            "criteria": ["자기표현 명확성", "핵심 경험 요약 능력", "논리적 흐름"],
            "focus": "1분 내외로 본인의 핵심 역량과 지원 직무 연관성을 구조적으로 전달했는지 평가",
            "scoring": {"technical_score": "전달 내용의 직무 관련성 (0-5)", "communication_score": "논리적 구성과 전달력 (0-5)"}
        },
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
        "rubric": {
            "criteria": ["직무 이해도", "지원 동기 진정성", "회사 및 직무 연구 수준"],
            "focus": "단순한 취업 목적이 아니라 해당 직무와 회사에 대한 구체적인 이해와 열정이 드러나는지 평가",
            "scoring": {"technical_score": "직무에 대한 기술적 이해 수준 (0-5)", "communication_score": "지원 동기의 진정성과 설득력 (0-5)"}
        },
        "order": 2
    },

    # 3. 직무 지식 평가 (자격증 중심 템플릿)
    {
        "stage": "skill",
        "display_name": "직무지식질문",
        "type": "template",
        "template": "이력서를 보니 {cert_list} 자격증을 취득하셨네요. 이 과정에서 습득한 지식과 기술이 무엇인지 구체적으로 말씀해 주세요.",
        "variables": ["cert_list"],
        "rubric": {
            "criteria": ["기술적 정확성", "개념-실무 연계", "용어 사용 적절성"],
            "focus": "자격증 취득 과정에서 습득한 핵심 기술 개념을 실무와 연결하여 설명하는 능력 평가",
            "scoring": {"technical_score": "기술 지식의 정확성과 깊이 (0-5)", "communication_score": "기술 내용을 명확히 전달하는 능력 (0-5)"}
        },
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
        "template": " 경력사항 부분을 보니 {act_org}에서 {act_role}을 하셨고, {proj_org}에서 {proj_name} 관련 프로젝트를 하셨네요. 각 분야에서 구체적으로 어떤 일을 하셨는지 설명해 주세요.",
        "variables": ["act_org", "act_role", "proj_org", "proj_name"],
        "rubric": {
            "criteria": ["STAR 구조", "역할 명확성", "성과 구체성"],
            "focus": "Situation-Task-Action-Result 구조로 답변이 전개되었는지, 본인의 역할과 팀 기여가 명확히 구분되는지 평가",
            "scoring": {"technical_score": "프로젝트/경험의 기술적 구체성 (0-5)", "communication_score": "경험을 STAR 구조로 논리적으로 전달한 능력 (0-5)"}
        },
        "order": 5
    },

    # 6. 직무 경험 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "experience_followup",
        "display_name": "실무심층질문",
        "type": "followup",
        "parent": "experience",
        "guide": "이전 답변에서 가장 핵심적인 기술 키워드(예: 특정 기술 명칭, 방법론 등)를 하나 찾아내십시오. 그 후, '실행하신 프로젝트에서 {키워드}에 대해 말씀해 주셨는데, {키워드}라는 개념은 무엇이고 그 과정에서 어떻게 활용하셨나요?'와 같은 형식으로 완성된 한 문장의 질문을 작성하십시오. 반드시 어미는 '~인가요?' 혹은 '~무엇인가요?'로 끝내고 물음표를 포함하십시오. 문장이 도중에 끊기지 않도록 최종 확인 후 출력하십시오.",
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
        "template": "그렇다면, 언급하신 '{proj_name}' 프로젝트를 진행하며 겪었던 기술적인 어려움이 있었나요? 어떤 상황이었고, 그걸 어떻게 해결하셨는지 구체적으로 말씀해 주세요.",
        "variables": ["proj_name"],
        "rubric": {
            "criteria": ["문제 분석력", "해결 과정 논리성", "결과 측정"],
            "focus": "문제 상황을 정확히 인식하고 단계적으로 해결해나간 과정을 구체적 수치나 결과와 함께 설명하는지 평가",
            "scoring": {"technical_score": "기술적 문제 해결 접근의 타당성 (0-5)", "communication_score": "문제-원인-해결-결과를 논리적으로 서술하는 능력 (0-5)"}
        },
        "order": 7
    },

    # 8. 문제 해결 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "problem_solving_followup",
        "display_name": "문제해결심층",
        "type": "followup",
        "parent": "problem_solving",
        "guide": "지원자의 이전 답변을 '~라고 하셨는데,'와 같이 한 줄 요약하며 인용하십시오. 그 후, 해결 과정에서 고려했던 다른 대안은 없었는지, 혹은 그 해결책이 최선이었다고 판단한 기술적 근거가 무엇인지 구체적으로 질문하십시오. 이 단계에서는 반드시 '~인가요?' 혹은 '~무엇인가요?' 어조를 사용하고 물음표를 포함하십시오.",
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
        "template": "{candidate_name} 지원자님, 자기소개서에 팀 프로젝트에 대해 상세히 적어주셨는데요. 해당 프로젝트에서 구체적으로 어떤 직무를 담당하셨고, 협업 과정에서는 본인이 어떤 기여를 하셨는지 말씀해 주세요.",
        "variables": ["candidate_name"],
        "rubric": {
            "criteria": ["협업 기여도", "갈등 해결 방식", "팀 내 역할 명확성"],
            "focus": "팀에서 본인이 구체적으로 어떤 역할과 기여를 했는지, 협업 과정에서 어떤 방식으로 소통했는지 평가",
            "scoring": {"technical_score": "팀 내 기술적 기여의 구체성 (0-5)", "communication_score": "협업 과정에서의 소통 방식과 기여도 설명 (0-5)"}
        },
        "order": 9
    },

    # 10. 의사소통 꼬리질문 (AI 생성 - 답변 기반)
    {
        "stage": "communication_followup",
        "display_name": "협업소통심층",
        "type": "followup",
        "parent": "communication",
        "guide": "지원자의 이전 답변에서 언급된 '구체적인 기여 내용' 중 핵심 한 문장을 '~라고 하셨는데,'로 인용하며 시작하십시오. 그 다음, 팀 프로젝트에서 겪었떤 의견 충돌 경험과 해결 방식을 묻는 질문을 하나의 완결된 문장으로 이어서 작성하십시오. 반드시 전체를 하나의 문장으로 완결하고 '~주세요.'로 끝내며 물음표를 사용하지 마십시오.",
        "rubric": {
            "criteria": ["갈등 해결 구체성", "설득 방식", "의견 조율 능력"],
            "focus": "의견 충돌 상황에서 감정적이 아닌 논리적/데이터 기반으로 해결한 경험이 있는지, 타인의 입장을 존중하며 합의점을 찾는지 평가",
            "scoring": {"technical_score": "갈등 해결 과정의 논리성과 구체성 (0-5)", "communication_score": "타인 설득과 합의 도출 능력 (0-5)"}
        },
        "order": 10
    },

    # 11. 책임감 및 가치관 평가 (자소서 직접 인용 - hallucination 차단)
    {
        "stage": "responsibility",
        "display_name": "가치관책임질문",
        "type": "template_quoted",
        "query_template": "{target_role} 직무에서 중요하게 생각하는 가치관 직업관 신념 소신",
        "extract_keywords": ["중요", "가치", "신념", "생각", "직무", "일하는", "임하는", "소신", "철학", "중시"],
        "template": "{candidate_name} 지원자님, 자기소개서에 '{quote}'라고 쓰셨는데, 이 표현이 의미하는 바와 {target_role} 분야에서 어떻게 실천하고자 하는지 구체적으로 말씀해 주세요.",
        "rubric": {
            "criteria": ["가치관 일관성", "직업윤리 인식 수준", "직무 연계성"],
            "focus": "지원자가 밝힌 가치관이 지원 직무에서 어떻게 발현될 수 있는지 구체적 근거를 제시했는지, 면접 전반의 답변과 일관성이 있는지 평가",
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

    # 13. 성장의지 평가 (자소서 직접 인용 - hallucination 차단)
    {
        "stage": "growth",
        "display_name": "성장가능성질문",
        "type": "template_quoted",
        "query_template": "{target_role} 입사 후 포부 성장 목표 기여 계획 발전",
        "extract_keywords": ["입사", "앞으로", "목표", "성장", "기여", "배우", "발전", "도전", "이루", "계획"],
        "template": "{candidate_name} 지원자님, 자기소개서에 '{quote}'라고 쓰셨는데, 입사 후 {target_role} 분야에서 구체적으로 어떻게 성장해 나가실 계획인지 말씀해 주세요.",
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
        "guide": "최근 기술 한계 극복 시도 및 구체적 학습 활동. 모든 질문은 반드시 '주세요.'로 끝내고 물음표를 사용하지 마십시오.",
        "rubric": {
            "criteria": ["실제 학습 사례", "자기계발 실천력", "지속적 성장 증거"],
            "focus": "최근 실제로 실행한 학습 활동(강의 수료, 사이드 프로젝트, 논문 읽기 등)이 구체적으로 언급되는지, 성장 의지가 행동으로 이어지고 있는지 평가",
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
        "rubric": {
            "criteria": ["마무리 인상", "역질문 적절성", "기업 이해도"],
            "focus": "면접 마지막까지 긍정적인 인상을 유지하고, 역질문이 있다면 회사와 직무에 대한 진지한 관심을 반영하는지 평가",
            "scoring": {"technical_score": "역질문의 질적 수준과 직무 이해 반영도 (0-5)", "communication_score": "마무리 발언의 전달력과 인상 (0-5)"}
        },
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
