
import sys
import os
import json

# /app 경로 추가 (도커 내부 실행 기준)
sys.path.append("/app")

from tasks.question_generator import QuestionGenerator

def test_task1_similarity():
    print("=" * 60)
    print("🚀 [Task 1 Test] 질문 하나를 주고 유사질문 3개씩 만들어보기")
    print("Strategy: User's 'Self-Critique Loop' Prompt")
    print("=" * 60)

    gen = QuestionGenerator()

    # 테스트 데이터 (이력서 요약 및 원본 질문)
    resume_summary = """
    [기술 스택] Python, FastAPI, Docker, PostgreSQL, Snort
    [주요 경험]
    - KISA 보안 관제 센터 인턴 (3개월): 실시간 트래픽 분석 및 침해 사고 대응
    - Snort를 활용한 오픈소스 IDS/IPS 구축 프로젝트: SQL Injection 및 XSS 탐지 정규식 설계 및 성능 테스트 진행
    - FastAPI 기반 보안 모니터링 대시보드 개발: 비동기 처리를 통한 데이터 시각화 속도 40% 개선
    """

    original_question = "프로젝트 경험에 대해 자세히 말씀해 주세요."

    print(f"\n📄 [User Resume Summary]:\n{resume_summary.strip()}")
    print(f"\n❓ [Original Question]: {original_question}")
    print("\n" + "-"*40)
    print("🔧 Generating 3 specialized questions...")
    print("-" * 40)

    try:
        # 1:N 생성을 위해 새로 정의한 _specialize_question 호출
        # (테스트용이므로 비공개 메서드를 직접 호출)
        specialized_qs = gen._specialize_question(
            original_question=original_question,
            resume_summary=resume_summary,
            count=3
        )

        print("\n✨ [Final Questions] (Generated Variants):")
        for i, q in enumerate(specialized_qs, 1):
            print(f"{i}. {q}")

    except Exception as e:
        print(f"❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_task1_similarity()
