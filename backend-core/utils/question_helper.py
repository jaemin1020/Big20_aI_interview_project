"""
질문 생성 헬퍼 함수 (평가 루브릭 자동 적용)
"""
from typing import Dict, Optional
from utils.rubric_generator import (
    create_area_a_rubric,
    create_area_b_rubric,
    create_area_c_rubric,
    create_area_d_rubric,
    create_area_e_rubric
)


class QuestionType:
    """질문 유형 정의"""
    SELF_INTRODUCTION = "자기소개"
    MOTIVATION = "지원 동기"
    KNOWLEDGE = "직무 지식"
    EXPERIENCE = "직무 경험"
    PROBLEM_SOLVING = "문제 해결"
    COLLABORATION = "협업"
    RESPONSIBILITY = "책임감"
    GROWTH = "성장 가능성"
    FINAL_STATEMENT = "최종 발언"


def get_rubric_for_question_type(question_type: str) -> Dict:
    """
    질문 유형에 맞는 평가 루브릭 반환
    
    Args:
        question_type: 질문 유형 (QuestionType 참조)
        
    Returns:
        dict: 해당 질문에 적용할 평가 루브릭
    """
    rubric_mapping = {
        QuestionType.SELF_INTRODUCTION: create_area_a_rubric(),
        QuestionType.FINAL_STATEMENT: create_area_a_rubric(),
        QuestionType.MOTIVATION: create_area_b_rubric(),
        QuestionType.KNOWLEDGE: create_area_c_rubric(),
        QuestionType.EXPERIENCE: create_area_d_rubric(),
        QuestionType.PROBLEM_SOLVING: create_area_d_rubric(),
        QuestionType.COLLABORATION: create_area_e_rubric(),
        QuestionType.RESPONSIBILITY: create_area_e_rubric(),
        QuestionType.GROWTH: create_area_e_rubric(),
    }
    
    return rubric_mapping.get(question_type, create_area_c_rubric())


def create_question_with_rubric(
    content: str,
    question_type: str,
    category: str = "TECHNICAL",
    difficulty: str = "MEDIUM",
    is_follow_up: bool = False
) -> Dict:
    """
    평가 루브릭이 포함된 질문 데이터 생성
    
    Args:
        content: 질문 내용
        question_type: 질문 유형 (QuestionType 참조)
        category: 질문 카테고리 (TECHNICAL, BEHAVIORAL 등)
        difficulty: 난이도 (EASY, MEDIUM, HARD)
        is_follow_up: 추가 질문 여부
        
    Returns:
        dict: Question 모델에 삽입할 데이터
    """
    rubric = get_rubric_for_question_type(question_type)
    
    # 추가 질문인 경우 follow_up_evaluation 활성화
    if is_follow_up and "follow_up_evaluation" in rubric:
        rubric["is_follow_up"] = True
    
    return {
        "content": content,
        "category": category,
        "difficulty": difficulty,
        "rubric_json": rubric,
        "question_type": question_type,
        "is_follow_up": is_follow_up
    }


# 사용 예시
if __name__ == "__main__":
    import json
    
    # 예시 1: 자기소개 질문
    q1 = create_question_with_rubric(
        content="간단히 자기소개 부탁드립니다.",
        question_type=QuestionType.SELF_INTRODUCTION,
        category="BEHAVIORAL",
        difficulty="EASY"
    )
    print("자기소개 질문:")
    print(json.dumps(q1, ensure_ascii=False, indent=2))
    print("\n" + "="*50 + "\n")
    
    # 예시 2: 직무 지식 질문
    q2 = create_question_with_rubric(
        content="LangChain의 RAG 시스템에 대해 설명해주세요.",
        question_type=QuestionType.KNOWLEDGE,
        category="TECHNICAL",
        difficulty="MEDIUM"
    )
    print("직무 지식 질문:")
    print(json.dumps(q2, ensure_ascii=False, indent=2))
    print("\n" + "="*50 + "\n")
    
    # 예시 3: 추가 질문 (follow-up)
    q3 = create_question_with_rubric(
        content="조금 더 구체적으로 설명해주시겠어요?",
        question_type=QuestionType.KNOWLEDGE,
        category="TECHNICAL",
        difficulty="MEDIUM",
        is_follow_up=True
    )
    print("추가 질문 (1-1):")
    print(json.dumps(q3, ensure_ascii=False, indent=2))
