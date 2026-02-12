import sys
import os
import json
from sqlalchemy import text as sql_text

# -----------------------------------------------------------
# [경로 설정]
# -----------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_core_docker = "/backend-core"
backend_core_local = os.path.join(current_dir, "backend-core")

if os.path.exists(backend_core_docker):
    sys.path.append(backend_core_docker)
elif os.path.exists(backend_core_local):
    sys.path.append(backend_core_local)

# 🚨 db.py에서 engine 불러오기
try:
    from db import engine
except ImportError as e:
    print(f"❌ db.py를 불러오는데 실패했습니다: {e}")
    sys.exit(1)

# -----------------------------------------------------------
# 벡터 데이터 저장 함수
# -----------------------------------------------------------
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document

# -----------------------------------------------------------
# [모델 설정] Step 5와 동일한 모델을 사용해야 함
# -----------------------------------------------------------
try:
    from .embedding import get_embedder
except ImportError:
    from embedding import get_embedder

# -----------------------------------------------------------
# 벡터 데이터 저장 함수 (LangChain PGVector 활용)
# -----------------------------------------------------------
def store_embeddings(resume_id, embedded_chunks):
    """
    LangChain의 PGVector를 사용하여 벡터 데이터를 저장합니다.
    """
    if not embedded_chunks:
        print("❌ 저장할 임베딩 데이터가 없습니다.")
        return

    print(f"\n[STEP6] DB 저장 시작 (Resume ID: {resume_id}, LangChain PGVector 활용)...")

    # 1. 문서화 (Document 객체 생성)
    documents = []
    for item in embedded_chunks:
        # 메타데이터에 resume_id 강제 삽입 (하이브리드 필터링용)
        metadata = item.get("metadata", {})
        metadata["resume_id"] = resume_id
        metadata["chunk_type"] = item.get("type", "unknown")
        
        doc = Document(
            page_content=item["text"],
            metadata=metadata
        )
        documents.append(doc)

    # 2. PGVector 연결 설정
    # database.py의 DATABASE_URL을 사용 (psycopg:// 형식이어야 함)
    connection_string = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
    
    # 3. 임베딩 모델 가져오기
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    embeddings = get_embedder(device)

    try:
        # 4. 저장 (collection_name을 통해 논리적 분리 가능)
        # 여기서는 단일 테이블에서 metadata 필터링을 사용하는 방식으로 표준화
        vector_store = PGVector.from_documents(
            embedding=embeddings,
            documents=documents,
            collection_name="resume_all_embeddings",
            connection_string=connection_string,
            pre_delete_collection=False, # 전체 컬렉션을 지우지 않음
        )
        
        # 5. 기존 동일 resume_id 데이터 관리
        # langchain_community 버전에서는 delete 기능을 metadata filter와 함께 쓰기 까다로움
        # 따라서 현재는 추가(Append) 모드로 동작하며, 추후 관리가 필요할 수 있음
        print(f"[STEP6] ✅ 총 {len(documents)}개의 청크가 LangChain PGVector에 저장되었습니다.")

    except Exception as e:
        print(f"\n❌ LangChain PGVector 저장 실패: {e}")

# -----------------------------------------------------------
# 메인 실행: 전체 파이프라인 테스트
# -----------------------------------------------------------
if __name__ == "__main__":
    try:
        # Step 1(load_resume)은 제거됨
        from parse_resume import parse_resume_final
        from chunking import chunk_resume
        from embedding import embed_chunks
    except ImportError as e:
        print(f"❌ 모듈 Import 실패: {e}")
        sys.exit(1)

    # 1. 파일 경로 확인
    target_pdf = "resume.pdf"
    if not os.path.exists(target_pdf):
        target_pdf = "/app/resume.pdf"
    
    if os.path.exists(target_pdf):
        print(f"🚀 [Pipeline 시작] 파일: {target_pdf}")
        
        # Step 2: 파싱
        parsed = parse_resume_final(target_pdf)
        
        if parsed:
            # Step 4: 청킹
            chunks = chunk_resume(parsed)
            
            if chunks:
                # Step 5: 임베딩
                embedded_data = embed_chunks(chunks)
                
                if embedded_data:
                    # Step 6: DB 저장
                    # Step 3에서 resume_id=1로 저장했으므로, 여기서도 1로 맞춤
                    store_embeddings(resume_id=1, embedded_chunks=embedded_data)
                else:
                    print("❌ 임베딩 실패")
            else:
                print("❌ 청킹 데이터 없음")
        else:
            print("❌ 파싱 실패")
    else:
        print("❌ 파일 없음")
