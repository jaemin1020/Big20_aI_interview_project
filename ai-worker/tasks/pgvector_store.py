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
    [함수의 역할] 임베딩된 데이터 조각들을 Document 객체로 변환하여 DB에 저장합니다.
    """
    if not embedded_chunks:
        print("❌ 저장할 임베딩 데이터가 없습니다.")
        return

    print(f"\n[STEP6] DB 저장 시작 (Resume ID: {resume_id})...")

    # -------------------------------------------------------
    # 3-1. 문서화 (Document 객체 생성)
    # [존재 이유] LangChain DB 도구를 쓰려면 데이터를 'Document'라는 표준 형식으로 포장해야 합니다.
    # -------------------------------------------------------
    documents = []
    for item in embedded_chunks:
        # [해석] 메타데이터(Metadata)는 데이터의 '견출지'입니다.
        # 나중에 수천 명의 이력서가 섞여 있어도 resume_id로 내 것만 쏙 골라낼 수 있습니다.
        metadata = item.get("metadata", {})
        metadata["resume_id"] = resume_id # 누구의 이력서인지 기록
        metadata["chunk_type"] = item.get("type", "unknown") # 이게 학력인지 경력인지 기록
        
        doc = Document(
            page_content=item["text"], # 실제 텍스트 내용
            metadata=metadata          # 부가 정보(견출지)
        )
        documents.append(doc)

    # -------------------------------------------------------
    # 3-2. DB 연결 및 저장
    # -------------------------------------------------------
    # [문법] os.getenv: 환경 변수에서 DB 접속 정보를 가져옵니다. 보안을 위해 아이디/비번을 코드에 직접 적지 않습니다.
    connection_string = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:1234@db:5432/interview_db")
    
    import torch
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    embeddings = get_embedder(device) # 저장할 때도 텍스트를 숫자로 바꿀 똑같은 모델이 필요합니다.

    try:
        # [해석] PGVector.from_documents: 
        # 1. 문서를 받는다 2. 모델로 숫자로 바꾼다 3. DB 테이블에 쏙 집어넣는다.
        # 이 모든 과정을 함수 하나가 자동으로 처리해줍니다.
        vector_store = PGVector.from_documents(
            embedding=embeddings,
            documents=documents,
            collection_name="resume_all_embeddings", # 테이블 내의 논리적 그룹 이름
            connection_string=connection_string,
            pre_delete_collection=False, # 기존 데이터를 싹 지우고 새로 저장할지 여부 (여기선 유지)
        )
        
        print(f"[STEP6] ✅ 총 {len(documents)}개의 조각이 DB에 저장되었습니다.")

    except Exception as e:
        print(f"\n❌ DB 저장 실패: {e}")

# -----------------------------------------------------------
# [4. 메인 실행부] 
# 전체 공정(파싱->청킹->임베딩->저장)을 한 번에 테스트합니다.
# -----------------------------------------------------------
if __name__ == "__main__":
    # ... (생략) ...
    # 실제 실행 시 store_embeddings(resume_id=1, ...)을 통해 DB에 최종 저장됩니다.