# -*- coding: utf-8 -*-
"""
AI Worker configuration package
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
