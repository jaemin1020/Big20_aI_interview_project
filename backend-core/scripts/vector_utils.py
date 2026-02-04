"""
VectorDB 검색 유틸리티
- 유사 질문 검색
- 답변 평가
- 질문 추천
"""

from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select, text, and_
from database import engine
from models import Question, AnswerBank, QuestionCategory, QuestionDifficulty

# 임베딩 모델 (전역 변수로 한 번만 로드)
_model = None

def get_embedding_model():
    """임베딩 모델 싱글톤"""
    global _model
    if _model is None:
        print("🔄 BGE-M3 모델 로딩 중...")
        _model = SentenceTransformer('BAAI/bge-m3')
        print("✅ 모델 로드 완료!")
        print(f"📊 임베딩 차원: {_model.get_sentence_embedding_dimension()}")
    return _model

def find_similar_questions(
    query_text: str,
    top_k: int = 5,
    position: Optional[str] = None,
    category: Optional[QuestionCategory] = None,
    difficulty: Optional[QuestionDifficulty] = None,
    company: Optional[str] = None,
    industry: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    입력 텍스트와 유사한 질문 검색

    Args:
        query_text: 검색할 텍스트
        top_k: 반환할 결과 개수
        position: 직무 필터 (예: "Backend 개발자")
        category: 카테고리 필터
        difficulty: 난이도 필터
        company: 회사 필터
        industry: 산업 필터

    Returns:
        유사 질문 리스트 (질문 객체 + 유사도 점수)
    """
    model = get_embedding_model()

    # 1. 쿼리 임베딩 생성
    query_embedding = model.encode(query_text).tolist()

    # 2. 벡터 유사도 검색
    with Session(engine) as session:
        # 기본 쿼리 (벡터 거리 계산)
        stmt = select(
            Question,
            text(f"embedding <=> '{query_embedding}' AS distance")
        )

        # 필터 조건 추가
        conditions = []
        if position:
            conditions.append(Question.position == position)
        if category:
            conditions.append(Question.category == category)
        if difficulty:
            conditions.append(Question.difficulty == difficulty)
        if company:
            conditions.append(Question.company == company)
        if industry:
            conditions.append(Question.industry == industry)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 정렬 및 제한
        stmt = stmt.order_by(text("distance")).limit(top_k)

        results = session.exec(stmt).all()

        return [
            {
                "question": result[0],
                "similarity": 1 - result[1],  # 거리 → 유사도 변환
                "distance": result[1]
            }
            for result in results
        ]

def find_similar_answers(
    question_id: int,
    user_answer: str,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    특정 질문에 대한 유사 답변 검색

    Args:
        question_id: 질문 ID
        user_answer: 사용자 답변
        top_k: 반환할 결과 개수

    Returns:
        유사 답변 리스트 (답변 객체 + 유사도 점수)
    """
    model = get_embedding_model()

    # 1. 사용자 답변 임베딩
    user_embedding = model.encode(user_answer).tolist()

    # 2. 해당 질문의 우수 답변들 검색
    with Session(engine) as session:
        stmt = select(
            AnswerBank,
            text(f"embedding <=> '{user_embedding}' AS distance")
        ).where(
            AnswerBank.question_id == question_id
        ).order_by(text("distance")).limit(top_k)

        results = session.exec(stmt).all()

        return [
            {
                "answer": result[0],
                "similarity": 1 - result[1],
                "distance": result[1]
            }
            for result in results
        ]

def evaluate_answer(
    question_id: int,
    user_answer: str
) -> Dict[str, Any]:
    """
    사용자 답변을 우수 답변과 비교하여 평가

    Args:
        question_id: 질문 ID
        user_answer: 사용자 답변

    Returns:
        평가 결과 (점수, 피드백, 참고 답변)
    """
    similar_answers = find_similar_answers(question_id, user_answer, top_k=1)

    if not similar_answers:
        return {
            "score": 0,
            "similarity": 0,
            "feedback": "참고할 답변이 없습니다.",
            "reference_answer": None,
            "reference_score": None
        }

    best_match = similar_answers[0]
    answer_obj = best_match["answer"]
    similarity = best_match["similarity"]

    # 유사도 기반 점수 계산
    # 유사도가 높을수록 참고 답변의 점수에 가까워짐
    estimated_score = similarity * answer_obj.score

    # 피드백 생성
    if similarity > 0.85:
        feedback = "✅ 우수한 답변입니다! 참고 답변과 매우 유사한 수준입니다."
    elif similarity > 0.70:
        feedback = "👍 좋은 답변입니다. 일부 개선 여지가 있습니다."
    elif similarity > 0.50:
        feedback = "⚠️ 기본적인 내용은 포함되어 있으나, 더 구체적인 설명이 필요합니다."
    else:
        feedback = "❌ 답변을 보완해주세요. 참고 답변을 확인하시기 바랍니다."

    return {
        "score": round(estimated_score, 2),
        "similarity": round(similarity, 4),
        "feedback": feedback,
        "reference_answer": answer_obj.answer_text,
        "reference_score": answer_obj.score,
        "evaluator_feedback": answer_obj.evaluator_feedback
    }

def recommend_questions_for_position(
    position: str,
    user_skills: str = "",
    num_questions: int = 5,
    difficulty_distribution: Dict[str, int] = None
) -> List[Question]:
    """
    직무별 질문 추천

    Args:
        position: 직무 (예: "Backend 개발자")
        user_skills: 사용자 기술 스택/경력 (텍스트)
        num_questions: 추천할 질문 개수
        difficulty_distribution: 난이도 분포 (예: {"easy": 1, "medium": 3, "hard": 1})

    Returns:
        추천 질문 리스트
    """
    if difficulty_distribution is None:
        difficulty_distribution = {
            "easy": 1,
            "medium": 3,
            "hard": 1
        }

    recommended = []

    with Session(engine) as session:
        for diff, count in difficulty_distribution.items():
            if count == 0:
                continue

            # 사용자 스킬 기반 유사도 검색
            if user_skills:
                similar = find_similar_questions(
                    query_text=user_skills,
                    top_k=count,
                    position=position,
                    difficulty=QuestionDifficulty(diff)
                )
                recommended.extend([item["question"] for item in similar])
            else:
                # 스킬 정보가 없으면 랜덤 선택
                stmt = select(Question).where(
                    and_(
                        Question.position == position,
                        Question.difficulty == QuestionDifficulty(diff),
                        Question.is_active == True
                    )
                ).limit(count)

                questions = session.exec(stmt).all()
                recommended.extend(questions)

    return recommended[:num_questions]

def get_question_statistics(question_id: int) -> Dict[str, Any]:
    """
    질문 통계 조회

    Args:
        question_id: 질문 ID

    Returns:
        질문 통계 (사용 횟수, 평균 점수 등)
    """
    with Session(engine) as session:
        question = session.get(Question, question_id)

        if not question:
            return None

        # 답변 통계
        stmt = select(AnswerBank).where(AnswerBank.question_id == question_id)
        answers = session.exec(stmt).all()

        if answers:
            avg_score = sum(a.score for a in answers) / len(answers)
            max_score = max(a.score for a in answers)
            min_score = min(a.score for a in answers)
        else:
            avg_score = max_score = min_score = None

        return {
            "question_id": question_id,
            "content": question.content,
            "category": question.category,
            "difficulty": question.difficulty,
            "usage_count": question.usage_count,
            "answer_count": len(answers),
            "avg_answer_score": round(avg_score, 2) if avg_score else None,
            "max_answer_score": max_score,
            "min_answer_score": min_score
        }

def batch_embed_questions(questions: List[str]) -> List[List[float]]:
    """
    질문 배치 임베딩 (성능 최적화)

    Args:
        questions: 질문 텍스트 리스트

    Returns:
        임베딩 벡터 리스트
    """
    model = get_embedding_model()
    embeddings = model.encode(questions, batch_size=32, show_progress_bar=True)
    return [emb.tolist() for emb in embeddings]

def search_questions_hybrid(
    query_text: str,
    top_k: int = 10,
    keyword_weight: float = 0.3,
    vector_weight: float = 0.7
) -> List[Dict[str, Any]]:
    """
    하이브리드 검색 (키워드 + 벡터)

    Args:
        query_text: 검색 쿼리
        top_k: 반환할 결과 개수
        keyword_weight: 키워드 검색 가중치
        vector_weight: 벡터 검색 가중치

    Returns:
        검색 결과 (하이브리드 점수 포함)
    """
    model = get_embedding_model()
    query_embedding = model.encode(query_text).tolist()

    with Session(engine) as session:
        # PostgreSQL의 전문 검색 + 벡터 검색 결합
        stmt = text(f"""
            SELECT
                q.*,
                (
                    {keyword_weight} * ts_rank(to_tsvector('korean', content), plainto_tsquery('korean', :query))
                    + {vector_weight} * (1 - (embedding <=> '{query_embedding}'))
                ) AS hybrid_score
            FROM questions q
            WHERE to_tsvector('korean', content) @@ plainto_tsquery('korean', :query)
               OR embedding <=> '{query_embedding}' < 0.5
            ORDER BY hybrid_score DESC
            LIMIT :limit
        """)

        results = session.exec(
            stmt,
            {"query": query_text, "limit": top_k}
        ).all()

        return [
            {
                "question_id": row[0],
                "content": row[1],
                "hybrid_score": row[-1]
            }
            for row in results
        ]

# ==================== 사용 예시 ====================

if __name__ == "__main__":
    # 1. 유사 질문 검색
    print("=" * 60)
    print("1️⃣ 유사 질문 검색")
    print("=" * 60)

    similar = find_similar_questions(
        query_text="파이썬 멀티스레딩과 GIL에 대해 설명해주세요",
        top_k=3,
        position="Backend 개발자"
    )

    for i, item in enumerate(similar, 1):
        print(f"\n{i}. 유사도: {item['similarity']:.4f}")
        print(f"   질문: {item['question'].content[:100]}...")
        print(f"   난이도: {item['question'].difficulty}")

    # 2. 답변 평가
    print("\n" + "=" * 60)
    print("2️⃣ 답변 평가")
    print("=" * 60)

    if similar:
        question_id = similar[0]["question"].id
        user_answer = "GIL은 Python의 멀티스레딩을 제한하는 락입니다."

        evaluation = evaluate_answer(question_id, user_answer)
        print(f"\n점수: {evaluation['score']}")
        print(f"유사도: {evaluation['similarity']}")
        print(f"피드백: {evaluation['feedback']}")

    # 3. 질문 추천
    print("\n" + "=" * 60)
    print("3️⃣ 질문 추천")
    print("=" * 60)

    recommendations = recommend_questions_for_position(
        position="Backend 개발자",
        user_skills="Python, FastAPI, PostgreSQL, Docker",
        num_questions=5
    )

    for i, q in enumerate(recommendations, 1):
        print(f"\n{i}. [{q.difficulty}] {q.content[:80]}...")
