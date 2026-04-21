"""Embedding service using Sentence Transformers. Caches model and vectors."""
import logging
from typing import List, Union

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        name = settings.EMBEDDING_CONFIG.get('MODEL_NAME', 'all-MiniLM-L6-v2')
        try:
            _model = SentenceTransformer(name, device="cpu")

        except NotImplementedError as e:
            logger.exception("Torch meta tensor error: %s", e)
            _model = None

        except RuntimeError as e:
            logger.exception("Runtime error initializing model: %s", e)
            _model = None

        except Exception as e:
            logger.exception("Unexpected error initializing model: %s", e)
            _model = None
    return _model


def encode(
    texts: List[str],
    normalize: bool = False,
    return_numpy: bool = False,
) -> Union[List[List[float]], np.ndarray]:
    """Batch encode texts to vectors. Optionally L2-normalize for cosine similarity (e.g. FAISS IndexFlatIP)."""
    if not texts:
        if return_numpy:
            return np.array([], dtype=np.float32)
        return []
    model = _get_model()
    if model is None:
        # Fallback: return zero vectors with configured dimension to keep pipeline running
        dim = settings.EMBEDDING_CONFIG.get('DIMENSION', 384)
        if return_numpy:
            return np.zeros((len(texts), dim), dtype=np.float32)
        return [[0.0] * dim for _ in texts]

    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
    )
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim == 1:
        vectors = np.expand_dims(vectors, 0)
    if return_numpy:
        return vectors
    return vectors.tolist()


def encode_single(text: str, normalize: bool = False) -> List[float]:
    """Encode single text."""
    if not text:
        dim = settings.EMBEDDING_CONFIG.get('DIMENSION', 384)
        return [0.0] * dim
    result = encode([text], normalize=normalize, return_numpy=False)
    return result[0]