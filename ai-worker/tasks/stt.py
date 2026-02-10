from celery import shared_task
from faster_whisper import WhisperModel
import os
import base64
import tempfile
import logging
import datetime
import shutil
import time
import subprocess
import torch

# 로깅 설정
logger = logging.getLogger("STT-Task")

# 전역 모델 변수
stt_model = None

# Faster-Whisper는 CTranslate2 변환 모델이 필요합니다.
# OpenAI 원본 모델(openai/whisper-large-v3-turbo)을 바로 사용할 수 없으므로,
# 변환된 모델(deepdml/faster-whisper-large-v3-turbo-ct2)을 기본값으로 사용하거나
# 직접 변환하여 경로를 지정해야 합니다.
DEFAULT_MODEL_ID = "deepdml/faster-whisper-large-v3-turbo-ct2"
MODEL_ID = os.getenv("WHISPER_MODEL_ID", DEFAULT_MODEL_ID)
DEBUG_DIR = "/app/debug_audio"

try:
    if not os.path.exists(DEBUG_DIR):
        os.makedirs(DEBUG_DIR, exist_ok=True)
except:
    pass

def load_stt_model():
    """
    Faster-Whisper 모델 로드
    """
    global stt_model
    try:
        if stt_model is not None:
            return
        
        # GPU 사용 가능 여부 확인
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        logger.info(f"Loading Faster-Whisper Model ({MODEL_ID}) on {device} (compute_type={compute_type})...")

        stt_model = WhisperModel(
            model_size_or_path=MODEL_ID,
            device=device,
            compute_type=compute_type,
            # 모델 다운로드 경로 지정 (선택 사항)
            download_root="/app/models/faster_whisper"
        )
        logger.info("Faster-Whisper Model loaded successfully.")
            
    except Exception as e:
        logger.error(f"Failed to load Faster-Whisper Model: {e}")
        stt_model = None

# 모듈 로드 시 또는 첫 실행 시 로드
load_stt_model()

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """
    사용자의 오디오를 받아 텍스트로 변환 (Faster-Whisper 사용 + 환각 방지)
    """
    global stt_model
    
    start_time = time.time()
    task_id = recognize_audio_task.request.id or f"local-{datetime.datetime.now().timestamp()}"
    logger.info(f"[{task_id}] STT 작업 시작.")
    
    if stt_model is None:
        load_stt_model()
        if stt_model is None:
             return {"status": "error", "message": "모델 로딩 실패"}

    input_path = None
    output_path = None
    
    try:
        if not audio_b64:
            return {"status": "error", "message": "오디오 데이터가 비어 있습니다."}
            
        audio_bytes = base64.b64decode(audio_b64)
        if len(audio_bytes) < 100: 
             return {"status": "success", "text": ""} 

        # 1. 임시 파일 저장 (.webm or etc)
        # Faster-Whisper는 ffmpeg를 내부적으로 사용하므로, 
        # 대부분의 오디오 포맷을 직접 처리할 수 있지만,
        # 안전하게 wav로 변환하는 과정을 유지하거나 직접 넣을 수 있습니다.
        # 여기서는 기존 로직대로 ffmpeg 변환을 유지합니다 (안정성 확보).
        
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            input_path = tmp.name
        
        # [디버그용] 원본 저장
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_path = os.path.join(DEBUG_DIR, f"{timestamp}_{task_id[-8:]}_input.webm")
            # shutil.copy(input_path, debug_path) # 디버그 필요 시 주석 해제
            # logger.info(f"[{task_id}] 디버グ 오디오 저장됨: {debug_path}")
        except:
            pass

        # 2. ffmpeg를 이용한 정규화 (16kHz, Mono WAV) - Faster-Whisper 최적화
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

        # 3. Whisper 추론 (Faster-Whisper)
        logger.info(f"[{task_id}] Whisper 추론 시작...")
        
        # transcribe returns a generator
        segments, info = stt_model.transcribe(
            output_path, 
            beam_size=5,
            language="ko",
            temperature=0.0,
            vad_filter=True, # VAD 필터 사용 (무음 제거)
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Generator를 순회하며 텍스트 합치기
        text_segments = []
        for segment in segments:
            text_segments.append(segment.text)
            
        full_text = " ".join(text_segments).strip()
        logger.info(f"[{task_id}] 인식 텍스트: '{full_text}'")

        # 4. 환각 필터링
        hallucination_filters = [
            "감사합니다", "시청해주셔서", "구독과 좋아요", "MBC 뉴스", "끝.", "시청해 주셔서", "고맙습니다",
            "자막 제공", "자막 제작", "SUBTITLES BY"
        ]
        
        clean_text = full_text
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
