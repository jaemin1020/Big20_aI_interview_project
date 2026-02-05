
import sys
import os

# /app 경로 추가 (도커 내부 실행 기준)
sys.path.append("/app")

from tasks.question_generator import QuestionGenerator

def test_task1_basic():
    print("=" * 60)
    print("🚀 [Task 1 - Basic Test] 질문 하나로 유사질문 3개 생성 (이력서 미포함)")
    print("Model Performance Test (Zero-Shot Augmentation)")
    print("=" * 60)

    gen = QuestionGenerator()

    # 테스트 질문
    original_question = "최근 가장 관심 있게 지켜보는 보안 트렌드나 기술은 무엇입니까?"

    print(f"\n❓ [Original Question]: {original_question}")
    print("\n" + "-"*40)
    print("🔧 Generating 3 similar variants...")
    print("-" * 40)

    try:
        # 이력서 없이 순수하게 질문 변항 생성
        variants = gen.generate_basic_variants(
            original_question=original_question,
            count=3
        )

        print("\n✨ [Final Questions] (3 Variants):")
        for i, q in enumerate(variants, 1):
            print(f"{i}. {q}")

    except Exception as e:
        print(f"❌ Error during generation: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_task1_basic()
