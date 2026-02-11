import os
import base64
import tempfile
from celery import shared_task
from faster_whisper import WhisperModel

# 로깅 설정
logger = logging.getLogger("STT-Task")

# 전역 모델 변수
stt_model = None
# 모델 사이즈: tiny, base, small, medium, large-v3-turbo. 
# CPU 환경을 위해 기본값은 'medium' 또는 'small' 권장.
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3-turbo")

def load_stt_pipeline():
    """
    Faster-Whisper 모델을 로드합니다. (싱글톤 패턴)
    Compute Type: int8 (CPU 성능 최적화)
    """
    global stt_model
    
    if stt_model is not None:
        return

    try:
        device = "cpu"
        # CPU에서 int8 양자화 사용 시 속도 대폭 향상
        compute_type = "int8" 
        
        logger.info(f"🚀 [LOADING] Faster-Whisper ({MODEL_SIZE}) on {device} (compute_type={compute_type})...")
        
        # 모델 로드 (최초 실행 시 다운로드됨)
        stt_model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
        
        logger.info("✅ Faster-Whisper loaded successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to load Faster-Whisper: {e}", exc_info=True)
        stt_model = None

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """
    Faster-Whisper를 사용하여 오디오(Base64)를 텍스트로 변환합니다.
    Args:
        audio_b64 (str): Base64 인코딩된 오디오 데이터 (헤더 포함될 수 있음)
    """
    global stt_pipeline
    
    # 모델 로드 (지연 로딩)
    if stt_model is None:
        load_stt_model()
        if stt_model is None:
             return {"status": "error", "message": "STT Model loading failed"}

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
        # suffix는 webm으로 가정하나, ffmpeg가 알아서 처리함
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
        
        # Inference
        # segments는 generator이므로 순회해야 실제 추론이 수행됨
        segments, info = stt_model.transcribe(
            temp_path, 
            beam_size=5, 
            language="ko", 
            vad_filter=True, # 음성 구간 감지 활성화 (무음 제거)
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        full_text = ""
        for segment in segments:
            full_text += segment.text
        
        full_text = full_text.strip()
        logger.info(f"STT Success: {len(full_text)} chars. Preview: {full_text[:50]}")
        
        return {"status": "success", "text": full_text}
        
    except Exception as e:
        logger.error(f"[{task_id}] Error: {e}")
        return {"status": "error", "message": str(e)}
        
    finally:
        # 임시 파일 정리
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
