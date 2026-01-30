"""
이력서 기반 면접 질문 생성기
- BGE-M3 모델 활용
- 기술 스택, 경력, 프로젝트 기반 맞춤형 질문 생성
"""

from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select, text, and_
import sys
import os

# 상위 디렉토리의 모듈 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from models import Question, QuestionCategory, QuestionDifficulty
from scripts.resume_parser import ResumeParser


class InterviewQuestionGenerator:
    """이력서 기반 면접 질문 생성"""

    def __init__(self, model_name: str = 'BAAI/bge-m3'):
        """
        Args:
            model_name: 사용할 임베딩 모델 (기본: BGE-M3)
        """
        print(f"🔄 {model_name} 모델 로딩 중...")
        self.model = SentenceTransformer(model_name)
        print("✅ 모델 로드 완료!")

    def generate_questions_from_resume(
        self,
        resume_data: Dict[str, Any],
        num_questions: int = 10,
        difficulty_distribution: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        이력서 기반 맞춤형 질문 생성

        Args:
            resume_data: 파싱된 이력서 데이터
            num_questions: 생성할 질문 개수
            difficulty_distribution: 난이도 분포 (예: {"easy": 2, "medium": 5, "hard": 3})

        Returns:
            생성된 질문 리스트
        """

        # 경력에 따른 기본 난이도 분포 설정
        if difficulty_distribution is None:
            difficulty_distribution = self._get_default_difficulty_distribution(
                resume_data.get('experience_years', 0)
            )

        questions = []

        # 1. 기술 스택 기반 질문 (50%)
        tech_count = int(num_questions * 0.5)
        if resume_data.get('skills'):
            tech_questions = self._get_tech_based_questions(
                resume_data['skills'],
                tech_count,
                difficulty_distribution
            )
            questions.extend(tech_questions)

        # 2. 프로젝트/경험 기반 질문 (30%)
        exp_count = int(num_questions * 0.3)
        if resume_data.get('raw_text'):
            exp_questions = self._get_experience_based_questions(
                resume_data['raw_text'],
                exp_count
            )
            questions.extend(exp_questions)

        # 3. 일반 질문 (20%)
        general_count = num_questions - len(questions)
        if general_count > 0:
            general_questions = self._get_general_questions(
                resume_data.get('experience_years', 0),
                general_count,
                difficulty_distribution
            )
            questions.extend(general_questions)

        # 중복 제거 및 개수 조정
        unique_questions = self._remove_duplicates(questions)
        return unique_questions[:num_questions]

    def _get_default_difficulty_distribution(self, experience_years: int) -> Dict[str, int]:
        """경력에 따른 기본 난이도 분포"""
        if experience_years == 0:
            # 신입: 쉬움 60%, 보통 30%, 어려움 10%
            return {"easy": 6, "medium": 3, "hard": 1}
        elif experience_years < 3:
            # 주니어: 쉬움 30%, 보통 50%, 어려움 20%
            return {"easy": 3, "medium": 5, "hard": 2}
        elif experience_years < 7:
            # 미들: 쉬움 20%, 보통 50%, 어려움 30%
            return {"easy": 2, "medium": 5, "hard": 3}
        else:
            # 시니어: 쉬움 10%, 보통 40%, 어려움 50%
            return {"easy": 1, "medium": 4, "hard": 5}

    def _get_tech_based_questions(
        self,
        skills: List[str],
        count: int,
        difficulty_dist: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """기술 스택 기반 질문 검색"""
        questions = []

        with Session(engine) as session:
            for skill in skills[:5]:  # 상위 5개 기술만
                # 기술 관련 검색 쿼리
                query = f"{skill} 기술 면접 질문 개념 원리"
                query_emb = self.model.encode(query, normalize_embeddings=True).tolist()

                # VectorDB에서 유사 질문 검색
                stmt = select(
                    Question,
                    text(f"embedding <=> '{query_emb}' AS distance")
                ).where(
                    and_(
                        Question.is_active == True,
                        Question.embedding.isnot(None)
                    )
                ).order_by(text("distance")).limit(2)

                results = session.exec(stmt).all()

                for result in results:
                    question = result[0]
                    similarity = 1 - result[1]

                    questions.append({
                        'id': question.id,
                        'content': question.content,
                        'category': question.category,
                        'difficulty': question.difficulty,
                        'similarity': similarity,
                        'source': f'기술: {skill}'
                    })

                if len(questions) >= count:
                    break

        return questions[:count]

    def _get_experience_based_questions(
        self,
        resume_text: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """경험/프로젝트 기반 질문 검색"""
        questions = []

        # 이력서 전체 텍스트로 유사 질문 검색
        resume_emb = self.model.encode(resume_text, normalize_embeddings=True).tolist()

        with Session(engine) as session:
            stmt = select(
                Question,
                text(f"embedding <=> '{resume_emb}' AS distance")
            ).where(
                and_(
                    Question.is_active == True,
                    Question.embedding.isnot(None),
                    Question.category.in_([
                        QuestionCategory.EXPERIENCE,
                        QuestionCategory.PROJECT,
                        QuestionCategory.PROBLEM_SOLVING
                    ])
                )
            ).order_by(text("distance")).limit(count)

            results = session.exec(stmt).all()

            for result in results:
                question = result[0]
                similarity = 1 - result[1]

                questions.append({
                    'id': question.id,
                    'content': question.content,
                    'category': question.category,
                    'difficulty': question.difficulty,
                    'similarity': similarity,
                    'source': '경험 기반'
                })

        return questions

    def _get_general_questions(
        self,
        experience_years: int,
        count: int,
        difficulty_dist: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """일반 질문 (난이도 기반)"""
        questions = []

        # 난이도 결정
        if experience_years < 2:
            target_difficulty = QuestionDifficulty.EASY
        elif experience_years < 5:
            target_difficulty = QuestionDifficulty.MEDIUM
        else:
            target_difficulty = QuestionDifficulty.HARD

        with Session(engine) as session:
            stmt = select(Question).where(
                and_(
                    Question.is_active == True,
                    Question.difficulty == target_difficulty
                )
            ).limit(count)

            results = session.exec(stmt).all()

            for question in results:
                questions.append({
                    'id': question.id,
                    'content': question.content,
                    'category': question.category,
                    'difficulty': question.difficulty,
                    'similarity': 0.0,
                    'source': f'일반 ({target_difficulty})'
                })

        return questions

    def _remove_duplicates(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 질문 제거"""
        seen_ids = set()
        unique_questions = []

        for q in questions:
            if q['id'] not in seen_ids:
                seen_ids.add(q['id'])
                unique_questions.append(q)

        return unique_questions

    def generate_interview_report(
        self,
        resume_data: Dict[str, Any],
        questions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """면접 리포트 생성"""

        # 카테고리별 질문 수
        category_count = {}
        for q in questions:
            cat = q['category']
            category_count[cat] = category_count.get(cat, 0) + 1

        # 난이도별 질문 수
        difficulty_count = {}
        for q in questions:
            diff = q['difficulty']
            difficulty_count[diff] = difficulty_count.get(diff, 0) + 1

        return {
            'candidate_name': resume_data.get('name', 'Unknown'),
            'experience_years': resume_data.get('experience_years', 0),
            'skills': resume_data.get('skills', []),
            'total_questions': len(questions),
            'category_distribution': category_count,
            'difficulty_distribution': difficulty_count,
            'questions': questions
        }


# ==================== 전체 워크플로우 ====================

def process_resume_and_generate_interview(
    resume_file_path: str,
    num_questions: int = 10
) -> Dict[str, Any]:
    """
    이력서 처리 및 면접 질문 생성 전체 워크플로우

    Args:
        resume_file_path: 이력서 파일 경로
        num_questions: 생성할 질문 개수

    Returns:
        면접 리포트
    """

    print("=" * 60)
    print("🎯 이력서 기반 면접 질문 생성 시스템")
    print("=" * 60)

    # 1. 이력서 파싱
    print("\n📄 1단계: 이력서 파싱 중...")
    parser = ResumeParser()
    resume_data = parser.parse_resume(resume_file_path)

    print(f"✅ 파싱 완료!")
    print(f"   - 이름: {resume_data.get('name', 'N/A')}")
    print(f"   - 경력: {resume_data.get('experience_years', 0)}년")
    print(f"   - 기술 스택: {len(resume_data.get('skills', []))}개")

    # 2. 질문 생성
    print("\n🎯 2단계: 맞춤형 면접 질문 생성 중...")
    generator = InterviewQuestionGenerator()
    questions = generator.generate_questions_from_resume(
        resume_data,
        num_questions=num_questions
    )

    print(f"✅ {len(questions)}개 질문 생성 완료!")

    # 3. 리포트 생성
    print("\n📊 3단계: 면접 리포트 생성 중...")
    report = generator.generate_interview_report(resume_data, questions)

    print("✅ 리포트 생성 완료!")

    # 4. 결과 출력
    print("\n" + "=" * 60)
    print("📋 면접 질문 리스트")
    print("=" * 60)

    for i, q in enumerate(questions, 1):
        print(f"\n{i}. [{q['category']}] [{q['difficulty']}]")
        print(f"   {q['content'][:100]}...")
        print(f"   출처: {q['source']} | 유사도: {q['similarity']:.3f}")

    print("\n" + "=" * 60)
    print("📊 통계")
    print("=" * 60)
    print(f"총 질문 수: {report['total_questions']}")
    print(f"\n카테고리별:")
    for cat, count in report['category_distribution'].items():
        print(f"  - {cat}: {count}개")
    print(f"\n난이도별:")
    for diff, count in report['difficulty_distribution'].items():
        print(f"  - {diff}: {count}개")

    return report


# ==================== 사용 예시 ====================

if __name__ == "__main__":
    import sys

    # 샘플 이력서 생성 및 테스트
    print("🚀 이력서 기반 면접 질문 생성 테스트")

    # 샘플 이력서 생성
    sample_text = """
이름: 김개발
이메일: kim.dev@example.com
전화번호: 010-1234-5678

[경력]
총 경력: 3년

[기술 스택]
- 백엔드: Python, FastAPI, Django, PostgreSQL
- 프론트엔드: React, TypeScript
- 인프라: Docker, Kubernetes, AWS

[프로젝트 경험]
1. 전자상거래 플랫폼 개발
   - FastAPI를 사용한 REST API 서버 개발
   - PostgreSQL 데이터베이스 설계 및 최적화
"""

    sample_file = "test_resume.txt"
    with open(sample_file, 'w', encoding='utf-8') as f:
        f.write(sample_text)

    try:
        # 면접 질문 생성
        report = process_resume_and_generate_interview(
            sample_file,
            num_questions=10
        )

        print("\n" + "=" * 60)
        print("✅ 테스트 완료!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 샘플 파일 삭제
        import os
        if os.path.exists(sample_file):
            os.remove(sample_file)
