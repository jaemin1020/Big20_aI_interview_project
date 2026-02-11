# -*- coding: utf-8 -*-
"""
Backend utilities package
"""
from .interview_helpers import (
    get_candidate_info,
    generate_template_question,
    get_next_stage_name
)
from .interview_scenario import (
    INTERVIEW_STAGES,
    get_stage_by_name,
    get_next_stage,
    get_initial_stages
)

__all__ = [
    "get_candidate_info",
    "generate_template_question",
    "get_next_stage_name",
    "INTERVIEW_STAGES",
    "get_stage_by_name",
    "get_next_stage",
    "get_initial_stages"
]
