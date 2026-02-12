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
EMBEDDING_MODEL = "nlpai-lab/KURE-v1" 

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        cache_dir = "/app/models/embeddings" if os.path.exists("/app/models") else "./models/embeddings"
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"[STEP7] 임베딩 모델 로드 중 ({EMBEDDING_MODEL}) on {device}...")
        print(f"📂 캐시 경로: {cache_dir}")
        
        try:
            _embedder = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={'device': device},
                encode_kwargs={'normalize_embeddings': True},
                cache_folder=cache_dir
            )
            print("✅ RAG 임베딩 모델 로드 완료!")
        except Exception as e:
            print(f"❌ 임베딩 모델 로드 실패: {e}")
            # 여기서 sys.exit(1)을 하면 워커 자체가 죽으므로 주의
            return None
    return _embedder

# -----------------------------------------------------------
# [핵심] 검색 함수 (하이브리드 검색 적용)
# -----------------------------------------------------------
from langchain_community.vectorstores import PGVector

# -----------------------------------------------------------
# [핵심] 검색 함수 (LangChain PGVector 활용)
# -----------------------------------------------------------
def retrieve_context(query, resume_id=1, top_k=3, filter_category=None):
    """
    LangChain PGVector를 사용하여 관련 문맥을 검색합니다.
    """
    print(f"\n🔍 [RAG 검색] 키워드: '{query}' (지원자 ID: {resume_id}, 필터: {filter_category})")
    
    # 1. 임베딩 모델 및 연결 설정
    embedder = get_embedder()
    if not embedder:
        print("❌ 임베딩 모델을 사용할 수 없습니다.")
        return []
    
    connection_string = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
    
    try:
        # 2. PGVector 인스턴스 생성
        vector_store = PGVector(
            connection_string=connection_string,
            embedding_function=embedder,
            collection_name="resume_all_embeddings"
        )

        # 3. 필터 설정 (resume_id + category)
        search_filter = {"resume_id": resume_id}
        if filter_category:
            search_filter["category"] = filter_category

        # 4. 유사도 검색 수행
        docs_with_scores = vector_store.similarity_search_with_score(
            query, 
            k=top_k,
            filter=search_filter
        )

        # 5. 결과 가공
        results = []
        for doc, score in docs_with_scores:
            results.append({
                'text': doc.page_content,
                'meta': doc.metadata,
                'score': float(score)  # 거리 점수 추가
            })

        print(f"   👉 {len(results)}개의 관련 내용을 찾았습니다.")
        for i, res in enumerate(results):
            preview = res['text'].replace('\n', ' ')[:80]
            category = res['meta'].get('category', 'N/A')
            print(f"      [{i+1}] (Dist: {res['score']:.4f}, Cat: {category}): {preview}...")

        return results

    except Exception as e:
        print(f"❌ LangChain PGVector 검색 실패: {e}")
        return []

# -----------------------------------------------------------
# [핵심] Retriever 생성 함수 (LangChain LCEL용)
# -----------------------------------------------------------
def get_retriever(resume_id=1, top_k=3, filter_category=None):
    """
    LangChain LCEL에서 사용할 수 있는 Retriever 객체를 반환합니다.
    """
    embedder = get_embedder()
    connection_string = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
    
    vector_store = PGVector(
        connection_string=connection_string,
        embedding_function=embedder,
        collection_name="resume_all_embeddings"
    )

    # 필터 설정
    search_filter = {"resume_id": resume_id}
    if filter_category:
        search_filter["category"] = filter_category

    # 검색 결과를 필터링하여 반환하도록 설정
    return vector_store.as_retriever(
        search_kwargs={
            "k": top_k,
            "filter": search_filter
        }
    )

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
