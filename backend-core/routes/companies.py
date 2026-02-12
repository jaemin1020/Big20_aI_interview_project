from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import logging

from database import get_session

from db_models import Company
from pydantic import BaseModel

logger = logging.getLogger("Backend-Core")
router = APIRouter(prefix="/companies", tags=["companies"])

# ==================== Request/Response Models ====================

class CompanyResponse(BaseModel):
    """회사 정보 응답 모델
    
    Args:
        id (str): 회사 ID
        company_name (str): 회사 이름
        ideal (str | None): 이상향
        description (str | None): 설명
    
    생성자: ejm
    생성일자: 2026-02-08
    """
    id: str
    company_name: str
    ideal: str | None
    description: str | None

# ==================== Endpoints ====================
# Note: 회사 데이터는 DB에 직접 삽입됩니다 (벡터 임베딩 포함)
# 임베딩 생성은 ai-worker의 별도 스크립트에서 처리

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str, db: Session = Depends(get_session)):
    """
    회사 정보 조회
    
    Args:
        company_id (str): 회사 ID
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).
        
    Returns:
        CompanyResponse: 회사 정보
    
    생성자: ejm
    생성일자: 2026-02-08
    """
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
    """
    회사 목록 조회
    
    Args:
        skip (int, optional): 건너뛸 개수. Defaults to 0.
        limit (int, optional): 가져올 개수. Defaults to 20.
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).
        
    Returns:
        List[CompanyResponse]: 회사 목록
    
    생성자: ejm
    생성일자: 2026-02-08
    """
    stmt = select(Company).offset(skip).limit(limit)
    companies = db.exec(stmt).all()
    return companies

@router.get("/{company_id}/similar", response_model=List[CompanyResponse])
async def find_similar_companies(
    company_id: str,
    limit: int = 5,
    db: Session = Depends(get_session)
):
    """
    유사한 회사 찾기 (벡터 유사도 기반)
    
    Args:
        company_id (str): 회사 ID
        limit (int, optional): 가져올 개수. Defaults to 5.
        db (Session, optional): 데이터베이스 세션. Defaults to Depends(get_session).
        
    Returns:
        List[CompanyResponse]: 유사한 회사 목록
    
    생성자: ejm
    생성일자: 2026-02-08
    """
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