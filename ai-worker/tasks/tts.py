import os
import time
import logging
import base64
import tempfile
import scipy.io.wavfile as wavfile
from abc import ABC, abstractmethod
from celery import shared_task

# 로깅 설정
logger = logging.getLogger("TTS-Task")

class TTSBase(ABC):
    @abstractmethod
    def load_model(self):
        pass
    
    @abstractmethod
    def generate_speech(self, text: str, output_path: str, language: str = "Korean") -> dict:
        pass

class SupertonicTTS(TTSBase):
    """
    Supertonic 2 음성 합성 엔진 (한국어 자막 지원)
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self.tts = None
        
    def load_model(self):
        if self.tts is not None:
            return True
            
        try:
            from supertonic import TTS
            self.tts = TTS(model="supertonic-2", auto_download=True)
            logger.info("✅ Supertonic 2 모델 로드 완료")
            return True
        except Exception as e:
            logger.error(f"❌ Supertonic 2 로드 실패: {e}")
            return False
    
    def generate_speech(self, text: str, output_path: str, language: str = "Korean") -> dict:
        if self.tts is None and not self.load_model():
            return {"success": False, "error": "모델 로드 실패"}
        
        try:
            gen_start = time.time()
            lang_code = "ko" if language.lower() in ["korean", "ko"] else "en"
            
            # 목소리 스타일 설정 (M1: 남성 권장)
            voice_style = self.tts.get_voice_style("M1")
            
            audio, _ = self.tts.synthesize(
                text=text,
                voice_style=voice_style,
                lang=lang_code
            )
            
            self.tts.save_audio(audio, output_path)
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

# 전역 엔진 인스턴스
tts_engine = None

def load_tts_engine():
    global tts_engine
    if tts_engine is None:
        tts_engine = SupertonicTTS()
        tts_engine.load_model()

# 초기화
load_tts_engine()

@shared_task(name="tasks.tts.synthesize")
def synthesize_task(text: str, language="ko", speed=1.0):
    """
    텍스트를 음성으로 변환하여 Base64로 반환하는 Celery 태스크
    """
    global tts_engine
    if tts_engine is None:
        load_tts_engine()
        
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_path = tmp.name
            
        result = tts_engine.generate_speech(text, temp_path, language=language)
        
        if not result["success"]:
            return {"status": "error", "message": result.get("error", "Synthesis failed")}

        with open(temp_path, "rb") as f:
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
        if temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass
