
import sys
import os

# /app 경로를 추가하여 내부 모듈을 참조할 수 있게 함
sys.path.append("/app")

from tasks.question_generator import QuestionGenerator

def test_gen():
    print("=" * 60)
    print("🤖 AI Interview Question Generation Test")
    print("Model: Llama-3.1-8B-Instruct")
    print("=" * 60)

    try:
        gen = QuestionGenerator()
        position = "DBA (데이터베이스 관리자)"
        print(f"\n🔍 Target Position: {position}")
        print("🚀 Generating questions using Llama-3.1-8B...\n")

        # DB 재활용 없이 순수 LLM 생성 테스트 (reuse_ratio=0.0)
        # count=5: 5개의 질문 생성
        questions = gen.generate_questions(position, count=5, reuse_ratio=0.0)

        if not questions:
            print("❌ No questions were generated.")
            return

        print("✨ Generated Questions:")
        print("-" * 60)
        for i, q in enumerate(questions, 1):
            print(f"{i}. {q}")
        print("-" * 60)

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gen()
