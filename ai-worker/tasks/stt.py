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
logger = logging.getLogger("STT-Task")

# 전역 모델 변수
stt_pipeline = None
MODEL_ID = os.getenv("WHISPER_MODEL_ID", "openai/whisper-large-v3-turbo") 
DEBUG_DIR = "/app/debug_audio"

try:
    if not os.path.exists(DEBUG_DIR):
        os.makedirs(DEBUG_DIR, exist_ok=True)
except:
    pass

def load_stt_pipeline():
    """
    Whisper 파이프라인 로드 (안정성을 위해 CPU 모드 권장)
    """
    global stt_pipeline
    try:
        if stt_pipeline is not None:
            return
            
        device = "cpu"
        torch_dtype = torch.float32 
        
        logger.info(f"Loading Whisper Pipeline ({MODEL_ID}) on {device}...")

        stt_pipeline = pipeline(
            "automatic-speech-recognition",
            model=MODEL_ID,
            torch_dtype=torch_dtype,
            device=device,
            chunk_length_s=30,
        )
        logger.info("Whisper Pipeline loaded successfully.")
            
    except Exception as e:
        logger.error(f"Failed to load Whisper Pipeline: {e}")
        stt_pipeline = None

# 모듈 로드 시 또는 첫 실행 시 로드
load_stt_pipeline()

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """
    사용자의 오디오를 받아 텍스트로 변환 (환각 방지 필터 포함)
    """
    global stt_pipeline
    
    start_time = time.time()
    task_id = recognize_audio_task.request.id or f"local-{datetime.datetime.now().timestamp()}"
    logger.info(f"[{task_id}] STT 작업 시작.")
    
    if stt_pipeline is None:
        load_stt_pipeline()
        if stt_pipeline is None:
             return {"status": "error", "message": "모델 로딩 실패"}

    input_path = None
    output_path = None
    
    try:
        if not audio_b64:
            return {"status": "error", "message": "오디오 데이터가 비어 있습니다."}
            
        audio_bytes = base64.b64decode(audio_b64)
        if len(audio_bytes) < 100: 
             return {"status": "success", "text": ""} 

        # 1. 임시 파일 저장 (.webm)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            input_path = tmp.name
        
        # [디버그용] 원본 저장 (필요시 활성화)
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_path = os.path.join(DEBUG_DIR, f"{timestamp}_{task_id[-8:]}_input.webm")
            shutil.copy(input_path, debug_path)
            logger.info(f"[{task_id}] 디버그 오디오 저장됨: {debug_path}")
        except:
            pass

        # 2. ffmpeg를 이용한 정규화 (16kHz, Mono WAV)
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
            logger.error(f"[{task_id}] ffmpeg 변환 실패: {process.stderr}")
            return {"status": "error", "message": f"FFmpeg 변환 실패: {process.stderr}"}

        # 3. Whisper 추론
        logger.info(f"[{task_id}] Whisper 추론 시작...")
        result = stt_pipeline(
            output_path, 
            generate_kwargs={
                "language": "ko", 
                "task": "transcribe",
                "max_new_tokens": 128,
                "temperature": 0.0,
            }
        )
        
        raw_text = result.get("text", "").strip()
        logger.info(f"[{task_id}] 인식 텍스트: '{raw_text}'")

        # 4. 환각 필터링 (불필요한 자동 생성 문구 제거)
        hallucination_filters = [
            "감사합니다", "시청해주셔서", "구독과 좋아요", "MBC 뉴스", "끝.", "시청해 주셔서", "고맙습니다",
            "자막 제공", "자막 제작", "SUBTITLES BY"
        ]
        
        clean_text = raw_text
        if any(filter_word in clean_text for filter_word in hallucination_filters):
             logger.warning(f"[{task_id}] 환각 필터에 의해 텍스트 제거됨: {clean_text}")
             clean_text = ""

        elapsed = time.time() - start_time
        logger.info(f"[{task_id}] 최종 결과 반환 (소요 시간: {elapsed:.2f}s)")
        
        return {"status": "success", "text": clean_text}
        
    except Exception as e:
        logger.error(f"[{task_id}] Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
        
    finally:
        # 임시 파일 삭제
        for path in [input_path, output_path]:
            if path and os.path.exists(path):
                try: os.remove(path)
                except: pass
