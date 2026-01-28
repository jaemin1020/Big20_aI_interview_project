"""
벡터 임베딩 생성 유틸리티
Question 및 AnswerBank의 텍스트를 벡터로 변환
"""
from sentence_transformers import SentenceTransformer
from typing import List
import logging

logger = logging.getLogger("VectorUtils")

# 한국어 특화 모델 (768차원)
# 질문/답변 모두 이 모델 사용 (일관성 확보)
MODEL_NAME = "jhgan/ko-sroberta-multitask"

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
            self._model = SentenceTransformer(MODEL_NAME)
            logger.info("✅ Embedding model loaded")
    
    def encode(self, text: str) -> List[float]:
        """
        텍스트를 768차원 벡터로 변환
        
        Args:
            text: 질문 또는 답변 텍스트
        
        Returns:
            768차원 벡터 (리스트)
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for encoding")
            return [0.0] * 768  # 빈 벡터 반환
        
        embedding = self._model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        여러 텍스트를 한 번에 벡터화 (배치 처리)
        
        Args:
            texts: 텍스트 리스트
        
        Returns:
            벡터 리스트
        """
        if not texts:
            return []
        
        embeddings = self._model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
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
    """질문 텍스트를 벡터로 변환"""
    generator = get_embedding_generator()
    return generator.encode(question_text)


def generate_answer_embedding(answer_text: str) -> List[float]:
    """답변 텍스트를 벡터로 변환"""
    generator = get_embedding_generator()
    return generator.encode(answer_text)
