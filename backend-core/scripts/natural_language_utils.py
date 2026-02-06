"""
자연어DB 검색 유틸리티
- 키워드 검색
- 전문 검색 (Full-Text Search)
- 필터링 및 정렬
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlmodel import Session, select, text, or_, and_, func
from database import engine, init_db
from models import User, Interview, Transcript, Question, EvaluationReport
from typing import Optional, List, Dict, Any

# ==================== 기본 키워드 검색 ====================

def search_questions_by_keyword(keyword: str, limit: int = 10) -> List[Question]:
    """질문 내용에서 키워드 검색 (ILIKE 사용)"""
    with Session(engine) as session:
        stmt = select(Question).where(
            Question.content.ilike(f"%{keyword}%")
        ).limit(limit)

        results = session.exec(stmt).all()
        return results

def search_transcripts_by_keyword(
    interview_id: int,
    keyword: str
) -> List[Transcript]:
    """특정 면접의 대화 기록에서 키워드 검색"""
    with Session(engine) as session:
        stmt = select(Transcript).where(
            and_(
                Transcript.interview_id == interview_id,
                Transcript.text.ilike(f"%{keyword}%")
            )
        ).order_by(Transcript.timestamp)

        results = session.exec(stmt).all()
        return results

def search_users(query: str, limit: int = 5) -> List[User]:
    """사용자 검색 (이름, 이메일, 사용자명)"""
    with Session(engine) as session:
        stmt = select(User).where(
            or_(
                User.username.ilike(f"%{query}%"),
                User.full_name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        ).limit(limit)

        results = session.exec(stmt).all()
        return results

# ==================== 다중 키워드 검색 ====================

def search_questions_multi_keyword(keywords: List[str]) -> List[Question]:
    """여러 키워드로 질문 검색 (OR 조건)"""
    with Session(engine) as session:
        conditions = [Question.content.ilike(f"%{kw}%") for kw in keywords]
        stmt = select(Question).where(or_(*conditions))

        results = session.exec(stmt).all()
        return results

# ==================== 고급 필터링 ====================

def filter_questions(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    keyword: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    limit: int = 20
) -> List[Question]:
    """다양한 조건으로 질문 필터링 및 정렬"""
    with Session(engine) as session:
        stmt = select(Question)

        # 필터 조건 추가
        conditions = []
        if category:
            conditions.append(Question.category == category)
        if difficulty:
            conditions.append(Question.difficulty == difficulty)
        if company:
            conditions.append(Question.company == company)
        if position:
            conditions.append(Question.position == position)
        if keyword:
            conditions.append(Question.content.ilike(f"%{keyword}%"))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # 정렬
        sort_column = getattr(Question, sort_by, Question.created_at)
        if order == "desc":
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column)

        stmt = stmt.limit(limit)

        results = session.exec(stmt).all()
        return results

def filter_interviews(
    candidate_id: Optional[int] = None,
    position: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20
) -> List[Interview]:
    """면접 필터링"""
    with Session(engine) as session:
        stmt = select(Interview)

        conditions = []
        if candidate_id:
            conditions.append(Interview.candidate_id == candidate_id)
        if position:
            conditions.append(Interview.position == position)
        if status:
            conditions.append(Interview.status == status)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Interview.created_at.desc()).limit(limit)

        results = session.exec(stmt).all()
        return results

# ==================== 전문 검색 (Full-Text Search) ====================

def fulltext_search_questions(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """PostgreSQL 전문 검색을 사용한 질문 검색"""
    with Session(engine) as session:
        try:
            stmt = text("""
                SELECT
                    id,
                    content,
                    category,
                    difficulty,
                    position,
                    ts_rank(to_tsvector('simple', content), query) AS rank
                FROM questions,
                     plainto_tsquery('simple', :query) query
                WHERE to_tsvector('simple', content) @@ query
                ORDER BY rank DESC
                LIMIT :limit
            """)

            results = session.exec(
                stmt,
                {"query": query, "limit": limit}
            ).all()

            return [
                {
                    "id": r[0],
                    "content": r[1],
                    "category": r[2],
                    "difficulty": r[3],
                    "position": r[4],
                    "rank": float(r[5])
                }
                for r in results
            ]
        except Exception as e:
            print(f"⚠️ 전문 검색 실패 (인덱스가 없을 수 있음): {e}")
            print("   기본 ILIKE 검색으로 대체합니다.")

            # 전문 검색 실패 시 기본 검색으로 폴백
            basic_results = search_questions_by_keyword(query, limit)
            return [
                {
                    "id": q.id,
                    "content": q.content,
                    "category": q.category,
                    "difficulty": q.difficulty,
                    "position": q.position,
                    "rank": 0.0
                }
                for q in basic_results
            ]

# ==================== 통계 및 분석 ====================

def analyze_interview_conversation(interview_id: int) -> Dict[str, Any]:
    """면접 대화 내용 분석"""
    with Session(engine) as session:
        # 모든 대화 조회
        stmt = select(Transcript).where(
            Transcript.interview_id == interview_id
        ).order_by(Transcript.timestamp)

        transcripts = session.exec(stmt).all()

        if not transcripts:
            return {"error": "대화 기록이 없습니다."}

        # 통계 계산
        user_responses = [t for t in transcripts if t.speaker == "User"]
        ai_messages = [t for t in transcripts if t.speaker == "AI"]

        total_words = sum(len(t.text.split()) for t in transcripts)
        user_words = sum(len(t.text.split()) for t in user_responses)

        avg_response_length = (
            sum(len(t.text.split()) for t in user_responses) / len(user_responses)
            if user_responses else 0
        )

        # 키워드 빈도 분석
        from collections import Counter
        all_words = " ".join(t.text for t in user_responses).split()
        keyword_freq = Counter(all_words).most_common(10)

        # 감정 분석
        emotions = [t.emotion for t in transcripts if t.emotion]
        emotion_counts = Counter(emotions)

        return {
            "interview_id": interview_id,
            "total_messages": len(transcripts),
            "user_messages": len(user_responses),
            "ai_messages": len(ai_messages),
            "total_words": total_words,
            "user_words": user_words,
            "avg_response_length": round(avg_response_length, 1),
            "top_keywords": keyword_freq,
            "emotions": dict(emotion_counts)
        }

def get_question_statistics() -> Dict[str, Any]:
    """질문 통계"""
    with Session(engine) as session:
        total = session.exec(select(func.count(Question.id))).one()

        # 카테고리별 통계
        category_stats = session.exec(
            text("""
                SELECT category, COUNT(*) as count
                FROM questions
                GROUP BY category
            """)
        ).all()

        # 난이도별 통계
        difficulty_stats = session.exec(
            text("""
                SELECT difficulty, COUNT(*) as count
                FROM questions
                GROUP BY difficulty
            """)
        ).all()

        # 직무별 통계
        position_stats = session.exec(
            text("""
                SELECT position, COUNT(*) as count
                FROM questions
                WHERE position IS NOT NULL
                GROUP BY position
                ORDER BY count DESC
                LIMIT 10
            """)
        ).all()

        return {
            "total_questions": total,
            "by_category": {r[0]: r[1] for r in category_stats},
            "by_difficulty": {r[0]: r[1] for r in difficulty_stats},
            "by_position": {r[0]: r[1] for r in position_stats}
        }

# ==================== 페이지네이션 ====================

def get_questions_paginated(
    page: int = 1,
    page_size: int = 20,
    **filters
) -> Dict[str, Any]:
    """페이지네이션을 사용한 질문 조회"""
    with Session(engine) as session:
        # 전체 개수 조회
        count_stmt = select(func.count(Question.id))

        # 필터 적용
        conditions = []
        if filters.get("category"):
            conditions.append(Question.category == filters["category"])
        if filters.get("difficulty"):
            conditions.append(Question.difficulty == filters["difficulty"])
        if filters.get("position"):
            conditions.append(Question.position == filters["position"])

        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))

        total_count = session.exec(count_stmt).one()

        # 페이지 데이터 조회
        offset = (page - 1) * page_size
        stmt = select(Question)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.offset(offset).limit(page_size)
        questions = session.exec(stmt).all()

        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "data": questions
        }

# ==================== 사용 예시 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🗣️ 자연어DB 검색 테스트")
    print("=" * 60)

    # DB 초기화
    init_db()

    # 1. 질문 통계
    print("\n1️⃣ 질문 통계")
    print("-" * 60)
    stats = get_question_statistics()
    print(f"총 질문 수: {stats['total_questions']}")
    print(f"카테고리별: {stats['by_category']}")
    print(f"난이도별: {stats['by_difficulty']}")

    if stats['total_questions'] == 0:
        print("\n⚠️ 질문 데이터가 없습니다.")
        print("   다음 명령어로 샘플 데이터를 삽입하세요:")
        print("   python scripts/populate_vectordb.py")
    else:
        # 2. 키워드 검색
        print("\n2️⃣ 키워드 검색: 'Python'")
        print("-" * 60)
        results = search_questions_by_keyword("Python", limit=3)
        for i, q in enumerate(results, 1):
            print(f"{i}. [{q.difficulty}] {q.content[:80]}...")

        # 3. 다중 키워드 검색
        print("\n3️⃣ 다중 키워드 검색: ['데이터베이스', 'FastAPI']")
        print("-" * 60)
        results = search_questions_multi_keyword(["데이터베이스", "FastAPI"])
        for i, q in enumerate(results[:3], 1):
            print(f"{i}. [{q.category}] {q.content[:80]}...")

        # 4. 필터링
        print("\n4️⃣ 필터링: 기술 질문 + 어려움")
        print("-" * 60)
        results = filter_questions(
            category="technical",
            difficulty="hard",
            limit=3
        )
        for i, q in enumerate(results, 1):
            print(f"{i}. {q.content[:80]}...")

        # 5. 전문 검색
        print("\n5️⃣ 전문 검색: '멀티스레딩'")
        print("-" * 60)
        results = fulltext_search_questions("멀티스레딩", limit=3)
        for i, r in enumerate(results, 1):
            print(f"{i}. [순위: {r['rank']:.4f}] {r['content'][:80]}...")

        # 6. 페이지네이션
        print("\n6️⃣ 페이지네이션 (1페이지, 5개씩)")
        print("-" * 60)
        page_data = get_questions_paginated(page=1, page_size=5)
        print(f"전체: {page_data['total']}개, 페이지: {page_data['page']}/{page_data['total_pages']}")
        for i, q in enumerate(page_data['data'], 1):
            print(f"{i}. {q.content[:60]}...")

    print("\n" + "=" * 60)
    print("✅ 자연어DB 검색 테스트 완료!")
    print("=" * 60)
