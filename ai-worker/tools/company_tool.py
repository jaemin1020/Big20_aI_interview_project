"""
Company 관련 데이터 조회 도구
"""
from sqlmodel import Session, select
from db import Company, Interview, engine
from typing import Dict, Optional
import logging

logger = logging.getLogger("CompanyTools")

class CompanyTool:
    """회사 정보 조회 도구"""
    
    @staticmethod
    def get_company_by_interview(interview_id: int) -> Dict:
        """
        면접 ID로 회사 정보 조회
        
        Args:
            interview_id: 면접 ID
            
        Returns:
            dict: {
                "id": str,
                "name": str,
                "ideal": str,
                "description": str,
                "has_company": bool
            }
        """
        with Session(engine) as session:
            # Interview 조회
            stmt = select(Interview).where(Interview.id == interview_id)
            interview = session.exec(stmt).first()
            
            if not interview or not interview.company_id:
                logger.warning(f"Interview {interview_id}에 연결된 회사 없음")
                return {
                    "id": "",
                    "name": "",
                    "ideal": "",
                    "description": "",
                    "has_company": False
                }
            
            # Company 조회
            company = session.get(Company, interview.company_id)
            if not company:
                logger.error(f"Company {interview.company_id} 찾을 수 없음")
                return {
                    "id": "",
                    "name": "",
                    "ideal": "",
                    "description": "",
                    "has_company": False
                }
            
            return {
                "id": company.id,
                "name": company.company_name,
                "ideal": company.ideal or "",
                "description": company.description or "",
                "has_company": True
            }
    
    @staticmethod
    def get_company_by_id(company_id: str) -> Optional[Company]:
        """Company ID로 직접 조회"""
        with Session(engine) as session:
            return session.get(Company, company_id)
    
    @staticmethod
    def format_for_llm(company_info: Dict) -> str:
        """
        LLM 프롬프트용 포맷팅
        
        Args:
            company_info: get_company_by_interview 반환값
            
        Returns:
            str: LLM에 전달할 포맷팅된 텍스트
        """
        if not company_info.get("has_company"):
            return "회사 정보 없음"
        
        parts = []
        parts.append("=== 회사 정보 ===")
        parts.append(f"회사명: {company_info.get('name', 'N/A')}")
        
        if company_info.get("ideal"):
            parts.append(f"\n인재상:")
            parts.append(company_info["ideal"])
        
        if company_info.get("description"):
            parts.append(f"\n회사 소개:")
            parts.append(company_info["description"])
        
        return "\n".join(parts)
