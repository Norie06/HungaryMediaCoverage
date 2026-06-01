import unittest
from unittest.mock import patch

from bertopic.backend._utils import ScikitPipeline

from bertopic_pipeline_old import load_embedding_model


class TestEmbeddingFallback(unittest.TestCase):
    @patch("bertopic_pipeline.SentenceTransformer", side_effect=RuntimeError("network failure"))
    def test_load_embedding_model_falls_back_to_sklearn_pipeline(self, _mock_sentence_transformer):
        embedding_backend = load_embedding_model("paraphrase-multilingual-MiniLM-L12-v2", retries=1)
        self.assertIsInstance(embedding_backend, ScikitPipeline)


if __name__ == "__main__":
    unittest.main()
