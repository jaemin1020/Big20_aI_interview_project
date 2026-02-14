import logging
import os
import sys
from typing import List, Optional

# 경로 설정 (db_models 및 db 임포트 지원)
app_root = "/app" if os.path.exists("/app") else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_root = os.path.abspath(os.path.join(app_root, "..", "backend-core"))
if backend_root not in sys.path:
    sys.path.append(backend_root)
if app_root not in sys.path:
    sys.path.append(app_root)

from sqlmodel import Session, select
from db import engine
from db_models import Question, QuestionCategory
from utils.vector_utils import get_embedding_generator

logger = logging.getLogger("QuestionRetriever")

class QuestionRetriever:
    """
    6만 개의 질문 은행(DB)에서 이력서 맥락과 가장 유사한 질문을 찾아주는 엔진
    """
    def __init__(self):
        self.generator = get_embedding_generator()

    def find_relevant_questions(
        self, 
        text_context: str, 
        question_type: Optional[str] = None, 
        category: Optional[QuestionCategory] = None,
        position: Optional[str] = None,
        top_k: int = 5
    ) -> List[Question]:
        """
        텍스트 문맥(이력서 내용 등)을 기반으로 가장 관련성 높은 질문을 DB에서 추출합니다.
        
        Args:
            text_context: 검색의 기준이 되는 텍스트 (이력서 요약 등)
            question_type: 질문 유형 필터 (직무지식, 인성면접 등)
            category: 질문 카테고리 필터 (TECHNICAL, BEHAVIORAL 등)
            position: 직무 필터 (Backend 개발자 등)
            top_k: 반환할 질문 개수
            
        Returns:
            List[Question]: 검색된 질문 리스트
        """
        # 1. 입력 텍스트 벡터화 (Query 모드)
        query_vector = self.generator.encode_query(text_context)
        
        with Session(engine) as session:
            # 2. 기본 쿼리 생성
            stmt = select(Question)
            
            # 3. 하드 필터링 적용 (성능 및 정확도 향상)
            if question_type:
                stmt = stmt.where(Question.question_type == question_type)
            if category:
                stmt = stmt.where(Question.category == category)
            if position:
                # 대소문자 구분 없이 유사 직무 검색 (SQL ILIKE 느낌)
                stmt = stmt.where(Question.position.contains(position))
            
            # 4. 시맨틱 검색 (벡터 유사도 정렬)
            # pgvector의 <=> 연산자 (cosine distance) 사용
            stmt = stmt.order_by(Question.embedding.cosine_distance(query_vector)).limit(top_k)
            
            results = session.exec(stmt).all()
            
            return results

# 싱글톤 인스턴스
_retriever = None

def get_question_retriever() -> QuestionRetriever:
    global _retriever
    if _retriever is None:
        _retriever = QuestionRetriever()
    return _retriever
