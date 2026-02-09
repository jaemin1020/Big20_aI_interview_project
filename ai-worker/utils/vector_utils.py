"""
벡터 임베딩 생성 유틸리티
Question 및 AnswerBank의 텍스트를 벡터로 변환
"""
from sentence_transformers import SentenceTransformer
from typing import List
import logging

logger = logging.getLogger("VectorUtils")

# 한국어 특화 모델 (KURE-v1)
# 질문/답변/문서 등 용도에 따라 prefix 필요 ("query: ", "passage: ")
MODEL_NAME = "nlpai-lab/KURE-v1"

class EmbeddingGenerator:
    """싱글톤 패턴의 임베딩 생성기"""
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            logger.info(f"Loading embedding model: {MODEL_NAME}")
            # trust_remote_code=True 권장 (KURE 모델)
            self._model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
            logger.info("✅ Embedding model loaded")
    
    def encode(self, text: str, is_query: bool = True) -> List[float]:
        """
        텍스트를 벡터로 변환
        
        Args:
            text: 변환할 텍스트
            is_query: 쿼리(질문/검색어) 여부. True면 "query: ", False면 "passage: " 접두어 사용
        
        Returns:
            벡터 (리스트)
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for encoding")
            # KURE-v1 output dimension is 1024 (based on BAAI/bge-m3)
            return [0.0] * 1024
        
        prefix = "query: " if is_query else "passage: "
        # 텍스트 앞부분에 접두어 추가
        full_text = prefix + text
        
        embedding = self._model.encode(full_text, convert_to_tensor=False)
        return embedding.tolist()
    
    def encode_passage(self, text: str) -> List[float]:
        """문서(Passage) 임베딩 생성 ("passage: " 접두어 사용)"""
        return self.encode(text, is_query=False)

    def encode_query(self, text: str) -> List[float]:
        """질문(Query) 임베딩 생성 ("query: " 접두어 사용)"""
        return self.encode(text, is_query=True)
    
    def encode_batch(self, texts: List[str], is_query: bool = True) -> List[List[float]]:
        """
        여러 텍스트를 한 번에 벡터화 (배치 처리)
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
    """임베딩 생성기 싱글톤 인스턴스 반환"""
    global _generator
    if _generator is None:
        _generator = EmbeddingGenerator()
    return _generator


def generate_question_embedding(question_text: str) -> List[float]:
    """질문 텍스트를 벡터로 변환 (Query 모드)"""
    generator = get_embedding_generator()
    return generator.encode_query(question_text)


def generate_answer_embedding(answer_text: str) -> List[float]:
    """답변 텍스트를 벡터로 변환 (Passage 모드)"""
    generator = get_embedding_generator()
    # 답변은 검색 대상이므로 Passage로 취급
    return generator.encode_passage(answer_text)
