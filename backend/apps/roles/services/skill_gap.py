"""
Skill gap analysis.
Skill Gap = Role Skills - User Skills
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def compute_skill_gap(
    user_skill_ids: set,
    role_skill_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute the delta between a user's skills and a role's required skills.

    Args:
        user_skill_ids:   set of skill UUID strings the user has
        role_skill_list:  list of {skill_id, skill_name, importance_weight}
                          from RoleSkill DB rows

    Returns:
        missing_skills      — names of skills user is missing
        coverage_percent    — % of role skills the user has
        learning_priority   — missing skills sorted by importance (highest first)
        matched_skills      — names of skills user already has
        match_score         — same as coverage_percent (0-100)
        total_required      — total skills the role requires
        matched_count       — how many the user has
    """
    if not role_skill_list:
        return {
            'missing_skills':    [],
            'coverage_percent':  100.0,
            'learning_priority': [],
            'matched_skills':    [],
            'match_score':       100.0,
            'total_required':    0,
            'matched_count':     0,
        }

    logger.info(
        "compute_skill_gap: %d user skills vs %d role skills",
        len(user_skill_ids), len(role_skill_list),
    )

    role_skill_ids = {str(s['skill_id']) for s in role_skill_list}

    missing = [s for s in role_skill_list if str(s['skill_id']) not in user_skill_ids]
    matched = [s for s in role_skill_list if str(s['skill_id']) in user_skill_ids]

    coverage = (len(role_skill_ids) - len(missing)) / len(role_skill_ids) * 100

    learning_priority = sorted(
        [
            {
                'skill_id':   s['skill_id'],
                'skill_name': s.get('skill_name', ''),
                'importance': s.get('importance_weight', 0.5),
            }
            for s in missing
        ],
        key=lambda x: x['importance'],
        reverse=True,
    )

    return {
        'missing_skills':    [s.get('skill_name', '') for s in missing],
        'coverage_percent':  round(coverage, 2),
        'learning_priority': learning_priority,
        'matched_skills':    [s.get('skill_name', '') for s in matched],
        'match_score':       round(coverage, 2),
        'total_required':    len(role_skill_ids),
        'matched_count':     len(matched),
    }