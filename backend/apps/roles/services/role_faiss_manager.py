"""
FAISS manager for CSV-based role index (resume upload flow).
Create index, save/load, similarity search returning (score, metadata).
"""
from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

#Used to handle FAISS index creation, saving, loading, and searching for role embeddings.
import faiss
import numpy as np

logger = logging.getLogger(__name__)

#FAISS index and metadata file paths. 
FAISS_DIR = Path(__file__).resolve().parent.parent / "data" / "faiss"
FAISS_INDEX_FILE = "faiss.index"
FAISS_METADATA_FILE = "faiss.json"


class VectorDBError(Exception):
    """FAISS index / metadata error."""
    pass


class RoleFAISSManager:
    """FAISS index for CSV-based roles. Used by resume upload and offline build pipeline."""

    def __init__(self) -> None:
        self.index_path = Path(FAISS_DIR) / FAISS_INDEX_FILE
        self.metadata_path = Path(FAISS_DIR) / FAISS_METADATA_FILE
        self.index: faiss.Index | None = None
        self.metadata: List[Dict[str, Any]] | None = None

    def create_index(
        self,
        vectors: np.ndarray,
        metadata: List[Dict[str, Any]],
    ) -> None:
        #Every vector must have metadata.
        if len(vectors) != len(metadata):
            raise VectorDBError("Vectors and metadata size mismatch.")
        dimension = vectors.shape[1]
        logger.info("Creating FAISS index (dim=%s)", dimension)
        try:
            #Creates a FAISS index for inner product similarity search. The vectors are expected to be normalized. The index and metadata are saved to disk for later use.
            index = faiss.IndexFlatIP(dimension)
            #Stores embeddings in FAISS.
            index.add(vectors)
            self.index = index
            self.metadata = metadata
            self._save()
            logger.info("FAISS index created and persisted.")
        except Exception as e:
            raise VectorDBError(f"Index creation failed: {e}") from e

    def _save(self) -> None:
        if self.index is None or self.metadata is None:
            raise VectorDBError("Nothing to save.")
        #Ensures folder exists.
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "w") as f:
            json.dump(self.metadata, f)

    def load(self) -> None:
        if not self.index_path.exists():
            raise VectorDBError("FAISS index not found. Run roles build pipeline first.")
        try:
            logger.info("Loading FAISS index...")
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, "r") as f:
                self.metadata = json.load(f)
            logger.info("FAISS loaded successfully.")
        except Exception as e:
            raise VectorDBError(f"Failed to load FAISS: {e}") from e

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 30,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """Similarity search. Returns [(score, metadata)]."""
        if self.index is None or self.metadata is None:
            self.load()
        if self.index is None or self.metadata is None:
            return []
        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)
        try:
            scores, indices = self.index.search(query_vector, top_k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue
                results.append((float(score), self.metadata[idx]))
            return results
        except Exception as e:
            raise VectorDBError(f"Search failed: {e}") from e


# Singleton for resume upload / search
_role_faiss_manager: RoleFAISSManager | None = None

#Returns the singleton RoleFAISSManager instance. If the FAISS index file exists on disk, it loads the index and metadata into memory for use in similarity search.
def get_role_faiss_manager() -> RoleFAISSManager:
    global _role_faiss_manager
    if _role_faiss_manager is None:
        _role_faiss_manager = RoleFAISSManager()
        if _role_faiss_manager.index_path.exists():
            _role_faiss_manager.load()
    return _role_faiss_manager