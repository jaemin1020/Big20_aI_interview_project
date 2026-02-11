import os
import base64
import tempfile
import logging
import datetime
import shutil
import time
import subprocess
from celery import shared_task
from transformers import pipeline
import torch

# 로깅 설정
logger = logging.getLogger("STT-Task")

# 1. 모델 설정 (사용자가 원하는 Whisper Turbo 모델)
MODEL_ID = os.getenv("WHISPER_MODEL_ID", "openai/whisper-large-v3-turbo")
stt_pipeline = None

def load_stt_pipeline():
    """
    Transformers Pipeline 로드 (어제 작업한 방식 그대로)
    """
    global stt_pipeline
    try:
        if stt_pipeline is not None:
            return
            
        device = "cuda" if torch.cuda.is_available() else "cpu"
        torch_dtype = torch.float16 if device == "cuda" else torch.float32
        
        logger.info(f"Loading Transformers Pipeline ({MODEL_ID}) on {device}...")
        
        stt_pipeline = pipeline(
            "automatic-speech-recognition",
            model=MODEL_ID,
            torch_dtype=torch_dtype,
            device=device,
            chunk_length_s=30,
        )
        logger.info("Transformers Pipeline loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Transformers Pipeline: {e}")
        stt_pipeline = None

# 초기 로드
load_stt_pipeline()

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """
    STT 변환 작업 (Transformers Pipeline 사용)
    """
    global stt_pipeline
    
    start_time = time.time()
    task_id = recognize_audio_task.request.id or f"local-{datetime.datetime.now().timestamp()}"
    logger.info(f"[{task_id}] STT Task Started")
    
    if stt_pipeline is None:
        load_stt_pipeline()
        if stt_pipeline is None:
            return {"status": "error", "message": "Model load failed"}

    input_path = None
    output_path = None

    try:
        if not audio_b64:
             return {"status": "error", "message": "Empty audio data"}

        # 1. Decode Base64
        audio_bytes = base64.b64decode(audio_b64)
        
        # 2. Save Temporary File (.webm)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            input_path = tmp.name

        # 3. Convert to WAV (16kHz, Mono) using ffmpeg
        output_path = input_path + ".wav"
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            output_path
        ]
        
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            logger.error(f"[{task_id}] ffmpeg failed: {process.stderr}")
            return {"status": "error", "message": "FFmpeg conversion failed"}

        # 4. Inference
        logger.info(f"[{task_id}] Running Inference...")
        
        result = stt_pipeline(
            output_path,
            generate_kwargs={
                "language": "ko",
                "task": "transcribe",
                "max_new_tokens": 128
            }
        )
        
        text = result.get("text", "").strip()
        logger.info(f"[{task_id}] Result: {text}")

        # 5. Hallucination Filter
        filters = ["MBC 뉴스", "시청해 주셔서", "구독과 좋아요", "자막 제공", "SUBTITLES BY"]
        if any(f in text for f in filters):
            logger.warning(f"[{task_id}] Filtered: {text}")
            text = ""

        elapsed = time.time() - start_time
        return {"status": "success", "text": text}

    except Exception as e:
        logger.error(f"[{task_id}] Error: {e}")
        return {"status": "error", "message": str(e)}
        
    finally:
        # Cleanup
        for p in [input_path, output_path]:
            if p and os.path.exists(p):
                try: os.remove(p)
                except: pass
