import os
import logging
from celery import shared_task
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
from typing import Optional, List
import torch
import re

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
            device_map="cuda:0",
            token=token
        )
        
        pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=256,  # [최적화] 256토큰
            temperature=0.5, 
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id,
            return_full_text=False  # 입력 프롬프트가 출력에 포함되지 않도록 설정
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
            # db.py의 함수명에 맞춰 호출
            db_questions = get_best_questions_by_position(position, limit=count)
            
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
        
        
        # Few-Shot 예시 구성 (예시가 없으면 강력한 한국어 기본 예시 제공)
        if examples:
            few_shot_examples = "\n".join([f"- {q}" for q in examples[:3]])
        else:
            few_shot_examples = """
- React의 Virtual DOM이 무엇이며, 이것이 성능에 어떤 영향을 미치는지 설명해주세요.
- 비동기 프로그래밍에서 Promise와 async/await의 차이점은 무엇인가요?
- 사용해본 상태 관리 라이브러리는 무엇이며, 그 선택 이유는 무엇인가요?
"""
        
        # 컨텍스트 추가
        context_section = f"\n\n추가 컨텍스트:\n{context}" if context else ""
        
        # 사용자 요청에 따른 프롬프트 구조
        prompt = [{'role':'system','content':
        (f"""
        당신은 한국 기업의 면접관이자 채용 전문가입니다.
        아래 정보를 바탕으로 {position} 직무에 적합한 '한국어 면접 질문'을 {count}개 생성하세요.
        {context_section}
        
        기존 질문 예시:
        {few_shot_examples}
        
        [중요 요구사항]
        1. 모든 질문은 반드시 자연스러운 한국어로 작성해야 합니다. (영어, 태국어 등 타 언어 혼용 금지)
        2. 기술적 깊이와 실무 경험을 구체적으로 물어보세요.
        3. 지원자의 이력서 내용과 연관된 질문을 포함하세요. (이력서 정보가 있는 경우)
        4. 회사의 인재상과 연결된 질문을 포함하세요. (회사 정보가 있는 경우)
        5. 각 질문은 번호 없이 한 줄씩만 작성하세요.
        6. 질문의 어조는 정중하고 전문적이어야 합니다.
        7. 강조 표시(**text**) 금지
        """)}]
        
        try:
            # Llama 3.2 모델을 위한 채팅 템플릿 적용
            prompt_str = self.tokenizer.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True)
            
            # 질문 생성을 위해 더 긴 토큰 허용 (return_full_text=False 설정 덕분에 prompt_str은 제외됨)
            response = self.llm.invoke(prompt_str)
            
            # 응답 파싱
            
            # 1. 특수 토큰 및 시스템 메시지 제거 패턴
            system_patterns = [
                r"<\|.*?\|>",  # 특수 토큰
                r"Cutting Knowledge Date",
                r"Today Date",
                r"^system$", # 헤더 잔여물
                r"^user$",
                r"^assistant$",
                r"당신은 면접 질문 생성 전문가입니다", # 프롬프트 에코 방지
                r"요구사항:",
                r"기존 질문 예시:",
                r"질문 \d+개:"
            ]
            
            clean_lines = []
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # 시스템 메시지 패턴이 포함된 라인 건너뛰기
                if any(re.search(pat, line) for pat in system_patterns):
                    continue
                
                # 프롬프트의 지시사항 문장과 유사하면 건너뛰기 (Echo 방지 2차 필터)
                if "평가할 수 있는 질문" in line or "이력서 내용과 연관" in line or "한 줄로 작성" in line:
                    continue

                # #으로 시작하는 주석 라인 건너뛰기
                if line.startswith('#'):
                    continue
                    
                clean_lines.append(line)

            # 2. 질문 추출 및 정제
            questions = []
            for line in clean_lines:
                # 번호 제거 (예: "1. 질문" -> "질문", "- 질문" -> "질문")
                clean_q = re.sub(r'^[\d\-\.\s]+', '', line)
                
                # Markdown 강조 제거 (**text** -> text)
                clean_q = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_q)
                
                # 앞뒤 따옴표 및 공백 제거
                clean_q = clean_q.strip('"\' ')
                
                # [필터링 개선] Whitelist 방식은 너무 엄격하여 Blacklist 방식으로 변경
                # 일본어(히라가나/가타카나), 한자, 태국어 등이 포함된 경우만 제외하고 나머지는 허용
                # 기술 면접 질문에는 다양한 특수문자(@, #, &, [] 등)가 사용될 수 있음
                forbidden_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u0E00-\u0E7F]'
                if re.search(forbidden_pattern, clean_q):
                    logger.warning(f"제외된 질문(다국어 포함): {clean_q}")
                    continue
                
                # 길이가 너무 짧은 것은 질문이 아닐 확률 높음 (10자 이상)
                if len(clean_q) > 10:
                    questions.append(clean_q)
            
            # 만약 결과가 부족하면 Fallback 질문으로 채움
            if len(questions) < count:
                logger.warning(f"생성된 질문 수 부족 ({len(questions)}/{count}). Fallback으로 보충합니다.")
                fallback_needed = count - len(questions)
                fallbacks = self._get_fallback_questions(position, fallback_needed)
                questions.extend(fallbacks)
                
            logger.info(f"최종 반환 질문: {questions[:count]}")
            return questions[:count]
        except Exception as e:
            logger.error(f"LLM 질문 생성 중 에러 발생: {e}")
            # 에러 발생 시에도 빈 리스트 보단 Fallback 리턴
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
