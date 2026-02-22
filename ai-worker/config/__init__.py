# -*- coding: utf-8 -*-
"""
AI Worker configuration package
[단일 소스] 실제 시나리오는 backend-core/config/ 에서 관리합니다.
"""
from .interview_scenario import (
    INTERVIEW_STAGES,
    get_stage_by_name,
    get_next_stage,
    get_initial_stages
)

__all__ = [
    "INTERVIEW_STAGES",
    "get_stage_by_name",
    "get_next_stage",
    "get_initial_stages"
]
