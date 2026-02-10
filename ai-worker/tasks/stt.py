from celery import shared_task
from faster_whisper import WhisperModel
import os
import logging
import base64
import tempfile
import torch

logger = logging.getLogger("STT-Task")

# 전역 모델 변수
stt_model = None
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3-turbo") 

def load_stt_model():
    """
    Faster-Whisper 모델 로드
    """
    global stt_model
    try:
        use_gpu = os.getenv("USE_GPU", "false").lower() == "true"
        device = "cuda" if use_gpu else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        logger.info(f"Attempting to load Faster-Whisper ({MODEL_SIZE}) on {device}...")
        
        try:
             stt_model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
             logger.info(f"✅ Faster-Whisper loaded on {device}")
        except Exception as e:
             if device == "cuda":
                 logger.warning(f"Failed to load on CUDA: {e}. Falling back to CPU.")
                 device = "cpu"
                 compute_type = "int8"
                 stt_model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
                 logger.info(f"✅ Faster-Whisper loaded on CPU (Fallback)")
             else:
                 raise e
    except Exception as e:
        logger.error(f"Failed to load Faster-Whisper Model: {e}")
        stt_model = None

# 모듈 로드 시 시도
load_stt_model()

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """
    Faster-Whisper를 사용한 통합 STT Task (파일/청크)
    
    Args:
        audio_b64: Base64 encoded audio string
        
    Returns:
        dict: {"status": "success", "text": "..."}
    """
    global stt_model
    
    if stt_model is None:
        load_stt_model()
        if stt_model is None:
             return {"status": "error", "message": "Model loading failed"}

    temp_path = None
    try:
        if not audio_b64:
            return {"status": "error", "message": "Empty audio data"}
            
        # Base64 decoding & Save to Temp File
        audio_bytes = base64.b64decode(audio_b64)
        
        # 파일 저장 (faster-whisper는 파일 경로 또는 binary stream 지원)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name
        
        # Inference
        segments, info = stt_model.transcribe(
            temp_path, 
            beam_size=5, 
            language="ko", # 한국어 강제
            vad_filter=True # 음성 활동 감지 사용
        )
        
        full_text = ""
        for segment in segments:
            full_text += segment.text
        
        full_text = full_text.strip()
        logger.info(f"STT Success: {len(full_text)} chars")
        
        return {"status": "success", "text": full_text}
        
    except Exception as e:
        logger.error(f"STT Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
        
    finally:
        # 임시 파일 삭제
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
