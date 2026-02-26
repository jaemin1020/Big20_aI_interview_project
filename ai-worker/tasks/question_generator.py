# interview_question_generator.py

import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ==============================
# 1. Prompt Builder
# ==============================

class ExaonePromptBuilder:
    """
    EXAONE 모델 최적화 질문 생성 프롬프트 생성기
    """

    @staticmethod
    def build_question_prompt(context: Dict[str, Any]) -> str:
        resume = context.get("resume", "")
        job_description = context.get("job_description", "")
        experience = context.get("experience", "")
        question_type = context.get("question_type", "technical")

        prompt = f"""
[시스템 역할]
당신은 대기업 기술 면접관입니다.
지원자의 깊이 있는 사고력과 실무 문제 해결 능력을 검증하는 질문을 생성하세요.

[지원자 정보]
- 주요 경험: {experience}
- 이력서 요약: {resume}

[직무 정보]
{job_description}

[질문 유형]
{question_type}

[지시사항]
1. 단순 지식 확인 질문은 금지합니다.
2. 반드시 실무 상황 기반 심층 질문으로 작성하세요.
3. 기술 선택의 이유, 트레이드오프, 장애 대응 경험을 검증할 수 있도록 구성하세요.
4. 질문은 하나만 생성하세요.
5. 불필요한 설명 없이 질문만 출력하세요.

[출력 형식]
면접 질문 1개만 자연스럽게 작성
"""
        return prompt.strip()


# ==============================
# 2. LLM Client
# ==============================

@dataclass
class LLMConfig:
    temperature: float = 0.3
    max_tokens: int = 500
    top_p: float = 0.9


class LLMService:

    def __init__(self, model_client, config: LLMConfig):
        self.client = model_client
        self.config = config

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.generate(
                prompt=prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p
            )

            return response.strip()

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise


# ==============================
# 3. Question Generator Service
# ==============================

class InterviewQuestionGenerator:

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def generate_question(self, context: Dict[str, Any]) -> str:
        prompt = ExaonePromptBuilder.build_question_prompt(context)

        logger.info("Generating interview question with EXAONE optimized prompt")

        question = self.llm_service.generate(prompt)

        return question


# ==============================
# 4. Usage Example
# ==============================

if __name__ == "__main__":

    # mock model client 예시
    class MockModelClient:
        def generate(self, prompt, temperature, max_tokens, top_p):
            return "AWS 기반 데이터 파이프라인 구축 시 발생했던 병목 현상을 어떻게 진단하고 해결하셨는지 구체적으로 설명해 주세요."

    model_client = MockModelClient()

    llm_config = LLMConfig(
        temperature=0.2,   # EXAONE은 낮은 temperature가 일관성 좋음
        max_tokens=400,
        top_p=0.85
    )

    llm_service = LLMService(model_client, llm_config)
    generator = InterviewQuestionGenerator(llm_service)

    context_data = {
        "resume": "AWS 기반 데이터 분석 및 ML 모델 배포 경험",
        "job_description": "AI 기반 서비스 백엔드 개발",
        "experience": "S3, EC2, Airflow 사용 경험",
        "question_type": "technical-depth"
    }

    result = generator.generate_question(context_data)

    print(result)