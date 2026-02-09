# ============================================================
# Supertonic 2 한국어 음성 합성 모듈
# ============================================================
# 파일명: tts_supertonic.py
# 모델: Supertonic 2 (Supertone 제작, ONNX 형식)
# 목적: AI 면접관이 질문을 한국어 음성으로 읽어주는 TTS 엔진
# 
# 📌 Supertonic 2 특징:
#    - 한국어(ko), 영어(en), 스페인어, 포르투갈어, 프랑스어 지원
#    - 66M 파라미터, 실시간 167배 빠른 속도
#    - ONNX Runtime 기반 (크로스 플랫폼)
#    - 숫자, 날짜, 통화 기호 등 자연스럽게 처리
#
# 📌 설치 방법:
#    pip install supertonic
#
# 📌 모델 파일 위치:
#    /app/stt_poc/StyleTTS2/onnx/ (사용자가 다운로드한 파일)
#    - duration_predictor.onnx (1.5MB)
#    - text_encoder.onnx (27MB)
#    - vector_estimator.onnx (132MB)
#    - vocoder.onnx (101MB)
#    - tts.json (설정 파일)
#    - unicode_indexer.json (문자 인덱싱)
# ============================================================

# ============================================================
# [Step 0] 필수 라이브러리 임포트
# ============================================================
# os: 파일 경로 및 디렉토리 관리를 위한 표준 라이브러리
import os

# time: 실행 시간 측정용 (성능 분석에 활용)
import time

# logging: 로그 메시지 출력을 위한 표준 라이브러리
#          INFO, WARNING, ERROR 등 레벨별 로깅 지원
import logging

# ABC, abstractmethod: 추상 클래스 정의를 위한 모듈
#                      인터페이스 패턴 구현에 사용
from abc import ABC, abstractmethod

# scipy.io.wavfile: WAV 파일 저장을 위한 라이브러리
#                   supertonic은 numpy 배열로 오디오 반환
import scipy.io.wavfile as wavfile

# ============================================================
# [Step 1] 로거 설정
# ============================================================
# 로거를 설정하여 TTS 작업의 진행 상황과 오류를 기록합니다.
# - logger.info(): 정상 진행 상황
# - logger.warning(): 주의가 필요한 상황
# - logger.error(): 오류 발생 시
logger = logging.getLogger("TTS-Supertonic")
logging.basicConfig(level=logging.INFO)


# ============================================================
# [Step 2] TTS 베이스 클래스 정의 (통합용 인터페이스)
# ============================================================
# 다른 TTS 모델(Qwen3-TTS 등)과 동일한 인터페이스를 사용합니다.
# 이렇게 하면 나중에 TTS 모델을 쉽게 교체할 수 있습니다.

