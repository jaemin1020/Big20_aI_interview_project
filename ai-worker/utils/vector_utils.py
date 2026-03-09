"""
벡터 임베딩 생성 유틸리티
Question 및 AnswerBank의 텍스트를 벡터로 변환
"""
from sentence_transformers import SentenceTransformer
from typing import List
import os
import logging

logger = logging.getLogger("VectorUtils")

# 한국어 특화 모델 (KURE-v1)
# 질문/답변/문서 등 용도에 따라 prefix 필요 ("query: ", "passage: ")
MODEL_NAME = "nlpai-lab/KURE-v1"

class EmbeddingGenerator:
    """설명:
        싱글톤 패턴의 임베딩 생성기

        생성자: ejm
        생성일자: 2026-02-04
    """
    _instance = None
    _model = None
    
    def __new__(cls):
        """설명:
            싱글톤 패턴으로 EmbeddingGenerator 인스턴스를 생성.
            이미 인스턴스가 있으면 기존 것을 반환하여 모델 중복 로드를 방지.

        Returns:
            EmbeddingGenerator: 싱글톤 인스턴스.

        생성자: ejm
        생성일자: 2026-02-04
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """설명:
            KURE-v1 임베딩 모델을 로드하고 캐시 디렉토리를 설정.
            싱글톤 패턴으로 한 번만 실행되며 모델이 이미 로드된 경우 초기화를 건너뜀.

        생성자: ejm
        생성일자: 2026-02-04
        """
        if self._model is None:
            cache_dir = "/app/models/embeddings" if os.path.exists("/app/models") else "./models/embeddings"
            os.makedirs(cache_dir, exist_ok=True)
            
            logger.info(f"Loading embedding model: {MODEL_NAME}")
            logger.info(f"📂 Cache path: {cache_dir}")
            
            # trust_remote_code=True 권장 (KURE 모델)
            self._model = SentenceTransformer(
                MODEL_NAME, 
                trust_remote_code=True,
                cache_folder=cache_dir
            )
            logger.info("✅ Embedding model loaded")
    
    def encode(self, text: str, is_query: bool = True) -> List[float]:
        """설명:
            텍스트를 벡터로 변환

            Args:
            text: 변환할 텍스트
            is_query: 쿼리(질문/검색어) 여부. True면 "query: ", False면 "passage: " 접두어 사용

            Returns:
            

            생성자: ejm
            생성일자: 2026-02-04
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for encoding")
            # KURE-v1 output dimension typically 1024.
            return [0.0] * 1024
        
        prefix = "query: " if is_query else "passage: "
        # 텍스트 앞부분에 접두어 추가
        full_text = prefix + text
        
        embedding = self._model.encode(full_text, convert_to_tensor=False)
        return embedding.tolist()
    
    def encode_passage(self, text: str) -> List[float]:
        """설명:
            문서(Passage) 임베딩 생성 ("passage: " 접두어 사용)

            Args:
            text: 파라미터 설명.

            Returns:
            반환값 정보.

            생성자: ejm
            생성일자: 2026-02-04
        """
        return self.encode(text, is_query=False)

    def encode_query(self, text: str) -> List[float]:
        """설명:
            질문(Query) 임베딩 생성 ("query: " 접두어 사용)

            Args:
            text: 파라미터 설명.

            Returns:
            반환값 정보.

            생성자: ejm
            생성일자: 2026-02-04
        """
        return self.encode(text, is_query=True)
    
    def encode_batch(self, texts: List[str], is_query: bool = True) -> List[List[float]]:
        """설명:
            여러 텍스트를 한 번에 벡터화 (배치 처리)

            Args:
            texts: 파라미터 설명.
            is_query: 파라미터 설명.

            Returns:
            반환값 정보.

            생성자: ejm
            생성일자: 2026-02-04
        """
        if not texts:
            return []
        
        prefix = "query: " if is_query else "passage: "
        prefixed_texts = [prefix + t for t in texts]
        
        embeddings = self._model.encode(prefixed_texts, convert_to_tensor=False, show_progress_bar=True)
        return [emb.tolist() for emb in embeddings]


# 전역 인스턴스
_generator = None

def get_embedding_generator() -> EmbeddingGenerator:
    """설명:
        임베딩 생성기 싱글톤 인스턴스 반환

        Returns:
        반환값 정보.

        생성자: ejm
        생성일자: 2026-02-04
    """
    global _generator
    if _generator is None:
        _generator = EmbeddingGenerator()
    return _generator


def generate_question_embedding(question_text: str) -> List[float]:
    """설명:
        질문 텍스트를 벡터로 변환 (Query 모드)

        Args:
        question_text: 파라미터 설명.

        Returns:
        반환값 정보.

        생성자: ejm
        생성일자: 2026-02-04
    """
    generator = get_embedding_generator()
    return generator.encode_query(question_text)


def generate_answer_embedding(answer_text: str) -> List[float]:
    """설명:
        답변 텍스트를 벡터로 변환 (Passage 모드)

        Args:
        answer_text: 파라미터 설명.

        Returns:
        반환값 정보.

        생성자: ejm
        생성일자: 2026-02-04
    """
    generator = get_embedding_generator()
    # 답변은 검색 대상이므로 Passage로 취급
    return generator.encode_passage(answer_text)
