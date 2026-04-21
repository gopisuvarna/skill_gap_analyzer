"""
Skill intelligence scoring.

Builds global importance scores for skills from IT_Job_Roles_Skills.csv using:
  0.40 × semantic IDF    — rare skills score higher
  0.25 × market demand   — frequency across all roles
  0.20 × graph PageRank  — skill co-occurrence network centrality
  0.15 × TF-IDF          — distinctiveness across corpus

Results are cached to apps/documents/data/skill_scores.json on first run.
"""
from __future__ import annotations

import json
import logging
import math
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Set

import networkx as nx
import pandas as pd

logger = logging.getLogger(__name__)

_DATA_DIR   = Path(__file__).resolve().parent.parent.parent.parent / "apps" / "documents" / "data"
_CSV_PATH   = _DATA_DIR / "IT_Job_Roles_Skills.csv"
_CACHE_PATH = _DATA_DIR / "skill_scores.json"

# Singleton — loaded once per process
_SKILL_SCORES: Dict[str, float] | None = None


def _normalize_skills(raw) -> Set[str]:
    parts = raw.split(",") if isinstance(raw, str) else list(raw or [])
    return {s.strip().lower() for s in parts if isinstance(s, str) and s.strip()}


def _minmax(scores: Dict[str, float]) -> Dict[str, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    mn, mx = min(vals), max(vals)
    if math.isclose(mn, mx):
        return dict.fromkeys(scores, 0.0)
    return {k: (v - mn) / (mx - mn) for k, v in scores.items()}


def _semantic_idf(docs: List[Set[str]]) -> Dict[str, float]:
    N = len(docs)
    df: Dict[str, int] = {}
    for d in docs:
        for s in d:
            df[s] = df.get(s, 0) + 1
    return _minmax({s: math.log((N + 1) / (c + 1)) + 1 for s, c in df.items()})


def _market_demand(docs: List[Set[str]]) -> Dict[str, float]:
    total = len(docs)
    demand: Dict[str, int] = {}
    for d in docs:
        for s in d:
            demand[s] = demand.get(s, 0) + 1
    return _minmax({k: v / total for k, v in demand.items()})


def _graph_importance(docs: List[Set[str]]) -> Dict[str, float]:
    g = nx.Graph()
    for d in docs:
        for a, b in combinations(d, 2):
            if g.has_edge(a, b):
                g[a][b]["weight"] += 1
            else:
                g.add_edge(a, b, weight=1)
    if not g.nodes:
        return {}
    pagerank = nx.pagerank(g, weight="weight")
    degree   = nx.degree_centrality(g)
    return _minmax({s: 0.7 * pagerank.get(s, 0) + 0.3 * degree.get(s, 0) for s in g.nodes})


def _tfidf_distinctiveness(docs: List[Set[str]]) -> Dict[str, float]:
    N = len(docs)
    df: Dict[str, int] = {}
    for d in docs:
        for s in d:
            df[s] = df.get(s, 0) + 1
    tfidf: Dict[str, float] = {}
    for d in docs:
        for s in d:
            idf = math.log((N + 1) / (df[s] + 1)) + 1
            tfidf[s] = tfidf.get(s, 0) + idf
    return _minmax(tfidf)


def _compute_skill_scores() -> Dict[str, float]:
    df   = pd.read_csv(_CSV_PATH, encoding="latin1").dropna(subset=["Skills"])
    docs = [d for d in (_normalize_skills(r) for r in df["Skills"]) if d]

    semantic = _semantic_idf(docs)
    demand   = _market_demand(docs)
    graph    = _graph_importance(docs)
    tfidf    = _tfidf_distinctiveness(docs)

    return {
        skill: round(
            0.40 * semantic.get(skill, 0.0)
            + 0.25 * demand.get(skill, 0.0)
            + 0.20 * graph.get(skill, 0.0)
            + 0.15 * tfidf.get(skill, 0.0),
            6,
        )
        for skill in set().union(*docs)
    }


def get_skill_scores() -> Dict[str, float]:
    """Return cached skill scores, loading from disk or computing if needed."""
    global _SKILL_SCORES
    if _SKILL_SCORES is not None:
        return _SKILL_SCORES

    if _CACHE_PATH.exists():
        try:
            with open(_CACHE_PATH, "r") as f:
                _SKILL_SCORES = json.load(f)
            logger.info("Loaded cached skill scores (%d skills)", len(_SKILL_SCORES))
            return _SKILL_SCORES
        except Exception:
            logger.warning("Skill score cache corrupt — recomputing", exc_info=True)

    if not _CSV_PATH.exists():
        logger.warning("IT_Job_Roles_Skills.csv not found — using uniform BM25 weights")
        _SKILL_SCORES = {}
        return _SKILL_SCORES

    logger.info("Computing skill intelligence scores from CSV...")
    _SKILL_SCORES = _compute_skill_scores()

    try:
        with open(_CACHE_PATH, "w") as f:
            json.dump(_SKILL_SCORES, f)
        logger.info("Skill scores cached (%d skills)", len(_SKILL_SCORES))
    except Exception:
        logger.warning("Could not write skill score cache", exc_info=True)

    return _SKILL_SCORES


def skill_importance(token: str) -> float:
    """Return importance score for a skill token. Floor at 0.1 so unknowns still count."""
    return max(0.1, get_skill_scores().get(token.replace("_", " "), 0.0))