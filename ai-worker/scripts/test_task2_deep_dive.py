
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
