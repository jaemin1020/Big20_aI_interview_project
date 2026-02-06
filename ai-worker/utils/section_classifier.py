"""
이력서 섹션 분류기 (Section Classifier)
LLM을 사용하여 이력서 텍스트를 의미 단위로 분류
"""
import logging
from typing import Dict, List
import re

logger = logging.getLogger("SectionClassifier")


class ResumeSectionClassifier:
    """
    이력서 텍스트를 섹션별로 분류하는 클래스
    
    섹션 타입:
    - SKILL_CERT: 기술 스택, 자격증
    - CAREER_PROJECT: 경력, 프로젝트
    - COVER_LETTER: 자기소개서 (지원동기, 성격, 포부 등)
    """
    
    # 키워드 기반 분류 규칙
    SKILL_KEYWORDS = [
        "기술", "스킬", "skill", "자격증", "certification", "언어", "language",
        "프로그래밍", "programming", "도구", "tool", "프레임워크", "framework",
        "데이터베이스", "database", "네트워크", "network", "보안", "security"
    ]
    
    CAREER_KEYWORDS = [
        "경력", "career", "프로젝트", "project", "경험", "experience",
        "인턴", "intern", "근무", "work", "담당", "수행", "개발", "develop",
        "구축", "설계", "design", "운영", "operation"
    ]
    
    COVER_KEYWORDS = [
        "자기소개", "지원동기", "motivation", "성장과정", "성격", "personality",
        "장점", "단점", "strength", "weakness", "포부", "목표", "goal",
        "비전", "vision", "가치관", "value"
    ]
    
    @classmethod
    def classify_chunk(cls, text: str, chunk_index: int = 0) -> str:
        """
        텍스트 청크를 분석하여 섹션 타입 반환
        
        Args:
            text: 분류할 텍스트
            chunk_index: 청크 인덱스 (순서 정보)
            
        Returns:
            str: 'skill_cert', 'career_project', 'cover_letter'
        """
        text_lower = text.lower()
        
        # 점수 계산
        skill_score = sum(1 for keyword in cls.SKILL_KEYWORDS if keyword in text_lower)
        career_score = sum(1 for keyword in cls.CAREER_KEYWORDS if keyword in text_lower)
        cover_score = sum(1 for keyword in cls.COVER_KEYWORDS if keyword in text_lower)
        
        logger.debug(f"Chunk {chunk_index} scores - Skill: {skill_score}, Career: {career_score}, Cover: {cover_score}")
        
        # 가장 높은 점수의 섹션 반환
        scores = {
            'skill_cert': skill_score,
            'career_project': career_score,
            'cover_letter': cover_score
        }
        
        max_section = max(scores, key=scores.get)
        
        # 점수가 모두 0이면 내용 길이로 판단
        if scores[max_section] == 0:
            # 긴 텍스트는 자기소개서일 가능성이 높음
            if len(text) > 500:
                return 'cover_letter'
            # 짧은 텍스트는 기술/자격증일 가능성이 높음
            return 'skill_cert'
        
        return max_section
    
    @classmethod
    def classify_full_resume(cls, chunks: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        전체 이력서 청크들을 분류
        
        Args:
            chunks: [{"content": "...", "chunk_index": 0}, ...]
            
        Returns:
            List[Dict]: [{"content": "...", "chunk_index": 0, "section_type": "skill_cert"}, ...]
        """
        classified_chunks = []
        
        for chunk in chunks:
            section_type = cls.classify_chunk(
                chunk['content'],
                chunk.get('chunk_index', 0)
            )
            
            classified_chunks.append({
                **chunk,
                'section_type': section_type
            })
            
            logger.info(f"Chunk {chunk.get('chunk_index', 0)}: {section_type}")
        
        return classified_chunks
