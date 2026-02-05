 """
검색 헬퍼 Task
- 검색 쿼리를 임베딩으로 변환
- Backend에서 Celery를 통해 호출
"""
from celery import shared_task
from utils.vector_utils import get_embedding_generator
import logging

logger = logging.getLogger("SearchHelper")


@shared_task(bind=True, name="generate_query_embedding")
def generate_query_embedding_task(self, query: str):
    """
    검색 쿼리를 임베딩으로 변환
    
    Args:
        query: 검색 쿼리 (예: "Python 백엔드 개발자")
        
    Returns:
        list: 1024차원 임베딩 벡터
    """
    logger.info(f"🔍 [Task {self.request.id}] Generating embedding for query: '{query}'")
    
    try:
        # 임베딩 생성기 가져오기
        generator = get_embedding_generator()
        
        # 쿼리를 임베딩으로 변환
        embedding = generator.encode_query(query)
        
        logger.info(f"✅ [Task {self.request.id}] Embedding generated successfully (dim: {len(embedding)})")
        
        # numpy array를 list로 변환하여 반환
        return embedding.tolist()
        
    except Exception as e:
        logger.error(f"❌ [Task {self.request.id}] Failed to generate embedding: {e}")
        raise
