import os
import sys
import logging
from importlib import import_module

logger = logging.getLogger("Scenario")

# backend-core의 시나리오 정의를 임포트하기 위한 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
scenario_path = os.path.abspath(os.path.join(BASE_DIR, "../../backend-core/config"))
sys.path.append(scenario_path)

# 기본값 선언 (항상 정의되어 있어야 함)
INTERVIEW_STAGES = []

def get_stage_by_name(stage_name):
    """설명:
        시나리오 단계 이름을 입력받아 해당 단계의 정보를 반환하는 안전 장치 함수.
        파일 로드 실패 시 시스템 중단을 방지하기 위해 사용됨.

    Args:
        stage_name (str): 조회할 스테이지 이름.

    Returns:
        None: 폴백 상태이므로 항상 None 반환.

    생성자: ejm
    생성일자: 2026-02-04
    """
    return None

def get_next_stage(current_stage):
    """설명:
        현재 단계의 다음 단계 정보를 조회하는 안전 장치 함수.
        파일 로드 실패 시 시스템 중단을 방지하기 위해 사용됨.

    Args:
        current_stage (str): 현재 스테이지 이름.

    Returns:
        None: 폴백 상태이므로 항상 None 반환.

    생성자: ejm
    생성일자: 2026-02-04
    """
    return None

def get_initial_stages():
    """설명:
        면접 시작 시 필요한 초기 스테이지 목록을 반환하는 안전 장치 함수.
        파일 로드 실패 시 시스템 중단을 방지하기 위해 사용됨.

    Returns:
        list: 빈 리스트([]) 반환.

    생성자: ejm
    생성일자: 2026-02-04
    """
    return []

try:
    # backend-core의 로직을 동적으로 로드 시도
    # Note: interview_scenario_transition 과 달리 "interview_scenario" 파일이 backend-core/config 에 있는지 확인 필요
    # 보통 transition 버전을 주로 사용하지만 표준 버전도 로드 시도
    _mod = import_module("interview_scenario")
    
    # 로드 성공 시 함수 교체
    INTERVIEW_STAGES = getattr(_mod, "INTERVIEW_STAGES", [])
    get_stage_by_name = _mod.get_stage_by_name
    get_next_stage = _mod.get_next_stage
    get_initial_stages = _mod.get_initial_stages

    logger.info(f"✅ Standard scenario loaded from {scenario_path}")

except Exception as e:
    logger.error(f"backend-core 시나리오 로드 실패 ({scenario_path}), fallback 사용: {e}")
