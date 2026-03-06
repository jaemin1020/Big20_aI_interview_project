import os
import base64
import tempfile
import logging
import numpy as np
from celery import shared_task
from faster_whisper import WhisperModel

# ==========================================
# 1. 초기 설정 및 전역 변수 (Global Variables)
# ==========================================

# [문법] logging.getLogger: 프로그램 실행 중 발생하는 일을 기록하는 '장부'를 만듭니다.
logger = logging.getLogger("STT-Task")

# [문법] 전역 변수: 함수 밖에서 선언되어 프로그램 어디서든 접근 가능한 변수입니다.
# 초기값으로 'None'(아무것도 없음)을 주어, 나중에 모델이 로드되었는지 확인하는 용도로 씁니다.
stt_model = None

# [문법] os.getenv(A, B): 환경변수 A를 찾고, 없으면 기본값 B를 사용하라는 뜻입니다.
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "large-v3-turbo")

def load_stt_model():
    """
    Faster-Whisper 모델을 메모리에 올리는 함수입니다.
    """
    # [문법] global 키워드: 함수 안에서 함수 밖(전역)에 있는 변수(stt_model)를 
    # 수정하고 싶을 때 반드시 선언해야 합니다. 안 쓰면 함수 안의 '지역 변수'로 취급됩니다.
    global stt_model
    
    # [문법] if 변수 is not None: 모델이 이미 존재한다면(None이 아니라면) 
    # 더 실행하지 않고 함수를 종료(return)합니다. 효율적인 자원 관리입니다.
    if stt_model is not None:
        logger.info(f"✅ STT Model already loaded: {MODEL_SIZE}")
        return True

    # [문법] try-except: "일단 시도(try)해보고, 에러(Exception)나면 catch해서 처리해라"는 뜻입니다.
    # 프로그램이 에러 하나 때문에 통째로 꺼지는 것을 막아주는 안전장치입니다.
    try:
        # 팀 공통 설정: CPU 및 int8 양자화 사용
        # [수정] beam_size는 WhisperModel 생성자 파라미터가 아님 → transcribe() 호출 시 전달
        device = "cpu"
        compute_type = "int8"

        logger.info(f"🚀 [LOADING] Faster-Whisper ({MODEL_SIZE}) on CPU (compute_type=int8)...")

        # 모델 로드
        stt_model = WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)

        logger.info(f"✅ Faster-Whisper loaded successfully on CPU: {MODEL_SIZE}")
        return True
    except Exception as e:
        # [문법] f-string: 문자열 앞에 f를 붙이고 {e}처럼 중괄호를 쓰면 변수 값을 문자열 안에 바로 넣을 수 있습니다.
        logger.error(f"❌ Failed to load Faster-Whisper ({MODEL_SIZE}): {e}", exc_info=True)
        stt_model = None
        return False

# ==========================================
# 2. 메인 STT 작업 함수
# ==========================================

