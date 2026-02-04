import os
import logging
from celery import shared_task
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
MODEL_PATH = os.getenv("EVALUATOR_MODEL_PATH", "/app/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf")

class QuestionGenerator:
    """
    GGUF 기반 질문 생성기 (CPU 최적화)
    전략: DB 재활용 및 이력서 기반 구체화
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

        logger.info(f"Loading Question Gen Model from: {MODEL_PATH}")

        try:
            self.llm = LlamaCpp(
                model_path=MODEL_PATH,
                n_ctx=4096,
                n_threads=6,
                n_gpu_layers=0,
                temperature=0.7, # 질문 생성은 약간의 창의성 필요
                max_tokens=512,
                verbose=False
            )
            logger.info("✅ Question Generator Model Loaded")
        except Exception as e:
            logger.error(f"Failed to Load Question Gen Model: {e}")
            self.llm = None

        self._initialized = True

    def generate_questions(self, position: str, interview_id: Optional[int] = None, count: int = 5, reuse_ratio: float = 0.4):
        from tools import ResumeTool, CompanyTool

        # 1. 이력서 요약 가져오기
        resume_summary = ""
        if interview_id:
            resume_info = ResumeTool.get_resume_by_interview(interview_id)
            if resume_info.get("has_resume"):
                resume_summary = resume_info.get("summary", "")

        # 2. 베이스 질문 가져오기 (DB 또는 폴백)
        base_questions = self._reuse_questions_from_db(position, count)
        if len(base_questions) < count:
            remaining = count - len(base_questions)
            base_questions.extend(self._get_fallback_questions(position, remaining))

        # 3. 이력서 기반 구체화 (Specialization)
        # 만약 이력서 정보가 있다면, 베이스 질문들을 구체화하고
        # 이 중 reuse_ratio에 따라 일부는 원본 그대로, 나머지는 구체화된 질문을 섞음
        if resume_summary and self.llm:
            specialized_questions = []
            reuse_count = int(count * reuse_ratio)

            # 원본 그대로 유지할 질문들
            final_questions = base_questions[:reuse_count]

            # 구체화할 대상 질문들
            targets_to_specialize = base_questions[reuse_count:count]

            for original_q in targets_to_specialize:
                spec_qs = self._specialize_question(original_q, resume_summary, count=1)
                final_questions.extend(spec_qs)

            return final_questions[:count]

        return base_questions[:count]

    def _reuse_questions_from_db(self, position: str, count: int):
        try:
            # db.py에 정의된 get_best_questions_by_position 사용
            db_questions = get_best_questions_by_position(position, limit=count)

            # 재활용 시 사용량 증가
            for q in db_questions:
                try:
                    increment_question_usage(q.id)
                except:
                    pass
            return [q.content for q in db_questions]
        except Exception as e:
            logger.warning(f"DB 질문 조회 실패: {e}")
            return []

    def generate_questions_from_resume(self, resume_summary: str, count: int = 5):
        """[Task 4] DB 없이 이력서만으로 면접 질문 생성"""
        import re

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# Role
당신은 20년 차 IT 기술 면접관이자 테크 리드입니다. 지원자의 이력서를 정밀 분석하여 기술적 실체와 문제 해결 능력을 검증할 수 있는 질문을 생성하십시오.

# Persona & Rules
1. 냉철하고 전문적인 태도를 유지하며, 말투는 반드시 격식체(~하십시오체)를 사용하십시오.
2. 기술 용어는 원어(English) 그대로 사용하십시오.
3. 질문은 2문장 이내로 간결하게 작성하십시오.
4. 이력서에 기재된 기술 스택과 프로젝트의 '진위 여부'를 확인하는 데 집중하십시오.

# Internal Process (Self-Critique Loop)
Step 1. 이력서에서 가장 비중 있는 프로젝트와 기술 스택을 선별하십시오.
Step 2. 해당 기술의 핵심 원리나 실무에서 발생할 수 있는 엣지 케이스를 질문으로 구성하십시오.
Step 3. 자가 검수 (구체성 부족 시 문항 수정).<|eot_id|><|start_header_id|>user<|end_header_id|>
# User Resume Summary
{resume_summary}

# Task
위 이력서를 바탕으로 지원자의 역량을 현미경처럼 분석할 수 있는 날카로운 질문을 {count}개 생성하십시오.
단순한 경험 나열이 아닌, "왜 이 기술인가?", "어떻게 해결했나?"를 묻는 질문이어야 합니다.

# Output Format
1. [질문 내용]
2. [질문 내용]
...

[Generated Questions]:<|eot_id|><|start_header_id|>assistant<|end_header_id|>
1. """

        try:
            response = self.llm.invoke(prompt)
            full_response = "1. " + response.strip()
            found_questions = re.findall(r'\d+\.\s*(.+)', full_response)
            questions = [q.strip() for q in found_questions if len(q.strip()) > 5]

            if not questions:
                lines = [l.strip() for l in full_response.split('\n') if l.strip()]
                questions = [re.sub(r'^\d+[\.\s]+', '', l).strip() for l in lines]

            return questions[:count]
        except Exception as e:
            logger.error(f"이력서 기반 질문 생성 실패: {e}")
            return ["본인의 기술적 강점에 대해 설명해 주십시오."] * count

    def generate_basic_variants(self, original_question: str, count: int = 3):
        """[Task 1] 이력서 없이 질문 하나로 유사 질문 생성 (기본 성능 테스트용)"""
        import re

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# Role
당신은 20년 차 IT 기술 면접관이자 테크 리드입니다. 주어진 원본 질문의 핵심 주제를 유지하면서, 지원자의 기술적 역량을 다각도로 검증할 수 있는 유사한 질문들을 생성하십시오.

