"""
EXAONE-3.5-7.8B-Instruct 통합 LLM 모듈
질문 생성 및 답변 평가를 하나의 모델로 처리
"""
import os
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, BitsAndBytesConfig
from langchain_huggingface import HuggingFacePipeline
from typing import Optional, Dict, List

logger = logging.getLogger("EXAONE-LLM")

# 모델 설정
MODEL_ID = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"

class ExaoneLLM:
    """
    EXAONE-3.5-7.8B-Instruct 싱글톤 LLM
    질문 생성과 답변 평가를 모두 처리
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
            
        logger.info(f"🚀 Loading EXAONE Model: {MODEL_ID}")
        token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        
        # 4-bit 양자화 (메모리 최적화)
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True
        )
        
        # 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            token=token,
            trust_remote_code=True
        )
        
        # 모델 로드
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=quantization_config,
            device_map="auto",  # 자동 GPU 할당
            token=token,
            trust_remote_code=True
        )
        
        # Pipeline 생성 (질문 생성용)
        self.question_pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=self.tokenizer.eos_token_id,
            return_full_text=False
        )
        
        # Pipeline 생성 (평가용 - 더 결정적)
        self.eval_pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=256,
            temperature=0.1,  # 더 결정적
            do_sample=True,
            top_p=0.95,
            pad_token_id=self.tokenizer.eos_token_id,
            return_full_text=False
        )
        
        # LangChain 래퍼
        self.question_llm = HuggingFacePipeline(pipeline=self.question_pipeline)
        self.eval_llm = HuggingFacePipeline(pipeline=self.eval_pipeline)
        
        self._initialized = True
        logger.info("✅ EXAONE Model Initialized (Question Gen + Evaluation)")
    
    def generate_questions(
        self,
        position: str,
        context: str = "",
        examples: List[str] = None,
        count: int = 5
    ) -> List[str]:
        """
        면접 질문 생성
        
        Args:
            position: 지원 직무
            context: 이력서/회사 정보 컨텍스트
            examples: Few-shot 예시 질문
            count: 생성할 질문 수
            
        Returns:
            생성된 질문 리스트
        """
        # Few-shot 예시 구성
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
        
        # EXAONE 프롬프트 구성
        prompt = f"""당신은 한국 기업의 면접관이자 채용 전문가입니다.
아래 정보를 바탕으로 {position} 직무에 적합한 한국어 면접 질문을 {count}개 생성하세요.
{context_section}

기존 질문 예시:
{few_shot_examples}

[중요 요구사항]
1. 모든 질문은 반드시 자연스러운 한국어로 작성해야 합니다.
2. 기술적 깊이와 실무 경험을 구체적으로 물어보세요.
3. 지원자의 이력서 내용과 연관된 질문을 포함하세요. (이력서 정보가 있는 경우)
4. 회사의 인재상과 연결된 질문을 포함하세요. (회사 정보가 있는 경우)
5. 각 질문은 번호 없이 한 줄씩만 작성하세요.
6. 질문의 어조는 정중하고 전문적이어야 합니다.

질문 {count}개:
"""
        
        try:
            # 질문 생성
            response = self.question_llm.invoke(prompt)
            
            # 응답 파싱
            import re
            
            # 특수 토큰 제거 패턴
            system_patterns = [
                r"<\|.*?\|>",
                r"당신은 면접 질문 생성 전문가입니다",
                r"요구사항:",
                r"기존 질문 예시:",
                r"질문 \d+개:"
            ]
            
            clean_lines = []
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # 시스템 메시지 패턴 제거
                if any(re.search(pat, line) for pat in system_patterns):
                    continue
                
                # 프롬프트 에코 방지
                if "평가할 수 있는 질문" in line or "한 줄로 작성" in line:
                    continue
                
                # 주석 제거
                if line.startswith('#'):
                    continue
                    
                clean_lines.append(line)
            
            # 질문 추출 및 정제
            questions = []
            for line in clean_lines:
                # 번호 제거
                clean_q = re.sub(r'^[\d\-\.\s]+', '', line)
                
                # Markdown 강조 제거
                clean_q = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_q)
                
                # 따옴표 제거
                clean_q = clean_q.strip('"\'')
                
                # 다국어 필터링
                forbidden_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u0E00-\u0E7F]'
                if re.search(forbidden_pattern, clean_q):
                    logger.warning(f"제외된 질문(다국어 포함): {clean_q}")
                    continue
                
                # 길이 체크
                if len(clean_q) > 10:
                    questions.append(clean_q)
            
            logger.info(f"✅ 생성된 질문 {len(questions)}개: {questions[:count]}")
            return questions[:count]
            
        except Exception as e:
            logger.error(f"질문 생성 실패: {e}")
            return self._get_fallback_questions(position, count)
    
    def evaluate_answer(
        self,
        question_text: str,
        answer_text: str,
        rubric: Optional[Dict] = None
    ) -> Dict:
        """
        답변 평가
        
        Args:
            question_text: 질문
            answer_text: 답변
            rubric: 평가 루브릭 (선택)
            
        Returns:
            평가 결과 dict
        """
        if not answer_text or not answer_text.strip():
            logger.warning("빈 답변 - 평가 생략")
            return {
                "technical_score": 0,
                "communication_score": 0,
                "feedback": "답변이 제공되지 않았습니다."
            }
        
        # EXAONE 평가 프롬프트
        prompt = f"""당신은 전문 면접관입니다. 지원자의 답변을 평가하세요.

질문: {question_text}

답변: {answer_text}

평가 기준:
- 기술적 정확성 (1-5점)
- 의사소통 능력 (1-5점)
- 논리성과 구조

아래 JSON 형식으로만 답변하세요:
{{
    "technical_score": (1-5 정수),
    "communication_score": (1-5 정수),
    "feedback": "(한국어 피드백 문장)"
}}

평가:
"""
        
        try:
            # 평가 생성
            response = self.eval_llm.invoke(prompt)
            
            # JSON 파싱
            import json
            import re
            
            # JSON 부분만 추출
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # 점수 검증
                tech_score = max(1, min(5, result.get("technical_score", 3)))
                comm_score = max(1, min(5, result.get("communication_score", 3)))
                feedback = result.get("feedback", "평가 완료")
                
                return {
                    "technical_score": tech_score,
                    "communication_score": comm_score,
                    "feedback": feedback
                }
            else:
                logger.warning("JSON 파싱 실패 - 기본값 반환")
                return {
                    "technical_score": 3,
                    "communication_score": 3,
                    "feedback": "평가를 완료했습니다."
                }
                
        except Exception as e:
            logger.error(f"답변 평가 실패: {e}")
            return {
                "technical_score": 3,
                "communication_score": 3,
                "feedback": f"평가 중 오류 발생: {str(e)}"
            }
    
    def _get_fallback_questions(self, position: str, count: int) -> List[str]:
        """폴백 질문"""
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


# 싱글톤 인스턴스 가져오기
def get_exaone_llm() -> ExaoneLLM:
    """EXAONE LLM 싱글톤 인스턴스 반환"""
    return ExaoneLLM()


# Worker 시작 시 모델 미리 로드
try:
    logger.info("🔥 Pre-loading EXAONE model...")
    _warmup_llm = ExaoneLLM()
    logger.info("✅ EXAONE model ready for requests")
except Exception as e:
    logger.warning(f"⚠️ Failed to pre-load model (will load on first request): {e}")
