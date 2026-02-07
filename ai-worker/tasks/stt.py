from celery import shared_task
from huggingface_hub import InferenceClient
import os
import logging
import base64

logger = logging.getLogger("STT-Task")

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """
    Hugging Face Whisper API를 사용한 STT Task
    
    Args:
        audio_b64: Base64 encoded audio string (from frontend/backend)
        
    Returns:
        dict: {"status": "success", "text": "..."} or {"status": "error", "message": "..."}
    """
    token = os.getenv("HUGGINGFACE_HUB_TOKEN")
    if not token:
        # Fallback to HF_TOKEN if available
        token = os.getenv("HF_TOKEN")
        
    if not token:
        logger.error("HUGGINGFACE_HUB_TOKEN is missing in AI-Worker environment")
        return {"status": "error", "message": "Server configuration error: Token missed"}

    try:
        # Base64 decoding
        if not audio_b64:
            return {"status": "error", "message": "Empty audio data"}
            
        audio_bytes = base64.b64decode(audio_b64)
        
        # Hugging Face Inference API 호출
        client = InferenceClient(token=token)
        
        # 모델명은 상수로 관리하거나 설정에서 가져올 수 있음
        MODEL_ID = "openai/whisper-large-v3-turbo"
        
        logger.info(f"Requesting ASR to Hugging Face ({MODEL_ID})...")
        response = client.automatic_speech_recognition(
            audio_bytes, 
            model=MODEL_ID
        )
        
        # 결과 추출
        text = response.text if hasattr(response, 'text') else str(response)
        logger.info(f"STT Task Success: {len(text)} chars")
        
        return {"status": "success", "text": text}
        
    except Exception as e:
        logger.error(f"STT Task processing failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
