from .interview_scenario import *  # 기존 인터페이스 유지 (필요 시)
import os
import sys
import logging
from importlib import import_module

logger = logging.getLogger("ScenarioTransition")

# backend-core의 시나리오 정의를 임포트하기 위한 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
scenario_path = os.path.abspath(os.path.join(BASE_DIR, "../../backend-core/config"))
sys.path.append(scenario_path)

# 기본값 선언 (항상 정의되어 있어야 함)
INTERVIEW_STAGES = []

def get_stage_by_name(stage_name):
    """설명:
        시나리오 단계 정보를 조회하는 함수 (기본값: None)

        Args:
        stage_name: 파라미터 설명.

        Returns:
        반환값 정보.

        생성자: ejm
        생성일자: 2026-02-04
    """
    return None

def get_next_stage(current_stage):
    """설명:
        다음 단계를 조회하는 함수 (기본값: None)

        Args:
        current_stage: 파라미터 설명.

        Returns:
        반환값 정보.

        생성자: ejm
        생성일자: 2026-02-04
    """
    return None

def get_initial_stages():
    """설명:
        초기 단계를 조회하는 함수 (기본값: [])

        Returns:
        반환값 정보.

        생성자: ejm
        생성일자: 2026-02-04
    """
    return []

try:
    # backend-core의 로직을 동적으로 로드 시도
    _mod = import_module("interview_scenario_transition")
    
    # 로드 성공 시 함수 교체
    INTERVIEW_STAGES = getattr(_mod, "INTERVIEW_STAGES", [])
    get_stage_by_name = _mod.get_stage_by_name
    get_next_stage = _mod.get_next_stage
    get_initial_stages = _mod.get_initial_stages

    logger.info(f"✅ Transition scenario loaded from {scenario_path}")

except Exception as e:
    logger.error(f"backend-core transition 시나리오 로드 실패 ({scenario_path}), fallback 사용: {e}")
