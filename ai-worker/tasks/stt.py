import os
import base64
import tempfile
import logging # [NEW] Added missing import
from celery import shared_task
from faster_whisper import WhisperModel

# 로깅 설정
logger = logging.getLogger("STT-Task")

# 전역 모델 변수
stt_model = None
# 모델 사이즈: tiny, base, small, medium, large-v1, large-v2, large-v3, large-v3-turbo
# CPU 환경: small 또는 medium 권장 (정확도 80-85%, 속도 5-15초)
# GPU 환경: large-v3-turbo 권장 (정확도 90%, 속도 2-5초)
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3-turbo")

def load_stt_pipeline():
    """
    Faster-Whisper 모델을 로드합니다. (싱글톤 패턴)
    Compute Type: int8 (CPU 성능 최적화)
    """
    global stt_model
    
    if stt_model is not None:
        logger.info(f"✅ STT Model already loaded: {MODEL_SIZE}")
        return True

    try:
        device = "cpu"
        # CPU에서 int8 양자화 사용 시 속도 대폭 향상
        compute_type = "int8" 
        
        logger.info(f"🚀 [LOADING] Faster-Whisper ({MODEL_SIZE}) on {device} (compute_type={compute_type})...")
        
        # 모델 로드 (최초 실행 시 다운로드됨)
        stt_model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
        
        logger.info(f"✅ Faster-Whisper loaded successfully: {MODEL_SIZE}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to load Faster-Whisper ({MODEL_SIZE}): {e}", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        stt_model = None
        return False

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """
    Faster-Whisper를 사용하여 오디오(Base64)를 텍스트로 변환합니다.
    Args:
        audio_b64 (str): Base64 인코딩된 오디오 데이터 (헤더 포함될 수 있음)
    """
    
    logger.info(f"[STT] Task received. Model status: {'Loaded' if stt_model else 'Not loaded'}")
    
    # 모델 로드 (지연 로딩)
    if stt_model is None:
        logger.info("[STT] Model not loaded. Attempting to load...")
        success = load_stt_pipeline() # 함수명 수정: load_stt_model -> load_stt_pipeline
        if not success or stt_model is None:
            error_msg = f"STT Model loading failed. Model: {MODEL_SIZE}"
            logger.error(f"[STT] {error_msg}")
            return {"status": "error", "message": error_msg}

    input_path = None
    try:
        if not audio_b64:
            return {"status": "error", "message": "Empty audio data"}
            
        # Base64 헤더 처리 (data:audio/webm;base64,...)
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",")[1]
            
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            return {"status": "error", "message": f"Base64 decode failed: {e}"}
        
        # 임시 파일 저장 (faster-whisper는 파일 경로 입력 권장)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            input_path = tmp.name

        # Faster-Whisper 사용 (stt_model.transcribe)
        # logger.debug(f"🎤 Transcribing audio... (Model: {MODEL_SIZE})") # [Log Reduced]
        
        segments, info = stt_model.transcribe(
            input_path, 
            beam_size=1, 
            language="ko",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        full_text = ""
        for segment in segments:
            full_text += segment.text
        
        full_text = full_text.strip()
        logger.info(f"STT Success: {len(full_text)} chars. Preview: {full_text[:50]}")
        
        return {"status": "success", "text": full_text}
        
    except Exception as e:
        logger.error(f"STT Task Error: {e}")
        return {"status": "error", "message": str(e)}
        
    finally:
        # 임시 파일 정리
        if input_path and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except OSError:
                pass
