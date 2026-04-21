"""FAISS index for role vector search (DB-based roles). Used by analytics and recommendations."""
import logging
from pathlib import Path
from typing import List, Tuple

import faiss
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

INDEX_PATH = Path(settings.BASE_DIR) / 'data' / 'faiss_role_index.bin'
MAPPING_PATH = Path(settings.BASE_DIR) / 'data' / 'faiss_role_mapping.txt'


class FAISSRoleIndex:
    def __init__(self):
        self.index = None
        self.id_list: List[str] = []
        self.dimension = settings.EMBEDDING_CONFIG.get('DIMENSION', 384)

    def build(self, vectors: List[List[float]], role_ids: List[str]):
        if not vectors or not role_ids:
            return
        X = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(X)
        self.index = faiss.IndexFlatIP(X.shape[1])
        self.index.add(X)
        self.id_list = list(role_ids)
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(INDEX_PATH))
        with open(MAPPING_PATH, 'w') as f:
            f.write('\n'.join(self.id_list))

    def load(self) -> bool:
        if not INDEX_PATH.exists():
            return False
        try:
            self.index = faiss.read_index(str(INDEX_PATH))
            if MAPPING_PATH.exists():
                with open(MAPPING_PATH) as f:
                    self.id_list = [ln.strip() for ln in f if ln.strip()]
            return True
        except Exception as e:
            logger.warning("FAISS load failed: %s", e)
        return False

    def search(self, query_vector: List[float], k: int = 30) -> List[Tuple[str, float]]:
        """Return top k (role_id, score) by cosine similarity (IP on L2-normalized vectors)."""
        if self.index is None and not self.load():
            return []
        X = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(X)
        scores, indices = self.index.search(X, min(k, len(self.id_list)))
        results = []
        for idx, sc in zip(indices[0], scores[0]):
            if 0 <= idx < len(self.id_list):
                results.append((self.id_list[idx], float(sc)))
        return results


_faiss_index = None


def get_faiss_index() -> FAISSRoleIndex:
    global _faiss_index
    if _faiss_index is None:
        _faiss_index = FAISSRoleIndex()
        _faiss_index.load()
    return _faiss_index
