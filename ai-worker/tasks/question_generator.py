import os
import logging
from celery import shared_task
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
from typing import Optional, List
import torch

# DB 헬퍼 함수 import
from db import (
    get_best_questions_by_position,  # 직무별 우수 질문 조회
    increment_question_usage,
    engine
)
from sqlmodel import Session, select

logger = logging.getLogger("AI-Worker-QuestionGen")

# 모델 설정
MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"

class QuestionGenerator:
    """
    하이브리드 질문 생성기
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
            
        logger.info(f"Loading Question Gen Model: {MODEL_ID}")
        token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        
        # 4-bit 양자화 (메모리 최적화)
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4"
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=token)
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=quantization_config,
            device_map="auto",
            token=token
        )
        
        pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=100,
            temperature=0.8, # 창의성 확보
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        self.llm = HuggingFacePipeline(pipeline=pipe)
        self._initialized = True
        logger.info("✅ Question Generator Initialized")

    def generate_questions(self, position: str, interview_id: Optional[int] = None, count: int = 5, reuse_ratio: float = 0.4):
        """
        하이브리드 질문 생성 로직 (이력서 및 회사 정보 기반)
        1. DB에서 검증된 질문 일부 재활용 (Reuse)
        2. 이력서 + 회사 정보로 컨텍스트 구성
        3. 재활용된 질문을 예시(Few-Shot)로 삼아 나머지 질문 생성 (Create)
        
        Args:
            position: 지원 직무
            interview_id: 면접 ID (이력서/회사 정보 조회용)
            count: 생성할 총 질문 수
            reuse_ratio: 재활용 비율 (0.0 ~ 1.0)
        """
        from tools import ResumeTool, CompanyTool
        
        questions = []
        reuse_count = int(count * reuse_ratio)
        generate_count = count - reuse_count
        
        # 1. 컨텍스트 수집 (이력서 + 회사 정보)
        context_parts = []
        
        if interview_id:
            # 이력서 정보
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
        
        # 3. LLM으로 새 질문 생성 (Create with Context)
        if generate_count > 0:
            generated = self._generate_new_questions(position, generate_count, questions, context)
            questions.extend(generated)
            logger.info(f"✅ LLM으로 {len(generated)}개 질문 생성 (컨텍스트 포함)")
        
        return questions[:count]  # 정확히 count개만 반환
    
    def _reuse_questions_from_db(self, position: str, count: int):
        """DB에서 검증된 질문 가져오기"""
        
        try:
            db_questions = get_questions_by_position(position, limit=count)
            
            # 재활용 시 사용량 증가
            for q in db_questions:
                try:
                    increment_question_usage(q.id)
                except Exception as e:
                    logger.warning(f"Question {q.id} 사용량 증가 실패: {e}")
            
            return [q.content for q in db_questions]
        except Exception as e:
            logger.warning(f"DB 질문 조회 실패: {e}. 빈 리스트 반환")
            return []
    
    def _generate_new_questions(self, position: str, count: int, examples: list, context: str = ""):
        """LLM으로 새 질문 생성 (Few-Shot + Context)"""
        if not self._initialized:
            self._initialize()
        
        # Few-Shot 예시 구성
        few_shot_examples = "\n".join([f"- {q}" for q in examples[:3]]) if examples else "예시 없음"
        
        # 컨텍스트 추가
        context_section = f"\n\n추가 컨텍스트:\n{context}" if context else ""
        
        prompt = f"""당신은 면접 질문 생성 전문가입니다.
아래 정보를 바탕으로 {position} 직무에 적합한 면접 질문을 {count}개 생성하세요.
{context_section}

기존 질문 예시:
{few_shot_examples}

요구사항:
1. 기술적 깊이와 실무 경험을 평가할 수 있는 질문
2. 지원자의 이력서 내용과 연관된 질문 (이력서 정보가 있는 경우)
3. 회사의 인재상에 부합하는지 평가할 수 있는 질문 (회사 정보가 있는 경우)
4. 각 질문은 한 줄로 작성
5. 질문만 나열하고 번호나 추가 설명 없이

질문 {count}개:
"""
        
        try:
            response = self.llm.invoke(prompt)
            # 응답 파싱
            lines = [line.strip() for line in response.split('\n') if line.strip() and not line.strip().startswith('#')]
            questions = [line.lstrip('- ').lstrip('1234567890. ') for line in lines if len(line) > 10]
            return questions[:count]
        except Exception as e:
            logger.error(f"LLM 질문 생성 실패: {e}")
            return self._get_fallback_questions(position, count)
    
    def _get_fallback_questions(self, position: str, count: int) -> List[str]:
        """폴백 질문 생성"""
        fallback_questions = [
            f"{position} 직무에서 가장 중요하게 생각하는 역량은 무엇인가요?",
            "최근 겪었던 가장 어려운 기술적 챌린지는 무엇이었나요?",
            f"{position} 직무를 수행하는 데 필요한 핵심 기술은 무엇이라고 생각하나요?",
            "팀 프로젝트에서 의견 충돌이 있을 때 어떻게 해결하나요?",
            "본인의 강점을 실무에서 어떻게 활용할 수 있을까요?",
            "우리 회사에 지원한 이유를 구체적으로 말씀해주세요.",
            "5년 후 본인의 모습을 어떻게 그리고 계신가요?",
            "실패한 프로젝트 경험과 그로부터 배운 점을 공유해주세요."
        ]
        return fallback_questions[:count]

@shared_task(name="tasks.question_generator.generate_questions")
def generate_questions_task(position: str, interview_id: int = None, count: int = 5):
    try:
        generator = QuestionGenerator()
        return generator.generate_questions(position, interview_id, count)
    except Exception as e:
        logger.error(f"Task Error: {e}")
        return []

# Eager Initialization: Worker 시작 시 모델 미리 로드
# 이렇게 하면 첫 요청에서 타임아웃이 발생하지 않습니다
try:
    logger.info("🔥 Pre-loading Question Generator model...")
    _warmup_generator = QuestionGenerator()
    logger.info("✅ Question Generator ready for requests")
except Exception as e:
    logger.warning(f"⚠️ Failed to pre-load model (will load on first request): {e}")
