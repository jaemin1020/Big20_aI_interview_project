# ============================================================
# Qwen3-TTS 한국어 음성 합성 모듈
# ============================================================
# 파일명: tts_qwen3.py
# 모델: Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
# 목적: AI 면접관이 질문을 음성으로 읽어주는 TTS 엔진
# ============================================================

# ============================================================
# [Step 0] 필수 라이브러리 임포트
# ============================================================
import torch  # PyTorch: GPU 가속 및 텐서 연산을 위한 딥러닝 프레임워크
import soundfile as sf  # soundfile: WAV 오디오 파일 읽기/쓰기를 위한 라이브러리
import os  # os: 파일 경로 및 디렉토리 관리
import time  # time: 실행 시간 측정용
import logging  # logging: 로그 메시지 출력을 위한 표준 라이브러리
from abc import ABC, abstractmethod  # ABC: 추상 클래스 정의를 위한 모듈

# ============================================================
# [Step 1] 로거 설정
# ============================================================
# 로거를 설정하여 TTS 작업의 진행 상황과 오류를 기록합니다.
logger = logging.getLogger("TTS-Qwen3")
logging.basicConfig(level=logging.INFO)

# ============================================================
# [Step 2] TTS 베이스 클래스 정의 (통합용 인터페이스)
# ============================================================
# 모든 TTS 모델이 공통으로 구현해야 하는 인터페이스입니다.
# 이 클래스를 상속받아 Qwen3-TTS, StyleTTS2 등 다양한 모델을 구현합니다.
# 통합 시, 어떤 TTS 모델을 사용하든 동일한 방식으로 호출할 수 있습니다.

