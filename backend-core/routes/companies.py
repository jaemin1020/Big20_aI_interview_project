from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from sentence_transformers import SentenceTransformer
import logging

from database import get_session
from models import Company
from pydantic import BaseModel

logger = logging.getLogger("Backend-Core")
router = APIRouter(prefix="/companies", tags=["companies"])

# 임베딩 모델 (한국어 지원)
embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# ==================== Request/Response Models ====================

class CompanyCreate(BaseModel):
    id: str
    company_name: str
    ideal: str | None = None
    description: str | None = None

class CompanyResponse(BaseModel):
    id: str
    company_name: str
    ideal: str | None
    description: str | None

# ==================== Endpoints ====================

@router.post("/", response_model=CompanyResponse)
async def create_company(company_data: CompanyCreate, db: Session = Depends(get_session)):
    """회사 정보 생성 (자동 벡터화)"""
    
    # 벡터 임베딩 생성 (ideal + description 통합)
    text_for_embedding = " ".join(filter(None, [
        company_data.ideal or "",
        company_data.description or ""
    ]))
    
    embedding = None
    if text_for_embedding.strip():
        embedding = embedding_model.encode(text_for_embedding).tolist()
    
    # 회사 생성
    new_company = Company(
        **company_data.model_dump(),
        embedding=embedding
    )
    
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    
    logger.info(f"Company created: {new_company.id} - {new_company.company_name}")
    return new_company

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str, db: Session = Depends(get_session)):
    """회사 정보 조회"""
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.get("/", response_model=List[CompanyResponse])
async def list_companies(
    skip: int = 0, 
    limit: int = 20,
    db: Session = Depends(get_session)
):
    """회사 목록 조회"""
    stmt = select(Company).offset(skip).limit(limit)
    companies = db.exec(stmt).all()
    return companies

@router.get("/{company_id}/similar", response_model=List[CompanyResponse])
async def find_similar_companies(
    company_id: str,
    limit: int = 5,
    db: Session = Depends(get_session)
):
    """유사한 회사 찾기 (벡터 유사도 기반)"""
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    if not company.embedding:
        raise HTTPException(status_code=400, detail="Company has no embedding")
    
    # pgvector 코사인 유사도 검색
    stmt = select(Company).where(
        Company.id != company_id,
        Company.embedding.isnot(None)
    ).order_by(
        Company.embedding.cosine_distance(company.embedding)
    ).limit(limit)
    
    similar_companies = db.exec(stmt).all()
    return similar_companies

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_data: CompanyCreate,
    db: Session = Depends(get_session)
):
    """회사 정보 업데이트 (벡터 재생성)"""
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # 벡터 재생성
    text_for_embedding = " ".join(filter(None, [
        company_data.ideal or "",
        company_data.description or ""
    ]))
    
    if text_for_embedding.strip():
        embedding = embedding_model.encode(text_for_embedding).tolist()
        company.embedding = embedding
    
    # 필드 업데이트
    company.company_name = company_data.company_name
    company.ideal = company_data.ideal
    company.description = company_data.description
    
    from datetime import datetime
    company.updated_at = datetime.utcnow()
    
    db.add(company)
    db.commit()
    db.refresh(company)
    
    logger.info(f"Company updated: {company.id}")
    return company

@router.delete("/{company_id}")
async def delete_company(company_id: str, db: Session = Depends(get_session)):
    """회사 삭제"""
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    db.delete(company)
    db.commit()
    
    logger.info(f"Company deleted: {company_id}")
    return {"message": "Company deleted successfully"}
