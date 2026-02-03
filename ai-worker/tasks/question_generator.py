
import os
import logging
from celery import shared_task
from transformers import AutoTokenizer
from langchain_community.llms import LlamaCpp
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Optional, List

# DB 헬퍼 함수 import
from db import (
    get_best_questions_by_position,
    increment_question_usage,
    engine
)

logger = logging.getLogger("AI-Worker-QuestionGen")

# 모델 설정 (Evaluator와 동일하게 GGUF 사용)
# GGUF 모델은 CPU에서 훨씬 적은 메모리로 안정적으로 돌아갑니다.
MODEL_PATH = os.getenv("EVALUATOR_MODEL_PATH", "/app/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")

class QuestionGenerator:
    """
    GGUF 기반 질문 생성기 (CPU 최적화)
    전략: DB 재활용 (40%) + Few-Shot LLM 생성 (60%)
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        logger.info(f"Loading Question Gen GGUF Model: {MODEL_PATH}")

        try:
            self.llm = LlamaCpp(
                model_path=MODEL_PATH,
                n_ctx=4096,
                n_threads=6,  # CPU 코어 수에 맞춰 조절
                n_gpu_layers=0, # CPU 모드 강제
                temperature=0.7,
                verbose=False
            )
            self._initialized = True
            logger.info("✅ Question Generator Initialized (GGUF)")
        except Exception as e:
            logger.error(f"Failed to Load Question Gen Model: {e}")
            self.llm = None

    def generate_questions(self, position: str, interview_id: Optional[int] = None, count: int = 5, reuse_ratio: float = 0.4):
        from tools import ResumeTool, CompanyTool

        questions = []
        reuse_count = int(count * reuse_ratio)
        generate_count = count - reuse_count

        context_parts = []
        if interview_id:
            resume_info = ResumeTool.get_resume_by_interview(interview_id)
            if resume_info.get("has_resume"):
                context_parts.append(ResumeTool.format_for_llm(resume_info))

            company_info = CompanyTool.get_company_by_interview(interview_id)
            if company_info.get("has_company"):
                context_parts.append(CompanyTool.format_for_llm(company_info))

        context = "\n\n".join(context_parts) if context_parts else ""

        if reuse_count > 0:
            reused = self._reuse_questions_from_db(position, reuse_count)
            questions.extend(reused)

        if generate_count > 0 and self.llm:
            generated = self._generate_new_questions(position, generate_count, questions, context)
            questions.extend(generated)

        # LLM 로드 실패 시 폴백
        if len(questions) < count:
            remaining = count - len(questions)
            questions.extend(self._get_fallback_questions(position, remaining))

        return questions[:count]

    def _reuse_questions_from_db(self, position: str, count: int):
        try:
            db_questions = get_best_questions_by_position(position, limit=count)
            for q in db_questions:
                try:
                    increment_question_usage(q.id)
                except:
                    pass
            return [q.content for q in db_questions]
        except Exception as e:
            logger.warning(f"DB 질문 조회 실패: {e}")
            return []

    def _generate_new_questions(self, position: str, count: int, examples: list, context: str = ""):
        few_shot_examples = "\n".join([f"- {q}" for q in examples[:3]]) if examples else "예시 없음"

        # 사용자가 제공한 Integrated Prompt 반영
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# Role
당신은 20년 차 IT 기술 면접관이자 테크 리드입니다. 지원자의 이력서와 관련 기술 문서를 바탕으로 기술적 깊이를 확인할 수 있는 첫 번째 질문을 생성하고 검수하십시오.

# Persona & Rules
1. 냉철하고 전문적인 태도를 유지하며, 말투는 반드시 격식체(~하십시오체)를 사용하십시오.
2. 기술 용어는 원어(English) 그대로 사용하되, 설명은 한국어로 하십시오.
3. 질문은 2문장 이내로 간결하게 작성하십시오.
4. "느낀 점"과 같은 추상적 질문은 배제하고, 기술적 근거(Metric, Logic)를 요구하십시오.

# Internal Process (Self-Critique Loop)
Step 1. [User Resume]와 [Technical Context]를 매칭하여 핵심 기술 질문 생성.
Step 2. 자가 검수 수행 (Fact-Check / Specificity / Tone & Manner).
Step 3. 검수 기준 미달 시 문항 즉시 수정.

# Input Data
- [User Resume]: {context if context else "이력서 정보 없음"}
- [Technical Context]: {position} 관련 기술 표준 및 모범 사례

# Task
제공된 이력서에서 가장 핵심적인 프로젝트 하나를 선정하십시오. 해당 프로젝트에 사용된 기술 중 연관된 부분을 찾아, '왜(Why)' 해당 기술을 썼는지 혹은 '어떻게(How)' 문제를 해결했는지 묻는 날카로운 질문을 생성하십시오.
최종 질문은 반드시 한국어로 출력하되 기술 용어는 English를 유지하십시오.

# Final Output (Only one question)
[Final Question]: (검수가 완료된 최종 질문만 출력하십시오.)<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        try:
            response = self.llm.invoke(prompt)
            # "[Final Question]:" 이후의 텍스트만 추출
            if "[Final Question]:" in response:
                question = response.split("[Final Question]:")[-1].strip()
            else:
                question = response.strip()

            # 한 문항씩 생성하도록 최적화 (유저 요청에 따라)
            return [question] if question else []
        except Exception as e:
            logger.error(f"LLM 질문 생성 실패: {e}")
            return []

    def _get_fallback_questions(self, position: str, count: int) -> List[str]:
        fallback_questions = [
            f"{position} 직무에서 가장 중요하게 생각하는 역량은 무엇인가요?",
            "최근 겪었던 가장 어려운 기술적 챌린지는 무엇이었나요?",
            f"{position} 직무를 수행하는 데 필요한 핵심 기술은 무엇이라고 생각하나요?",
            "팀 프로젝트에서 의견 충돌이 있을 때 어떻게 해결하나요?",
            "본인의 강점을 실무에서 어떻게 활용할 수 있을까요?"
        ]
        return fallback_questions[:count]

    def generate_deep_dive_question(self, history: str, current_answer: str):
        """
        [Analysis Logic (BS Detection)] 기반 심화 꼬리질문 생성
        """
        if not self.llm: return "추가 질문을 구성할 수 없습니다."

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# Role
당신은 지원자의 답변에서 모순을 찾아내고 기술적 밑바닥을 확인하는 20년 차 테크 리드입니다.

# Guidelines
1. 최근 대화 내역을 바탕으로 맥락을 유지하십시오.
2. 사용자의 답변에 구체적인 '수치'나 '기술적 근거'가 부족하다면 이를 집요하게 파고드십시오.
3. 질문 시작 시 "앞서 말씀하신 [특정 키워드] 부분과 관련하여..."와 같은 연결어를 사용하여 맥락을 연결하십시오.
4. 질문은 반드시 2문장 이내로 제한하십시오.

# Analysis Logic (BS Detection)
- 답변이 너무 원론적이거나 구글링으로 알 수 있는 내용인가? -> 구체적인 구현 사례를 요구하십시오.
- 본인의 기여도가 모호한가? -> 본인이 직접 설계하거나 코딩한 범위를 확인하십시오.

# Input Data
- [Conversation History]: {history}
- [User Current Answer]: {current_answer}

# Task
[User Current Answer]를 분석하여 논리적 허점이나 보완이 필요한 부분을 찾으십시오. 이전 대화와 연결되는 심화 꼬리질문을 1개 생성하십시오.<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        try:
            response = self.llm.invoke(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Deep-Dive 생성 실패: {e}")
            return "구체적인 기술적 구현 사례에 대해 더 자세히 설명해 주십시오."

@shared_task(name="tasks.question_generator.generate_questions")
def generate_questions_task(position: str, interview_id: int = None, count: int = 5):
    try:
        generator = QuestionGenerator()
        return generator.generate_questions(position, interview_id, count)
    except Exception as e:
        logger.error(f"Task Error: {e}")
        return []

@shared_task(name="tasks.question_generator.generate_deep_dive")
def generate_deep_dive_task(history: str, current_answer: str):
    try:
        generator = QuestionGenerator()
        return generator.generate_deep_dive_question(history, current_answer)
    except Exception as e:
        logger.error(f"Deep-Dive Task Error: {e}")
        return "관련하여 구체적인 기술적 근거를 말씀해 주십시오."
