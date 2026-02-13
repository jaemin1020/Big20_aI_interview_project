import os
import base64
import tempfile
import logging
import numpy as np
from celery import shared_task
from faster_whisper import WhisperModel

# 로깅 설정
logger = logging.getLogger("STT-Task")

# 전역 모델 변수
stt_model = None
# 모델 사이즈: tiny, base, small, medium, large-v1, large-v2, large-v3, large-v3-turbo
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3-turbo")

def load_stt_model():
    """
    Faster-Whisper 모델을 로드합니다. (싱글톤 패턴)
    GPU 환경이면 CUDA + float16, CPU 환경이면 int8 양자화 사용
    """
    global stt_model
    
    if stt_model is not None:
        logger.info(f"✅ STT Model already loaded: {MODEL_SIZE}")
        return True

    try:
        # [GPU 가속] 환경 변수 확인 (개인 브랜치 방식 채택)
        use_gpu = os.getenv("USE_GPU", "false").lower() == "true"
        
        if use_gpu:
            device = "cuda"
            compute_type = "float16"  # GPU에서는 float16이 최적
        else:
            device = "cpu"
            compute_type = "int8"     # CPU에서는 int8이 최적
        
        logger.info(f"🚀 [LOADING] Faster-Whisper ({MODEL_SIZE}) on {device.upper()} (compute_type={compute_type})...")
        
        # 모델 로드
        stt_model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
        
        logger.info(f"✅ Faster-Whisper loaded successfully: {MODEL_SIZE}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to load Faster-Whisper ({MODEL_SIZE}): {e}", exc_info=True)
        stt_model = None
        return False

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """
    Faster-Whisper를 사용하여 오디오(Base64)를 텍스트로 변환합니다.
    Args:
        audio_b64 (str): Base64 인코딩된 오디오 데이터 (헤더 포함될 수 있음)
    """
    global stt_model
    
    logger.info(f"[STT] Task received. Model status: {'Loaded' if stt_model else 'Not loaded'}")
    
    # 모델 로드 (지연 로딩)
    if stt_model is None:
        logger.info("[STT] Model not loaded. Attempting to load...")
        success = load_stt_model()
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
        
        # 1. raw PCM 확인 (media-server에서 보낸 실시간 2초 chunks 처리 최적화)
        # 16000Hz * 1ch * 2bytes(int16) * 2sec = 64000 bytes
        if len(audio_bytes) == 64000:
            try:
                # np.int16 -> np.float32 (Whisper 권장 포맷)
                audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                segments, info = stt_model.transcribe(audio_np, beam_size=5, language="ko")
                full_text = "".join([s.text for s in segments]).strip()
                if full_text:
                    logger.info(f"STT Success (Raw): {full_text[:50]}...")
                    return {"status": "success", "text": full_text}
            except Exception as e:
                logger.warning(f"Raw PCM processing failed, falling back to file mode: {e}")

        # 2. 파일 기반 처리 (녹음 파일 업로드 등 일반적인 경우)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            input_path = tmp.name
        
        segments, info = stt_model.transcribe(
            input_path, 
            beam_size=5, 
            language="ko", 
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        full_text = "".join([s.text for s in segments]).strip()
        logger.info(f"STT Success (File): {full_text[:50]}...")
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
