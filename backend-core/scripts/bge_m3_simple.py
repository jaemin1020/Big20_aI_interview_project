"""
BGE-M3 모델 사용 (sentence-transformers 사용)
- 간단한 설치 및 사용
- 다국어 임베딩
- 벡터 검색
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any
import time

class BGEM3Embedder:
    """BGE-M3 임베딩 생성기 (sentence-transformers 사용)"""

    def __init__(self):
        """BGE-M3 모델 초기화"""
        print("🔄 BGE-M3 모델 로딩 중...")
        print("   (처음 실행 시 모델 다운로드에 시간이 걸릴 수 있습니다)")
        start_time = time.time()

        # BGE-M3 모델 로드
        self.model = SentenceTransformer('BAAI/bge-m3')

        load_time = time.time() - start_time
        print(f"✅ 모델 로드 완료! ({load_time:.2f}초)")
        print(f"📦 모델: BAAI/bge-m3")
        print(f"📊 임베딩 차원: {self.model.get_sentence_embedding_dimension()}")
        print(f"🌍 지원 언어: 100+ (한국어, 영어, 중국어, 일본어 등)")
        print(f"📏 최대 토큰 길이: {self.model.max_seq_length}")

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
        normalize: bool = True
    ) -> np.ndarray:
        """
        텍스트를 임베딩 벡터로 변환

        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            show_progress: 진행률 표시 여부
            normalize: 벡터 정규화 여부 (코사인 유사도 계산 시 권장)

        Returns:
            임베딩 벡터 배열
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=normalize
        )

        return embeddings

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        if len(vec1.shape) == 1 and len(vec2.shape) == 1:
            # 이미 정규화된 벡터라면 내적만 계산
            return float(np.dot(vec1, vec2))
        else:
            # 정규화되지 않은 경우
            return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    def search(
        self,
        query: str,
        corpus: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        벡터 검색

        Args:
            query: 검색 쿼리
            corpus: 검색 대상 문서 리스트
            top_k: 반환할 결과 개수

        Returns:
            검색 결과 (문서 + 유사도)
        """
        # 임베딩 생성 (정규화됨)
        query_emb = self.encode([query])[0]
        corpus_embs = self.encode(corpus)

        # 유사도 계산 (정규화된 벡터이므로 내적 = 코사인 유사도)
        similarities = np.dot(corpus_embs, query_emb)

        # 결과 정리
        results = []
        for i, sim in enumerate(similarities):
            results.append({
                'index': i,
                'text': corpus[i],
                'similarity': float(sim)
            })

        # 정렬 및 상위 k개 반환
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]


# ==================== 사용 예시 ====================

def example_basic_usage():
    """기본 사용법"""
    print("\n" + "="*60)
    print("📝 기본 사용법")
    print("="*60)

    embedder = BGEM3Embedder()

    # 단일 텍스트 임베딩
    texts = [
        "Python에서 GIL이 무엇인가요?",
        "FastAPI의 장점은 무엇인가요?",
        "Docker와 Kubernetes의 차이점은?"
    ]

    embeddings = embedder.encode(texts)
    print(f"\n✅ {len(texts)}개 텍스트 임베딩 완료")
    print(f"   임베딩 shape: {embeddings.shape}")
    print(f"   첫 번째 벡터 샘플: {embeddings[0][:5]}...")


def example_search():
    """벡터 검색 예시"""
    print("\n" + "="*60)
    print("🔍 벡터 검색 예시")
    print("="*60)

    embedder = BGEM3Embedder()

    # 검색 대상 문서
    corpus = [
        "Python의 GIL(Global Interpreter Lock)은 한 번에 하나의 스레드만 Python 바이트코드를 실행할 수 있도록 제한하는 뮤텍스입니다.",
        "FastAPI는 Python 3.6+ 기반의 현대적이고 빠른 웹 프레임워크로, 자동 문서화와 타입 힌팅을 지원합니다.",
        "Docker는 컨테이너 플랫폼이고, Kubernetes는 컨테이너 오케스트레이션 도구입니다.",
        "React는 사용자 인터페이스를 구축하기 위한 JavaScript 라이브러리입니다.",
        "PostgreSQL은 강력한 오픈소스 관계형 데이터베이스 시스템입니다."
    ]

    # 검색 쿼리
    query = "파이썬 멀티스레딩 제약사항"

    print(f"\n🔎 검색 쿼리: '{query}'")
    print("\n검색 결과:")

    results = embedder.search(query, corpus, top_k=3)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. 유사도: {result['similarity']:.4f}")
        print(f"   내용: {result['text'][:80]}...")


def example_multilingual():
    """다국어 지원 예시"""
    print("\n" + "="*60)
    print("🌍 다국어 지원 예시")
    print("="*60)

    embedder = BGEM3Embedder()

    # 다국어 문서
    corpus = [
        "Python is a high-level programming language.",  # 영어
        "Python은 고수준 프로그래밍 언어입니다.",  # 한국어
        "Python是一种高级编程语言。",  # 중국어
        "Pythonは高水準プログラミング言語です。"  # 일본어
    ]

    query = "파이썬 프로그래밍"

    print(f"\n🔎 검색 쿼리: '{query}'")
    print("\n검색 결과 (다국어 문서):")

    results = embedder.search(query, corpus, top_k=4)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. 유사도: {result['similarity']:.4f}")
        print(f"   내용: {result['text']}")


def example_interview_questions():
    """면접 질문 검색 예시"""
    print("\n" + "="*60)
    print("💼 면접 질문 검색 예시")
    print("="*60)

    embedder = BGEM3Embedder()

    # 면접 질문 데이터베이스
    interview_questions = [
        "Python의 GIL(Global Interpreter Lock)에 대해 설명하고, 멀티스레딩 성능에 미치는 영향을 설명해주세요.",
        "Django와 FastAPI의 차이점은 무엇이며, 각각 어떤 상황에서 사용하는 것이 적합한가요?",
        "RESTful API 설계 원칙에 대해 설명하고, 좋은 API 설계 예시를 들어주세요.",
        "Docker와 가상 머신(VM)의 차이점은 무엇인가요?",
        "데이터베이스 인덱스의 동작 원리와 장단점을 설명해주세요.",
        "Git의 rebase와 merge의 차이점은 무엇인가요?",
        "SOLID 원칙에 대해 설명하고, 각 원칙의 예시를 들어주세요.",
        "비동기 프로그래밍(async/await)의 개념과 장점을 설명해주세요.",
    ]

    # 사용자 검색 쿼리
    user_queries = [
        "파이썬 멀티스레딩 성능 문제",
        "웹 프레임워크 선택 기준",
        "컨테이너 기술"
    ]

    for query in user_queries:
        print(f"\n🔎 검색: '{query}'")
        results = embedder.search(query, interview_questions, top_k=2)

        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result['similarity']:.3f}] {result['text'][:60]}...")


def example_performance_test():
    """성능 테스트"""
    print("\n" + "="*60)
    print("⚡ 성능 테스트")
    print("="*60)

    embedder = BGEM3Embedder()

    # 테스트 데이터 생성
    test_texts = [
        f"이것은 테스트 문장 {i}입니다. Python, FastAPI, Docker에 대한 내용입니다."
        for i in range(100)
    ]

    print(f"\n📊 {len(test_texts)}개 텍스트 임베딩 성능 테스트")

    # 배치 크기별 성능 비교
    for batch_size in [8, 16, 32]:
        start = time.time()
        embeddings = embedder.encode(test_texts, batch_size=batch_size)
        elapsed = time.time() - start

        print(f"   배치 크기 {batch_size:2d}: {elapsed:.2f}초 ({len(test_texts)/elapsed:.1f} texts/sec)")


if __name__ == "__main__":
    print("🚀 BGE-M3 모델 사용 가이드 (sentence-transformers)")
    print("="*60)

    try:
        # 1. 기본 사용법
        example_basic_usage()

        # 2. 벡터 검색
        example_search()

        # 3. 다국어 지원
        example_multilingual()

        # 4. 면접 질문 검색
        example_interview_questions()

        # 5. 성능 테스트 (선택)
        # example_performance_test()

        print("\n" + "="*60)
        print("✅ 모든 예시 실행 완료!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
