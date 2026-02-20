# -*- coding: utf-8 -*-
"""
[단일 소스 관리] 실제 시나리오 정의는 backend-core/config/interview_scenario.py 에서 관리합니다.
이 파일은 backend-core의 파일을 그대로 재사용하기 위한 브릿지입니다.
"""
import sys
import os

# backend-core/config 경로를 우선적으로 추가
_backend_config = "/backend-core"
if _backend_config not in sys.path:
    sys.path.insert(0, _backend_config)

# backend-core 버전에서 모든 심볼 임포트 (단일 소스)
try:
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "backend_interview_scenario",
        "/backend-core/config/interview_scenario.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)

    INTERVIEW_STAGES = _mod.INTERVIEW_STAGES
    get_stage_by_name = _mod.get_stage_by_name
    get_next_stage = _mod.get_next_stage
    get_initial_stages = _mod.get_initial_stages

except Exception as e:
    import logging
    logging.getLogger(__name__).error(f"backend-core 시나리오 로드 실패, fallback 사용: {e}")
    # Fallback: 기본 구조만 정의
    INTERVIEW_STAGES = []
    def get_stage_by_name(stage_name): return None
    def get_next_stage(current_stage): return None
    def get_initial_stages(): return []
