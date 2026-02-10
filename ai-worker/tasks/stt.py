from celery import shared_task
from transformers import pipeline
import torch
import os
import logging
import base64
import tempfile

logger = logging.getLogger("STT-Task")

# 전역 파이프라인 변수
stt_pipeline = None
MODEL_ID = os.getenv("WHISPER_MODEL_ID", "openai/whisper-large-v3-turbo") 

def load_stt_pipeline():
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
    Transformers Pipeline을 사용한 로컬 STT Task
    
    Args:
        audio_b64: Base64 encoded audio string
        
    Returns:
        dict: {"status": "success", "text": "..."}
    """
    global stt_pipeline
    
    if stt_pipeline is None:
        load_stt_pipeline()
        if stt_pipeline is None:
             return {"status": "error", "message": "Model loading failed"}

    temp_path = None
    try:
        if not audio_b64:
            return {"status": "error", "message": "Empty audio data"}
            
        # Base64 decoding & Save to Temp File
        audio_bytes = base64.b64decode(audio_b64)
        
        # Transformers Pipeline은 파일 경로를 입력받는 것이 안정적 (ffmpeg 사용)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name
        
        # Inference
        # generate_kwargs={"language": "korean"} 추가하여 한국어 강제 가능 (선택 사항)
        result = stt_pipeline(
            temp_path, 
            generate_kwargs={"language": "korean"}
        )
        
        text = result.get("text", "").strip()
        logger.info(f"STT Pipeline Success: {len(text)} chars")
        
        return {"status": "success", "text": text}
        
    except Exception as e:
        logger.error(f"STT Pipeline Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
        
    finally:
        # 임시 파일 삭제
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
