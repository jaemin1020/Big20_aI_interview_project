"""
AI 모의면접 평가 루브릭 생성 도구 (실제 평가 기준 반영)
"""
from typing import Dict, List


def create_evaluation_rubric() -> Dict:
    """
    AI 모의면접 전체 평가 루브릭 생성
    
    Returns:
        dict: 5개 영역(A~E) 평가 루브릭
    """
    return {
        "evaluation_areas": [
            create_area_a_rubric(),  # 자기 표현 & 기본 커뮤니케이션 (15%)
            create_area_b_rubric(),  # 지원 동기 & 회사 적합성 (15%)
            create_area_c_rubric(),  # 직무 지식 이해도 (20%)
            create_area_d_rubric(),  # 직무 경험 & 문제 해결 (30%)
            create_area_e_rubric(),  # 인성 & 성장 가능성 (20%)
        ],
        "total_weight": 1.0,
        "scoring_method": "weighted_average",
        "output_format": {
            "score_range": [0, 100],
            "pass_probability": ["High", "Medium", "Low"],
            "feedback_required": True
        }
    }


def create_area_a_rubric() -> Dict:
    """A. 자기 표현 & 기본 커뮤니케이션 (15%)"""
    return {
        "code": "A",
        "name": "자기 표현 & 기본 커뮤니케이션",
        "weight": 0.15,
        "target_stages": ["자기소개", "최종 자유 발언", "intro", "closing"],
        "purpose": "지원자의 배경과 강점을 빠르고 명확하게 전달하는 능력 평가",
        "criteria": [
            "본인 배경과 강점이 명확히 전달되는가",
            "답변 구조가 이해하기 쉬운가",
            "질문 의도에서 벗어나지 않는가"
        ],
        "llm_observation_points": [
            "서론–본론–결론 구조 존재 여부",
            "핵심 키워드 반복 및 강조 여부"
        ],
        "deduction_factors": [
            "장황하지만 핵심이 없음",
            "질문과 무관한 이야기 반복"
        ],
        "scoring_guide": {
            "excellent": {
                "range": [85, 100],
                "description": "명확한 구조와 핵심 전달력이 탁월함",
                "indicators": [
                    "서론-본론-결론 구조가 명확함",
                    "배경과 강점이 구체적으로 전달됨",
                    "질문 의도에 정확히 부합하는 답변"
                ]
            },
            "good": {
                "range": [70, 84],
                "description": "구조와 전달력이 양호함",
                "indicators": [
                    "기본 구조는 갖추었으나 일부 개선 필요",
                    "핵심 내용은 전달되나 다소 장황함"
                ]
            },
            "fair": {
                "range": [50, 69],
                "description": "기본적인 전달은 되나 구조가 미흡함",
                "indicators": [
                    "구조가 불명확함",
                    "핵심이 흐릿함"
                ]
            },
            "poor": {
                "range": [0, 49],
                "description": "전달력이 부족하고 구조가 없음",
                "indicators": [
                    "질문과 무관한 답변",
                    "핵심 없이 장황함"
                ]
            }
        }
    }


def create_area_b_rubric() -> Dict:
    """B. 지원 동기 & 회사 적합성 (15%)"""
    return {
        "code": "B",
        "name": "지원 동기 & 회사 적합성",
        "weight": 0.15,
        "target_stages": ["지원 동기", "resume_intro"],
        "purpose": "회사와 직무를 이해한 상태에서 지원했는지 판단",
        "criteria": [
            "지원 직무를 정확히 이해하고 있는가",
            "회사/도메인 언급이 구체적인가",
            "단순 열정이 아닌 명확한 선택 이유가 있는가"
        ],
        "llm_observation_points": [
            "회사 인재상 키워드와의 정렬 여부",
            "이력서 프로젝트·경험과 동기의 연결성"
        ],
        "deduction_factors": [
            "어디든 쓸 수 있는 범용 동기",
            "회사명만 바꿔도 성립하는 답변"
        ],
        "scoring_guide": {
            "excellent": {
                "range": [85, 100],
                "description": "회사와 직무에 대한 깊은 이해와 명확한 동기",
                "indicators": [
                    "회사 인재상과 본인 경험이 구체적으로 연결됨",
                    "직무에 대한 정확한 이해",
                    "이력서 내용과 동기가 일관됨"
                ]
            },
            "good": {
                "range": [70, 84],
                "description": "회사와 직무 이해가 양호함",
                "indicators": [
                    "회사/직무 언급이 있으나 다소 일반적",
                    "동기가 명확하나 차별성 부족"
                ]
            },
            "fair": {
                "range": [50, 69],
                "description": "기본적인 동기는 있으나 구체성 부족",
                "indicators": [
                    "범용적인 동기",
                    "회사 특성 이해 부족"
                ]
            },
            "poor": {
                "range": [0, 49],
                "description": "동기가 불명확하거나 회사 이해 부족",
                "indicators": [
                    "회사명만 바꿔도 되는 답변",
                    "직무 이해 부족"
                ]
            }
        }
    }


