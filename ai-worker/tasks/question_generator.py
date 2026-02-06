import os
import logging
from celery import shared_task
from typing import Optional, List

# DB 헬퍼 함수 import
from db import (
    get_best_questions_by_position,
    increment_question_usage,
    engine
)

# EXAONE LLM import
from utils.exaone_llm import get_exaone_llm

logger = logging.getLogger("AI-Worker-QuestionGen")

class QuestionGenerator:
    """
    하이브리드 질문 생성기 (EXAONE-3.5-7.8B-Instruct 사용)
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
            
        logger.info("Initializing Question Generator with EXAONE model")
        self.llm = get_exaone_llm()
        self._initialized = True

    def generate_questions(self, position: str, interview_id: Optional[int] = None, count: int = 5, reuse_ratio: float = 0.4):
        from tools import ResumeTool, CompanyTool

        # 1. 이력서 요약 가져오기
        resume_summary = ""
        if interview_id:
            resume_info = ResumeTool.get_resume_by_interview(interview_id)
            if resume_info.get("has_resume"):
                context_parts.append(ResumeTool.format_for_llm(resume_info))
                logger.info(f"이력서 정보 로드 완료: {resume_info.get('summary', '')[:50]}...")
            
            # 회사 정보
            company_info = CompanyTool.get_company_by_interview(interview_id)
            if company_info.get("has_company"):
                context_parts.append(CompanyTool.format_for_llm(company_info))
                logger.info(f"회사 정보 로드 완료: {company_info.get('name', '')}")
        
        context = "\n\n".join(context_parts) if context_parts else ""
        
        # 2. DB에서 기존 질문 재활용 (Reuse)
        if reuse_count > 0:
            reused = self._reuse_questions_from_db(position, reuse_count)
            questions.extend(reused)
            logger.info(f"✅ DB에서 {len(reused)}개 질문 재활용")
        
        # 3. EXAONE LLM으로 새 질문 생성 (Create with Context)
        if generate_count > 0:
            generated = self.llm.generate_questions(
                position=position,
                context=context,
                examples=questions,  # Few-shot 예시로 재활용된 질문 사용
                count=generate_count
            )
            questions.extend(generated)
            logger.info(f"✅ EXAONE으로 {len(generated)}개 질문 생성 (컨텍스트 포함)")
        
        return questions[:count]  # 정확히 count개만 반환
    
    def _reuse_questions_from_db(self, position: str, count: int):
        try:
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

# Eager Initialization: Worker 시작 시 모델 미리 로드
try:
    logger.info("🔥 Pre-loading Question Generator with EXAONE...")
    _warmup_generator = QuestionGenerator()
    logger.info("✅ Question Generator ready for requests")
except Exception as e:
    logger.warning(f"⚠️ Failed to pre-load model (will load on first request): {e}")