class TTSBase(ABC):
    """
    TTS 모델의 추상 베이스 클래스
    
    모든 TTS 구현체는 이 클래스를 상속받아 다음 메서드를 구현해야 합니다:
    - load_model(): 모델을 메모리에 로드
    - generate_speech(): 텍스트를 음성으로 변환
    - get_model_name(): 모델 이름 반환
    """
    
    @abstractmethod
    def load_model(self):
        """모델을 로드하는 추상 메서드"""
        pass
    
    @abstractmethod
    def generate_speech(self, text: str, output_path: str, speaker: str = "default", language: str = "Korean") -> dict:
        """
        텍스트를 음성으로 변환하는 추상 메서드
        
        Args:
            text: 변환할 텍스트
            output_path: 저장할 WAV 파일 경로
            speaker: 화자 (목소리) 선택
            language: 언어 선택
            
        Returns:
            dict: 생성 결과 (성공 여부, 생성 시간, 파일 경로 등)
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """모델 이름을 반환하는 추상 메서드"""
        pass


# ============================================================
# [Step 3] Qwen3-TTS 구현 클래스
# ============================================================
# Alibaba의 Qwen3-TTS 모델을 사용한 TTS 구현체입니다.
# 한국어를 포함한 10개 언어를 공식 지원합니다.

class Qwen3TTS(TTSBase):
    """
    Qwen3-TTS 음성 합성 엔진
    
    특징:
    - 모델: Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
    - 지원 언어: 한국어, 영어, 중국어, 일본어 등 10개
    - 지원 화자: Vivian, Ethan 등 9개 프리미엄 음색
    - 감정/스타일 조절: 자연어 지시로 톤 변경 가능
    """
    
    # 싱글톤 패턴을 위한 클래스 변수
    _instance = None
    _model = None
    
    def __new__(cls):
        """
        싱글톤 패턴 구현
        - 모델이 매번 새로 로드되지 않도록 합니다.
        - GPU 메모리를 효율적으로 사용합니다.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        초기화 메서드
        - 이미 초기화되었다면 다시 초기화하지 않습니다.
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self.model = None
        self.model_id = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
        
    def load_model(self):
        """
        Qwen3-TTS 모델을 GPU에 로드합니다.
        
        프로세스:
        1. qwen_tts 라이브러리에서 Qwen3TTSModel 임포트
        2. Hugging Face에서 모델 가중치 다운로드 (최초 1회)
        3. GPU 메모리에 모델 로드 (bfloat16 정밀도)
        
        Returns:
            bool: 로드 성공 여부
        """
        if self.model is not None:
            logger.info("✅ 모델이 이미 로드되어 있습니다.")
            return True
            
        try:
            # [Step 3-1] qwen_tts 라이브러리 임포트
            # 이 라이브러리는 pip install qwen-tts로 설치됩니다.
            from qwen_tts import Qwen3TTSModel
            logger.info("🔄 Qwen3-TTS 모델 로딩 시작...")
            
            load_start = time.time()
            
            # [Step 3-2] Hugging Face에서 모델 로드
            # - device_map="cuda:0": 첫 번째 GPU 사용
            # - dtype=torch.bfloat16: 메모리 효율을 위해 16비트 정밀도 사용
            self.model = Qwen3TTSModel.from_pretrained(
                self.model_id,  # Hugging Face 모델 ID
                device_map="cuda:0",  # GPU 디바이스 지정
                dtype=torch.bfloat16,  # 메모리 절약을 위한 데이터 타입
            )
            
            load_time = time.time() - load_start
            logger.info(f"✅ Qwen3-TTS 모델 로드 완료! (소요 시간: {load_time:.2f}초)")
            return True
            
        except ImportError as e:
            # [에러 처리] 라이브러리 미설치 시
            logger.error(f"❌ qwen_tts 라이브러리를 찾을 수 없습니다: {e}")
            logger.error("   해결: pip install qwen-tts 실행")
            return False
            
        except Exception as e:
            # [에러 처리] 기타 오류 (GPU 메모리 부족 등)
            logger.error(f"❌ 모델 로드 실패: {e}")
            return False
    
    def generate_speech(self, text: str, output_path: str, speaker: str = "Vivian", language: str = "Korean") -> dict:
        """
        텍스트를 음성으로 변환하여 WAV 파일로 저장합니다.
        
        Args:
            text (str): 변환할 텍스트 (예: "안녕하세요, 면접을 시작하겠습니다.")
            output_path (str): 저장할 파일 경로 (예: "/app/output/question_1.wav")
            speaker (str): 화자 선택 ("Vivian", "Ethan" 등)
            language (str): 언어 ("Korean", "English", "Chinese" 등)
            
        Returns:
            dict: {
                "success": bool,        # 성공 여부
                "model": str,           # 사용된 모델명
                "output_path": str,     # 저장된 파일 경로
                "duration_ms": float,   # 생성 소요 시간 (밀리초)
                "sample_rate": int,     # 샘플링 레이트
                "error": str (optional) # 에러 메시지 (실패 시)
            }
        """
        # [Step 4-1] 모델 로드 확인
        if self.model is None:
            if not self.load_model():
                return {"success": False, "error": "모델 로드 실패"}
        
        try:
            gen_start = time.time()
            
            # [Step 4-2] 음성 생성
            # - text: 변환할 텍스트
            # - language: 발화 언어 (한국어, 영어 등)
            # - speaker: 목소리 톤 (Vivian: 여성, Ethan: 남성)
            # - instruct: 발화 스타일 지시 (매우 혁신적인 기능!)
            wavs, sr = self.model.generate_custom_voice(
                text=text,
                language=language,
                speaker=speaker,
                instruct="부드럽고 전문적인 면접관 어조로 말씀해 주세요.",  # 스타일 지시
            )
            
            # [Step 4-3] 파일 저장
            # - wavs[0]: 생성된 오디오 데이터 (NumPy 배열)
            # - sr: 샘플링 레이트 (보통 24000Hz)
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            sf.write(output_path, wavs[0], sr)
            
            gen_time_ms = (time.time() - gen_start) * 1000
            
            logger.info(f"✅ 음성 생성 완료: {output_path} ({gen_time_ms:.0f}ms)")
            
            return {
                "success": True,
                "model": self.get_model_name(),
                "output_path": output_path,
                "duration_ms": gen_time_ms,
                "sample_rate": sr,
            }
            
        except Exception as e:
            logger.error(f"❌ 음성 생성 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def get_model_name(self) -> str:
        """모델 이름 반환"""
        return "Qwen3-TTS-12Hz-0.6B-CustomVoice"


# ============================================================
# [Step 5] 독립 실행 테스트
# ============================================================
# 이 파일을 직접 실행하면 테스트가 수행됩니다.
# 통합 시에는 이 부분이 실행되지 않습니다.

if __name__ == "__main__":
    print("=" * 60)
    print("🎙️ Qwen3-TTS 한국어 음성 합성 테스트")
    print("=" * 60)
    
    # [테스트 1] TTS 엔진 초기화
    tts = Qwen3TTS()
    
    # [테스트 2] 모델 로드
    if not tts.load_model():
        print("❌ 모델 로드 실패. 종료합니다.")
        exit(1)
    
    # [테스트 3] 한국어 음성 생성
    test_text = "안녕하세요. 오늘 면접에 참석해 주셔서 대단히 감사합니다. 편안한 마음으로 시작해 볼까요?"
    output_path = "/app/stt_poc/outputs/qwen3_test_output.wav"
    
    result = tts.generate_speech(
        text=test_text,
        output_path=output_path,
        speaker="Vivian",
        language="Korean"
    )
    
    # [테스트 4] 결과 출력
    if result["success"]:
        print(f"✅ 테스트 성공!")
        print(f"   - 모델: {result['model']}")
        print(f"   - 파일: {result['output_path']}")
        print(f"   - 생성 시간: {result['duration_ms']:.0f}ms")
        print(f"   - 샘플 레이트: {result['sample_rate']}Hz")
    else:
        print(f"❌ 테스트 실패: {result['error']}")
    
    print("=" * 60)
