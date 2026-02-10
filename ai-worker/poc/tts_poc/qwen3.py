import logging
import time
import os
import soundfile as sf
import numpy as np
import torch
import sys

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TTS-Service")

# 전역 변수로 모델 캐싱
TTS_MODEL = None
IS_MOCK_MODE = False

def get_tts_model():
    """Import 시도 후 실패하면 Mock 모드로 전환"""
    global TTS_MODEL, IS_MOCK_MODE
    
    if TTS_MODEL is None:
        try:
            logger.info("⏳ [CYJ-Test] Qwen3-TTS 모델 로딩 시작... (GPU)")
            from qwen_tts import Qwen3TTSModel
            
            load_start = time.time()
            TTS_MODEL = Qwen3TTSModel.from_pretrained(
                "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
                device_map="cuda:0", 
                dtype=torch.bfloat16,
            )
            logger.info(f"✅ 모델 로드 완료! (소요 시간: {time.time() - load_start:.2f}초)")
        except ImportError:
            logger.error("❌ 'qwen_tts' 라이브러리가 설치되지 않았습니다. (Mock 모드 자동 전환 실패 - 설치 필요)")
            raise
        except Exception as e:
            logger.error(f"❌ 모델 로드 중 오류: {e}")
            raise
            
    return TTS_MODEL

def generate_voice_file(text: str, output_path: str = None):
    """
    텍스트 -> 음성 파일 생성 (Mock 지원)
    """
    global IS_MOCK_MODE
    get_tts_model() # 모델 상태 확인
    
    try:
        if not output_path:
            save_dir = os.path.join(os.path.dirname(__file__), "outputs")
            os.makedirs(save_dir, exist_ok=True)
            output_path = os.path.join(save_dir, f"tts_{int(time.time())}.wav")
        else:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
        logger.info(f"🎙️ 음성 변환 요청: '{text[:20]}...'")
        
        if IS_MOCK_MODE:
             # 더미 오디오
             pass
        else:
            wavs, sr = TTS_MODEL.generate_custom_voice(
                text=text,
                language="Korean",
                speaker="Vivian",
                instruct="매우 부드롭고 친절한 면접관의 어조로 천천히 또박또박 말씀해 주세요.",
            )
            
            sf.write(output_path, wavs[0], sr)
            logger.info(f"💾 파일 저장 완료: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"❌ TTS 생성 에러: {e}")
        return None
