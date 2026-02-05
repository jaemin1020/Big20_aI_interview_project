
import sys
import os

# /app 경로 추가 (도커 환경 대응)
sys.path.append("/app")

from tasks.question_generator import QuestionGenerator

def test_task3_answer_analysis():
    print("=" * 60)
    print("🚀 [Task 3 Test] 제시된 답변 정밀 분석 (Detailed Answer Analysis)")
    print("Focus: 기술적 구체성, 수치/성과, 논리적 정합성, 실무 적용성")
    print("=" * 60)

    gen = QuestionGenerator()

    # 테스트 데이터 (이전 질문 + 지원자 답변)
    test_cases = [
        {
            "history": "실시간 보안 위협에 대해 즉각적인 차단(Blocking)을 원하는 관리자와 '서비스 가용성'을 중시하는 운영팀 사이의 갈등을 어떻게 해결했습니까?",
            "answer": "'양치기 소년' 효과, 즉 잦은 오탐 알람이 실제 정교한 APT 공격 시 대응 집중력을 떨어뜨려 **'알람 피로도'**를 유발할 수 있음을 기술적 근거(탐지율 대비 오탐율 그래프 등)로 설득했습니다. 대신, 즉시 통보하지 않는 이벤트들도 '엣지 로깅' 시스템에 정교하게 기록하여 추후 사후 분석(Forensics) 및 정책 업데이트의 기초 데이터로 활용하는 '단계적 방어 체계'를 제안함으로써 양측의 합의를 도출했습니다."
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Case {i}")
        print(f"📜 [Question]: {case['history']}")
        print(f"💬 [User Answer]: {case['answer']}")
        print("\n🔍 Analyzing Answer in detail...")

        try:
            # Task 3 전용 메서드 호출
            analysis = gen.generate_answer_analysis(
                history=case['history'],
                current_answer=case['answer']
            )
            print(f"\n✨ [Detailed Analysis]:\n{analysis}")

        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 60)

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_task3_answer_analysis()
