import re
import logging
from typing import Dict, List

logger = logging.getLogger("SectionSplitter")

class SectionSplitter:
    """
    Phase_2.md 규칙에 따라 이력서를 섹션별로 분할하는 엔진

    Attributes:
    - SECTION_RULES: 섹션별 키워드 매핑

    생성자: lyn
    생성일자: 2026-02-07
    """
    
    # Phase_2.md에 정의된 키워드 매핑 + 교육 정보 추가
    SECTION_RULES = {
        "target_info": ["지원", "희망", "포지션", "직무", "직군", "TARGET", "POSITION", "회사명", "기업명"],
        "education": ["학력", "대학교", "석사", "학사", "박사", "전공", "EDUCATION", "UNIVERSITY", "GRADUATED"],
        "skill_cert": ["기술", "자격증", "스택", "언어", "프레임워크", "도구", "환경", "SKILL", "CERT", "STACK"],
        "career_project": ["경력", "프로젝트", "인턴", "담당", "수행", "구축", "인프라", "설계", "EXPERIENCE", "PROJECT"],
        "cover_letter": ["자기소개", "지원동기", "성격", "가치관", "포부", "배움", "극복", "COVER LETTER", "성장과정"]
    }

    @classmethod
    def split_by_sections(cls, text: str) -> List[Dict[str, str]]:
        """
        이력서 원문을 훼손하지 않고 섹션별로 분할
        
        Args:
            text: 이력서 원문
            
        Returns:
            List[Dict[str, str]]: 섹션별 분할된 텍스트
        
        생성자: lyn
        생성일자: 2026-02-07
        """
        logger.info("✂️ 원문 기반 섹션 분할 시작...")
        
        # 1. 모든 키워드의 위치를 찾음
        all_markers = []
        for section, keywords in cls.SECTION_RULES.items():
            for kw in keywords:
                for m in re.finditer(re.escape(kw), text, re.IGNORECASE):
                    all_markers.append({
                        "pos": m.start(),
                        "type": section,
                        "keyword": kw
                    })
        
        # 위치 순으로 정렬
        all_markers.sort(key=lambda x: x["pos"])
        
        # 2. 섹션 경계 확정 (중복되거나 너무 가까운 마커 정리)
        segments = []
        last_pos = 0
        last_type = "skill_cert" # 기본값은 첫 섹션
        
        for marker in all_markers:
            # 새로운 구역이 시작됨을 감지
            if marker["pos"] > last_pos + 20: # 최소 20자 이상 거리가 있을 때만 분할
                content = text[last_pos:marker["pos"]].strip()
                if content:
                    segments.append({
                        "section_type": last_type,
                        "content": content
                    })
                last_pos = marker["pos"]
                last_type = marker["type"]
        
        # 마지막 조각 추가
        last_content = text[last_pos:].strip()
        if last_content:
            segments.append({
                "section_type": last_type,
                "content": last_content
            })
            
        logger.info(f"✅ 총 {len(segments)}개의 섹션 조각 생성 완료")
        return segments