def create_area_c_rubric() -> Dict:
    """C. 직무 지식 이해도 (20%)"""
    return {
        "code": "C",
        "name": "직무 지식 이해도",
        "weight": 0.20,
        "target_stages": ["직무 관련 지식 질문", "직무 관련 지식 추가 질문 (1-1)", "skill", "skill_followup"],
        "purpose": "직무 수행에 필요한 기본 지식 수준 검증",
        "criteria": [
            "기본 개념을 정확히 설명했는가",
            "용어를 맥락에 맞게 사용했는가",
            "추가 질문 후 설명이 개선되었는가"
        ],
        "llm_observation_points": [
            "개념 오류 여부",
            "재질문 후 답변 명확성 변화"
        ],
        "deduction_factors": [
            "용어 나열만 하고 설명 불가",
            "재질문 후에도 동일한 모호한 답변"
        ],
        "follow_up_evaluation": {
            "enabled": True,
            "improvement_bonus": 10,  # 개선 시 가산점
            "no_change_penalty": -5   # 개선 없으면 감점
        },
        "scoring_guide": {
            "excellent": {
                "range": [85, 100],
                "description": "개념을 정확히 이해하고 명확하게 설명함",
                "indicators": [
                    "개념 설명이 정확함",
                    "용어를 맥락에 맞게 사용",
                    "추가 질문 시 더 명확한 설명 제공"
                ]
            },
            "good": {
                "range": [70, 84],
                "description": "기본 개념 이해가 양호함",
                "indicators": [
                    "개념 이해는 있으나 설명이 다소 부족",
                    "추가 질문 후 개선됨"
                ]
            },
            "fair": {
                "range": [50, 69],
                "description": "개념 이해가 표면적임",
                "indicators": [
                    "용어는 알지만 설명 부족",
                    "추가 질문에도 개선 미미"
                ]
            },
            "poor": {
                "range": [0, 49],
                "description": "개념 이해 부족",
                "indicators": [
                    "개념 오류",
                    "용어 나열만 함"
                ]
            }
        }
    }


def create_area_d_rubric() -> Dict:
    """D. 직무 경험 & 문제 해결 (30%)"""
    return {
        "code": "D",
        "name": "직무 경험 & 문제 해결",
        "weight": 0.30,
        "target_stages": [
            "직무 관련 경험 질문",
            "직무 관련 문제 해결 질문",
            "추가 질문 (2-1, 3-1)",
            "experience",
            "experience_followup",
            "problem_solving",
            "problem_solving_followup"
        ],
        "purpose": "실제로 문제를 해결해 본 경험과 사고 흐름 평가",
        "criteria": [
            "실제 경험 기반 설명인가",
            "문제 정의 → 접근 → 결과 흐름이 있는가",
            "대안·개선 관점이 있는가",
            "추가 질문 후 논리 보완이 되었는가"
        ],
        "llm_observation_points": [
            '"내가 했다" 중심 서술 여부',
            "추상적 설명 vs 구체적 행동"
        ],
        "deduction_factors": [
            "팀이 했다는 이야기만 반복",
            "결과 없는 과정 설명"
        ],
        "follow_up_evaluation": {
            "enabled": True,
            "improvement_bonus": 15,
            "no_change_penalty": -10
        },
        "scoring_guide": {
            "excellent": {
                "range": [85, 100],
                "description": "구체적 경험과 명확한 문제 해결 과정",
                "indicators": [
                    "문제 정의 → 접근 → 결과가 명확함",
                    '"내가" 한 행동이 구체적으로 서술됨',
                    "대안 고려 및 개선 관점 존재",
                    "추가 질문 시 논리가 더 명확해짐"
                ]
            },
            "good": {
                "range": [70, 84],
                "description": "경험과 문제 해결 과정이 양호함",
                "indicators": [
                    "기본 흐름은 있으나 일부 모호함",
                    "본인 역할은 설명되나 구체성 부족"
                ]
            },
            "fair": {
                "range": [50, 69],
                "description": "경험은 있으나 문제 해결 과정이 불명확함",
                "indicators": [
                    "팀 중심 설명",
                    "과정은 있으나 결과 불명확"
                ]
            },
            "poor": {
                "range": [0, 49],
                "description": "경험 부족 또는 설명 불가",
                "indicators": [
                    "추상적 설명만 반복",
                    "본인 역할 불명확"
                ]
            }
        }
    }


