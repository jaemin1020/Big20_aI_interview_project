"""
이력서 멀티 섹션 임베딩 생성기
각 섹션(프로필, 경력, 프로젝트, 자기소개 등)별로 벡터를 생성하여 RAG에 활용
"""
import logging
from typing import Dict, List, Optional
from .vector_utils import get_embedding_generator

logger = logging.getLogger("ResumeEmbedder")


class ResumeEmbedder:
    """이력서 섹션별 임베딩 생성 클래스
    
    Attributes:
        generator: 임베딩 생성기
    
    생성자: ejm
    생성일자: 2026-02-04
    """
    
    def __init__(self):
        self.generator = get_embedding_generator()
    
    # =========================
    # 직렬화 함수 (텍스트 변환)
    # =========================
    
    @staticmethod
    def serialize_profile(profile: Dict) -> str:
        """
        프로필 정보를 텍스트로 변환
        
        Args:
            profile: 프로필 정보 (dict)
            
        Returns:
            str: 변환된 텍스트
        
        생성자: ejm,lyn
        생성일자: 2026-02-04
        """
        return f"""
이름: {profile.get('name', '')}
지원직무: {profile.get('target_position', '')}
지원회사: {profile.get('target_company', '')}
연락처: {profile.get('contact', '')}
""".strip()
    
    @staticmethod
    def serialize_experience(exp: Dict) -> str:
        """
        경력 정보를 텍스트로 변환
        
        Args:
            exp: 경력 정보 (dict)
            
        Returns:
            str: 변환된 텍스트
        
        생성자: ejm,lyn
        생성일자: 2026-02-04
        """
        return f"""
회사: {exp.get('company', '')}
지역: {exp.get('location', '')}
직무: {exp.get('role', '')}
기간: {exp.get('period', '')}
내용: {exp.get('description', '')}
""".strip()
    
    @staticmethod
    def serialize_project(proj: Dict) -> str:
        """
        프로젝트 정보를 텍스트로 변환
        
        Args:
            proj: 프로젝트 정보 (dict)
            
        Returns:
            str: 변환된 텍스트
        
        생성자: ejm,lyn
        생성일자: 2026-02-04
        """
        return f"""
프로젝트명: {proj.get('title', '')}
기간: {proj.get('period', '')}
내용: {proj.get('description', '')}
""".strip()
    
    @staticmethod
    def serialize_education(edu: Dict) -> str:
        """
        학력 정보를 텍스트로 변환
        
        Args:
            edu: 학력 정보 (dict)
            
        Returns:
            str: 변환된 텍스트
        
        생성자: ejm,lyn
        생성일자: 2026-02-04
        """
        return f"""
학교: {edu.get('school', '')}
전공: {edu.get('major', '')}
학위: {edu.get('degree', '')}
기간: {edu.get('period', '')}
""".strip()
    
    @staticmethod
    def serialize_certifications(certs: List[Dict]) -> str:
        """
        자격증 정보를 텍스트로 변환
        
        Args:
            certs: 자격증 정보 (list of dict)
            
        Returns:
            str: 변환된 텍스트
        
        생성자: ejm,lyn
        생성일자: 2026-02-04
        """
        if not certs:
            return ""
        return "\n".join([f"{c.get('name', '')} {c.get('date', '')}" for c in certs])
    
    @staticmethod
    def serialize_languages(langs: List[Dict]) -> str:
        """
        어학 정보를 텍스트로 변환
        
        Args:
            langs: 어학 정보 (list of dict)
            
        Returns:
            str: 변환된 텍스트
        
        생성자: ejm,lyn
        생성일자: 2026-02-04
        """
        if not langs:
            return ""
        return "\n".join([f"{l.get('name', '')} {l.get('level', '')} {l.get('date', '')}" for l in langs])
    
    @staticmethod
    def serialize_skills(skills: Dict) -> str:
        """
        기술 스택 정보를 텍스트로 변환
        
        Args:
            skills: 기술 스택 정보 (dict)
            
        Returns:
            str: 변환된 텍스트
        
        생성자: ejm,lyn
        생성일자: 2026-02-04
        """
        if not skills:
            return ""
        
        parts = []
        for category, skill_list in skills.items():
            if isinstance(skill_list, list):
                parts.append(f"{category}: {', '.join(skill_list)}")
            else:
                parts.append(f"{category}: {skill_list}")
        
        return "\n".join(parts)
    
    # =========================
    # 임베딩 생성 함수
    # =========================
    
    def build_resume_embeddings(self, resume_data: Dict) -> Dict:
        """
        이력서 전체 섹션별 임베딩 생성
        
        Args:
            resume_data: 파싱된 이력서 데이터 (dict)
        
        Returns:
            dict: 섹션별 임베딩 벡터
        
        Raises:
            ValueError: resume_data가 dict 타입이 아닐 때

        생성자: lyn
        생성일자: 2026-02-04
        """
        logger.info("이력서 멀티 섹션 임베딩 생성 시작")
        
        output = {
            "resume_id": resume_data.get("resume_id", "unknown"),
            "role": resume_data.get("profile", {}).get("target_position", ""),
            "embeddings": {
                "profile": {},
                "experience": [],
                "projects": [],
                "education": [],
                "self_introduction": [],
                "certifications": {},
                "languages": {},
                "skills": {}
            }
        }
        
        # -------- 프로필 --------
        if "profile" in resume_data:
            profile_text = self.serialize_profile(resume_data["profile"])
            if profile_text:
                output["embeddings"]["profile"]["text"] = profile_text
                output["embeddings"]["profile"]["vector"] = self.generator.encode_passage(profile_text)
                logger.debug("✅ 프로필 임베딩 생성 완료")
        
        # -------- 경력 --------
        for idx, exp in enumerate(resume_data.get("experience", []), start=1):
            text = self.serialize_experience(exp)
            if text:
                output["embeddings"]["experience"].append({
                    "id": f"exp_{idx}",
                    "text": text,
                    "vector": self.generator.encode_passage(text)
                })
        logger.debug(f"✅ 경력 {len(output['embeddings']['experience'])}개 임베딩 생성 완료")
        
        # -------- 프로젝트 --------
        for idx, proj in enumerate(resume_data.get("projects", []), start=1):
            text = self.serialize_project(proj)
            if text:
                output["embeddings"]["projects"].append({
                    "id": f"proj_{idx}",
                    "text": text,
                    "vector": self.generator.encode_passage(text)
                })
        logger.debug(f"✅ 프로젝트 {len(output['embeddings']['projects'])}개 임베딩 생성 완료")
        
        # -------- 학력 --------
        for idx, edu in enumerate(resume_data.get("education", []), start=1):
            text = self.serialize_education(edu)
            if text:
                output["embeddings"]["education"].append({
                    "id": f"edu_{idx}",
                    "text": text,
                    "vector": self.generator.encode_passage(text)
                })
        logger.debug(f"✅ 학력 {len(output['embeddings']['education'])}개 임베딩 생성 완료")
        
        # -------- 자기소개 --------
        for si in resume_data.get("self_introduction", []):
            si_text = f"""
질문: {si.get('question', '')}
답변: {si.get('answer', '')}
""".strip()
            
            q = si.get("question", "")
            
            # 질문 타입 자동 분류 (룰 기반)
            if "지원한 이유" in q or "성장계획" in q or "지원동기" in q:
                si_type = "지원동기/성장계획"
            elif "협업" in q or "팀워크" in q:
                si_type = "협업경험"
            elif "연구" in q or "프로젝트" in q:
                si_type = "연구/프로젝트"
            elif "학습" in q or "노하우" in q:
                si_type = "학습노하우"
            elif "강점" in q or "장점" in q:
                si_type = "강점/역량"
            else:
                si_type = "기타"
            
            if si_text:
                output["embeddings"]["self_introduction"].append({
                    "type": si_type,
                    "text": si_text,
                    "vector": self.generator.encode_passage(si_text)
                })
        logger.debug(f"✅ 자기소개 {len(output['embeddings']['self_introduction'])}개 임베딩 생성 완료")
        
        # -------- 자격증 --------
        cert_text = self.serialize_certifications(resume_data.get("certifications", []))
        if cert_text:
            output["embeddings"]["certifications"]["text"] = cert_text
            output["embeddings"]["certifications"]["vector"] = self.generator.encode_passage(cert_text)
            logger.debug("✅ 자격증 임베딩 생성 완료")
        
        # -------- 어학 --------
        lang_text = self.serialize_languages(resume_data.get("languages", []))
        if lang_text:
            output["embeddings"]["languages"]["text"] = lang_text
            output["embeddings"]["languages"]["vector"] = self.generator.encode_passage(lang_text)
            logger.debug("✅ 어학 임베딩 생성 완료")
        
        # -------- 기술 스택 --------
        skills_text = self.serialize_skills(resume_data.get("skills", {}))
        if skills_text:
            output["embeddings"]["skills"]["text"] = skills_text
            output["embeddings"]["skills"]["vector"] = self.generator.encode_passage(skills_text)
            logger.debug("✅ 기술 스택 임베딩 생성 완료")
        
        logger.info("✅ 이력서 멀티 섹션 임베딩 생성 완료")
        return output
    
    def search_relevant_sections(self, query: str, resume_embeddings: Dict, top_k: int = 3) -> List[Dict]:
        """
        쿼리와 가장 관련있는 이력서 섹션 검색
        
        Args:
            query: 검색 쿼리 (예: "프로젝트 경험")
            resume_embeddings: build_resume_embeddings()의 결과
            top_k: 반환할 상위 결과 개수
        
        Returns:
            list: 유사도가 높은 섹션 리스트
        
        Raises:
            ValueError: resume_embeddings가 dict 타입이 아닐 때
        
        생성자: lyn,ejm
        생성일자: 2026-02-04
        """
        from numpy import dot
        from numpy.linalg import norm
        
        query_vector = self.generator.encode_query(query)
        
        results = []
        
        # 모든 섹션의 벡터와 유사도 계산
        embeddings = resume_embeddings.get("embeddings", {})
        
        # 프로필
        if "vector" in embeddings.get("profile", {}):
            similarity = dot(query_vector, embeddings["profile"]["vector"]) / (
                norm(query_vector) * norm(embeddings["profile"]["vector"])
            )
            results.append({
                "section": "profile",
                "text": embeddings["profile"].get("text", ""),
                "similarity": float(similarity)
            })
        
        # 경력
        for exp in embeddings.get("experience", []):
            if "vector" in exp:
                similarity = dot(query_vector, exp["vector"]) / (
                    norm(query_vector) * norm(exp["vector"])
                )
                results.append({
                    "section": "experience",
                    "id": exp.get("id", ""),
                    "text": exp.get("text", ""),
                    "similarity": float(similarity)
                })
        
        # 프로젝트
        for proj in embeddings.get("projects", []):
            if "vector" in proj:
                similarity = dot(query_vector, proj["vector"]) / (
                    norm(query_vector) * norm(proj["vector"])
                )
                results.append({
                    "section": "project",
                    "id": proj.get("id", ""),
                    "text": proj.get("text", ""),
                    "similarity": float(similarity)
                })
        
        # 자기소개
        for si in embeddings.get("self_introduction", []):
            if "vector" in si:
                similarity = dot(query_vector, si["vector"]) / (
                    norm(query_vector) * norm(si["vector"])
                )
                results.append({
                    "section": "self_introduction",
                    "type": si.get("type", ""),
                    "text": si.get("text", ""),
                    "similarity": float(similarity)
                })
        
        # 유사도 기준 정렬 및 상위 k개 반환
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]


# 전역 인스턴스
_embedder = None

def get_resume_embedder() -> ResumeEmbedder:
    """이력서 임베더 싱글톤 인스턴스 반환"""
    global _embedder
    if _embedder is None:
        _embedder = ResumeEmbedder()
    return _embedder
