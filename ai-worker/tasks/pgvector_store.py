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
def store_embeddings(resume_id, embedded_chunks):
    if not embedded_chunks:
        print("❌ 저장할 임베딩 데이터가 없습니다.")
        return

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