# Persona & Rules
1. 냉철하고 전문적인 태도를 유지하며, 말투는 반드시 격식체(~하십시오체)를 사용하십시오.
2. 기술 용어는 원어(English) 그대로 사용하고, 설명은 한국어로 하십시오.
3. 각 질문은 2문장 이내로 간결하게 작성하십시오.
4. 원본 질문의 '의도'와 '기술 주제'를 절대 벗어나지 마십시오.<|eot_id|><|start_header_id|>user<|end_header_id|>
# Original Question
"{original_question}"

# Task
위 원본 질문과 기술적 주제는 동일하지만, 질문의 관점이나 구체적 요구사항을 달리한 유사 질문을 {count}개 생성하십시오.

# Final Output Format
1. [질문 내용]
2. [질문 내용]
...

[Final Questions]:<|eot_id|><|start_header_id|>assistant<|end_header_id|>
1. """

        try:
            response = self.llm.invoke(prompt)
            full_response = "1. " + response.strip()
            found_questions = re.findall(r'\d+\.\s*(.+)', full_response)
            questions = [q.strip() for q in found_questions if len(q.strip()) > 5]

            if not questions:
                lines = [l.strip() for l in full_response.split('\n') if l.strip()]
                questions = [re.sub(r'^\d+[\.\s]+', '', l).strip() for l in lines]

            return questions[:count]
        except Exception as e:
            logger.error(f"기본 유사질문 생성 실패: {e}")
            return [original_question] * count

    def _specialize_question(self, original_question: str, resume_summary: str, count: int = 1):
        """이력서 기반 초기 질문 생성 및 자가 검증 프롬프트 적용 (1:N 생성 가능)"""
        import re

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# Role
당신은 20년 차 IT 기술 면접관이자 테크 리드입니다. 지원자의 이력서와 원본 질문을 바탕으로 기술적 깊이를 확인할 수 있는 질문을 생성하고 검수하십시오.
# Persona & Rules
1. 냉철하고 전문적인 태도를 유지하며, 말투는 반드시 격식체(~하십시오체)를 사용하십시오.
2. 기술 용어는 원어(English) 그대로 사용하되, 설명은 한국어로 하십시오.
3. 질문은 2문장 이내로 간결하게 작성하십시오.
4. "느낀 점"과 같은 추상적 질문은 배제하고, 기술적 근거(Metric, Logic)를 요구하십시오.
# Internal Process (Self-Critique Loop)
Step 1. [Original Question]의 핵심 주제와 의도를 파악하십시오.
Step 2. [User Resume]에서 해당 주제와 관련된 구체적인 내용(프로젝트, 기술, 경험)을 찾으십시오.
Step 3. 원본 질문의 주제를 유지하면서 이력서 내용으로 구체화한 질문을 생성하십시오.
Step 4. 자가 검수 수행 (원본 질문 주제 일치 여부 / Specificity / Tone & Manner).
Step 5. 검수 기준 미달 시 문항 즉시 수정.<|eot_id|><|start_header_id|>user<|end_header_id|>
# Input Data
- [User Resume]:
{resume_summary}
- [Original Question]:
"{original_question}"

# Task
**중요**: [Original Question]의 핵심 주제와 의도를 반드시 유지하십시오.
[User Resume]에서 [Original Question]과 관련된 프로젝트나 경험을 찾으십시오. 해당 부분에 대해 원본 질문의 주제를 유지하면서 '왜(Why)' 그 기술을 선택했는지 혹은 '어떻게(How)' 문제를 해결했는지 묻는 날카로운 질문을 {count}개 생성하십시오.

예시:
- 원본: "자기소개를 해보세요" → 생성: "보안 엔지니어로서의 KISA 인턴 경험과 IDS 구축 프로젝트를 중심으로 자기소개를 하십시오."
- 원본: "프로젝트 경험은?" → 생성: "Snort 기반 IDS 구축 프로젝트에서 SQL Injection 탐지 규칙을 어떻게 설계하셨습니까?"

# Final Output Format
각 질문은 다음 형식으로 출력하십시오:
1. [질문 내용]
2. [질문 내용]
...

[Final Questions]:<|eot_id|><|start_header_id|>assistant<|end_header_id|>
1. """

        try:
            response = self.llm.invoke(prompt)
            # 첫 번째 질문 앞에 "1. "이 이미 있으므로 붙여줌
            full_response = "1. " + response.strip()

            # 숫자. [내용] 패턴으로 질문들 추출
            found_questions = re.findall(r'\d+\.\s*(.+)', full_response)

            # 정제 작업
            questions = [q.strip() for q in found_questions if len(q.strip()) > 5]

            if not questions:
                # 파싱 실패 시 줄바꿈 단위로 시도
                lines = [l.strip() for l in full_response.split('\n') if l.strip()]
                questions = [re.sub(r'^\d+[\.\s]+', '', l).strip() for l in lines]

            return questions[:count] if questions else [original_question]

        except Exception as e:
            logger.error(f"질문 구체화 실패: {e}")
            return [original_question]

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
        """동적 꼬리질문(Deep-Dive) 생성 프롬프트 고도화 (BS Detection 강화)"""
        if not self.llm: return "추가 질문을 구성할 수 없습니다."

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
# Role
당신은 지원자의 답변에서 허세(BS)를 찾아내고 기술적 밑바닥을 확인하는 20년 차 베테랑 테크 리드입니다.

