"""
Individual scoring signals for role matching.

Signal 1: skill_coverage      — fraction of role skills the user has
Signal 2: importance_weight   — avg DB importance of matched skills
"""
from __future__ import annotations

from typing import Dict


def skill_coverage(user_skill_ids: set, role_skill_ids: set) -> float:
    """matched / total role skills. Returns 0-1."""
    if not role_skill_ids:
        return 0.0
    return len(user_skill_ids & role_skill_ids) / len(role_skill_ids)


def importance_weight(
    user_skill_ids: set,
    role_skill_weights: Dict[str, float],
) -> float:
    """Average DB importance_weight of matched skills. Returns 0-1."""
    matched = [role_skill_weights[sid] for sid in user_skill_ids if sid in role_skill_weights]
    return sum(matched) / len(matched) if matched else 0.0