class TTSBase(ABC):
    """
    TTS 모델의 추상 베이스 클래스
    
    모든 TTS 구현체는 이 클래스를 상속받아야 합니다.
    동일한 인터페이스를 제공하여 모델 교체를 용이하게 합니다.
    """
    
    @abstractmethod
    def load_model(self):
        """모델을 로드합니다. 성공 시 True 반환."""
        pass
    
    @abstractmethod
    def generate_speech(self, text: str, output_path: str, 
                       speaker: str = "default", 
                       language: str = "Korean") -> dict:
        """텍스트를 음성으로 변환합니다."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """모델 이름을 반환합니다."""
        pass


# ============================================================
# [Step 3] Supertonic 2 구현 클래스
# ============================================================
# Supertone 회사에서 만든 Supertonic 2 TTS 모델을 사용합니다.
# 
# 💡 주요 특징:
#    - 한국어 공식 지원
#    - ONNX Runtime 기반 (GPU 없이도 빠른 추론)
#    - pip install supertonic 으로 간단 설치
#
# 💡 StyleTTS2와 다른 점:
#    - StyleTTS2: 연구용 PyTorch 모델 (설치 복잡)
#    - Supertonic 2: 상용 ONNX 모델 (설치 간단, 빠름)

class SupertonicTTS(TTSBase):
    """
    Supertonic 2 음성 합성 엔진
    
    🔧 사용법:
        tts = SupertonicTTS()
        tts.load_model()
        result = tts.generate_speech("안녕하세요", "output.wav")
    
    📌 지원 언어:
        - Korean (ko): 한국어 ✅
        - English (en): 영어
        - Spanish (es): 스페인어
        - Portuguese (pt): 포르투갈어
        - French (fr): 프랑스어
    """
    
    # ========================================================
    # [Step 3-1] 싱글톤 패턴을 위한 클래스 변수
    # ========================================================
    # 모델을 한 번만 로드하고 재사용하기 위해 싱글톤 패턴을 사용합니다.
    # GPU 메모리 효율과 로딩 시간 절약을 위한 설계입니다.
    _instance = None
    
    # 모델 파일이 있는 디렉토리 (사용자가 다운로드한 경로)
    MODEL_DIR = "/app/stt_poc/StyleTTS2/onnx"
    
    def __new__(cls):
        """
        싱글톤 패턴 구현
        
        클래스의 인스턴스가 하나만 생성되도록 보장합니다.
        SupertonicTTS()를 여러 번 호출해도 같은 객체를 반환합니다.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        초기화 메서드
        
        이미 초기화된 경우 건너뜁니다 (싱글톤 패턴).
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self.tts = None  # supertonic TTS 엔진 인스턴스
        
    # ========================================================
    # [Step 3-2] 모델 로드 메서드
    # ========================================================
    def load_model(self):
        """
        Supertonic 2 모델을 로드합니다.
        
        동작 과정:
        1. 이미 로드된 경우 건너뜀
        2. supertonic 패키지에서 TTS 클래스 임포트
        3. model_dir 경로에서 ONNX 모델 로드
        4. 모델 초기화 완료
        
        Returns:
            bool: 로드 성공 시 True, 실패 시 False
        """
        # 이미 모델이 로드되어 있으면 건너뜁니다
        if self.tts is not None:
            logger.info("✅ Supertonic 모델이 이미 로드되어 있습니다.")
            return True
            
        try:
            load_start = time.time()
            
            # [Step 3-2-1] supertonic 패키지에서 TTS 클래스 임포트
            # pip install supertonic 으로 설치됩니다
            from supertonic import TTS
            
            # [Step 3-2-2] TTS 엔진 초기화
            # model_dir: ONNX 파일이 있는 디렉토리
            # auto_download: True (필요시 자동 다운로드)
            self.tts = TTS(
                model="supertonic-2",      # Supertonic 2 모델 사용
                auto_download=True         # 자동 다운로드 활성화
            )
            
            load_time = time.time() - load_start
            logger.info(f"✅ Supertonic 2 모델 로드 완료! (소요 시간: {load_time:.2f}초)")
            return True
            
        except ImportError as e:
            # supertonic 패키지가 설치되지 않은 경우
            logger.error(f"❌ supertonic 패키지를 찾을 수 없습니다: {e}")
            logger.error("   해결: pip install supertonic")
            return False
            
        except FileNotFoundError as e:
            # ONNX 모델 파일을 찾을 수 없는 경우
            logger.error(f"❌ 모델 파일을 찾을 수 없습니다: {e}")
            logger.error(f"   확인: {self.MODEL_DIR} 폴더에 ONNX 파일이 있는지 확인하세요")
            return False
            
        except Exception as e:
            # 기타 오류
            logger.error(f"❌ 모델 로드 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ========================================================
    # [Step 3-3] 음성 생성 메서드
    # ========================================================
    def generate_speech(self, text: str, output_path: str, 
                       speaker: str = "default", 
                       language: str = "Korean") -> dict:
        """
        텍스트를 음성으로 변환하여 WAV 파일로 저장합니다.
        
        Args:
            text (str): 변환할 텍스트 (한국어 지원)
            output_path (str): 저장할 WAV 파일 경로
            speaker (str): 화자 (현재 미사용)
            language (str): 언어 ("Korean" 또는 "ko")
            
        Returns:
            dict: 생성 결과
                - success (bool): 성공 여부
                - model (str): 모델 이름
                - output_path (str): 저장된 파일 경로
                - duration_ms (float): 생성 소요 시간 (밀리초)
                - sample_rate (int): 샘플레이트
                
        사용 예시:
            result = tts.generate_speech(
                "안녕하세요. 면접을 시작하겠습니다.",
                "/app/outputs/greeting.wav"
            )
        """
        # [Step 3-3-1] 모델이 로드되지 않았으면 로드
        if self.tts is None:
            if not self.load_model():
                return {"success": False, "error": "모델 로드 실패"}
        
        try:
            gen_start = time.time()
            
            # [Step 3-3-2] 출력 디렉토리 생성
            # 부모 디렉토리가 없으면 자동으로 생성합니다
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # [Step 3-3-3] 언어 코드 변환
            # "Korean" → "ko", "English" → "en"
            lang_code = "ko" if language.lower() in ["korean", "ko"] else "en"
            
            # [Step 3-3-4] 음성 스타일 로드
            # M1~M5: 남성 음성, F1~F5: 여성 음성
            # 면접관은 전문적인 느낌의 M1(남성) 또는 F1(여성) 권장
            voice_style = self.tts.get_voice_style("M1")
            
            # [Step 3-3-5] 음성 생성
            # Supertonic TTS synthesize 메서드 호출
            # 반환값: (audio_array, duration_array)
            audio, duration = self.tts.synthesize(
                text=text,
                voice_style=voice_style,
                total_steps=5,       # 품질 (높을수록 좋지만 느림)
                speed=1.0,           # 속도 (1.0 = 기본)
                lang=lang_code       # "ko" for 한국어
            )
            
            # [Step 3-3-6] WAV 파일로 저장
            # save_audio 메서드 사용 (내장 저장 기능)
            sample_rate = self.tts.sample_rate
            self.tts.save_audio(audio, output_path)
            
            gen_time_ms = (time.time() - gen_start) * 1000
            
            logger.info(f"✅ 음성 생성 완료: {output_path} ({gen_time_ms:.0f}ms)")
            
            return {
                "success": True,
                "model": self.get_model_name(),
                "output_path": output_path,
                "duration_ms": gen_time_ms,
                "sample_rate": sample_rate,
            }
            
        except Exception as e:
            logger.error(f"❌ 음성 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    # ========================================================
    # [Step 3-4] 모델 이름 반환 메서드
    # ========================================================
    def get_model_name(self) -> str:
        """
        모델 이름을 반환합니다.
        
        비교 테스트나 로그에서 어떤 모델을 사용했는지 구분할 때 사용합니다.
        
        Returns:
            str: "Supertonic-2-Korean"
        """
        return "Supertonic-2-Korean"


# ============================================================
# [Step 4] 독립 실행 테스트
# ============================================================
# 이 파일을 직접 실행하면 테스트가 수행됩니다.
# 예: python tts_supertonic.py

if __name__ == "__main__":
    print("=" * 60)
    print("🎙️ Supertonic 2 한국어 음성 합성 테스트")
    print("=" * 60)
    
    # TTS 엔진 인스턴스 생성
    tts = SupertonicTTS()
    
    # 모델 로드
    if not tts.load_model():
        print("❌ 모델 로드 실패. 종료합니다.")
        exit(1)
    
    # 테스트 문장 (한국어)
    test_text = "안녕하세요. 오늘 면접에 참석해 주셔서 대단히 감사합니다. 면접을 시작하겠습니다."
    output_path = "/app/stt_poc/outputs/supertonic_korean_test.wav"
    
    # 음성 생성
    result = tts.generate_speech(
        text=test_text,
        output_path=output_path,
        language="Korean"
    )
    
    # 결과 출력
    if result["success"]:
        print(f"✅ 테스트 성공!")
        print(f"   - 모델: {result['model']}")
        print(f"   - 파일: {result['output_path']}")
        print(f"   - 생성 시간: {result['duration_ms']:.0f}ms")
        print(f"   - 샘플레이트: {result['sample_rate']}Hz")
    else:
        print(f"❌ 테스트 실패: {result['error']}")
    
    print("=" * 60)