# Mission (Strict)
1. **분석**: 답변을 요약하지 마십시오. 대신 "구체적 수치 부재", "원론적인 개념 나열", "직접 구현 여부 불분명" 등 **기술적 허점**을 반드시 한 줄로 지적하십시오.
2. **질문**: 분석한 허점을 파고들어, 지원자가 실제 경험했는지 증명하게 만드는 날카로운 질문을 한 문장으로 던지십시오.

# Persona & Guidelines
- 말투는 반드시 냉철한 격식체(~하십시오체)를 사용하십시오.
- 질문 시작은 반드시 "앞서 말씀하신 [특정 키워드] 부분과 관련하여..."를 사용하십시오.
- 불필요한 서론/미사여구는 절대 배제하십시오.

# Example
지원자 답변: "서버 성능 향상을 위해 인덱스 최적화를 진행하여 속도를 많이 개선했습니다."
[분석]: 어떤 인덱스 구조를 사용했는지와 구체적인 성능 개선 지표(TPS, Latency)가 누락되었습니다.
[질문]: 앞서 말씀하신 인덱스 최적화 부분과 관련하여, 당시 사용한 인덱스 구조와 쿼리 응답 속도를 몇 ms에서 몇 ms로 개선하셨는지 구체적인 수치를 말씀해 주십시오.<|eot_id|><|start_header_id|>user<|end_header_id|>
# Input Data
- [History]: {history}
- [Answer]: {current_answer}

[분석]:
[질문]:<|eot_id|><|start_header_id|>assistant<|end_header_id|>
[분석]: """

        try:
            response = self.llm.invoke(prompt)
            # 깔끔하게 [분석]부터 시작하도록 보정
            full_response = "[분석]: " + response.strip()

            # 줄바꿈 정제 (최대한 상위 2개 라인만 유지)
            lines = [l.strip() for l in full_response.split('\n') if l.strip()]
            valid_lines = [l for l in lines if l.startswith('[분석]:') or l.startswith('[질문]:')]

            if len(valid_lines) >= 2:
                return "\n".join(valid_lines[:2])

            return "\n".join(lines[:2])

        except Exception as e:
            logger.error(f"Deep-Dive 생성 실패: {e}")
            return "[분석]: 답변 내용이 추상적이며 기술적 근거가 부족합니다.\n[질문]: 앞서 말씀하신 내용 중 본인이 직접 설계하고 구현한 구체적인 로직에 대해 설명해 주십시오."

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
