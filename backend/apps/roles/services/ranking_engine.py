"""
Re-ranking engine.

FINAL SCORE = 0.4 × skill_coverage
            + 0.3 × bm25_intelligence
            + 0.2 × importance_weight
            + 0.1 × bm25_raw
"""
from __future__ import annotations

from typing import Any, Dict, List

from .scoring    import skill_coverage, importance_weight
from .similarity import bm25_raw, bm25_intelligence, tokenise


def re_rank(
    candidate_roles: List[Dict[str, Any]],
    user_skill_ids: set,
    user_skill_names: List[str],
    role_skills_map: Dict[str, List[Dict]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Re-rank FAISS top-30 candidates → return top_k with scores.

    Formula:
        0.4 × skill_coverage     — fraction of role skills user has
        0.3 × bm25_intelligence  — BM25 weighted by market importance
        0.2 × importance_weight  — DB importance of matched skills
        0.1 × bm25_raw           — pure BM25 baseline
    """
    scored = []

    for role in candidate_roles:
        rid              = str(role.get("id", ""))
        rs_list          = role_skills_map.get(rid, [])
        role_skill_ids   = {str(s["skill_id"]) for s in rs_list}
        role_skill_names = [s.get("skill_name", "") for s in rs_list]
        role_weights     = {str(s["skill_id"]): s.get("importance_weight", 1.0) for s in rs_list}

        cov      = skill_coverage(user_skill_ids, role_skill_ids)
        imp      = importance_weight(user_skill_ids, role_weights)
        bm25_si  = bm25_intelligence(user_skill_names, role_skill_names)
        bm25_r   = bm25_raw(tokenise(user_skill_names), tokenise(role_skill_names))

        final = 0.4 * cov + 0.3 * bm25_si + 0.2 * imp + 0.1 * bm25_r

        scored.append({
            **role,
            "match_score":      round(final,   4),
            "skill_coverage":   round(cov,     4),
            "importance_score": round(imp,     4),
            "bm25_score":       round(bm25_si, 4),
            "bm25_raw_score":   round(bm25_r,  4),
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:top_k]