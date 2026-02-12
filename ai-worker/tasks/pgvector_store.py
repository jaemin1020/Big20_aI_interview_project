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
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
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
<<<<<<< HEAD
=======
def store_embeddings(resume_id, embedded_chunks):
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
    if not embedded_chunks:
        print("❌ 저장할 임베딩 데이터가 없습니다.")
        return

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea
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
<<<<<<< HEAD
=======
    # 1. 벡터 차원 확인 (예: 768 or 1024)
    # 첫 번째 청크의 벡터 길이를 확인하여 테이블 생성 시 사용
    vector_dim = len(embedded_chunks[0]["vector"])
    print(f"\n[STEP6] DB 저장 시작 (Resume ID: {resume_id}, 차원: {vector_dim})...")

    try:
        with engine.begin() as conn:
            # 2. pgvector 확장 설치 (한 번만 실행되면 됨)
            conn.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector;"))

            # 3. 테이블 생성
            # resume_id: Step 3의 resumes 테이블 id와 연결되는 외래키 역할 (Integer)
            create_table_sql = sql_text(f"""
                CREATE TABLE IF NOT EXISTS resume_embeddings (
                    id SERIAL PRIMARY KEY,
                    resume_id INTEGER, 
                    chunk_type TEXT,
                    chunk_text TEXT,
                    metadata JSONB,
                    embedding vector({vector_dim}),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute(create_table_sql)

            # 4. 기존 데이터 삭제 (중복 적재 방지)
            # 해당 이력서(resume_id)의 기존 벡터들을 지우고 새로 넣습니다.
            conn.execute(sql_text("DELETE FROM resume_embeddings WHERE resume_id = :rid"), {"rid": resume_id})

            # 5. 데이터 삽입
            insert_sql = sql_text("""
                INSERT INTO resume_embeddings 
                (resume_id, chunk_type, chunk_text, metadata, embedding)
                VALUES (:rid, :ctype, :ctext, :meta, :vec)
            """)

            for item in embedded_chunks:
                conn.execute(insert_sql, {
                    "rid": resume_id,
                    "ctype": item["type"],
                    "ctext": item["text"],
                    "meta": json.dumps(item["metadata"], ensure_ascii=False),
                    "vec": str(item["vector"]) # 벡터 리스트를 문자열 "[0.1, 0.2, ...]"로 변환
                })

        print(f"[STEP6] ✅ 총 {len(embedded_chunks)}개의 임베딩 데이터 저장 완료!")

    except Exception as e:
        print(f"\n❌ DB 저장 실패: {e}")
        # 차원 불일치 에러일 경우 힌트 출력
        if "dimensions" in str(e):
            print("💡 힌트: DB에 이미 존재하는 테이블의 벡터 차원과 현재 모델의 차원이 다를 수 있습니다.")
            print("   (해결책: DROP TABLE resume_embeddings; 명령어로 테이블을 지우고 다시 시도하세요.)")
>>>>>>> bcab0a98e56e154aae50f9fad3ffa7ac7d936acf
=======
>>>>>>> d4e80d6d076861616e2c5afc84a50bbc841db3ea

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
