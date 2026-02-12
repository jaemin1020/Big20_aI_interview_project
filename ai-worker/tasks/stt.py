<<<<<<< HEAD
<<<<<<< HEAD
from celery import shared_task
from faster_whisper import WhisperModel
=======

>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======

>>>>>>> 린_phase4
import os
import logging
import base64
import tempfile
<<<<<<< HEAD
<<<<<<< HEAD
import torch
=======
from celery import shared_task
from faster_whisper import WhisperModel
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
from celery import shared_task
from faster_whisper import WhisperModel
>>>>>>> 린_phase4

logger = logging.getLogger("STT-Task")

# 전역 모델 변수
stt_model = None
<<<<<<< HEAD
<<<<<<< HEAD
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3-turbo") 
=======
# 모델 사이즈: tiny, base, small, medium, large-v3-turbo. 
# CPU 환경을 위해 기본값은 'medium' 또는 'small' 권장.
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3-turbo")
>>>>>>> 린_phase4

def load_stt_model():
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
<<<<<<< HEAD
        logger.error(f"❌ Failed to load Whisper Pipeline: {e}")
        stt_pipeline = None

# 모듈 로드 시 전역 호출 제거 (실제 태스크 수행 시 로드하도록 수정)
# load_stt_pipeline()
=======
# 모델 사이즈: tiny, base, small, medium, large-v3-turbo. 
# CPU 환경을 위해 기본값은 'medium' 또는 'small' 권장.
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3-turbo")

def load_stt_model():
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
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
        logger.error(f"❌ Failed to load Faster-Whisper: {e}", exc_info=True)
        stt_model = None
>>>>>>> 린_phase4

@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """
<<<<<<< HEAD
<<<<<<< HEAD
    Faster-Whisper를 사용한 통합 STT Task (파일/청크)
    
=======
    Faster-Whisper를 사용하여 오디오(Base64)를 텍스트로 변환합니다.
>>>>>>> 린_phase4
    Args:
        audio_b64 (str): Base64 인코딩된 오디오 데이터 (헤더 포함될 수 있음)
    """
    global stt_model
    
    # 모델 로드 (지연 로딩)
    if stt_model is None:
        load_stt_model()
        if stt_model is None:
<<<<<<< HEAD
             return {"status": "error", "message": "Model loading failed"}
=======
    Faster-Whisper를 사용하여 오디오(Base64)를 텍스트로 변환합니다.
    Args:
        audio_b64 (str): Base64 인코딩된 오디오 데이터 (헤더 포함될 수 있음)
    """
    global stt_model
    
    # 모델 로드 (지연 로딩)
    if stt_model is None:
        load_stt_model()
        if stt_model is None:
             return {"status": "error", "message": "STT Model loading failed"}
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
             return {"status": "error", "message": "STT Model loading failed"}
>>>>>>> 린_phase4

    temp_path = None
    try:
        if not audio_b64:
            return {"status": "error", "message": "Empty audio data"}
            
<<<<<<< HEAD
<<<<<<< HEAD
        # Base64 decoding & Save to Temp File
        audio_bytes = base64.b64decode(audio_b64)
        
        # 파일 저장 (faster-whisper는 파일 경로 또는 binary stream 지원)
=======
        # Base64 헤더 처리 (data:audio/webm;base64,...)
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",")[1]
            
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            return {"status": "error", "message": f"Base64 decode failed: {e}"}
        
        # 임시 파일 저장 (faster-whisper는 파일 경로 입력 권장)
        # suffix는 webm으로 가정하나, ffmpeg가 알아서 처리함
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
        # Base64 헤더 처리 (data:audio/webm;base64,...)
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",")[1]
            
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            return {"status": "error", "message": f"Base64 decode failed: {e}"}
        
        # 임시 파일 저장 (faster-whisper는 파일 경로 입력 권장)
        # suffix는 webm으로 가정하나, ffmpeg가 알아서 처리함
>>>>>>> 린_phase4
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name
        
        # Inference
<<<<<<< HEAD
<<<<<<< HEAD
        segments, info = stt_model.transcribe(
            temp_path, 
            beam_size=5, 
            language="ko", # 한국어 강제
            vad_filter=True # 음성 활동 감지 사용
=======
        # segments는 generator이므로 순회해야 실제 추론이 수행됨
        segments, info = stt_model.transcribe(
            temp_path, 
            beam_size=5, 
            language="ko", 
            vad_filter=True, # 음성 구간 감지 활성화 (무음 제거)
            vad_parameters=dict(min_silence_duration_ms=500)
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
        # segments는 generator이므로 순회해야 실제 추론이 수행됨
        segments, info = stt_model.transcribe(
            temp_path, 
            beam_size=5, 
            language="ko", 
            vad_filter=True, # 음성 구간 감지 활성화 (무음 제거)
            vad_parameters=dict(min_silence_duration_ms=500)
>>>>>>> 린_phase4
        )
        
        full_text = ""
        for segment in segments:
            full_text += segment.text
        
        full_text = full_text.strip()
<<<<<<< HEAD
<<<<<<< HEAD
        logger.info(f"STT Success: {len(full_text)} chars")
=======
        logger.info(f"STT Success: {len(full_text)} chars. Preview: {full_text[:50]}")
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
        logger.info(f"STT Success: {len(full_text)} chars. Preview: {full_text[:50]}")
>>>>>>> 린_phase4
        
        return {"status": "success", "text": full_text}
        
    except Exception as e:
        logger.error(f"STT Error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
        
    finally:
<<<<<<< HEAD
<<<<<<< HEAD
        # 임시 파일 삭제
=======
        # 임시 파일 정리
>>>>>>> 3c3c7ad852cb791ad6eea3c101528407d064e29d
=======
        # 임시 파일 정리
>>>>>>> 린_phase4
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
