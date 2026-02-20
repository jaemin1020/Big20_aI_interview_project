import os
import time
import logging
import base64
import tempfile
import scipy.io.wavfile as wavfile
from abc import ABC, abstractmethod # [문법] 추상 클래스를 만들기 위한 도구입니다.
from celery import shared_task

# 로깅 설정: 장부에 "TTS-Task"라는 이름으로 기록을 남깁니다.
logger = logging.getLogger("TTS-Task")

# ==========================================
# 1. 설계도 만들기 (Abstract Base Class)
# ==========================================

# [문법] (ABC): 추상 클래스(Abstract Base Class)의 약자입니다. 
# "이 클래스를 상속받는 모든 TTS는 반드시 load_model과 generate_speech 함수를 가져야 해!"라고 강제하는 설계도입니다.
class TTSBase(ABC):
    
    # [문법] @abstractmethod: "내용은 없지만, 나를 물려받는 자식들은 이 함수를 꼭 직접 구현해야 해"라는 뜻입니다.
    # 왜? 나중에 다른 TTS 엔진(예: 구글 TTS)으로 바꿔 끼우더라도 코드 구조를 통일하기 위해서입니다.
    @abstractmethod
    def load_model(self):
        pass
    
    @abstractmethod
    def generate_speech(self, text: str, output_path: str, language: str = "Korean") -> dict:
        pass

# ==========================================
# 2. 실제 엔진 구현 (Supertonic TTS)
# ==========================================

class SupertonicTTS(TTSBase):
    """
    Supertonic 2 엔진을 실제로 작동시키는 클래스입니다.
    싱글톤 패턴을 사용하여 메모리 낭비를 방지합니다.
    """
    # [문법] _instance: 클래스 변수입니다. 단 하나의 일꾼(객체)만 저장하기 위한 공간입니다.
    _instance = None
    
    # [문법] __new__: 객체가 생성될 때 가장 먼저 호출되는 '조상' 함수입니다.
    # 왜 썼나? 싱글톤(Singleton) 패턴 구현을 위해서입니다. 
    # "이미 만들어진 일꾼이 있으면 새로 만들지 말고 걔를 돌려줘!"라는 뜻입니다. (메모리 아끼기!)
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    # [문법] __init__: 객체의 속성을 초기화하는 '생성자'입니다.
    def __init__(self):
        # [문법] hasattr: "나한테 _initialized라는 속성이 이미 있니?"라고 묻는 것입니다.
        # 싱글톤 패턴에서 초기화가 두 번 일어나는 것을 방지하는 안전장치입니다.
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self.tts = None
        
    def load_model(self):
        """실제 AI 모델 파일을 메모리에 올립니다."""
        if self.tts is not None:
            return True
            
        try:
            from supertonic import TTS
            # [문법] 인스턴스 변수 self.tts에 모델을 저장합니다.
            self.tts = TTS(model="supertonic-2", auto_download=True)
            logger.info("✅ Supertonic 2 모델 로드 완료")
            return True
        except Exception as e:
            logger.error(f"❌ Supertonic 2 로드 실패: {e}")
            return False
    
    def generate_speech(self, text: str, output_path: str, language: str = "Korean") -> dict:
        """텍스트를 받아서 음성 파일(.wav)로 저장합니다."""
        # [문법] and not: 모델이 없는데 로드까지 실패했다면 작업을 중단합니다.
        if self.tts is None and not self.load_model():
            return {"success": False, "error": "모델 로드 실패"}
        
        try:
            gen_start = time.time()
            # [문법] if-else 한 줄 쓰기(삼항 연산자): 언어 코드를 깔끔하게 결정합니다.
            lang_code = "ko" if language.lower() in ["korean", "ko"] else "en"
            
            # 목소리 스타일 설정 (M1: 남성 권장)
            voice_style = self.tts.get_voice_style("M1")
            
            # synthesize: "글자를 소리 데이터로 합성해라"는 핵심 명령어입니다.
            audio, _ = self.tts.synthesize(
                text=text,
                voice_style=voice_style,
                lang=lang_code
            )
            
            # 소리 데이터를 지정된 경로(output_path)에 파일로 저장합니다.
            self.tts.save_audio(audio, output_path)
            
            # [문법] * 1000: 초 단위 시간을 밀리초(ms) 단위로 바꿔 가독성을 높입니다.
            gen_time_ms = (time.time() - gen_start) * 1000
            
            return {
                "success": True,
                "output_path": output_path,
                "duration_ms": gen_time_ms,
                "sample_rate": self.tts.sample_rate,
            }
        except Exception as e:
            logger.error(f"❌ 음성 생성 실패: {e}")
            return {"success": False, "error": str(e)}

# ==========================================
# 3. 전역 관리 및 Celery 작업 (Worker)
# ==========================================

# [문법] None 초기화: 프로그램 시작 시점에는 아직 모델을 로드하지 않겠다는 뜻입니다.
tts_engine = None

def load_tts_engine():
    """전역 엔진을 안전하게 하나만 생성하는 함수입니다."""
    global tts_engine
    if tts_engine is None:
        tts_engine = SupertonicTTS()
        tts_engine.load_model()

# 초기화: 프로그램 실행 시점에 미리 엔진을 준비시킵니다.
load_tts_engine()

@shared_task(name="tasks.tts.synthesize")
def synthesize_task(text: str, language="ko", speed=1.0):
    """
    Celery 일꾼이 수행할 실제 작업입니다.
    텍스트를 소리로 바꾸고, 그 결과를 텍스트(Base64)로 돌려줍니다.
    """
    global tts_engine
    if tts_engine is None:
        load_tts_engine()
        
    temp_path = None
    try:
        # 1. 임시 파일 생성
        # [문법] with문: 작업이 끝나면 임시 파일을 안전하게 닫습니다.
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_path = tmp.name
            
        # 2. 음성 생성
        result = tts_engine.generate_speech(text, temp_path, language=language)
        
        if not result["success"]:
            return {"status": "error", "message": result.get("error", "Synthesis failed")}

        # 3. 파일을 Base64로 변환 (문자열로 만들어서 네트워크로 보내기 위함)
        # [문법] open(path, "rb"): 파일을 '이진 읽기(Read Binary)' 모드로 엽니다.
        with open(temp_path, "rb") as f:
            # [문법] encode('utf-8'): 바이트 데이터를 일반 문자열로 바꿔서 JSON 전송이 가능하게 만듭니다.
            audio_b64 = base64.b64encode(f.read()).decode('utf-8')
            
        return {
            "status": "success", 
            "audio_base64": audio_b64,
            "duration_ms": result.get("duration_ms")
        }
    except Exception as e:
        logger.error(f"TTS Task Error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        # [문법] finally + os.path.exists: 에러가 나더라도 내 컴퓨터에 쓰레기 파일이 남지 않게 무조건 지웁니다.
        if temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass