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

# GPU/CPU 자동 설정
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"[STEP7] 임베딩 모델 로드 중 ({EMBEDDING_MODEL}) on {device}...")

try:
    embedder = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device},
        encode_kwargs={'normalize_embeddings': True}
    )
except Exception as e:
    print(f"❌ 임베딩 모델 로드 실패: {e}")
    sys.exit(1)

# -----------------------------------------------------------
# [핵심] 검색 함수 (하이브리드 검색 적용)
# -----------------------------------------------------------
def retrieve_context(query, resume_id=1, top_k=3, filter_category=None):
    """
    Args:
        query (str): 검색할 질문 내용
        resume_id (int): 대상 지원자 ID
        top_k (int): 가져올 개수
        filter_category (str): 'project', 'narrative', 'activity' 등 (없으면 전체 검색)
    """
    print(f"\n🔍 [RAG 검색] 키워드: '{query}' (필터: {filter_category})")
    
    # 1. 검색어(Query)를 벡터로 변환
    try:
        query_vector = embedder.embed_query(query)
    except Exception as e:
        print(f"❌ 쿼리 임베딩 실패: {e}")
        return []
    
    results = []
    
    try:
        with engine.connect() as conn:
            # 2. 동적 SQL 생성 (필터링 조건 추가)
            # 기본 쿼리
            base_sql = """
                SELECT chunk_text, metadata, (embedding <=> :qv) as distance
                FROM resume_embeddings
                WHERE resume_id = :rid
            """
            
            # ★ 메타데이터 필터링 추가 (이게 핵심!)
            # DB에 저장된 metadata JSON의 'category' 키를 확인합니다.
            if filter_category:
                base_sql += f" AND metadata->>'category' = '{filter_category}'"
            
            # 정렬 및 제한
            final_sql = base_sql + " ORDER BY distance ASC LIMIT :k"
            
            # 3. 쿼리 실행
            rows = conn.execute(text(final_sql), {
                "qv": str(query_vector),
                "rid": int(resume_id),
                "k": top_k
            }).fetchall()

            # 4. 결과 가공
            for row in rows:
                chunk_text = row[0]
                meta_data = row[1] # DB에서 꺼낸 메타데이터 (dict)
                
                # 결과 리스트에 텍스트와 메타데이터를 함께 담음
                results.append({
                    'text': chunk_text,
                    'meta': meta_data  # Step 8에서 활용 가능
                })

            print(f"   👉 {len(results)}개의 관련 내용을 찾았습니다.")

    except Exception as e:
        print(f"❌ DB 검색 실패: {e}")
        
    return results

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