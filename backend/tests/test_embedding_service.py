"""Unit tests for embedding service."""
import types
from unittest.mock import Mock, patch

import numpy as np
from django.test import SimpleTestCase, override_settings

from core.services import embedding_service


class TestEmbeddingService(SimpleTestCase):
    def tearDown(self):
        embedding_service._model = None

    def test_encode_empty_inputs(self):
        self.assertEqual(embedding_service.encode([]), [])
        arr = embedding_service.encode([], return_numpy=True)
        self.assertIsInstance(arr, np.ndarray)
        self.assertEqual(arr.size, 0)

    @override_settings(EMBEDDING_CONFIG={"DIMENSION": 5})
    def test_encode_returns_zero_vectors_when_model_unavailable(self):
        with patch("core.services.embedding_service._get_model", return_value=None):
            vectors_list = embedding_service.encode(["a", "b"], return_numpy=False)
            vectors_np = embedding_service.encode(["a", "b"], return_numpy=True)

        self.assertEqual(vectors_list, [[0.0] * 5, [0.0] * 5])
        self.assertEqual(vectors_np.shape, (2, 5))

    def test_encode_uses_model_and_expands_1d_output(self):
        model = Mock()
        model.encode.return_value = np.array([1.0, 2.0, 3.0], dtype=np.float32)

        with patch("core.services.embedding_service._get_model", return_value=model):
            vectors = embedding_service.encode(["hello"], return_numpy=True)

        self.assertEqual(vectors.shape, (1, 3))

    def test_encode_returns_list_when_return_numpy_false(self):
        model = Mock()
        model.encode.return_value = np.array([[1.0, 2.0]], dtype=np.float32)

        with patch("core.services.embedding_service._get_model", return_value=model):
            vectors = embedding_service.encode(["hello"], return_numpy=False)

        self.assertEqual(vectors, [[1.0, 2.0]])

    @override_settings(EMBEDDING_CONFIG={"DIMENSION": 3})
    def test_encode_single_behaviour(self):
        self.assertEqual(embedding_service.encode_single(""), [0.0, 0.0, 0.0])

        with patch("core.services.embedding_service.encode", return_value=[[0.1, 0.2, 0.3]]):
            self.assertEqual(embedding_service.encode_single("text"), [0.1, 0.2, 0.3])

    @override_settings(EMBEDDING_CONFIG={"MODEL_NAME": "fake-model"})
    def test_get_model_initializes_and_caches_model(self):
        calls = {"count": 0}

        class FakeSentenceTransformer:
            def __init__(self, name, device):
                calls["count"] += 1
                self.name = name
                self.device = device

        fake_module = types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer)
        embedding_service._model = None

        with patch.dict("sys.modules", {"sentence_transformers": fake_module}):
            m1 = embedding_service._get_model()
            m2 = embedding_service._get_model()

        self.assertIsNotNone(m1)
        self.assertIs(m1, m2)
        self.assertEqual(calls["count"], 1)

    @override_settings(EMBEDDING_CONFIG={"MODEL_NAME": "fake-model"})
    def test_get_model_handles_constructor_exceptions(self):
        class NotImpl:
            def __init__(self, name, device):
                raise NotImplementedError("meta")

        class RuntimeFail:
            def __init__(self, name, device):
                raise RuntimeError("rt")

        class GenericFail:
            def __init__(self, name, device):
                raise ValueError("other")

        for cls in (NotImpl, RuntimeFail, GenericFail):
            embedding_service._model = None
            fake_module = types.SimpleNamespace(SentenceTransformer=cls)
            with patch.dict("sys.modules", {"sentence_transformers": fake_module}):
                self.assertIsNone(embedding_service._get_model())
