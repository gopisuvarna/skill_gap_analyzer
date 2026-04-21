"""
Backwards-compatible re-export.

All existing imports of the form:
    from apps.roles.services.ranking import re_rank, compute_skill_coverage, ...
continue to work without any changes elsewhere in the codebase.
"""
from .ranking_engine    import re_rank                          # noqa: F401
from .scoring           import skill_coverage as compute_skill_coverage   # noqa: F401
from .scoring           import importance_weight as compute_importance_weight  # noqa: F401
from .similarity        import bm25_raw as _bm25_raw            # noqa: F401
from .similarity        import bm25_intelligence as compute_bm25_intelligence_score  # noqa: F401
from .similarity        import tokenise as _tokenise            # noqa: F401
from .skill_intelligence import get_skill_scores, skill_importance as _skill_importance  # noqa: F401