import os
import base64
import tempfile
import logging
import datetime
import shutil
import time
import subprocess
from celery import shared_task
import torch
from transformers import pipeline

# 로깅 설정
logger = logging.getLogger(__name__)

# 전역 모델 변수
stt_pipeline = None
MODEL_ID = os.getenv("WHISPER_MODEL_ID", "openai/whisper-large-v3-turbo") 
DEBUG_DIR = "/app/debug_audio"

try:
    os.makedirs(DEBUG_DIR, exist_ok=True)
except:
    pass

def load_models():
    global stt_pipeline
    try:
        # CPU 강제 사용 (안정성)
        device = "cpu"
        torch_dtype = torch.float32 
        
        logger.info(f"Loading Whisper Pipeline ({MODEL_ID}) on {device}...")

        if stt_pipeline is None:
            stt_pipeline = pipeline(
                "automatic-speech-recognition",
                model=MODEL_ID,
                torch_dtype=torch_dtype,
                device=device,
                chunk_length_s=30,
            )
            logger.info("Models loaded successfully.")
            
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        stt_pipeline = None

load_models()

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    global stt_pipeline
    
    start_time = time.time()
    task_id = recognize_audio_task.request.id or f"local-{datetime.datetime.now().timestamp()}"
    logger.info(f"[{task_id}] STT Task Received.")
    
    if stt_pipeline is None:
        load_models()
        if stt_pipeline is None:
             return {"status": "error", "message": "Model loading failed"}

    input_path = None
    output_path = None
    
    try:
        if not audio_b64:
            return {"status": "error", "message": "Empty audio data"}
            
        audio_bytes = base64.b64decode(audio_b64)
        if len(audio_bytes) < 100: 
             return {"status": "success", "text": ""} 

        # 1. 원본 파일 저장 (확장자 없이 저장 후 ffmpeg가 알아서 판단하게 함, 혹은 .webm 시도)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            input_path = tmp.name
        
        # 디버그: 원본 저장
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_path = os.path.join(DEBUG_DIR, f"{timestamp}_{task_id[-8:]}_input.webm")
            shutil.copy(input_path, debug_path)
            logger.info(f"[{task_id}] Debug audio saved: {debug_path}")
        except:
            pass

        # 2. ffmpeg 직접 호출하여 WAV 변환 (가장 확실한 방법)
        output_path = input_path + ".wav"
        
        # -y: 덮어쓰기, -i: 입력, -ar 16000: 16kHz, -ac 1: Mono, -c:a pcm_s16le: PCM 16bit
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
            return {"status": "error", "message": f"FFmpeg conversion failed: {process.stderr}"}

        # 변환된 파일 확인
        if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
             logger.error(f"[{task_id}] Converted WAV is empty.")
             return {"status": "error", "message": "Converted audio is empty"}

        # 3. Whisper 추론
        logger.info(f"[{task_id}] Running Whisper inference...")
        
        result = stt_pipeline(
            output_path, 
            generate_kwargs={
                "language": "ko", 
                "task": "transcribe",
                # 환각 방지를 위한 보수적 설정
                "max_new_tokens": 128,
                "temperature": 0.0,
                # "condition_on_previous_text": False,  <-- 에러 원인 제거
                # "no_speech_threshold": 0.3 
            }
        )
        
        raw_text = result.get("text", "")
        clean_text = raw_text.strip()
        
        logger.info(f"[{task_id}] Raw Output: '{raw_text}'")

        # 필터링
        if clean_text.replace("-", "").strip() == "":
            clean_text = ""
            
        hallucination_filters = [
            "감사합니다", "시청해주셔서", "구독과 좋아요", "MBC 뉴스", "끝.", "시청해 주셔서", "고맙습니다",
            "자막 제공", "자막 제작", "SUBTITLES BY"
        ]
        if any(filter_word in clean_text for filter_word in hallucination_filters):
             logger.warning(f"[{task_id}] Hallucination filtered: {clean_text}")
             clean_text = ""

        elapsed = time.time() - start_time
        logger.info(f"[{task_id}] Final Result: '{clean_text}' (Time: {elapsed:.2f}s)")
        
        return {"status": "success", "text": clean_text}
        
    except Exception as e:
        # condition_on_previous_text 에러가 나면 재시도하는 로직을 넣을 수도 있지만, 일단 로그 남김
        if "condition_on_previous_text" in str(e):
             logger.warning(f"[{task_id}] API Error (param mismatch). Retrying without it.")
             # (여기서 재귀 호출 등을 할 수도 있으나 복잡해짐. 일단 에러 반환)
             
        logger.error(f"[{task_id}] Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
        
    finally:
        for path in [input_path, output_path]:
            if path and os.path.exists(path):
                try: os.remove(path)
                except: pass
