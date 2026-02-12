"""
이력서 파싱 결과 품질 검증 유틸리티
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("ResumeValidation")


class ResumeValidator:
    """이력서 파싱 결과 품질 검증 클래스"""
    
    # 검증 기준 상수
    MIN_TEXT_LENGTH = 100  # 최소 텍스트 길이 (글자)
    MIN_KOREAN_RATIO = 0.3  # 최소 한글 비율
    MIN_SECTION_LENGTH = 20  # 섹션별 최소 길이
    
    @classmethod
    def validate_extracted_text(cls, text: str) -> Tuple[bool, str]:
        """추출된 텍스트 품질 검증"""
        if not text or not text.strip():
            return False, "추출된 텍스트가 비어있습니다"
        
        # 최소 길이 검증
        if len(text) < cls.MIN_TEXT_LENGTH:
            return False, f"추출된 텍스트가 너무 짧습니다 ({len(text)}자 < {cls.MIN_TEXT_LENGTH}자)"
        
        # 한글 비율 검증
        korean_chars = len(re.findall(r'[가-힣]', text))
        total_chars = len(text)
        korean_ratio = korean_chars / total_chars if total_chars > 0 else 0
        
        if korean_ratio < cls.MIN_KOREAN_RATIO:
            logger.warning(
                f"한글 비율이 낮습니다: {korean_ratio:.2%} "
                f"({korean_chars}/{total_chars}자)"
            )
            return False, f"한글 비율이 너무 낮습니다 ({korean_ratio:.2%} < {cls.MIN_KOREAN_RATIO:.0%})"
        
        # 의미 있는 단어 검증 (최소 10개 이상의 한글 단어)
        korean_words = re.findall(r'[가-힣]{2,}', text)
        if len(korean_words) < 10:
            return False, f"의미 있는 한글 단어가 부족합니다 ({len(korean_words)}개 < 10개)"
        
        return True, ""
    
    @classmethod
    def validate_sections(cls, segments: List[Dict]) -> Tuple[bool, str]:
        """섹션 분할 결과 검증"""
        if not segments:
            return False, "섹션이 비어있습니다"
        
        # 최소 섹션 개수 검증
        if len(segments) < 2:
            logger.warning(f"섹션 개수가 적습니다: {len(segments)}개")
        
        # 각 섹션의 최소 길이 검증
        invalid_sections = []
        for idx, segment in enumerate(segments):
            content = segment.get("content", "")
            if len(content) < cls.MIN_SECTION_LENGTH:
                invalid_sections.append(f"섹션 {idx} ({segment.get('section_type')}): {len(content)}자")
        
        if invalid_sections:
            logger.warning(f"짧은 섹션 발견: {', '.join(invalid_sections)}")
        
        return True, ""
    
    @classmethod
    def validate_structured_data(cls, structured_data: Dict) -> Tuple[bool, str]:
        """구조화된 데이터 검증"""
        if not structured_data:
            return False, "구조화된 데이터가 비어있습니다"
        
        # 필수 필드 검증
        required_fields = ["target_company", "target_position"]
        missing_fields = []
        for field in required_fields:
            value = structured_data.get(field)
            if not value or value == "Unknown":
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"필수 필드 누락 또는 Unknown: {', '.join(missing_fields)}")
        
        return True, ""
    
    @classmethod
    def validate_resume_data_for_embedding(cls, resume_data: Dict) -> Tuple[bool, str]:
        """임베딩 생성용 이력서 데이터 검증"""
        if not resume_data:
            return False, "이력서 데이터가 비어있습니다"
        
        has_data = any([
            resume_data.get("experience"),
            resume_data.get("projects"),
            resume_data.get("education"),
            resume_data.get("self_introduction"),
            resume_data.get("skills")
        ])
        
        if not has_data:
            return False, "임베딩 생성 가능한 데이터가 없습니다 (모든 섹션이 비어있음)"
        
        return True, ""
    
    @classmethod
    def validate_embedding_vector(cls, vector: List[float], expected_dim: int = 1024) -> Tuple[bool, str]:
        """임베딩 벡터 검증"""
        if not vector:
            return False, "임베딩 벡터가 비어있습니다"
        
        if len(vector) != expected_dim:
            return False, f"임베딩 차원 불일치 ({len(vector)} != {expected_dim})"
        
        return True, ""
    
    @classmethod
    def get_quality_score(cls, text: str, segments: List[Dict], structured_data: Dict) -> Dict:
        """전체 품질 점수 계산"""
        score = 100
        issues = []
        
        text_valid, text_error = cls.validate_extracted_text(text)
        if not text_valid:
            score -= 40
            issues.append(f"텍스트: {text_error}")
        
        sections_valid, sections_error = cls.validate_sections(segments)
        if not sections_valid:
            score -= 30
            issues.append(f"섹션: {sections_error}")
        
        data_valid, data_error = cls.validate_structured_data(structured_data)
        if not data_valid:
            score -= 30
            issues.append(f"데이터: {data_error}")
        
        return {
            "score": max(0, score),
            "grade": "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "D",
            "issues": issues,
            "is_acceptable": score >= 50
        }
