"""
BM25 similarity functions for role matching.

Two variants:
  bm25_raw               — pure BM25, no intelligence weighting
  bm25_intelligence      — BM25 weighted by global skill importance scores
"""
from __future__ import annotations

from typing import Dict, List

from .skill_intelligence import skill_importance

BM25_K1 = 1.5
BM25_B  = 0.75

_PERFECT_TERM = (BM25_K1 + 1) / (1 + BM25_K1 * (1 - BM25_B + BM25_B))


def tokenise(skills: List[str]) -> List[str]:
    """Lowercase and underscore-join skill names for BM25 token matching."""
    return [s.lower().replace(" ", "_") for s in skills if s]


def _bm25_term(freq: int, dl: int, avg_dl: float = 0.0) -> float:
    effective_avg = avg_dl if avg_dl > 0 else dl
    num = freq * (BM25_K1 + 1)
    den = freq + BM25_K1 * (1 - BM25_B + BM25_B * (dl / effective_avg))
    return num / den


def bm25_raw(query_tokens: List[str], doc_tokens: List[str]) -> float:
    """Pure BM25 similarity between query and document token lists. Returns 0-1."""
    if not query_tokens or not doc_tokens:
        return 0.0
    dl = len(doc_tokens)
    tf: Dict[str, int] = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1
    total = sum(_bm25_term(tf[qt], dl) for qt in query_tokens if qt in tf)
    max_p = _PERFECT_TERM * len(query_tokens)
    return max(0.0, min(1.0, total / max_p)) if max_p else 0.0


def bm25_intelligence(
    user_skill_names: List[str],
    role_skill_names: List[str],
) -> float:
    """
    BM25 where each matched term is weighted by its global market importance.
    Returns 0-1.
    """
    if not user_skill_names or not role_skill_names:
        return 0.0

    query_tokens = tokenise(user_skill_names)
    doc_tokens   = tokenise(role_skill_names)
    dl = len(doc_tokens)

    tf: Dict[str, int] = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1

    total_score  = 0.0
    max_possible = 0.0

    for qt in query_tokens:
        w = skill_importance(qt)
        max_possible += _PERFECT_TERM * w
        if qt in tf:
            total_score += w * _bm25_term(tf[qt], dl)

    return max(0.0, min(1.0, total_score / max_possible)) if max_possible else 0.0