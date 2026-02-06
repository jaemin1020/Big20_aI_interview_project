import logging
import json
import os
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

logger = logging.getLogger("ResumeStructurer")

# 데이터 구조 정의용 Pydantic 모델
class StructuredResume(BaseModel):
    personal_info: Dict = Field(description="이름, 이메일, 연락처 등 개인 정보")
    education: List[Dict] = Field(description="학력 사항 리스트 (학교, 전공, 학위, 졸업일)")
    experience: List[Dict] = Field(description="경력 사항 리스트 (회사명, 직무, 기간, 상세업무)")
    projects: List[Dict] = Field(description="프로젝트 리스트 (프로젝트명, 기간, 내용, 사용기술)")
    skills: Dict = Field(description="보유 기술 (언어, 프레임워크, DB, 보안기술 등)")
    certifications: List[Dict] = Field(description="자격증 및 수상 내역")
    cover_letter: Dict = Field(description="자기소개서 각 항목별 내용")

class ResumeStructurer:
    """LLM 기반 이력서 구조화 엔진"""

    def __init__(self):
        # 환경 변수에서 모델 설정 로드
        model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY가 없습니다. 구조화 작업이 실패할 수 있습니다.")

        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,  # 정확도를 위해 0으로 설정
            openai_api_key=api_key
        )
        self.parser = JsonOutputParser(pydantic_object=StructuredResume)

    def structure_resume(self, text: str) -> Dict:
        """
        LLM을 사용하여 이력서 텍스트를 완벽하게 구조화
        """
        logger.info("🤖 LLM을 이용한 이력서 구조화 시작...")
        
        prompt = ChatPromptTemplate.from_template("""
        당신은 최고의 채용 컨설턴트입니다. 아래 제공된 [이력서 텍스트]를 분석하여 지정된 JSON 형식으로 구조화하세요.
        
        ### 지침:
        1. **절대로 가짜 정보를 생성하지 마세요.** 텍스트에 없는 내용은 빈 리스트[]나 빈 딕셔너리{{}}로 처리하세요.
        2. 이력서의 실제 내용을 최대한 구체적으로 반영하세요. 특히 경력과 프로젝트 설명은 원문의 의미를 보존해야 합니다.
        3. 날짜 형식은 YYYY-MM-DD 또는 YYYY-MM 형식으로 통일해 주세요.
        
        ### [이력서 텍스트]
        {resume_text}
        
        ### [출력 형식]
        {format_instructions}
        """)

        chain = prompt | self.llm | self.parser
        
        try:
            result = chain.invoke({
                "resume_text": text,
                "format_instructions": self.parser.get_format_instructions()
            })
            logger.info("✅ 이력서 구조화 완료")
            return result
        except Exception as e:
            logger.error(f"❌ 이력서 구조화 실패: {e}")
            return self._get_fallback_data()

    def structure_with_rules(self, text: str) -> Dict:
        """기존 코드와의 호환성을 위한 별칭"""
        return self.structure_resume(text)

    def _get_fallback_data(self) -> Dict:
        """실패 시 반환할 기본 구조"""
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
