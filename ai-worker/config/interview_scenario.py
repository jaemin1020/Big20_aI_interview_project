# -*- coding: utf-8 -*-
"""
[단일 소스 관리] 실제 시나리오 정의는 backend-core/config/interview_scenario.py 에서 관리합니다.
이 파일은 backend-core의 파일을 그대로 재사용하기 위한 브릿지입니다.
"""
import sys
import os
import importlib.util
import logging

logger = logging.getLogger(__name__)

# 경로 동적 로드 (Docker vs Local)
docker_path = "/backend-core/config/interview_scenario.py"
local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend-core", "config", "interview_scenario.py"))
scenario_path = docker_path if os.path.exists(docker_path) else local_path

# backend-core 버전에서 모든 심볼 임포트 (단일 소스)
try:
    if not os.path.exists(scenario_path):
        raise FileNotFoundError(f"Scenario file not found at {scenario_path}")
        
    _spec = importlib.util.spec_from_file_location("backend_interview_scenario", scenario_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)

    INTERVIEW_STAGES = _mod.INTERVIEW_STAGES
    get_stage_by_name = _mod.get_stage_by_name
    get_next_stage = _mod.get_next_stage
    get_initial_stages = _mod.get_initial_stages
    
    logger.info(f"✅ Standard scenario loaded from {scenario_path}")

except Exception as e:
    logger.error(f"backend-core 시나리오 로드 실패 ({scenario_path}), fallback 사용: {e}")
    # Fallback: 기본 구조만 정의
    INTERVIEW_STAGES = []
    def get_stage_by_name(stage_name): return None
    def get_next_stage(current_stage): return None
    def get_initial_stages(): return []
