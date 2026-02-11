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
    global stt_pipeline
    
    # [최적화] GPU 워커(질문 생성 전용)는 STT 모델을 로드할 필요가 없음
    gpu_layers = int(os.getenv("N_GPU_LAYERS", "-1"))
    if gpu_layers == -1:
        logger.info("⏩ [SKIP] GPU Worker detected. Skipping Whisper Pipeline loading.")
        return

    try:
        # cuDNN 에러 방지를 위해 CPU 사용 강제
        device = "cpu" 
        torch_dtype = torch.float32

        logger.info(f"🚀 [LOADING] Whisper Pipeline ({MODEL_ID}) on {device}...")
        
        stt_pipeline = pipeline(
            "automatic-speech-recognition",
            model=MODEL_ID,
            torch_dtype=torch_dtype,
            device=device,
            chunk_length_s=30,
        )
        logger.info("✅ Whisper Pipeline loaded successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to load Whisper Pipeline: {e}")
        stt_pipeline = None

# 모듈 로드 시 전역 호출 제거 (실제 태스크 수행 시 로드하도록 수정)
# load_stt_pipeline()

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
