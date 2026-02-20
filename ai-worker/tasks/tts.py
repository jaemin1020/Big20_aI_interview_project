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
    """설명:
        텍스트 음성 합성(TTS) 엔진의 공통 인터페이스를 정의하는 추상 기초 클래스

    생성자: CYJ
    생성일자: 2026-02-10
    """
    @abstractmethod
    def load_model(self):
        """설명:
            TTS 모델을 메모리에 로드

        생성자: CYJ
        생성일자: 2026-02-10
        """
        pass
    
    @abstractmethod
    def generate_speech(self, text: str, output_path: str, language: str = "Korean") -> dict:
        """설명:
            텍스트를 음성으로 합성하여 파일로 저장

        Args:
            text (str): 합성할 대상 텍스트
            output_path (str): 생성된 오디오 파일을 저장할 경로
            language (str): 합성할 언어 (기본값: "Korean")

        Returns:
            dict: 성공 여부 및 생성 정보를 포함하는 딕셔너리

        생성자: CYJ, hyl
        생성일자: 2026-02-10, 2026-02-19
        """
        pass

class SupertonicTTS(TTSBase):
    """설명:
        Supertonic 2 엔진을 사용하여 한국어/영어 음성 합성을 수행하는 클래스

    Attributes:
        tts (TTS): Supertonic TTS 엔진 인스턴스
        _instance (SupertonicTTS): 싱글톤 패턴을 위한 인스턴스 저장 변수
        _initialized (bool): 초기화 여부 플래그

    생성자: CYJ
    생성일자: 2026-02-10
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
        """설명:
            Supertonic 2 모델을 로드하고 엔진을 초기화

        Returns:
            bool: 모델 로드 성공 시 True, 실패 시 False

        생성자: CYJ
        생성일자: 2026-02-10
        """
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
        """설명:
            입력된 텍스트를 지정된 보이스 스타일(F2)로 합성하여 WAV 파일로 저장

        Args:
            text (str): 음성으로 변환할 텍스트
            output_path (str): 출력 파일 경로
            language (str): 언어 설정 (Korean/English)

        Returns:
            dict: 성공 여부, 출력 경로, 생성 시간(ms), 샘플 레이트 등을 포함

        생성자: CYJ,hyl
        생성일자: 2026-02-10,2026-02-19
        """
        if self.tts is None and not self.load_model():
            return {"success": False, "error": "모델 로드 실패"}
        
        try:
            gen_start = time.time()
            lang_code = "ko" if language.lower() in ["korean", "ko"] else "en"
            
            # 목소리 스타일 설정 (F2: 여성 권장)
            style_name = "F2"
            voice_style = self.tts.get_voice_style(style_name)
            logger.info(f"🎭 [목소리 스타일 적용] {style_name}")
            
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
    """설명:
        전역 TTS 엔진 인스턴스를 초기화하고 모델 로드를 수행

    생성자: CYJ
    생성일자: 2026-02-10
    """
    global tts_engine
    if tts_engine is None:
        tts_engine = SupertonicTTS()
        tts_engine.load_model()

# 초기화
load_tts_engine()

@shared_task(name="tasks.tts.synthesize")
def synthesize_task(text: str, language="ko", speed=1.0, **kwargs):
    """설명:
        텍스트를 음성으로 변환하여 Base64 인코딩된 문자열로 반환하는 Celery 태스크

    Args:
        text (str): 변환할 텍스트
        language (str): 언어 코드 (기본값: "ko")
        speed (float): 음성 속도 (기본값: 1.0)
        **kwargs: 추가 설정 (question_id 등)

    Returns:
        dict: 상태(success/error), Base64 오디오 데이터, 합성 시간 등을 포함

    생성자: CYJ, hyl
    생성일자: 2026-02-10, 2026-02-19
    """
    global tts_engine
    question_id = kwargs.get("question_id")
    
    logger.info(f"🔊 [TTS 태스크 시작] ID: {question_id if question_id else 'N/A'}, 텍스트 길이: {len(text)}")
    
    if tts_engine is None:
        logger.info("⚙️ TTS 엔진 초기화 중...")
        load_tts_engine()
        
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_path = tmp.name
        
        logger.info(f"🟡 음성 합성 진행 중... (언어: {language})")
        result = tts_engine.generate_speech(text, temp_path, language=language)
        
        if not result["success"]:
            logger.error(f"❌ 음성 합성 실패: {result.get('error')}")
            return {"status": "error", "message": result.get("error", "Synthesis failed")}

        logger.info(f"✅ 음성 합성 완료 (소요시간: {result.get('duration_ms', 0):.2f}ms)")
        logger.info(f"📖 [TTS 읽는 텍스트]: {text}")

        with open(temp_path, "rb") as f:
            audio_bytes = f.read()
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        # [추가] question_id가 있으면 공유 볼륨에 직접 저장 (백엔드가 이 URL로 서빙)
        if question_id is not None:
            try:
                import pathlib
                tts_dir = pathlib.Path("/app/uploads/tts")
                tts_dir.mkdir(parents=True, exist_ok=True)
                out_path = tts_dir / f"q_{question_id}.wav"
                with open(out_path, "wb") as f:
                    f.write(audio_bytes)
                logger.info(f"💾 [파일 저장 성공] 경로: {out_path} (크기: {len(audio_bytes)} bytes)")
            except Exception as save_err:
                logger.warning(f"⚠️ [파일 저장 실패] {save_err}")
            
        return {
            "status": "success", 
            "audio_base64": audio_b64[:100] + "...(truncated for log visibility)",
            "duration_ms": result.get("duration_ms")
        }
    except Exception as e:
        logger.error(f"TTS Task Error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass
