"""
EXAONE-3.5-7.8B-Instruct 순수 LLM 엔진 모듈 (GGUF 버전)
프롬프트나 비즈니스 로직 없이, 모델 로딩 및 텍스트 생성 기능만 제공합니다.
"""
import os
import logging
# from llama_cpp import Llama (Moved inside ExaoneLLM.__init__)

logger = logging.getLogger("EXAONE-ENGINE")

# 모델 경로 (컨테이너 내부 경로)
MODEL_PATH = "/app/models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"

from typing import Any, List, Optional, ClassVar
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
# from llama_cpp import Llama (Moved inside ExaoneLLM.__init__)

class ExaoneLLM(LLM):
    """
    EXAONE-3.5-7.8B-Instruct (GGUF) 싱글톤 LLM 엔진
    LangChain LLM 인터페이스를 상속받아 LCEL 호환성을 제공합니다.
    """
    _instance: ClassVar[Optional["ExaoneLLM"]] = None
    llm: ClassVar[Any] = None
    _initialized: ClassVar[bool] = False
    
    def __new__(cls, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        # CPU 환경에서도 GGUF는 실행 가능하므로 로딩 허용
        use_gpu = os.getenv("USE_GPU", "true").lower() == "true"
        gpu_layers = int(os.getenv("N_GPU_LAYERS", "-1"))
        
        if not use_gpu:
            logger.info("ℹ️ CPU mode detected. Loading EXAONE on CPU (this may be slow).")
            gpu_layers = 0 # GPU 사용 안함 강제 설정
            
        logger.info(f"🚀 Loading EXAONE Engine from: {MODEL_PATH}")
        
        if not os.path.exists(MODEL_PATH):
            local_path = r"C:\big20\Big20_aI_interview_project\ai-worker\models\EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf"
            if os.path.exists(local_path):
                target_path = local_path
            else:
                 raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH} (Local fallback also failed: {local_path})")
        else:
            target_path = MODEL_PATH

        try:
            # 🚨 CPU 환경에서 CUDA 빌드된 llama-cpp 로딩 시 발생하는 크래시 방지를 위해 지연 임포트
            from llama_cpp import Llama
            
            # 클래스 변수로 llm 객체 관리 (싱글톤)
            ExaoneLLM.llm = Llama(
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
        
        ExaoneLLM._initialized = True

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """LLM 실행 핵심 메서드 (LangChain 표준)"""
        if ExaoneLLM.llm is None:
            logger.error("❌ EXAONE 모델이 로드되지 않았습니다. (CPU 모드이거나 로딩 실패)")
            raise RuntimeError("EXAONE engine is not initialized. Check if this is a GPU worker.")

        try:
            # stop 시퀀스 기본값 설정
            stop_sequences = ["[|endofturn|]", "[|user|]"] if stop is None else stop
            
            output = ExaoneLLM.llm(
                prompt,
                max_tokens=kwargs.get("max_tokens", 512),
                stop=stop_sequences,
                temperature=kwargs.get("temperature", 0.7),
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"생성 도중 오류 발생: {e}")
            return ""

    @property
    def _llm_type(self) -> str:
        return "exaone_gguf"

    def _create_prompt(self, system_msg: str, user_msg: str) -> str:
        """EXAONE 3.5 전용 Chat Template 포맷팅 (하위 호환성 유지)"""
        return f"[|system|]{system_msg}[|endofturn|]\n[|user|]{user_msg}[|endofturn|]\n[|assistant|]"


def get_exaone_llm() -> ExaoneLLM:
    """엔진 싱글톤 인스턴스 반환"""
    return ExaoneLLM()