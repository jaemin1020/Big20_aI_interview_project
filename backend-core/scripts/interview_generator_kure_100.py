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
    KURE-v1 모델을 활용한 면접 질문 매칭 시스템
    (nlpai-lab/KURE-v1) - 100개 질문 확장판
    """

    def __init__(self):
        print("🔄 모델을 로드하고 있습니다... (nlpai-lab/KURE-v1)")
        # trust_remote_code=True가 필요할 수 있음
        self.model = SentenceTransformer('nlpai-lab/KURE-v1', trust_remote_code=True)
        print("✅ 모델 로드 완료!")

        # 100개로 확장된 면접 질문 데이터베이스
        self.question_bank = [
            # 1. Python (Basic & Advanced) - 15개
            "Python의 GIL(Global Interpreter Lock)에 대해 설명하고, 이것이 멀티스레딩 성능에 미치는 영향을 설명해주세요.",
            "Python의 메모리 관리 메커니즘(GC, Reference Counting)에 대해 설명해주세요.",
            "Decorator(데코레이터)의 동작 원리와 사용 예시를 설명해주세요.",
            "Generator와 Iterator의 차이점은 무엇인가요?",
            "Python 3.x에서 추가된 주요 기능들에 대해 아는 대로 설명해주세요.",
            "패킹(Packing)과 언패킹(Unpacking)에 대해 설명해주세요.",
            "mutable 객체와 immutable 객체의 차이와 예시를 들어주세요.",
            "lambda 함수와 일반 함수의 차이는 무엇인가요?",
            "Python에서 다중 상속의 문제점(Diamond Problem)과 해결 방법(MRO)에 대해 설명해주세요.",
            "Context Manager(with 구문)의 동작 원리와 `__enter__`, `__exit__` 메서드에 대해 설명해주세요.",
            "List Comprehension의 장점과 단점은 무엇인가요?",
            "Python의 copy(얕은 복사)와 deepcopy(깊은 복사)의 차이점은?",
            "Duck Typing(덕 타이핑)이란 무엇인가요?",
            "Python 3.10에서 도입된 Pattern Matching(match case)에 대해 설명해주세요.",
            "Python 코드의 성능을 최적화하기 위해 사용해본 도구나 기법이 있나요?",

            # 2. Web Framework (FastAPI / Django) - 15개
            "FastAPI와 Django의 주요 차이점은 무엇이며, 어떤 상황에서 FastAPI를 선택하시겠습니까?",
            "FASTAPI의 비동기 처리 방식과 Uvicorn의 역할에 대해 설명해주세요.",
            "Pydantic 모델을 사용한 데이터 유효성 검사(Validation)의 장점은 무엇인가요?",
            "Django ORM과 SQLAlchemy(Core/ORM)의 차이점은 무엇인가요?",
            "Middleware의 개념과 웹 프레임워크에서의 역할은 무엇인가요?",
            "Django의 MTV 패턴과 일반적인 MVC 패턴의 차이점은?",
            "FastAPI에서 의존성 주입(Dependency Injection)을 사용하는 이유와 장점은?",
            "Django Signals의 용도와 주의할 점은 무엇인가요?",
            "SSR(Server Side Rendering)과 CSR(Client Side Rendering)의 차이와 장단점은?",
            "웹 소켓(Web Socket)을 사용해본 경험과 HTTP와의 차이점을 설명해주세요.",
            "API 버전 관리(Versioning)를 어떻게 처리하는 것이 좋을까요?",
            "로그인 인증 방식 세션/쿠키 방식과 JWT 토큰 방식의 차이점을 설명해주세요.",
            "OAuth 2.0 인증 흐름에 대해 간단히 설명해주세요.",
            "Swagger/OpenAPI 자동 문서화의 장점은 무엇이라고 생각하시나요?",
            "Celery와 같은 Task Queue를 사용해야 하는 상황은 언제인가요?",

            # 3. Database (RDBMS / NoSQL) - 15개
            "RDBMS와 NoSQL의 차이점과 각각의 사용 사례를 설명해주세요.",
            "DB 인덱스(Index)의 동작 원리와 인덱스를 사용했을 때의 장단점을 설명해주세요.",
            "트랜잭션의 ACID 속성에 대해 설명해주세요.",
            "정규화(Normalization)와 비정규화(Denormalization)의 차이는 무엇인가요?",
            "SQL Injection 공격이란 무엇이며, 이를 방지하기 위한 방법은 무엇인가요?",
            "DB Replication(복제)과 Sharding(샤딩)의 차이점은 무엇인가요?",
            "Isolation Level(격리 수준) 4가지에 대해 설명해주세요.",
            "Redis와 같은 인메모리 DB는 주로 어떤 용도로 사용하나요?",
            "N+1 쿼리 문제가 발생하는 이유와 해결 방법(Fetch Join, prefetch_related 등)은?",
            "낙관적 락(Optimistic Lock)과 비관적 락(Pessimistic Lock)의 차이는?",
            "Composite Index(복합 인덱스) 사용 시 컬럼 순서가 중요한 이유는?",
            "Stored Procedure(저장 프로시저)의 장단점은 무엇인가요?",
            "View와 Materialized View의 차이점은 무엇인가요?",
            "DB 마이그레이션 도구(Alembic, Flyway 등)를 사용해본 경험이 있나요?",
            "CAP 이론에 대해 설명하고, 실제 DB들이 어떤 속성을 선택했는지 예시를 들어주세요.",

            # 4. Architecture & Design Patterns - 10개
            "RESTful API의 6가지 제약 조건에 대해 설명해주세요.",
            "MSA(Microservices Architecture)와 Monolithic Architecture의 장단점을 비교해주세요.",
            "SOLID 원칙 중 'O'(OCP: 개방-폐쇄 원칙)에 대해 설명해주세요.",
            "싱글톤(Singleton) 패턴의 특징과 Python에서의 구현 방법은?",
            "의존성 역전 원칙(DIP)이란 무엇인가요?",
            "Factory 패턴을 사용하면 어떤 점이 좋은가요?",
            "MVC, MVP, MVVM 패턴의 차이점에 대해 아는 대로 설명해주세요.",
            "DDD(Domain Driven Design)의 핵심 개념(Entity, VO, Aggregate)에 대해 설명해주세요.",
            "이벤트 소싱(Event Sourcing)과 CQRS 패턴에 대해 들어보았거나 사용해본 적이 있나요?",
            "TDD(Test Driven Development)를 실무에 적용할 때의 장단점은 무엇인가요?",

            # 5. CS & Network - 15개
            "프로세스(Process)와 스레드(Thread)의 차이점은 무엇인가요?",
            "멀티 프로세스와 멀티 스레드의 장단점과 사용 사례를 비교해주세요.",
            "TCP와 UDP의 차이점을 신뢰성 관점에서 설명해주세요.",
            "3-Way Handshake와 4-Way Handshake 과정을 설명해주세요.",
            "HTTP와 HTTPS의 동작 방식 차이(TLS/SSL)에 대해 설명해주세요.",
            "DNS(Domain Name System) Lookup 과정에 대해 설명해주세요.",
            "OSI 7계층에 대해 간략히 설명해주세요.",
            "교착 상태(Deadlock)의 발생 조건 4가지와 해결 방법은?",
            "가상 메모리(Virtual Memory)와 페이지 부재(Page Fault)란 무엇인가요?",
            "GET 요청과 POST 요청의 차이점은 무엇인가요? (멱등성 포함)",
            "쿠키(Cookie)와 세션(Session), 로컬 스토리지(Local Storage)의 차이는?",
            "CORS(Cross-Origin Resource Sharing) 이슈란 무엇이며, 어떻게 해결하나요?",
            "Load Balancer(로드 밸런서)의 역할과 주요 알고리즘(Round Robin 등)은?",
            "CDN(Content Delivery Network)의 원리와 사용 이유는?",
            "Blocking I/O와 Non-Blocking I/O의 차이점은?",

            # 6. DevOps & Tools - 10개
            "Docker와 VM(Virtual Machine)의 차이점은 무엇인가요?",
            "Docker Image와 Container의 차이는 무엇인가요?",
            "Kubernetes(k8s)의 Pod, Service, Deployment 개념을 설명해주세요.",
            "CI/CD 파이프라인 구축 경험이 있다면, 어떤 도구를 사용했고 어떤 과정을 자동화했나요?",
            "Git Flow와 GitHub Flow, GitLab Flow 등 브랜치 전략에 대해 아는 대로 설명해주세요.",
            "Git의 Merge와 Rebase의 차이점은 무엇인가요?",
            "Docker Compose는 어떤 상황에서 유용한가요?",
            "IaC(Infrastructure as Code) 도구(Terraform, Ansible 등)를 사용해본 경험이 있나요?",
            "블루-그린(Blue-Green) 배포와 카나리(Canary) 배포의 차이는?",
            "서버 모니터링을 위해 사용해본 도구(Prometheus, Grafana 등)가 있나요?",

            # 7. Soft Skills & Behavioral - 10개
            "가장 도전적이었던 프로젝트 경험과 그 과정에서 어떻게 문제를 해결했는지 말씀해주세요.",
            "팀원과의 갈등이 발생했을 때 어떻게 해결하시나요?",
            "새로운 기술을 습득하는 자신만의 노하우가 있나요?",
            "코드 리뷰를 할 때 가장 중요하게 생각하는 점은 무엇인가요?",
            "실패했던 경험이 있다면, 그로부터 무엇을 배웠나요?",
            "개발자로서 자신의 가장 큰 강점과 약점은 무엇이라고 생각하나요?",
            "동료가 작성한 코드에서 치명적인 버그를 발견했다면 어떻게 대처하겠습니까?",
            "일정 압박이 심한 상황에서 품질과 속도 중 어떤 것을 우선시하겠습니까?",
            "오픈소스 프로젝트에 기여해본 경험이나 개발 커뮤니티 활동 경험이 있나요?",
            "5년 후 어떤 개발자가 되고 싶나요?",

            # 8. Algorithm & Data Structure - 10개
            "시간 복잡도(Big-O) 표기법에 대해 설명하고, O(1), O(log n), O(n)의 예시를 들어주세요.",
            "스택(Stack)과 큐(Queue)의 차이점과 사용 사례는?",
            "해시 테이블(Hash Table)의 동작 원리와 해시 충돌(Collision) 해결 방법은?",
            "이진 탐색 트리(BST)와 균형 이진 탐색 트리(AVL, Red-Black Tree)의 차이는?",
            "정렬 알고리즘 중 Quick Sort와 Merge Sort의 차이점과 각각의 시간 복잡도는?",
            "DFS(깊이 우선 탐색)와 BFS(너비 우선 탐색)의 차이와 구현 방법은?",
            "동적 계획법(Dynamic Programming)이란 무엇이며, 어떤 문제에 적용하나요?",
            "그래프(Graph)와 트리(Tree)의 차이점은?",
            "Priority Queue(우선순위 큐)는 내부적으로 어떻게 구현되나요? (Heap)",
            "문자열 매칭 알고리즘(KMP, Rabin-Karp 등)에 대해 아는 것이 있나요?"
        ]

        # 질문 DB 미리 임베딩
        print(f"🔄 질문 데이터베이스 임베딩 중... ({len(self.question_bank)}개 문항)")
        self.question_embeddings = self.model.encode(self.question_bank, normalize_embeddings=True)
        print("✅ 모든 질문 데이터 임베딩 완료")

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """입력 텍스트(이력서/자기소개) 분석"""

        keywords = ['Python', 'Django', 'FastAPI', 'Java', 'Spring', 'Docker', 'AWS', 'SQL', 'React', 'DevOps', 'CI/CD']
        found_keywords = [k for k in keywords if k.lower() in text.lower()]

        return {
            'length': len(text),
            'keywords': found_keywords,
            'summary': text[:50] + "..." if len(text) > 50 else text
        }

    def generate_questions(self, input_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
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
    print("🤖 면접 질문 생성기 100문항 Ver. (KURE-v1)")
    print("   Powered by nlpai-lab/KURE-v1")
    print("=" * 60)
    print(f"총 100개의 방대한 면접 질문 DB에서 최적의 질문을 추천해드립니다.")
    print("-" * 60)

    generator = InterviewQuestionGenerator()

    while True:
        print("\n" + "=" * 60)
        print("텍스트를 입력하세요 (종료하려면 'q' 입력):")
        print("예시: '저는 파이썬 백엔드 개발자이고 비동기 처리 경험이 있습니다.'")

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
            relevance = ""
            if score > 0.6: relevance = "⭐⭐⭐ (매우 높음)"
            elif score > 0.5: relevance = "⭐⭐ (높음)"
            elif score > 0.4: relevance = "⭐ (보통)"
            else: relevance = "(낮음)"

            print(f"\n{i}. {item['question']}")
            print(f"   [유사도: {score:.4f}] {relevance}")

if __name__ == "__main__":
    main()
