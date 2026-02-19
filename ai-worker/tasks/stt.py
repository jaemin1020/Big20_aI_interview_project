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
    팀 프로젝트 결정 사항: STT는 CPU 리소스만 사용 (int8 양자화 적용)
    """
    global stt_model
    
    if stt_model is not None:
        logger.info(f"✅ STT Model already loaded: {MODEL_SIZE}")
        return True

    try:
        # 팀 공통 설정: CPU 및 int8 양자화 사용
        device = "cpu"
        compute_type = "int8"
        
        logger.info(f"🚀 [LOADING] Faster-Whisper ({MODEL_SIZE}) on CPU (compute_type=int8)...")
        
        # 모델 로드
        stt_model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)
        
        logger.info(f"✅ Faster-Whisper loaded successfully on CPU: {MODEL_SIZE}")
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

    # [추가] 알려진 환각(Hallucination) 문구 리스트
    HALLUCINATIONS = ["겨울이 이렇게", "넘치고 넘치고", "시청해 주셔서", "감사합니다", "청취해 주셔서"]

    input_path = None
    try:
        if not audio_b64:
            return {"status": "error", "message": "Empty audio data"}
            
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",")[1]
            
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            return {"status": "error", "message": f"Base64 decode failed: {e}"}
        
        # 1. WAV -> PCM 변환 (메모리 내 처리로 속도 향상)
        try:
            import io
            import wave
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wav:
                if wav.getnchannels() > 0:
                    frames = wav.readframes(wav.getnframes())
                    audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    segments, info = stt_model.transcribe(audio_np, beam_size=1, language="ko")
                    full_text = "".join([s.text for s in segments]).strip()
                    
                    # [필터] 환각 문구 제거 로직
                    if any(h in full_text for h in HALLUCINATIONS) and len(full_text) < 15:
                        logger.warning(f"🚫 환각 감지 및 필터링: {full_text}")
                        return {"status": "success", "text": ""}
                        
                    if full_text:
                        logger.info(f"STT Success (In-Memory): {full_text[:50]}...")
                        return {"status": "success", "text": full_text}
                    return {"status": "success", "text": ""} # 빈 텍스트 응답
        except Exception as e:
            logger.warning(f"In-memory processing failed, falling back to file: {e}")

        # 2. 파일 기반 처리 (최후의 보루)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            input_path = tmp.name
        
        segments, info = stt_model.transcribe(input_path, beam_size=1, language="ko")
        full_text = "".join([s.text for s in segments]).strip()
        
        if any(h in full_text for h in HALLUCINATIONS) and len(full_text) < 15:
            return {"status": "success", "text": ""}

        logger.info(f"STT Success (File Fallback): {full_text[:50]}...")
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
