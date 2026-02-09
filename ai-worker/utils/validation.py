"""
이력서 파싱 결과 품질 검증 유틸리티
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger("ResumeValidation")


class ResumeValidator:
    """
    이력서 파싱 결과 품질 검증 클래스

    Attributes:
    - MIN_TEXT_LENGTH: 최소 텍스트 길이 (글자)
    - MIN_KOREAN_RATIO: 최소 한글 비율
    - MIN_SECTION_LENGTH: 섹션별 최소 길이

    생성자: ejm
    생성일자: 2026-02-08
    """
    
    # 검증 기준 상수
    MIN_TEXT_LENGTH = 100  # 최소 텍스트 길이 (글자)
    MIN_KOREAN_RATIO = 0.3  # 최소 한글 비율
    MIN_SECTION_LENGTH = 20  # 섹션별 최소 길이
    
    @classmethod
    def validate_extracted_text(cls, text: str) -> Tuple[bool, str]:
        """
        추출된 텍스트 품질 검증
        
        Args:
            text: 추출된 텍스트
            
        Returns:
            (is_valid, error_message)
        
        생성자: ejm
        생성일자: 2026-02-08
        """
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
        """
        섹션 분할 결과 검증
        
        Args:
            segments: 섹션 리스트 [{"section_type": str, "content": str}, ...]
            
        Returns:
            (is_valid, error_message)
        
        생성자: ejm
        생성일자: 2026-02-08
        """
        if not segments:
            return False, "섹션이 비어있습니다"
        
        # 최소 섹션 개수 검증 (너무 적으면 분할 실패 가능성)
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
        
        # 모든 섹션이 같은 타입이면 분할 실패 가능성
        section_types = set(s.get("section_type") for s in segments)
        if len(section_types) == 1:
            logger.warning(f"모든 섹션이 같은 타입입니다: {section_types}")
        
        return True, ""
    
    @classmethod
    def validate_structured_data(cls, structured_data: Dict) -> Tuple[bool, str]:
        """
        구조화된 데이터 검증
        
        Args:
            structured_data: 파싱된 구조화 데이터
            
        Returns:
            (is_valid, error_message)
        
        생성자: ejm
        생성일자: 2026-02-08
        """
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
        
        # 청크 정보 검증
        chunks_info = structured_data.get("chunks_info", [])
        if not chunks_info:
            return False, "청크 정보가 비어있습니다"
        
        if len(chunks_info) < 2:
            logger.warning(f"청크 개수가 적습니다: {len(chunks_info)}개")
        
        return True, ""
    
    @classmethod
    def validate_resume_data_for_embedding(cls, resume_data: Dict) -> Tuple[bool, str]:
        """
        임베딩 생성용 이력서 데이터 검증
        
        Args:
            resume_data: 임베딩 생성용 데이터
            
        Returns:
            (is_valid, error_message)
        
        생성자: ejm
        생성일자: 2026-02-08
        """
        if not resume_data:
            return False, "이력서 데이터가 비어있습니다"
        
        # 최소 하나 이상의 섹션에 실제 데이터가 있는지 확인
        has_data = any([
            resume_data.get("experience"),
            resume_data.get("projects"),
            resume_data.get("education"),
            resume_data.get("self_introduction"),
            resume_data.get("skills")
        ])
        
        if not has_data:
            return False, "임베딩 생성 가능한 데이터가 없습니다 (모든 섹션이 비어있음)"
        
        # 프로필 정보 검증
        profile = resume_data.get("profile", {})
        if not profile.get("target_position") and not profile.get("target_company"):
            logger.warning("프로필 정보가 부족합니다 (지원 직무/회사 없음)")
        
        return True, ""
    
    @classmethod
    def validate_embedding_vector(cls, vector: List[float], expected_dim: int = 1024) -> Tuple[bool, str]:
        """
        임베딩 벡터 검증
        
        Args:
            vector: 임베딩 벡터
            expected_dim: 예상 차원 (기본값: 1024 for KURE-v1)
            
        Returns:
            (is_valid, error_message)
        
        생성자: ejm
        생성일자: 2026-02-08
        """
        if not vector:
            return False, "임베딩 벡터가 비어있습니다"
        
        # 차원 검증
        if len(vector) != expected_dim:
            return False, f"임베딩 차원 불일치 ({len(vector)} != {expected_dim})"
        
        # 모든 값이 0인지 검증
        if all(v == 0 for v in vector):
            return False, "임베딩 벡터가 모두 0입니다"
        
        # NaN 또는 Inf 검증
        import math
        if any(math.isnan(v) or math.isinf(v) for v in vector):
            return False, "임베딩 벡터에 NaN 또는 Inf가 포함되어 있습니다"
        
        return True, ""
    
    @classmethod
    def get_quality_score(cls, text: str, segments: List[Dict], structured_data: Dict) -> Dict:
        """
        전체 품질 점수 계산
        
        Args:
            text: 추출된 텍스트
            segments: 섹션 리스트
            structured_data: 구조화된 데이터
            
        Returns:
            dict: 품질 점수 및 세부 정보
        
        생성자: ejm
        생성일자: 2026-02-08
        """
        score = 100
        issues = []
        
        # 텍스트 품질 (40점)
        text_valid, text_error = cls.validate_extracted_text(text)
        if not text_valid:
            score -= 40
            issues.append(f"텍스트: {text_error}")
        else:
            # 한글 비율에 따른 부분 점수
            korean_ratio = len(re.findall(r'[가-힣]', text)) / len(text)
            if korean_ratio < 0.5:
                score -= 10
                issues.append(f"텍스트: 한글 비율 낮음 ({korean_ratio:.2%})")
        
        # 섹션 분할 품질 (30점)
        sections_valid, sections_error = cls.validate_sections(segments)
        if not sections_valid:
            score -= 30
            issues.append(f"섹션: {sections_error}")
        else:
            # 섹션 다양성에 따른 부분 점수
            section_types = set(s.get("section_type") for s in segments)
            if len(section_types) < 3:
                score -= 10
                issues.append(f"섹션: 타입 다양성 부족 ({len(section_types)}개)")
        
        # 구조화 데이터 품질 (30점)
        data_valid, data_error = cls.validate_structured_data(structured_data)
        if not data_valid:
            score -= 30
            issues.append(f"데이터: {data_error}")
        else:
            # 필수 필드 누락에 따른 부분 점수
            if structured_data.get("target_company") == "Unknown":
                score -= 10
                issues.append("데이터: 지원 회사 정보 없음")
            if structured_data.get("target_position") == "Unknown":
                score -= 10
                issues.append("데이터: 지원 직무 정보 없음")
        
        return {
            "score": max(0, score),
            "grade": "A" if score >= 90 else "B" if score >= 70 else "C" if score >= 50 else "D",
            "issues": issues,
            "is_acceptable": score >= 50  # 50점 이상이면 허용
        }
