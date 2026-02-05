"""
Resume 관련 데이터 조회 및 처리 도구
"""
from sqlmodel import Session, select
from db import Resume, Interview, engine
from typing import Dict, Optional
import logging

logger = logging.getLogger("ResumeTools")


class ResumeTool:
    """이력서 정보 조회 및 처리 도구"""
    
    @staticmethod
    def get_resume_by_interview(interview_id: int) -> Dict:
        """
        면접 ID로 이력서 정보 조회
        
        Args:
            interview_id: 면접 ID
            
        Returns:
            dict: {
                "extracted_text": str,
                "structured_data": dict,
                "summary": str,
                "has_resume": bool,
                "processing_status": str
            }
        """
        with Session(engine) as session:
            # Interview 조회
            stmt = select(Interview).where(Interview.id == interview_id)
            interview = session.exec(stmt).first()
            
            if not interview or not interview.resume_id:
                logger.warning(f"Interview {interview_id}에 연결된 이력서 없음")
                return {
                    "extracted_text": "",
                    "structured_data": {},
                    "summary": "",
                    "has_resume": False,
                    "processing_status": "none"
                }
            
            # Resume 조회
            resume = session.get(Resume, interview.resume_id)
            if not resume:
                logger.error(f"Resume {interview.resume_id} 찾을 수 없음")
                return {
                    "extracted_text": "",
                    "structured_data": {},
                    "summary": "",
                    "has_resume": False,
                    "processing_status": "error"
                }
            
            # 처리 완료 확인
            if resume.processing_status != "completed":
                logger.warning(f"Resume {resume.id} 아직 처리 중: {resume.processing_status}")
                return {
                    "extracted_text": resume.extracted_text or "",
                    "structured_data": {},
                    "summary": "이력서 처리 중...",
                    "has_resume": True,
                    "processing_status": resume.processing_status
                }
            
            return {
                "extracted_text": resume.extracted_text or "",
                "structured_data": resume.structured_data or {},
                "summary": ResumeTool._generate_summary(resume),
                "has_resume": True,
                "processing_status": resume.processing_status
            }
    
    @staticmethod
    def get_resume_by_id(resume_id: int) -> Optional[Resume]:
        """Resume ID로 직접 조회"""
        with Session(engine) as session:
            return session.get(Resume, resume_id)
    
    @staticmethod
    def _generate_summary(resume: Resume) -> str:
        """
        이력서 요약 생성
        
        Args:
            resume: Resume 객체
            
        Returns:
            str: 요약 텍스트
        """
        if not resume.structured_data:
            # 구조화 데이터가 없으면 텍스트 앞부분만 반환
            text = resume.extracted_text or ""
            return text[:500] + "..." if len(text) > 500 else text
        
        data = resume.structured_data
        summary_parts = []
        
        # 경력
        if "experience" in data and data["experience"]:
            exp_count = len(data["experience"])
            if exp_count > 0:
                latest_exp = data["experience"][0]
                company = latest_exp.get("company", "N/A")
                position = latest_exp.get("position", "N/A")
                summary_parts.append(f"최근 경력: {company} - {position} (총 {exp_count}개 경력)")
        
        # 기술스택 (dict 구조 처리)
        if "skills" in data:
            skills_data = data["skills"]
            if isinstance(skills_data, dict):
                # 보안 기술 우선 표시
                if "security" in skills_data and skills_data["security"]:
                    skills_str = ", ".join(skills_data["security"][:3])
                    summary_parts.append(f"보안 기술: {skills_str}")
            elif isinstance(skills_data, list):
                # 리스트인 경우 (하위 호환성)
                skills_str = ", ".join(skills_data[:5])
                summary_parts.append(f"주요 기술: {skills_str}")
        
        # 학력
        if "education" in data and data["education"]:
            edu = data["education"][0]
            school = edu.get("school", "N/A")
            degree = edu.get("degree", "N/A")
            major = edu.get("major", "N/A")
            summary_parts.append(f"학력: {school} {degree} ({major})")
        
        # 프로젝트
        if "projects" in data and data["projects"]:
            project_count = len(data["projects"])
            summary_parts.append(f"프로젝트: {project_count}개")
        
        return " | ".join(summary_parts) if summary_parts else "이력서 정보 없음"

    
    @staticmethod
    def format_for_llm(resume_info: Dict) -> str:
        """
        LLM 프롬프트용 포맷팅
        
        Args:
            resume_info: get_resume_by_interview 반환값
            
        Returns:
            str: LLM에 전달할 포맷팅된 텍스트
        """
        if not resume_info.get("has_resume"):
            return "이력서 정보 없음"
        
        parts = []
        parts.append("=== 지원자 이력서 요약 ===")
        parts.append(resume_info.get("summary", ""))
        parts.append("")
        
        structured = resume_info.get("structured_data", {})
        
        # 경력
        if "experience" in structured and structured["experience"]:
            parts.append("주요 경력:")
            for i, exp in enumerate(structured["experience"][:3], 1):  # 최근 3개만
                company = exp.get("company", "N/A")
                position = exp.get("position", "N/A")
                duration = exp.get("duration", "N/A")
                description = exp.get("description", "")
                parts.append(f"{i}. {company} - {position} ({duration})")
                if description:
                    parts.append(f"   {description[:100]}...")
            parts.append("")
        
        # 기술스택 (dict 구조 처리)
        if "skills" in structured:
            skills_data = structured["skills"]
            if isinstance(skills_data, dict):
                parts.append("기술스택:")
                if "security" in skills_data and skills_data["security"]:
                    parts.append(f"  보안: {', '.join(skills_data['security'])}")
                if "programming_languages" in skills_data and skills_data["programming_languages"]:
                    parts.append(f"  언어: {', '.join(skills_data['programming_languages'])}")
            elif isinstance(skills_data, list):
                # 리스트인 경우 (하위 호환성)
                parts.append(f"기술스택: {', '.join(skills_data)}")
            parts.append("")
        
        # 프로젝트
        if "projects" in structured and structured["projects"]:
            parts.append("주요 프로젝트:")
            for i, proj in enumerate(structured["projects"][:2], 1):  # 최근 2개만
                name = proj.get("name", "N/A")
                description = proj.get("description", "")
                parts.append(f"{i}. {name}")
                if description:
                    parts.append(f"   {description[:100]}...")
            parts.append("")
        
        return "\n".join(parts)
