import sys
import os
import torch
from sqlalchemy import text

# 🚨 [최신 표준] langchain_huggingface 사용
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

# -----------------------------------------------------------
# [경로 설정]
# -----------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "ai-worker"))

try:
    from db import engine
except ImportError:
    try:
        sys.path.append("/app/backend-core") 
        from db import engine
    except ImportError:
        print("❌ db.py 로드 실패")
        sys.exit(1)

# -----------------------------------------------------------
# [모델 설정] Step 6(저장) 때 쓴 모델과 100% 일치해야 함!
# -----------------------------------------------------------
from .embedding import get_embedder as _get_central_embedder

def get_embedder():
    """중앙화된 임베딩 모델 인스턴스 반환 (싱글톤)"""
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    return _get_central_embedder(device)

from langchain_community.vectorstores import PGVector

# -----------------------------------------------------------
# [핵심] 검색 인스턴스 싱글톤 관리
# -----------------------------------------------------------
_vector_stores = {}

def get_vector_store(collection_name):
    """지정된 컬렉션에 대한 PGVector 인스턴스 싱글톤 반환 (engine 공유)"""
    global _vector_stores
    if collection_name not in _vector_stores:
        embedder = get_embedder()
        if not embedder:
            return None
        
        # [최종 수정] 위치 인자(Positional)로 전달하여 라이브러리 호환성 문제 완벽 해결
        from db import engine
        connection_url = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@db:5432/interview_db")
        _vector_stores[collection_name] = PGVector(
            connection_url,        # 1. connection_string (위치 인자)
            embedder,              # 2. embedding_function (위치 인자)
            collection_name=collection_name,
            connection=engine      # 3. 객체 공유
        )
    return _vector_stores[collection_name]

# -----------------------------------------------------------
# [핵심] 검색 함수 (LangChain PGVector 활용)
# -----------------------------------------------------------
import logging

# 로거 설정
logger = logging.getLogger(__name__)

def retrieve_context(query, resume_id=1, top_k=10, filter_type=None):
    """
    LangChain PGVector를 사용하여 관련 문맥을 검색합니다.
    """
    logger.info(f"🔍 [RAG 검색 시작] Query: '{query}' | ResumeID: {resume_id} | Filter: {filter_type}")
    
    # 1. 임베딩 모델 및 연결 설정
    embedder = get_embedder()
    if not embedder:
        logger.error("❌ 임베딩 모델 로드 실패로 검색을 중단합니다.")
        return []
    
    try:
        # 2. PGVector 인스턴스 가져오기 (캐싱 활용)
        vector_store = get_vector_store("resume_all_embeddings")
        if not vector_store:
             return []

        # 3. 필터 설정 (resume_id + chunk_type)
        search_filter = {"resume_id": resume_id}
        if filter_type:
            search_filter["chunk_type"] = filter_type

        # 4. 유사도 검색 수행
        logger.debug(f"📐 쿼리 임베딩 및 유사도 계산 중...")
        docs_with_scores = vector_store.similarity_search_with_score(
            query, 
            k=top_k,
            filter=search_filter
        )

        # 5. 결과 가공 및 로깅
        results = []
        if not docs_with_scores:
            logger.warning(f"⚠️ 검색 결과가 없습니다. (Filter: {search_filter})")
            return []

        logger.info(f"✅ 검색 완료: {len(docs_with_scores)}개의 문맥을 발견했습니다.")
        for i, (doc, score) in enumerate(docs_with_scores):
            res = {
                'text': doc.page_content,
                'meta': doc.metadata,
                'score': float(score)
            }
            results.append(res)
            
            # 검색 결과 상세 로그 출력
            preview = res['text'].replace('\n', ' ')[:100]
            c_type = res['meta'].get('chunk_type', 'N/A')
            logger.info(f"   👉 [{i+1}] [Dist: {res['score']:.4f} | Type: {c_type}] {preview}...")

        return results

    except Exception as e:
        logger.error(f"❌ LangChain PGVector 검색 중 예외 발생: {str(e)}", exc_info=True)
        return []

# -----------------------------------------------------------
# [핵심] Retriever 생성 함수 (LangChain LCEL용)
# -----------------------------------------------------------
def get_retriever(resume_id=1, top_k=10, filter_type=None):
    """
    LangChain LCEL에서 사용할 수 있는 Retriever 객체를 반환합니다.
    """
    embedder = get_embedder()
    # 2. 인스턴스 가져오기
    vector_store = get_vector_store("resume_all_embeddings")
    if not vector_store:
         return None

    # 필터 설정
    search_filter = {"resume_id": resume_id}
    if filter_type:
        search_filter["chunk_type"] = filter_type

    logger.info(f"📡 Retriever 생성 완료 (ResumeID: {resume_id}, Filter: {filter_type})")
    return vector_store.as_retriever(
        search_kwargs={
            "k": top_k,
            "filter": search_filter
        }
    )

# -----------------------------------------------------------
# [변경 완료] 질문 은행(questions 테이블) 검색 함수 (All LangChain 방식)
# -----------------------------------------------------------
def retrieve_similar_questions(query, top_k=5):
    """
    LangChain PGVector를 사용하여 질문 은행에서 쿼리와 유사한 질문들을 검색합니다.
    """
    logger.info(f"🔍 [질문 은행 검색 시작] Query: '{query[:50]}...' (Framework: LangChain)")
    
    embedder = get_embedder()
    if not embedder:
        logger.error("❌ 임베딩 모델 로드 실패로 질문 은행 검색을 중단합니다.")
        return []
    
    try:
        # 질문 은행은 별도의 컬렉션/테이블(questions)을 사용하므로 collection_name을 맞춰줍니다.
        vector_store = get_vector_store("questions_collection")
        if not vector_store:
             return []
        
        # 유사도 검색 수행
        docs_with_scores = vector_store.similarity_search_with_score(query, k=top_k)
        
        results = []
        if not docs_with_scores:
            logger.warning("⚠️ 질문 은행에서 검색된 내용이 없습니다.")
            return []

        logger.info(f"✅ 검색 완료: 랭체인 엔진을 통해 {len(docs_with_scores)}개의 유사 질문을 추출했습니다.")
        for i, (doc, score) in enumerate(docs_with_scores):
            res = {
                "text": doc.page_content, 
                "meta": doc.metadata, 
                "score": float(score)
            }
            results.append(res)
            # 상세 데이터 로그 출력
            logger.info(f"   👉 [{i+1}] [Dist: {res['score']:.4f}] {res['text'][:100]}...")
            
        return results
            
    except Exception as e:
        logger.error(f"❌ 랭체인 기반 질문 은행 검색 중 예외 발생: {str(e)}", exc_info=True)
        return []

# -----------------------------------------------------------
# 테스트 코드
# -----------------------------------------------------------
if __name__ == "__main__":
    # 테스트 1: 필터 없이 검색 (기본)
    print("--- [Test 1: 전체 검색] ---")
    retrieve_context("보안 기술 스킬", resume_id=1)
    
    # 테스트 2: '프로젝트'만 콕 집어서 검색 (하이브리드)
    print("\n--- [Test 2: 프로젝트 필터링 검색] ---")
    found = retrieve_context("성과 달성 경험", resume_id=1, filter_category="project")

    if found:
        print("\n✅ [검색 결과 확인]")
        for item in found:
            # 메타데이터도 같이 출력해봅니다.
            print(f"[카테고리: {item['meta'].get('category')}] {item['text'][:50]}...")