import os
import logging
from celery import shared_task
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
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

    def generate_questions(self, position: str, count: int = 5, reuse_ratio: float = 0.4):
        """
        하이브리드 질문 생성 로직
        1. DB에서 검증된 질문 일부 재활용 (Reuse)
        2. 재활용된 질문을 예시(Few-Shot)로 삼아 나머지 질문 생성 (Create)
        """
        questions = []
        reuse_count = int(count * reuse_ratio)
        generate_count = count - reuse_count
        
        # 1. DB 재활용 (검증된 질문)
        # avg_score가 높고 usage_count가 적절한 질문 조회
        db_questions = get_best_questions_by_position(position, limit=reuse_count * 2)
        
        # (간단한 로직: 점수 높은 순으로 선택)
        selected_db_questions = db_questions[:reuse_count]
        
        for q in selected_db_questions:
            questions.append(q.content)
            increment_question_usage(q.id)
            logger.info(f"♻️ Reused Question (ID={q.id}): {q.content[:30]}...")

        # 2. Few-Shot 프롬프트 구성
        # DB 질문들을 예시로 제공하여 스타일을 모방하게 함
        few_shot_examples = ""
        if db_questions:
            examples = [f"- {q.content}" for q in db_questions[:3]]
            few_shot_examples = "\n".join(examples)
        
        prompt_template = """### Role:
You are an expert technical interviewer for the '{position}' role.

### Task:
Generate a single, sharp, and practical interview question in Korean.

### Context (Reference Style):
Here are some good examples of questions for this role:
{examples}

### Instructions:
1. Write ONLY the question in Korean.
2. Do not include any introductory text like "Here is a question".
3. The question should be technical and specific to the role.
4. Avoid duplicating the reference examples.

### Question:
"""
        prompt = PromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()

        # 3. LLM 생성 (나머지 개수만큼)
        for i in range(generate_count):
            try:
                raw_result = chain.invoke({
                    "position": position,
                    "examples": few_shot_examples
                })
                
                # 후처리 (불필요한 공백/특수문자 제거)
                generated_q = raw_result.strip().replace('"', '')
                
                if len(generated_q) > 10:
                    questions.append(generated_q)
                    logger.info(f"✨ Generated Question: {generated_q[:30]}...")
                else:
                    # 실패 시 폴백
                    questions.append(self._get_fallback_question(position, i))
                    
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                questions.append(self._get_fallback_question(position, i))

        return questions

    def _get_fallback_question(self, position, index):
        backups = [
            f"{position} 직무에서 가장 중요하게 생각하는 역량은 무엇인가요?",
            "최근 겪었던 가장 어려운 기술적 챌린지는 무엇이었나요?",
            "우리 회사 서비스 중 개선하고 싶은 부분이 있다면 무엇인가요?",
            "동료와 기술적 견해 차이가 있을 때 어떻게 해결하나요?"
        ]
        return backups[index % len(backups)]

@shared_task(name="tasks.question_generator.generate_questions")
def generate_questions_task(position: str, count: int = 5):
    try:
        generator = QuestionGenerator()
        return generator.generate_questions(position, count)
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