def create_area_e_rubric() -> Dict:
    """E. 인성 & 성장 가능성 (20%)"""
    return {
        "code": "E",
        "name": "인성 & 성장 가능성",
        "weight": 0.20,
        "target_stages": [
            "협업 평가 질문 (+1-1)",
            "책임감·가치관 질문 (+2-1)",
            "변화 수용·성장 질문 (+3-1)",
            "communication",
            "communication_followup",
            "responsibility",
            "responsibility_followup",
            "growth",
            "growth_followup"
        ],
        "purpose": "조직 적합성과 장기 성장 가능성 판단",
        "criteria": [
            "협업 시 태도가 성숙한가",
            "책임 회피 없이 설명하는가",
            "실패·변화를 학습 관점으로 해석하는가",
            "추가 질문 후 태도 설명이 명확해졌는가"
        ],
        "llm_observation_points": [
            "blame language vs ownership language",
            '"배웠다 / 개선했다" 표현 사용 여부'
        ],
        "deduction_factors": [
            "타인·환경 탓 중심 설명",
            "실패 경험 회피"
        ],
        "follow_up_evaluation": {
            "enabled": True,
            "improvement_bonus": 10,
            "no_change_penalty": -5
        },
        "scoring_guide": {
            "excellent": {
                "range": [85, 100],
                "description": "성숙한 태도와 높은 성장 가능성",
                "indicators": [
                    "ownership language 사용",
                    "실패를 학습 기회로 해석",
                    "협업 시 성숙한 태도",
                    "책임감 있는 설명"
                ]
            },
            "good": {
                "range": [70, 84],
                "description": "태도와 성장 가능성이 양호함",
                "indicators": [
                    "기본적인 책임감은 있음",
                    "학습 의지 표현"
                ]
            },
            "fair": {
                "range": [50, 69],
                "description": "태도는 있으나 성장 관점 부족",
                "indicators": [
                    "일부 blame language 사용",
                    "실패 경험 언급 회피"
                ]
            },
            "poor": {
                "range": [0, 49],
                "description": "태도와 성장 가능성 우려",
                "indicators": [
                    "타인 탓 중심",
                    "책임 회피",
                    "학습 의지 부족"
                ]
            }
        }
    }


def get_evaluation_prompt() -> str:
    """LLM 평가 프롬프트 생성 (EXAONE 3.5 최적화)"""
    return """[|system|]당신은 IT 기업의 신입 채용을 담당하는 전문 면접관입니다.
LG AI Research의 EXAONE으로서, 아래 제공되는 이력서 정보와 답변 로그를 바탕으로 지원자의 역량을 정밀하게 평가하십시오.

[평가 원칙]
1. 평가는 아래 A~E 기준에 따라 수행하며, 각 가중치를 반영하십시오.
2. 각 항목의 'LLM 관찰 포인트'를 점수 산정의 직접적 근거로 삼으십시오.
3. 추가 질문(꼬리질문)이 있는 경우, 이전 답변 대비 논리성이 얼마나 개선되었는지 분석하여 가산 또는 감산하십시오.
4. 모든 평가는 냉철하고 객관적이어야 하며, 시니어 면접관의 어조를 유지하십시오.[|endofturn|]
[|user|]제공된 데이터를 바탕으로 지원자의 답변을 A~E 영역별로 평가하여 JSON 형식으로 출력하십시오.

────────────────
[A. 자기 표현 & 기본 커뮤니케이션] (15%)
- 서론–본론–결론 구조 존재 여부
- 핵심 키워드 반복 및 강조 여부

[B. 지원 동기 & 회사 적합성] (15%)
- 회사 인재상 키워드와의 정렬
- 이력서 프로젝트/경험과 지원 동기의 연결성

[C. 직무 지식 이해도] (20%)
- 개념 오류 여부
- 재질문 후 답변의 명확성 변화

[D. 직무 경험 & 문제 해결] (30%)
- "내가 했다" 중심의 구체적 서술
- 문제 정의 → 접근 → 결과 흐름

[E. 인성 & 성장 가능성] (20%)
- blame language vs ownership language
- "배웠다 / 개선했다" 표현 사용 여부
────────────────

[출력 형식]
- 각 항목(A~E)을 0~100점으로 평가하고, 한 문장의 근거를 작성하십시오.
- 종합 평가와 최종 합격 가능성(High / Medium / Low)을 포함하십시오.
- **텍스트 정제**: 어떠한 마크다운 문법(** 등)도 사용하지 마십시오. 오직 순수한 평문으로만 작성하십시오.
- **중복 방지**: 동일한 문구의 반복이나 말더듬 현상을 철저히 배제하십시오.[|endofturn|]
[|assistant|]"""


# 사용 예시
if __name__ == "__main__":
    import json
    
    rubric = create_evaluation_rubric()
    print(json.dumps(rubric, ensure_ascii=False, indent=2))
    
    print("\n" + "="*50)
    print("LLM 평가 프롬프트:")
    print("="*50)
    print(get_evaluation_prompt())
