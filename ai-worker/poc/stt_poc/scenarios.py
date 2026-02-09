from dataclasses import dataclass  # 데이터 클래스 데코레이터 임포트
from typing import List, Optional  # 타입 힌팅 임포트

@dataclass
class Scenario:
    """테스트 시나리오 정보를 담는 데이터 클래스입니다."""
    name: str # 시나리오 이름 (예: "Normal")
    description: str # 시나리오 설명 (예: "일반적인 질문 답변 상황")
    audio_file: str # 테스트에 사용할 오디오 파일 경로 (data 폴더 기준 상대 경로)
    ground_truth: str # 해당 오디오의 정답 텍스트 (WER/CER 계산용)
    expected_result_type: str = "text" # 예상 결과 타입 (기본값 "text")

# poc_methodology.md 문서에 기반한 5가지 검증 시나리오 정의
# 주의: 실제로 테스트하려면 'data' 폴더에 해당 .wav 파일들이 존재해야 합니다.
SCENARIOS = [
    Scenario(
        name="Normal",
        description="정상 시나리오: 질문 -> 답변 흐름",
        audio_file="normal_answer.wav",
        ground_truth="This is a sample answer to the interview question." # 실제 오디오 내용에 맞춰 수정 필요
    ),
    Scenario(
        name="Short",
        description="단답 시나리오: 네/아니오/모르겠습니다",
        audio_file="short_answer.wav",
        ground_truth="Yes."
    ),
    Scenario(
        name="Irrelevant",
        description="무관 답변: 질문과 관계없는 엉뚱한 답변",
        audio_file="irrelevant_answer.wav",
        ground_truth="I had a sandwich for lunch today."
    ),
    Scenario(
        name="Long",
        description="장문 답변: 1분 이상 이어지는 답변",
        audio_file="long_answer.wav",
        ground_truth="This is a very long answer that continues for more than one minute..." # 긴 텍스트 필요
    ),
    Scenario(
        name="Exception_Noise",
        description="예외 상황: 잡음이 섞인 환경에서의 발화",
        audio_file="noisy_input.wav",
        ground_truth="I can still hear you despite the noise."
    ),
]
