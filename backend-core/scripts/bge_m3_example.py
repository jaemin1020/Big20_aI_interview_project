"""
BGE-M3 모델 사용 예시
- 다국어 임베딩 생성
- 벡터 검색
- 성능 비교
"""

from FlagEmbedding import BGEM3FlagModel
import numpy as np
from typing import List, Dict, Any
import time

class BGEM3Embedder:
    """BGE-M3 임베딩 생성기"""

    def __init__(self, use_fp16: bool = True):
        """
        Args:
            use_fp16: FP16 사용 여부 (메모리 절약, 속도 향상)
        """
        print("🔄 BGE-M3 모델 로딩 중...")
        start_time = time.time()

        self.model = BGEM3FlagModel(
            'BAAI/bge-m3',
            use_fp16=use_fp16  # GPU 사용 시 True 권장
        )

        load_time = time.time() - start_time
        print(f"✅ 모델 로드 완료! ({load_time:.2f}초)")
        print(f"📦 모델: BAAI/bge-m3")
        print(f"📊 임베딩 차원: 1024")
        print(f"🌍 지원 언어: 100+ (한국어, 영어, 중국어 등)")

    def encode(
        self,
        texts: List[str],
        batch_size: int = 12,
        max_length: int = 512
    ) -> np.ndarray:
        """
        텍스트를 임베딩 벡터로 변환

        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            max_length: 최대 토큰 길이

        Returns:
            임베딩 벡터 배열 (shape: [len(texts), 1024])
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            max_length=max_length
        )['dense_vecs']

        return embeddings

    def encode_queries(
        self,
        queries: List[str],
        batch_size: int = 12
    ) -> np.ndarray:
        """
        검색 쿼리 임베딩 (검색 최적화)

        Args:
            queries: 검색 쿼리 리스트
            batch_size: 배치 크기

        Returns:
            쿼리 임베딩 벡터
        """
        return self.encode(queries, batch_size=batch_size)

    def encode_corpus(
        self,
        corpus: List[str],
        batch_size: int = 12
    ) -> np.ndarray:
        """
        문서 코퍼스 임베딩

        Args:
            corpus: 문서 리스트
            batch_size: 배치 크기

        Returns:
            문서 임베딩 벡터
        """
        return self.encode(corpus, batch_size=batch_size)

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

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
        # 임베딩 생성
        query_emb = self.encode([query])[0]
        corpus_embs = self.encode(corpus)

        # 유사도 계산
        similarities = []
        for i, doc_emb in enumerate(corpus_embs):
            sim = self.cosine_similarity(query_emb, doc_emb)
            similarities.append({
                'index': i,
                'text': corpus[i],
                'similarity': float(sim)
            })

        # 정렬 및 상위 k개 반환
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]


# ==================== 사용 예시 ====================

def example_basic_usage():
    """기본 사용법"""
    print("\n" + "="*60)
    print("📝 기본 사용법")
    print("="*60)

    embedder = BGEM3Embedder(use_fp16=True)

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

    embedder = BGEM3Embedder(use_fp16=True)

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

    embedder = BGEM3Embedder(use_fp16=True)

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


def example_performance_comparison():
    """성능 비교 (BGE-M3 vs 기존 모델)"""
    print("\n" + "="*60)
    print("⚡ 성능 비교")
    print("="*60)

    from sentence_transformers import SentenceTransformer

    # 테스트 데이터
    test_texts = [
        "Python에서 비동기 프로그래밍을 어떻게 구현하나요?",
        "REST API와 GraphQL의 차이점은 무엇인가요?",
        "Docker 컨테이너의 네트워킹은 어떻게 작동하나요?"
    ] * 10  # 30개 텍스트

    # BGE-M3
    print("\n1️⃣ BGE-M3 모델")
    start = time.time()
    bge_model = BGEM3Embedder(use_fp16=True)
    bge_embs = bge_model.encode(test_texts)
    bge_time = time.time() - start
    print(f"   처리 시간: {bge_time:.2f}초")
    print(f"   임베딩 차원: {bge_embs.shape[1]}")

    # 기존 모델 (ko-sroberta)
    print("\n2️⃣ ko-sroberta-multitask 모델")
    start = time.time()
    sbert_model = SentenceTransformer('jhgan/ko-sroberta-multitask')
    sbert_embs = sbert_model.encode(test_texts)
    sbert_time = time.time() - start
    print(f"   처리 시간: {sbert_time:.2f}초")
    print(f"   임베딩 차원: {sbert_embs.shape[1]}")

    print(f"\n📊 속도 비교: BGE-M3가 {sbert_time/bge_time:.2f}배 {'빠름' if bge_time < sbert_time else '느림'}")


if __name__ == "__main__":
    print("🚀 BGE-M3 모델 사용 가이드")
    print("="*60)

    # 1. 기본 사용법
    example_basic_usage()

    # 2. 벡터 검색
    example_search()

    # 3. 다국어 지원
    example_multilingual()

    # 4. 성능 비교
    # example_performance_comparison()  # 시간이 오래 걸리므로 주석 처리

    print("\n" + "="*60)
    print("✅ 모든 예시 실행 완료!")
    print("="*60)
