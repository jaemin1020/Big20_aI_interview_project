import sys
import os
from sentence_transformers import SentenceTransformer
import numpy as np
import re
from typing import List, Dict, Any

# 스크립트 실행 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class InterviewQuestionGenerator:
    """
    BGE-M3 모델을 활용한 면접 질문 매칭 시스템
    (생성형 LLM이 아닌, 검색 기반의 질문 추천 시스템)
    """

    def __init__(self):
        print("🔄 모델을 로드하고 있습니다... (BGE-M3)")
        self.model = SentenceTransformer('BAAI/bge-m3')
        print("✅ 모델 로드 완료!")

        # 가상의 면접 질문 데이터베이스 (실제로는 DB에서 가져와야 함)
        self.question_bank = [
            # Python
            "Python의 GIL(Global Interpreter Lock)에 대해 설명하고, 이것이 멀티스레딩 성능에 미치는 영향을 설명해주세요.",
            "Python의 메모리 관리 메커니즘(GC, Reference Counting)에 대해 설명해주세요.",
            "Decorator(데코레이터)의 동작 원리와 사용 예시를 설명해주세요.",
            "Generator와 Iterator의 차이점은 무엇인가요?",
            "Python의 비동기 프로그래밍(asyncio)에 대해 설명해주세요.",

            # Web Framework (FastAPI/Django)
            "FastAPI와 Django의 주요 차이점은 무엇이며, 어떤 상황에서 FastAPI를 선택하시겠습니까?",
            "RESTful API의 멱등성(Idempotency)에 대해 설명하고, POST와 PUT의 차이를 설명해주세요.",
            "Dependency Injection(의존성 주입)이 FastAPI에서 어떻게 활용되는지 설명해주세요.",
            "ORM(Object-Relational Mapping)의 장단점과 N+1 문제 해결 방법을 설명해주세요.",
            "Middleware의 개념과 웹 프레임워크에서의 역할은 무엇인가요?",

            # Database (SQL/NoSQL)
            "RDBMS와 NoSQL의 차이점과 각각의 사용 사례를 설명해주세요.",
            "DB 인덱스(Index)의 동작 원리와 인덱스를 사용했을 때의 장단점을 설명해주세요.",
            "트랜잭션의 ACID 속성에 대해 설명해주세요.",
            "SQL Injection 공격이란 무엇이며, 이를 방지하기 위한 방법은 무엇인가요?",
            "정규화(Normalization)와 비정규화(Denormalization)의 차이는 무엇인가요?",

            # CS / Infra
            "Docker와 VM(Virtual Machine)의 차이점은 무엇인가요?",
            "CI/CD 파이프라인 구축 경험이 있다면, 어떤 도구를 사용했고 어떤 과정을 자동화했나요?",
            "프로세스(Process)와 스레드(Thread)의 차이점은 무엇인가요?",
            "TCP와 UDP의 차이점을 신뢰성 관점에서 설명해주세요.",
            "CORS(Cross-Origin Resource Sharing) 이슈란 무엇이며, 어떻게 해결하나요?",

            # 인성/협업
            "가장 도전적이었던 프로젝트 경험과 그 과정에서 어떻게 문제를 해결했는지 말씀해주세요.",
            "팀원과의 갈등이 발생했을 때 어떻게 해결하시나요?",
            "새로운 기술을 습득하는 자신만의 노하우가 있나요?",
            "코드 리뷰를 할 때 가장 중요하게 생각하는 점은 무엇인가요?",
            "실패했던 경험이 있다면, 그로부터 무엇을 배웠나요?"
        ]

        # 질문 DB 미리 임베딩
        print("🔄 질문 데이터베이스 임베딩 중...")
        self.question_embeddings = self.model.encode(self.question_bank, normalize_embeddings=True)
        print(f"✅ {len(self.question_bank)}개의 질문 데이터를 준비했습니다.")

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """입력 텍스트(이력서/자기소개) 분석"""

        # 간단한 키워드 추출 (비효율적이지만 데모용)
        keywords = ['Python', 'Django', 'FastAPI', 'Java', 'Spring', 'Docker', 'AWS', 'SQL', 'React']
        found_keywords = [k for k in keywords if k.lower() in text.lower()]

        return {
            'length': len(text),
            'keywords': found_keywords,
            'summary': text[:50] + "..." if len(text) > 50 else text
        }

    def generate_questions(self, input_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """입력 텍스트와 관련된 면접 질문 검색"""

        query_emb = self.model.encode([input_text], normalize_embeddings=True)[0]

        # 코사인 유사도 계산
        similarities = np.dot(self.question_embeddings, query_emb)

        # 상위 top_k개 추출
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                'question': self.question_bank[idx],
                'similarity': float(similarities[idx])
            })

        return results

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_screen()
    print("=" * 60)
    print("🤖 면접 질문 생성기 (Interview Question Generator)")
    print("   Powered by BGE-M3 (Retrieval-based)")
    print("=" * 60)
    print("이력서 내용이나 자기소개, 혹은 기술 스택을 입력하면")
    print("준비된 질문 DB에서 가장 적합한 면접 질문을 찾아줍니다.")
    print("-" * 60)

    generator = InterviewQuestionGenerator()

    while True:
        print("\n" + "=" * 60)
        print("텍스트를 입력하세요 (종료하려면 'q' 입력):")
        print("예시: '저는 파이썬과 FastAPI를 주로 사용했고 백엔드 개발 경험이 있습니다.'")

        user_input = input("\n입력 > ").strip()

        if user_input.lower() == 'q':
            print("👋 프로그램을 종료합니다.")
            break

        if not user_input:
            continue

        print("\n🔄 분석 및 질문 검색 중...")

        # 1. 텍스트 분석
        analysis = generator.analyze_text(user_input)
        if analysis['keywords']:
            print(f"💡 감지된 키워드: {', '.join(analysis['keywords'])}")

        # 2. 질문 매칭
        questions = generator.generate_questions(user_input, top_k=5)

        print(f"\n🎯 '{analysis['summary']}'에 대한 추천 면접 질문:")
        for i, item in enumerate(questions, 1):
            score = item['similarity']
            # 유사도가 너무 낮으면 표시 안 함 (옵션)
            relevance = ""
            if score > 0.6: relevance = "(매우 관련됨)"
            elif score > 0.4: relevance = "(관련됨)"
            else: relevance = "(약간 관련됨)"

            print(f"\n{i}. {item['question']}")
            print(f"   [유사도: {score:.4f} {relevance}]")

if __name__ == "__main__":
    main()
