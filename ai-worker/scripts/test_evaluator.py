
import sys
import os
import json

# /app 경로를 추가하여 내부 모듈을 참조할 수 있게 함
sys.path.append("/app")

from tasks.evaluator import analyze_answer

def test_eval():
    print("=" * 60)
    print("🤖 AI Interview Answer Evaluation Test")
    print("Model: Llama-3.1-8B-Instruct (GGUF)")
    print("=" * 60)

    # 테스트 데이터
    # 실제 DB 업데이트를 피하기 위해 transcript_id 등은 임의의 값을 사용하지만,
    # analyze_answer 내에서 DB 함수를 호출하므로 에러가 날 수 있습니다.
    # 여기서는 핵심 로직인 모델 점수 산출을 테스트합니다.

    test_cases = [
        {
            "question": "지원동기를 말해보세요.",
            "answer": "안녕하세요, 두나무에 블록체인 개발자 직무로 지원한 정민호입니다. 두나무는 업비트를 통해 디지털 자산 거래의 신뢰를 구축하고 웹 3.0 생태계를 선도하는 기술 중심 기업입니다. 그래서 저는 두나무에서 일하면 큰 돈을 벌며 명예로운 일을 할 수 있을거라 생각해 지원했습니다. 어차피 다들 돈 벌려고 취업하는거 아닌가요? 일단 뽑아만 주십쇼. 실망시키지 않을겁니다."
        },
        {
            "question": "프로젝트로 Ethereum 기반의 NFT 발행 및 거래 플랫폼 프로토타입 개발를 하셨네요. 중앙 서버 없이 동작하는 분산 시스템의 아키텍처를 설명해줄 수 있나요?",
            "answer": "사랑해 널 이 느낌 이대로 그려왔던 헤매임의 끝 이 세상 속에서 반복되는 슬픔 이젠 안녕 수많은 알 수 없는 길 속에 희미한 빛을 난 쫓아가 언제까지라도 함께 하는 거야 다시 만난 나의 세계"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}")
        print(f"❓ Question: {case['question']}")
        print(f"💬 Answer: {case['answer']}")
        print("\n🚀 Evaluating...")

        try:
            # analyze_answer를 직접 호출 (DB 업데이트 부분에서 에러가 날 수 있으므로 예외처리 필요)
            # 실제 운영 환경에서는 Celery가 호출하지만 테스트를 위해 직접 실행
            result = analyze_answer(
                transcript_id=0, # 테스트용 dummy ID
                question_text=case['question'],
                answer_text=case['answer'],
                question_id=0 # 테스트용 dummy ID
            )

            print("\n✨ Evaluation Result:")
            print(json.dumps(result, indent=4, ensure_ascii=False))

        except Exception as e:
            print(f"❌ Evaluation error (likely DB connection): {str(e)}")
            print("Note: If DB functions fail, it's expected in a standalone script. Check the LLM output above if possible.")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_eval()
