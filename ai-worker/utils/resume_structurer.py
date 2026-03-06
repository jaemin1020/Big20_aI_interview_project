import logging
import json
import os
from typing import Dict, List, Optional
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# EXAONE 엔진 임포트
try:
    from .exaone_llm import get_exaone_llm
except ImportError:
    # 절대 경로 fallback (ai-worker 루트 기준)
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from exaone_llm import get_exaone_llm

logger = logging.getLogger("ResumeStructurer")

# 데이터 구조 정의용 Pydantic 모델
class StructuredResume(BaseModel):
    """설명:
        이력서 구조화를 위한 Pydantic 모델

        생성자: lyn
        생성일자: 2026-02-04
    """
    personal_info: Dict = Field(description="이름, 이메일, 연락처 등 개인 정보")
    education: List[Dict] = Field(description="학력 사항 리스트 (학교, 전공, 학위, 졸업일)")
    experience: List[Dict] = Field(description="경력 사항 리스트 (회사명, 직무, 기간, 상세업무)")
    projects: List[Dict] = Field(description="프로젝트 리스트 (프로젝트명, 기간, 내용, 사용기술)")
    skills: Dict = Field(description="보유 기술 (언어, 프레임워크, DB, 보안기술 등)")
    certifications: List[Dict] = Field(description="자격증 및 수상 내역")
    cover_letter: Dict = Field(description="자기소개서 각 항목별 내용")

class ResumeStructurer:
    """설명:
        LLM 기반 이력서 구조화 엔진

        생성자: lyn
        생성일자: 2026-02-04
    """
    def __init__(self):
        """설명:
            ResumeStructurer 인스턴스를 초기화하고 EXAONE LLM 엔진과 JSON 파서를 준비.

        생성자: lyn
        생성일자: 2026-02-04
        """
        # EXAONE 엔진 초기화
        self.llm = get_exaone_llm()
        self.parser = JsonOutputParser(pydantic_object=StructuredResume)

    def structure_resume(self, text: str) -> Dict:
        """설명:
            LLM을 사용하여 이력서 텍스트를 완벽하게 구조화

            Args:
            text: 구조화할 이력서 텍스트

            Returns:
            

            생성자: lyn
            생성일자: 2026-02-04
        """
        logger.info("LLM을 이용한 이력서 구조화 시작...")
        
        system_msg = """당신은 문서를 정밀하게 분석하여 구조화된 데이터로 변환하는 이력서 파싱 전문가입니다.
LG AI Research의 EXAONE으로서, 제공된 [이력서 텍스트]를 분석하여 지정된 JSON 형식으로 완벽하게 구조화하십시오.

### 지침:
1. **절대로 가짜 정보를 생성하지 마세요.** 텍스트에 없는 내용은 빈 리스트[]나 빈 딕셔너리{}로 처리하십시오.
2. 이력서의 실제 내용을 최대한 구체적으로 반영하십시오. 특히 경력과 프로젝트 설명은 원문의 핵심 의미와 기술 스택을 보존해야 합니다.
3. 날짜 형식은 YYYY-MM-DD 또는 YYYY-MM 형식으로 통일하십시오."""

        user_msg = f"""아래의 [이력서 텍스트]를 분석하여 JSON 형식으로 출력하십시오.
        
### [이력서 텍스트]
{text}

### [출력 형식 가이드]
{self.parser.get_format_instructions()}"""

        # EXAONE 전용 프롬프트 생성
        prompt = self.llm._create_prompt(system_msg, user_msg)
        
        try:
            raw_output = self.llm.invoke(prompt, temperature=0.1)
            result = self.parser.parse(raw_output)
            logger.info("✅ 이력서 구조화 완료")
            return result
        except Exception as e:
            logger.error(f"LLM 이력서 구조화 실패: {e}")
            return self._get_fallback_data()

    def structure_with_rules(self, text: str) -> Dict:
        """설명:
            기존 코드와의 호환성을 위한 별칭

            Args:
            text: 구조화할 이력서 텍스트

            Returns:
            

            생성자: ejm
            생성일자: 2026-02-04
        """
        return self.structure_resume(text)

    def _get_fallback_data(self) -> Dict:
        """설명:
            실패 시 반환할 기본 구조

            Returns:
            

            생성자: lyn
            생성일자: 2026-02-04
        """
        return {
            "personal_info": {},
            "education": [],
            "experience": [],
            "projects": [],
            "skills": {},
            "certifications": [],
            "cover_letter": {}
        }


# 사용 예시
if __name__ == "__main__":
    # 테스트용 이력서 텍스트
    with open("resume_text.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
    
    structurer = ResumeStructurer()
    result = structurer.structure_resume(resume_text)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
