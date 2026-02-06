"""
데이터베이스 스키마 초기화 스크립트
WARNING: 모든 데이터를 삭제하고 테이블을 재생성합니다.
벡터 차원 불일치(768 -> 1024) 해결을 위해 사용합니다.
"""

import sys
import os

# backend-core 디렉토리를 path에 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlmodel import SQLModel, text
from database import engine, init_db

def reset_schema():
    print("WARNING: This will DROP ALL TABLES and DATA in the database.")
    # print("Proceed? (y/n)")
    # input()
    # 여기서는 안전하게 강제 진행합니다.
    
    print("🗑️ Dropping all tables...")
    try:
        # SQLModel에 등록된 메타데이터를 기반으로 테이블 삭제
        # 참고: cascade가 필요한 경우 raw sql을 사용해야 할 수 있음
        SQLModel.metadata.drop_all(engine)
        print("✅ Tables dropped.")
        
        print("🔄 Re-initializing database (Creating new tables with 1024 dims)...")
        init_db()
        print("✅ Database re-initialized successfully.")
        
    except Exception as e:
        print(f"❌ Error during reset: {str(e)}")
        # pgvector extension이 없으면 에러가 날 수 있으니 확인
        try:
            with Session(engine) as session:
                session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))
                session.commit()
                print("✅ pgvector extension ensured.")
        except:
            pass

if __name__ == "__main__":
    reset_schema()