# [문법] @데코레이터: 함수 위에 @가 붙은 것은 "이 함수를 Celery라는 도구의 작업(task)으로 등록하겠다"는 선언입니다.
@shared_task(name="tasks.stt.recognize")
def recognize_audio_task(audio_b64: str):
    """설명:
        Base64로 인코딩된 오디오 데이터를 받아 Faster-Whisper로 한국어 STT 수행.
        메모리 내 처리를 우선 시도하고, 실패 시 임시 파일 방식으로 전환.

    Args:
        audio_b64 (str): Base64 인코딩된 WAV/WebM 오디오 데이터.

    Returns:
        dict: 처리 결과. {"status": "success", "text": "인식된 텍스트"} 또는
              {"status": "error", "message": "에러 내용"}.

    생성자: CYJ
    생성일자: 2026-02-10
    """
    global stt_model
    
    # 1. 모델이 없으면 로드 시도 (지연 로딩)
    if stt_model is None:
        success = load_stt_model()
        if not success or stt_model is None:
            return {"status": "error", "message": "Model loading failed"}

    # [문법] 리스트(List): 여러 개의 문자열을 대괄호 [] 안에 묶어 관리합니다.
    HALLUCINATIONS = ["겨울이 이렇게", "넘치고 넘치고", "시청해 주셔서", "감사합니다", "청취해 주셔서"]

    input_path = None
    try:
        if not audio_b64:
            return {"status": "error", "message": "Empty audio data"}
            
        # [문법] .split(",")와 인덱싱 [1]: "헤더,데이터" 형태의 문자열을 쉼표 기준으로 쪼개서 
        # 뒤쪽(1번 위치)의 순수 데이터만 가져옵니다. (컴퓨터는 0부터 숫자를 셉니다)
        if "," in audio_b64:
            audio_b64 = audio_b64.split(",")[1]
            
        # Base64 문자열을 바이트(이진 데이터)로 변환
        audio_bytes = base64.b64decode(audio_b64)
        
        # ---------------------------------------------------------
        # 방식 A: 메모리 내 처리 (In-Memory) - 속도가 매우 빠름
        # ---------------------------------------------------------
        try:
            import io
            import wave
            
            # [문법] with 문 (Context Manager): 파일을 열거나 자원을 쓸 때 사용합니다. 
            # 이 블록이 끝나면 따로 close()를 안 해도 자동으로 자원을 반납(닫기)해줍니다.
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wav:
                if wav.getnchannels() > 0:
                    frames = wav.readframes(wav.getnframes())
                    
                    # [문법] numpy 연산: 수만 개의 오디오 데이터를 한꺼번에 32768.0으로 나누어 
                    # -1.0 ~ 1.0 사이의 숫자로 정규화합니다. 파이썬 리스트보다 훨씬 빠릅니다.
                    audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # ─── VAD 최적 파라미터 (5초 청크 기준) ───────────────────
                    # speech_pad_ms=400 : speech 시작 400ms 앞을 보호 → 앞부분 잘림 방지 (핵심)
                    # threshold=0.35    : 기본값(0.5)보다 낮춰 한국어 짧은 발화도 speech로 인식
                    # min_speech_duration_ms=80  : 80ms 이상이면 speech로 간주 (짧은 어절 보호)
                    # min_silence_duration_ms=300: 자연스러운 어절 사이 침묵 허용
                    # ────────────────────────────────────────────────────────
                    segments, info = stt_model.transcribe(
                        audio_np,
                        beam_size=1,
                        language="ko",
                        vad_filter=True,
                        vad_parameters=dict(
                            threshold=0.35,
                            min_speech_duration_ms=80,
                            min_silence_duration_ms=300,
                            speech_pad_ms=400,
                        ),
                        condition_on_previous_text=False
                    )
                    
                    # [문법] 리스트 컴프리헨션(List Comprehension): 
                    # [s.text for s in segments]는 "segments 안의 각 요소 s에서 text만 뽑아 리스트를 만들어라"는 뜻입니다.
                    # "".join(...)은 그 리스트 안의 문장들을 빈칸 없이 하나로 합칩니다.
                    full_text = "".join([s.text for s in segments]).strip()
                    
                    # [문법] any() 함수: 리스트 안의 환각 문구 중 하나라도(any) 텍스트에 포함되어 있는지 확인합니다.
                    if any(h in full_text for h in HALLUCINATIONS) and len(full_text) < 15:
                        logger.warning(f"🚫 환각 감지: {full_text}")
                        return {"status": "success", "text": ""}
                        
                    if full_text:
                        return {"status": "success", "text": full_text}
        except Exception as e:
            logger.warning(f"메모리 처리 실패, 파일 방식으로 전환합니다: {e}")

        # ---------------------------------------------------------
        # 방식 B: 임시 파일 처리 (Fallback) - 메모리 처리 실패 시 사용
        # ---------------------------------------------------------
        # [문법] tempfile: OS의 임시 폴더에 잠깐 쓰고 버릴 파일을 만듭니다.
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            input_path = tmp.name

        segments, info = stt_model.transcribe(
            input_path,
            beam_size=1,
            language="ko",
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.35,
                min_speech_duration_ms=80,
                min_silence_duration_ms=300,
                speech_pad_ms=400,
            ),
            condition_on_previous_text=False
        )
        full_text = "".join([s.text for s in segments]).strip()
        
        if any(h in full_text for h in HALLUCINATIONS) and len(full_text) < 15:
            return {"status": "success", "text": ""}

        return {"status": "success", "text": full_text}
        
    except Exception as e:
        logger.error(f"STT 최종 에러: {e}")
        return {"status": "error", "message": str(e)}
        
    finally:
        # [문법] finally: try 블록에서 에러가 나든 안 나든 "무조건 마지막에 실행"되는 블록입니다.
        # 사용했던 임시 파일을 삭제하여 서버 용량이 꽉 차는 것을 방지합니다.
        if input_path and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except OSError:
                pass