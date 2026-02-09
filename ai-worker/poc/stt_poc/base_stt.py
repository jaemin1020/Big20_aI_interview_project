# 1단계: 필요한 라이브러리 불러오기
from abc import ABC, abstractmethod  # 추상 클래스 생성을 위한 모듈
from typing import Dict, Any        # 데이터 타입 정의를 위한 모듈

# 2단계: 기본(부모) 클래스 정의
class BaseSTT(ABC):
    """
    모든 STT(음성 인식) 모델이 상속받아야 할 기본 클래스입니다.
    이 클래스는 공통된 구조(인터페이스)를 정의합니다.
    """

    # 3단계: 클래스 초기화 함수 정의
    def __init__(self, model_name: str, config: Dict[str, Any] = None):
        """
        모델을 초기화하는 함수입니다.
        
        매개변수:
        - model_name: 사용할 모델의 이름 (예: "large-v3", "nova-2")
        - config: 모델 설정값들을 담은 딕셔너리 (옵션)
        """
        self.model_name = model_name
        self.config = config or {}

    # 4단계: 음성 인식(Transcribe) 추상 메서드 정의
    @abstractmethod
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        오디오 파일을 입력받아 텍스트로 변환하는 함수입니다.
        모든 자식 클래스는 이 함수를 반드시 구현해야 합니다.
        
        매개변수:
        - audio_path: 분석할 오디오 파일의 경로 (.wav)
        
        반환값:
        - text: 변환된 텍스트
        - latency: 걸린 시간 (초)
        - error: 에러 메시지 (없으면 None)
        """
        pass
