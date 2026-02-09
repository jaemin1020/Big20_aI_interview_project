# ============================================================
# StyleTTS2 한국어 음성 합성 모듈 (pip 패키지 버전)
# ============================================================
# 파일명: tts_styletts2.py
# 모델: styletts2 (PyPI 패키지)
# 목적: AI 면접관이 질문을 음성으로 읽어주는 TTS 엔진 (비교용)
# ============================================================

# ============================================================
# [Step 0] 필수 라이브러리 임포트
# ============================================================
import os  # os: 파일 경로 및 디렉토리 관리
import time  # time: 실행 시간 측정용
import logging  # logging: 로그 메시지 출력을 위한 표준 라이브러리
from abc import ABC, abstractmethod  # ABC: 추상 클래스 정의를 위한 모듈

# ============================================================
# [Step 0-1] PyTorch 호환성 패치 (중요!)
# ============================================================
# PyTorch 2.6+ 에서는 torch.load의 weights_only 기본값이 True로 변경되어
# 오래된 체크포인트 로딩 시 WeightsUnpickler error가 발생합니다.
# 신뢰할 수 있는 출처의 모델이므로 weights_only=False를 강제 적용합니다.
import torch
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

# ============================================================
# [Step 1] 로거 설정
# ============================================================

# 로거를 설정하여 TTS 작업의 진행 상황과 오류를 기록합니다.
logger = logging.getLogger("TTS-StyleTTS2")
logging.basicConfig(level=logging.INFO)

# ============================================================
# [Step 2] TTS 베이스 클래스 정의 (통합용 인터페이스)
# ============================================================
# Qwen3-TTS와 동일한 인터페이스를 사용합니다.

class TTSBase(ABC):
    """TTS 모델의 추상 베이스 클래스"""
    
    @abstractmethod
    def load_model(self):
        pass
    
    @abstractmethod
    def generate_speech(self, text: str, output_path: str, speaker: str = "default", language: str = "Korean") -> dict:
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        pass


# ============================================================
# [Step 3] StyleTTS2 구현 클래스 (pip 패키지 버전)
# ============================================================
# pip install styletts2로 설치된 공식 PyPI 패키지를 사용합니다.
# 
# 설치: pip install styletts2
# 참고: https://pypi.org/project/styletts2/
# 
# 주의: 이 패키지는 영어 모델(LibriTTS)을 기본으로 사용합니다.
#       한국어는 지원되지 않으므로 영어 테스트용으로만 사용합니다.

class StyleTTS2(TTSBase):
    """
    StyleTTS2 음성 합성 엔진 (pip 패키지 버전)
    
    특징:
    - 설치: pip install styletts2 (간단!)
    - 기본 모델: LibriTTS (영어)
    - 자동 모델 다운로드: 처음 실행 시 Hugging Face에서 자동 다운로드
    - Voice Cloning: 참조 음성을 제공하면 해당 목소리 스타일로 합성
    
    한계:
    - 한국어 미지원 (영어만 가능)
    - 음질 비교용으로만 사용
    """
    
    # 싱글톤 패턴을 위한 클래스 변수
    _instance = None
    
    def __new__(cls):
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """초기화 메서드"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self.model = None
        
    def load_model(self):
        """
        StyleTTS2 모델을 로드합니다.
        
        pip 패키지는 처음 실행 시 자동으로 Hugging Face에서
        LibriTTS 체크포인트를 다운로드합니다.
        
        Returns:
            bool: 로드 성공 여부
        """
        if self.model is not None:
            logger.info("✅ StyleTTS2 모델이 이미 로드되어 있습니다.")
            return True
            
        try:
            load_start = time.time()
            
            # [Step 3-1] styletts2 패키지에서 tts 모듈 임포트
            from styletts2 import tts
            
            # [Step 3-2] StyleTTS2 모델 초기화
            # 경로를 지정하지 않으면 자동으로 기본 체크포인트 다운로드
            self.model = tts.StyleTTS2()
            
            load_time = time.time() - load_start
            logger.info(f"✅ StyleTTS2 모델 로드 완료! (소요 시간: {load_time:.2f}초)")
            return True
            
        except ImportError as e:
            logger.error(f"❌ styletts2 패키지를 찾을 수 없습니다: {e}")
            logger.error("   해결: pip install styletts2")
            return False
            
        except Exception as e:
            logger.error(f"❌ 모델 로드 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_speech(self, text: str, output_path: str, speaker: str = "default", language: str = "Korean") -> dict:
        """
        텍스트를 음성으로 변환하여 WAV 파일로 저장합니다.
        
        주의: StyleTTS2 pip 패키지는 영어만 지원합니다.
              한국어 텍스트를 넣어도 영어 발음으로 읽습니다.
        
        Args:
            text (str): 변환할 텍스트 (영어 권장)
            output_path (str): 저장할 파일 경로
            speaker (str): 미사용
            language (str): 미사용 (영어만 지원)
            
        Returns:
            dict: 생성 결과
        """
        if self.model is None:
            if not self.load_model():
                return {"success": False, "error": "모델 로드 실패"}
        
        try:
            gen_start = time.time()
            
            # [Step 4-1] 출력 디렉토리 생성
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # [Step 4-2] 음성 생성
            # inference 함수는 텍스트를 받아 음성을 생성합니다.
            # output_wav_file을 지정하면 자동으로 파일로 저장됩니다.
            audio_data = self.model.inference(
                text=text,
                output_wav_file=output_path,
                diffusion_steps=5,  # 생성 품질 (높을수록 좋지만 느림)
                alpha=0.3,  # 텍스트 vs 타겟 음성 스타일 비율 (timbre)
                beta=0.7,   # 텍스트 vs 타겟 음성 스타일 비율 (prosody)
            )
            
            gen_time_ms = (time.time() - gen_start) * 1000
            
            logger.info(f"✅ 음성 생성 완료: {output_path} ({gen_time_ms:.0f}ms)")
            
            return {
                "success": True,
                "model": self.get_model_name(),
                "output_path": output_path,
                "duration_ms": gen_time_ms,
                "sample_rate": 24000,  # StyleTTS2 기본값
            }
            
        except Exception as e:
            logger.error(f"❌ 음성 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def get_model_name(self) -> str:
        """모델 이름 반환"""
        return "StyleTTS2-pip-LibriTTS"


# ============================================================
# [Step 5] 독립 실행 테스트
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🎙️ StyleTTS2 (pip 패키지) 음성 합성 테스트")
    print("=" * 60)
    
    tts = StyleTTS2()
    
    if not tts.load_model():
        print("❌ 모델 로드 실패. 종료합니다.")
        exit(1)
    
    # 영어 테스트 (한국어 미지원)
    test_text = "Hello, thank you for joining us today. Let's begin the interview."
    output_path = "/app/stt_poc/outputs/styletts2_pip_test.wav"
    
    result = tts.generate_speech(
        text=test_text,
        output_path=output_path,
    )
    
    if result["success"]:
        print(f"✅ 테스트 성공!")
        print(f"   - 모델: {result['model']}")
        print(f"   - 파일: {result['output_path']}")
        print(f"   - 생성 시간: {result['duration_ms']:.0f}ms")
    else:
        print(f"❌ 테스트 실패: {result['error']}")
    
    print("=" * 60)
