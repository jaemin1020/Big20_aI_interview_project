# -*- coding: utf-8 -*-
"""
[단일 소스 관리] 실제 시나리오 정의는 backend-core/config/interview_scenario_transition.py 에서 관리합니다.
이 파일은 backend-core의 파일을 그대로 재사용하기 위한 브릿지입니다.
"""
import sys
import importlib.util
import logging

logger = logging.getLogger(__name__)

# backend-core 버전에서 모든 심볼 임포트 (단일 소스)
try:
    _spec = importlib.util.spec_from_file_location(
        "backend_interview_scenario_transition",
        "/backend-core/config/interview_scenario_transition.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)

    INTERVIEW_STAGES = _mod.INTERVIEW_STAGES
    get_stage_by_name = _mod.get_stage_by_name
    get_next_stage = _mod.get_next_stage
    get_initial_stages = _mod.get_initial_stages

    logger.info("✅ Transition scenario loaded from backend-core (single source)")

except Exception as e:
    logger.error(f"backend-core transition 시나리오 로드 실패, fallback 사용: {e}")
    INTERVIEW_STAGES = []
    def get_stage_by_name(stage_name): return None
    def get_next_stage(current_stage): return None
    def get_initial_stages(): return []
