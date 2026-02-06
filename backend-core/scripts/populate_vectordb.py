"""
VectorDB 데이터 삽입 스크립트
- 질문과 답변에 임베딩을 생성하여 저장
- sentence-transformers를 사용한 한국어 임베딩
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select
from database import engine, init_db
from models import Question, AnswerBank, QuestionCategory, QuestionDifficulty

# 임베딩 모델 로드
print("🔄 임베딩 모델 로딩 중...")
print("📦 모델: jhgan/ko-sroberta-multitask (768차원)")
model = SentenceTransformer('jhgan/ko-sroberta-multitask')
print("✅ 모델 로드 완료!\n")

def add_question_with_embedding(
    session: Session,
    content: str,
    category: QuestionCategory,
    difficulty: QuestionDifficulty,
    company: str = None,
    industry: str = None,
    position: str = None,
    rubric: dict = None
):
    """질문과 임베딩을 함께 저장"""

    # 1. 임베딩 생성
    print(f"🔄 임베딩 생성 중: {content[:50]}...")
    embedding = model.encode(content).tolist()

    # 2. Question 객체 생성
    question = Question(
        content=content,
        category=category,
        difficulty=difficulty,
        embedding=embedding,
        company=company,
        industry=industry,
        position=position,
        rubric_json=rubric or {}
    )

    # 3. DB 저장
    session.add(question)
    session.commit()
    session.refresh(question)

    print(f"✅ 질문 저장 완료 (ID: {question.id})\n")
    return question

def add_answer_with_embedding(
    session: Session,
    question_id: int,
    answer_text: str,
    score: float,
    company: str = None,
    industry: str = None,
    position: str = None,
    feedback: str = None
):
    """답변과 임베딩을 함께 저장"""

    # 1. 임베딩 생성
    print(f"🔄 답변 임베딩 생성 중... (점수: {score})")
    embedding = model.encode(answer_text).tolist()

    # 2. AnswerBank 객체 생성
    answer = AnswerBank(
        question_id=question_id,
        answer_text=answer_text,
        embedding=embedding,
        score=score,
        company=company,
        industry=industry,
        position=position,
        evaluator_feedback=feedback
    )

    # 3. DB 저장
    session.add(answer)
    session.commit()
    session.refresh(answer)

    print(f"✅ 답변 저장 완료 (ID: {answer.id})\n")
    return answer

def populate_sample_data():
    """샘플 데이터 삽입"""

    print("=" * 60)
    print("📊 VectorDB 샘플 데이터 삽입 시작")
    print("=" * 60 + "\n")

    # DB 초기화
    init_db()

    with Session(engine) as session:
        # ==================== 기술 질문 ====================
        print("🔧 [기술 질문] 카테고리 삽입 중...\n")

        # 질문 1: Python GIL
        q1 = add_question_with_embedding(
            session,
            content="Python에서 GIL(Global Interpreter Lock)이 무엇인지 설명하고, 멀티스레딩 성능에 미치는 영향을 설명해주세요.",
            category=QuestionCategory.TECHNICAL,
            difficulty=QuestionDifficulty.HARD,
            company="카카오",
            industry="IT",
            position="Backend 개발자",
            rubric={
                "정확성": 30,
                "깊이": 30,
                "실무 적용": 40
            }
        )

        add_answer_with_embedding(
            session,
            question_id=q1.id,
            answer_text="""GIL은 Python 인터프리터가 한 번에 하나의 스레드만 Python 바이트코드를 실행하도록 제한하는 뮤텍스입니다.
            이는 CPython의 메모리 관리(reference counting)를 thread-safe하게 만들기 위한 설계입니다.

            멀티스레딩 성능에 미치는 영향:
            1. CPU-bound 작업: GIL로 인해 멀티스레드가 병렬 실행되지 않아 성능 향상이 없습니다.
            2. I/O-bound 작업: I/O 대기 중에는 GIL을 해제하므로 멀티스레딩이 효과적입니다.

            실무 해결 방법:
            - CPU-bound: multiprocessing 모듈 사용 (프로세스 단위 병렬화)
            - I/O-bound: asyncio 또는 threading 사용
            - C 확장: NumPy, Pandas 등은 GIL을 우회하여 병렬 처리 가능""",
            score=95.0,
            company="카카오",
            industry="IT",
            position="Backend 개발자",
            feedback="GIL의 개념, 영향, 해결 방법을 모두 정확하고 깊이 있게 설명함. 실무 적용 사례도 구체적."
        )

        # 질문 2: FastAPI vs Flask
        q2 = add_question_with_embedding(
            session,
            content="FastAPI와 Flask의 차이점을 설명하고, 어떤 상황에서 FastAPI를 선택하는 것이 유리한지 설명해주세요.",
            category=QuestionCategory.TECHNICAL,
            difficulty=QuestionDifficulty.MEDIUM,
            company="네이버",
            industry="IT",
            position="Backend 개발자",
            rubric={
                "비교 정확성": 40,
                "실무 경험": 30,
                "기술 이해도": 30
            }
        )

        add_answer_with_embedding(
            session,
            question_id=q2.id,
            answer_text="""주요 차이점:
            1. 성능: FastAPI는 Starlette 기반으로 비동기 처리를 지원하여 높은 처리량을 제공합니다.
            2. 타입 힌팅: FastAPI는 Pydantic을 사용한 자동 검증과 문서화를 지원합니다.
            3. 문서화: FastAPI는 Swagger UI와 ReDoc을 자동 생성합니다.

            FastAPI가 유리한 상황:
            - 고성능 API가 필요한 경우 (비동기 처리)
            - 자동 문서화와 타입 안정성이 중요한 경우
            - 마이크로서비스 아키텍처
            - 실시간 데이터 처리 (WebSocket 지원)

            Flask가 유리한 상황:
            - 간단한 웹 애플리케이션
            - 레거시 시스템과의 호환성
            - 풍부한 확장 생태계 활용""",
            score=88.0,
            company="네이버",
            industry="IT",
            position="Backend 개발자",
            feedback="두 프레임워크의 차이를 명확히 이해하고, 상황별 선택 기준을 잘 제시함."
        )

        # 질문 3: 데이터베이스 인덱스
        q3 = add_question_with_embedding(
            session,
            content="데이터베이스 인덱스의 동작 원리와 장단점을 설명하고, 인덱스를 사용하면 안 되는 경우를 설명해주세요.",
            category=QuestionCategory.TECHNICAL,
            difficulty=QuestionDifficulty.MEDIUM,
            industry="IT",
            position="Backend 개발자",
            rubric={
                "원리 이해": 35,
                "장단점 분석": 35,
                "실무 적용": 30
            }
        )

        add_answer_with_embedding(
            session,
            question_id=q3.id,
            answer_text="""동작 원리:
            인덱스는 B-Tree 또는 Hash 구조로 데이터의 위치를 빠르게 찾을 수 있는 자료구조입니다.
            SELECT 쿼리 시 전체 테이블 스캔 대신 인덱스를 통해 O(log n) 시간에 검색합니다.

            장점:
            - 검색 속도 향상 (WHERE, JOIN, ORDER BY)
            - 유니크 제약 조건 강제

            단점:
            - 추가 저장 공간 필요
            - INSERT/UPDATE/DELETE 시 인덱스 갱신 오버헤드
            - 잘못된 인덱스는 오히려 성능 저하

            인덱스를 사용하면 안 되는 경우:
            1. 테이블 크기가 작을 때 (수백 건 이하)
            2. 카디널리티가 낮은 컬럼 (예: 성별, boolean)
            3. 자주 변경되는 컬럼
            4. 전체 데이터의 대부분을 조회하는 경우""",
            score=92.0,
            industry="IT",
            position="Backend 개발자",
            feedback="인덱스의 원리와 장단점을 정확히 이해하고, 실무 적용 시 주의사항을 잘 설명함."
        )

        # ==================== 행동 질문 ====================
        print("💬 [행동 질문] 카테고리 삽입 중...\n")

        # 질문 4: 팀 협업
        q4 = add_question_with_embedding(
            session,
            content="팀에서 의견 충돌이 발생했을 때 어떻게 해결하셨나요? 구체적인 사례를 들어 설명해주세요.",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=QuestionDifficulty.MEDIUM,
            industry="IT",
            position="Backend 개발자"
        )

        add_answer_with_embedding(
            session,
            question_id=q4.id,
            answer_text="""상황(Situation):
            이전 프로젝트에서 API 설계 방식에 대해 팀원과 의견이 달랐습니다.
            저는 RESTful API를, 팀원은 GraphQL을 선호했습니다.

            과제(Task):
            프로젝트 일정이 촉박한 상황에서 빠른 합의가 필요했습니다.

            행동(Action):
            1. 각자의 방식을 간단한 프로토타입으로 구현했습니다.
            2. 성능 테스트와 유지보수성을 비교 분석했습니다.
            3. 데이터를 기반으로 팀 회의에서 논의했습니다.

            결과(Result):
            RESTful API가 우리 프로젝트의 요구사항에 더 적합하다는 결론을 내렸고,
            팀원도 데이터 기반 의사결정에 동의했습니다. 프로젝트는 성공적으로 완료되었습니다.""",
            score=88.0,
            industry="IT",
            position="Backend 개발자",
            feedback="STAR 기법을 활용하여 구체적이고 설득력 있게 설명함. 데이터 기반 의사결정 강조."
        )

        # 질문 5: 실패 경험
        q5 = add_question_with_embedding(
            session,
            content="프로젝트에서 실패한 경험과 그로부터 배운 점을 설명해주세요.",
            category=QuestionCategory.BEHAVIORAL,
            difficulty=QuestionDifficulty.MEDIUM,
            industry="IT",
            position="Backend 개발자"
        )

        add_answer_with_embedding(
            session,
            question_id=q5.id,
            answer_text="""상황(Situation):
            첫 번째 프로젝트에서 성능 최적화 없이 기능 개발에만 집중했습니다.

            과제(Task):
            출시 직전 부하 테스트에서 서버가 다운되는 문제가 발생했습니다.

            행동(Action):
            1. 프로파일링 도구로 병목 지점을 파악했습니다.
            2. N+1 쿼리 문제를 발견하고 즉시 수정했습니다.
            3. 캐싱 전략을 도입하여 응답 시간을 80% 개선했습니다.

            결과(Result):
            출시는 2주 연기되었지만, 안정적인 서비스를 제공할 수 있었습니다.

            배운 점:
            - 개발 초기부터 성능을 고려해야 함
            - 정기적인 부하 테스트의 중요성
            - 모니터링과 로깅의 필요성""",
            score=85.0,
            industry="IT",
            position="Backend 개발자",
            feedback="실패를 솔직히 인정하고, 구체적인 해결 과정과 교훈을 잘 설명함."
        )

        # ==================== 상황 질문 ====================
        print("🎯 [상황 질문] 카테고리 삽입 중...\n")

        # 질문 6: 긴급 장애 대응
        q6 = add_question_with_embedding(
            session,
            content="서비스 운영 중 긴급 장애가 발생했을 때 어떻게 대응하시겠습니까?",
            category=QuestionCategory.SITUATIONAL,
            difficulty=QuestionDifficulty.HARD,
            company="토스",
            industry="IT",
            position="Backend 개발자"
        )

        add_answer_with_embedding(
            session,
            question_id=q6.id,
            answer_text="""1단계: 즉시 대응 (0-5분)
            - 모니터링 대시보드에서 에러 로그 확인
            - 영향 범위 파악 (전체 서비스 vs 특정 기능)
            - 필요시 긴급 롤백 결정

            2단계: 원인 분석 (5-30분)
            - 로그 분석 및 에러 추적
            - 최근 배포 내역 확인
            - 인프라 상태 점검 (CPU, 메모리, 네트워크)

            3단계: 임시 조치 (30분-1시간)
            - 핫픽스 배포 또는 롤백
            - 사용자 공지 (상황 전파)

            4단계: 사후 조치
            - 포스트모템 작성
            - 재발 방지 대책 수립
            - 모니터링 알림 개선""",
            score=90.0,
            company="토스",
            industry="IT",
            position="Backend 개발자",
            feedback="체계적인 장애 대응 프로세스를 단계별로 명확히 제시함. 실무 경험이 느껴짐."
        )

        # ==================== 문화 적합성 ====================
        print("🏢 [문화 적합성] 카테고리 삽입 중...\n")

        # 질문 7: 업무 스타일
        q7 = add_question_with_embedding(
            session,
            content="혼자 일하는 것과 팀으로 일하는 것 중 어느 것을 선호하시나요? 그 이유는 무엇인가요?",
            category=QuestionCategory.CULTURAL_FIT,
            difficulty=QuestionDifficulty.EASY,
            industry="IT",
            position="Backend 개발자"
        )

        add_answer_with_embedding(
            session,
            question_id=q7.id,
            answer_text="""저는 팀으로 일하는 것을 선호합니다.

            이유:
            1. 지식 공유: 팀원들과 코드 리뷰를 통해 서로 배울 수 있습니다.
            2. 문제 해결: 복잡한 문제를 다양한 관점에서 접근할 수 있습니다.
            3. 동기 부여: 팀의 목표를 향해 함께 나아가는 것이 더 큰 성취감을 줍니다.

            다만, 집중이 필요한 작업(알고리즘 설계, 복잡한 로직 구현)은
            혼자 작업한 후 팀과 공유하는 방식을 선호합니다.

            균형 잡힌 접근:
            - 개인 작업: 깊은 집중이 필요한 개발
            - 팀 작업: 설계, 리뷰, 문제 해결, 지식 공유""",
            score=82.0,
            industry="IT",
            position="Backend 개발자",
            feedback="팀워크의 중요성을 이해하면서도 개인 작업의 필요성도 인정하는 균형 잡힌 답변."
        )

        print("=" * 60)
        print("🎉 샘플 데이터 삽입 완료!")
        print("=" * 60)
        print(f"\n📊 통계:")
        print(f"  - 질문: 7개")
        print(f"  - 답변: 7개")
        print(f"  - 카테고리: 기술(3), 행동(2), 상황(1), 문화(1)")
        print(f"  - 난이도: 쉬움(1), 보통(4), 어려움(2)")
        print(f"\n💡 다음 단계:")
        print(f"  1. 벡터 검색 API 엔드포인트 추가")
        print(f"  2. 유사 질문 추천 기능 구현")
        print(f"  3. 답변 평가 시스템 구축")

if __name__ == "__main__":
    try:
        populate_sample_data()
    except Exception as e:
        print(f"\n❌ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
