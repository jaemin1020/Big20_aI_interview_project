"""
EXAONE-3.5-7.8B-Instruct 순수 LLM 엔진 모듈 (GGUF 버전)
프롬프트나 비즈니스 로직 없이, 모델 로딩 및 텍스트 생성 기능만 제공합니다.
"""
import os
import logging
from llama_cpp import Llama

logger = logging.getLogger("EXAONE-ENGINE")

# 모델 경로 (컨테이너 내부 경로)
MODEL_PATH = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"

class ExaoneLLM:
    """
    EXAONE-3.5-7.8B-Instruct (GGUF) 싱글톤 LLM 엔진
    
    이 클래스는 모델을 메모리에 유지(Singleton)하고 텍스트 생성 요청을 처리하는 엔진 역할만 수행합니다.
    모든 프롬프트는 호출하는 측(Task)에서 결정합니다.
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
            
        logger.info(f"🚀 Loading EXAONE Engine from: {MODEL_PATH}")
        
        # 모델 경로 확인
        if not os.path.exists(MODEL_PATH):
            local_path = r"C:\big20\Big20_aI_interview_project\ai-worker\models\EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
            if os.path.exists(local_path):
                target_path = local_path
            else:
                raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
        else:
            target_path = MODEL_PATH

        try:
            gpu_layers = int(os.getenv("N_GPU_LAYERS", "-1"))
            self.llm = Llama(
                model_path=target_path,
                n_gpu_layers=gpu_layers,
                n_ctx=4096,
                n_batch=512,
                verbose=False
            )
            logger.info(f"✅ EXAONE Engine Loaded (n_gpu_layers: {gpu_layers})")
        except Exception as e:
            logger.error(f"❌ 엔진 로드 실패: {e}")
            raise e
        
        self._initialized = True
    
    def _create_prompt(self, system_msg: str, user_msg: str) -> str:
        """EXAONE 3.5 전용 Chat Template 포맷팅"""
        return f"[|system|]{system_msg}[|endofturn|]\n[|user|]{user_msg}[|endofturn|]\n[|assistant|]"

    def invoke(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        입력받은 프롬프트로 텍스트 생성을 수행하는 순수 실행 메서드
        """
        try:
            output = self.llm(
                prompt,
                max_tokens=max_tokens,
                stop=["[|endofturn|]", "[|user|]"],
                temperature=temperature,
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"생성 도중 오류 발생: {e}")
            return ""

def get_exaone_llm() -> ExaoneLLM:
    """엔진 싱글톤 인스턴스 반환"""
    return ExaoneLLM()
