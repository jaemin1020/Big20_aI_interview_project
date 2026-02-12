"""
회사 데이터 임베딩 생성 및 DB 삽입 스크립트

Usage:
    python scripts/insert_companies.py
"""

import os
import sys
from pathlib import Path

# ai-worker 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer
from sqlmodel import Session, create_engine
from db_models import Company
from datetime import datetime

# 환경 변수에서 DB URL 가져오기
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:1234@localhost:5432/interview_db")

# 임베딩 모델 로드
print("📦 Loading embedding model...")
embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')
print("✅ Model loaded")

# 회사 데이터 정의
COMPANIES = [
    {
        "id": "KAKAO",
        "company_name": "카카오",
        "ideal": "도전적이고 창의적인 인재, 협업을 중시하며 사용자 중심의 서비스를 만드는 사람",
        "description": "IT 플랫폼 기업으로 메신저, 콘텐츠, 핀테크 등 다양한 서비스를 제공합니다."
    },
    {
        "id": "NAVER",
        "company_name": "네이버",
        "ideal": "기술 혁신을 추구하고 글로벌 마인드를 가진 인재, 끊임없이 학습하는 사람",
        "description": "검색, AI, 클라우드 등 기술 중심의 글로벌 IT 기업입니다."
    },
    {
        "id": "SAMSUNG",
        "company_name": "삼성전자",
        "ideal": "글로벌 리더십과 전문성을 갖춘 인재, 혁신과 품질을 중시하는 사람",
        "description": "반도체, 스마트폰, 가전 등을 생산하는 세계적인 전자 기업입니다."
    },
    {
        "id": "COUPANG",
        "company_name": "쿠팡",
        "ideal": "고객 만족을 최우선으로 하며 빠르게 실행하는 인재, 데이터 기반 의사결정을 하는 사람",
        "description": "이커머스 및 물류 혁신을 선도하는 기업입니다."
    },
    {
        "id": "TOSS",
        "company_name": "토스",
        "ideal": "금융 혁신에 열정이 있고 사용자 경험을 중시하는 인재, 빠른 실행력을 가진 사람",
        "description": "간편 송금부터 금융 슈퍼앱까지, 핀테크 혁신을 이끄는 기업입니다."
    }
]

def generate_embedding(text: str):
    """텍스트를 벡터로 변환"""
    return embedding_model.encode(text).tolist()

def insert_companies():
    """회사 데이터를 DB에 삽입"""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        for company_data in COMPANIES:
            # 기존 데이터 확인
            existing = session.get(Company, company_data["id"])
            if existing:
                print(f"⏭️  {company_data['id']} already exists, skipping...")
                continue
            
            # 임베딩 생성 (ideal + description 통합)
            text_for_embedding = " ".join([
                company_data["ideal"],
                company_data["description"]
            ])
            embedding = generate_embedding(text_for_embedding)
            
            # Company 객체 생성
            company = Company(
                id=company_data["id"],
                company_name=company_data["company_name"],
                ideal=company_data["ideal"],
                description=company_data["description"],
                embedding=embedding,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(company)
            print(f"✅ Inserted: {company.company_name} ({company.id})")
        
        session.commit()
        print("\n🎉 All companies inserted successfully!")

if __name__ == "__main__":
    print("=" * 60)
    print("회사 데이터 임베딩 생성 및 DB 삽입")
    print("=" * 60)
    insert_companies()
