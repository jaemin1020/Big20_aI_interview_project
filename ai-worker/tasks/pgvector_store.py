import sys
import os
import json
from sqlalchemy import text as sql_text

# -----------------------------------------------------------
# [1. 경로 설정] 왜 이 코드가 필요할까?
# 서버 환경(Docker)과 개발자 컴퓨터(Local)는 폴더 구조가 다릅니다.
# 어디서든 다른 파일(db.py 등)을 잘 불러올 수 있도록 길을 터주는 작업입니다.
# -----------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_core_docker = "/backend-core"
backend_core_local = os.path.join(current_dir, "backend-core")

# [문법] sys.path.append: 파이썬이 모듈을 찾을 때 검색하는 명단에 특정 폴더를 추가합니다.
if os.path.exists(backend_core_docker):
    sys.path.append(backend_core_docker)
elif os.path.exists(backend_core_local):
    sys.path.append(backend_core_local)

# 🚨 db.py에서 engine 불러오기 (데이터베이스와 연결하는 통로)
try:
    from db import engine
except ImportError as e:
    print(f"❌ db.py를 불러오는데 실패했습니다: {e}")
    sys.exit(1) # [문법] sys.exit(1): 심각한 에러가 발생했으므로 프로그램을 즉시 종료합니다.

# -----------------------------------------------------------
# [2. 도구 불러오기]
# LangChain은 AI 앱을 만들기 위한 '레고 블록' 같은 도구입니다.
# PGVector: PostgreSQL에 벡터를 저장하고 검색하게 해주는 레고 블록입니다.
# -----------------------------------------------------------
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document

try:
    from .embedding import get_embedder # 현재 폴더에서 가져오기 시도
except ImportError:
    from embedding import get_embedder    # 실패 시 그냥 가져오기

# -----------------------------------------------------------
# [3. 핵심 함수: store_embeddings]
# [존재 이유] 임베딩된 숫자 데이터는 그냥 두면 휘발됩니다. 이를 DB에 '영구 저장'해야 
# 나중에 면접관 AI가 이 데이터를 보고 질문을 던질 수 있습니다.
# -----------------------------------------------------------
def store_embeddings(resume_id, embedded_chunks):
    """
    [함수의 역할] 이미 계산된 임베딩(숫자) 데이터를 사용하여 DB에 직접 주입합니다.
    [개선 사항] from_documents 대신 add_embeddings를 사용하여 중복 AI 연산을 제거했습니다.
    """
    if not embedded_chunks:
        print("❌ 저장할 임베딩 데이터가 없습니다.")
        return

    print(f"\n[STEP6] DB 저장 시작 (Resume ID: {resume_id})... (중복 연산 제거 모드)")

    # 1. 속도 향상을 위해 이미 계산된 텍스트, 벡터, 메타데이터를 각각 분리합니다.
    texts = []
    vectors = []
    metadatas = []

    for item in embedded_chunks:
        texts.append(item["text"])
        vectors.append(item["vector"])
        
        # 메타데이터 정리 (견출지 붙이기)
        m = item.get("metadata", {}).copy()
        m["resume_id"] = resume_id
        m["chunk_type"] = item.get("type", "unknown")
        metadatas.append(m)

    # 2. DB 연결 정보 및 임베딩 모델 준비 
    # (add_embeddings를 써도 객체 생성을 위해 embedding_function 인자는 필요합니다.)
    connection_string = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
    
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    embeddings_model = get_embedder(device)

    try:
        from db import engine
        # 3. PGVector 객체 생성 (기존 collection에 연결)
        vector_store = PGVector(
            connection_string=connection_string,
            connection=engine,
            collection_name="resume_all_embeddings",
            embedding_function=embeddings_model
        )
        
        # 4. 핵심: 다시 계산하지 않고 '이미 만든 숫자(vectors)'를 바로 저장!
        vector_store.add_embeddings(
            texts=texts,
            embeddings=vectors,
            metadatas=metadatas
        )
        
        print(f"[STEP6] ✅ 고효율 모드로 {len(texts)}개의 조각을 DB에 저장 완료!")

    except Exception as e:
        print(f"\n❌ 고효율 DB 저장 실패: {e}")

# -----------------------------------------------------------
# [4. 메인 실행부] 
# 전체 공정(파싱->청킹->임베딩->저장)을 한 번에 테스트합니다.
# -----------------------------------------------------------
if __name__ == "__main__":
    # ... (생략) ...
    # 실제 실행 시 store_embeddings(resume_id=1, ...)을 통해 DB에 최종 저장됩니다.
    pass
