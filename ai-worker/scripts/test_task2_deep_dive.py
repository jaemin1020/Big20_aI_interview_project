
import sys
import os

# /app 경로 추가
sys.path.append("/app")

from tasks.question_generator import QuestionGenerator

def test_task2_deep_dive():
    print("=" * 60)
    print("🚀 [Task 2 Test] 질문 & 답변 기반 꼬리질문(Deep-Dive) 생성")
    print("Strategy: BS Detection & Technical Deep-Dive")
    print("=" * 60)

    gen = QuestionGenerator()

    # 테스트 데이터 (이전 대화 맥락 + 현재 지원자 답변)
    test_cases = [
        {
            "history": "보안 정책 강화로 인해 개발팀이나 현업 부서의 업무가 불편해진 상황입니다. 거세게 항의하는 동료를 어떻게 설득하시겠습니까??",
            "answer": "저는 보안을 '통제'가 아닌 '지원'의 관점으로 접근하겠습니다. 먼저 상대방의 불만을 경청하여 업무의 어떤 단계에서 병목 현상이 생기는지 정확히 파악하겠습니다. 단순히 규정을 강조하기보다, **'보안은 서비스의 신뢰를 완성하는 마지막 퍼즐'임을 공유하겠습니다. 예를 들어, 보안이 무너졌을 때 발생할 복구 비용과 신뢰 하락이 결과적으로 개발팀의 성과에도 악영향을 줄 수 있음을 수치로 설명하며, 현업의 불편함을 최소화할 수 있는 '맞춤형 보안 가이드'를 함께 만들어가자고 제안하겠습니다."
        },
        {
            "history": "보안 전문가로서 본인이 내린 판단이 옳다고 확신하지만, 팀원 대다수가 다른 의견을 낸다면 어떻게 행동하시겠습니까?",
            "answer": "제 판단의 근거를 데이터(로그, 취약점 분석 결과)를 통해 객관적으로 다시 검토하겠습니다. 그럼에도 다수의 의견과 대립한다면, **제 의견이 '옳음'을 증명하기보다 '우리 팀이 놓칠 수 있는 리스크'**를 짚어주는 데 집중하겠습니다. 팀의 결정을 따르되, 제가 우려하는 지점에 대해서는 별도의 모니터링을 강화하거나 사후 대책(Roll-back plan)을 미리 제안하여 팀 전체의 안전망을 확보하는 방향으로 협력하겠습니다. 보안은 독단적인 영웅주의보다 조직적인 방어망 구축이 더 중요하기 때문입니다."
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Case {i}")
        print(f"📜 [History]: {case['history']}")
        print(f"💬 [User Answer]: {case['answer']}")
        print("\n🚀 Generating Deep-Dive Question...")

        try:
            # Task 2 전용 메서드 호출
            follow_up = gen.generate_deep_dive_question(
                history=case['history'],
                current_answer=case['answer']
            )
            print(f"\n✨ [AI Tail Question]:\n{follow_up}")

        except Exception as e:
            print(f"❌ Error: {e}")
        print("-" * 60)

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_task2_deep_dive()
