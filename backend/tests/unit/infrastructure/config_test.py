import unittest

from app.core.config import Settings


class TestGetVectorSize(unittest.TestCase):
    def test_nomic_v2_moe_returns_256(self):
        settings = Settings(local_llm=True, ollama_embeddings_model="nomic-embed-text-v2-moe")
        self.assertEqual(settings.get_vector_size(), 256)

    def test_nomic_v1_5_returns_768(self):
        settings = Settings(local_llm=True, ollama_embeddings_model="nomic-embed-text:v1.5")
        self.assertEqual(settings.get_vector_size(), 768)

    def test_openai_ada_002_returns_1536(self):
        settings = Settings(local_llm=False, embeddings_model="text-embedding-ada-002")
        self.assertEqual(settings.get_vector_size(), 1536)

    def test_openai_3_large_returns_3072(self):
        settings = Settings(local_llm=False, embeddings_model="text-embedding-3-large")
        self.assertEqual(settings.get_vector_size(), 3072)

    def test_vertex_ai_multilingual_returns_768(self):
        settings = Settings(local_llm=False, embeddings_model="text-multilingual-embedding-002")
        self.assertEqual(settings.get_vector_size(), 768)

    def test_unknown_model_defaults_to_768(self):
        settings = Settings(local_llm=True, ollama_embeddings_model="unknown-model")
        self.assertEqual(settings.get_vector_size(), 768)


class TestSettingsDefaults(unittest.TestCase):
    def test_chromadb_port_default_is_8000(self):
        settings = Settings()
        self.assertEqual(settings.chromadb_port, 8000)

    def test_app_port_default_is_8106(self):
        settings = Settings()
        self.assertEqual(settings.app_port, 8106)


if __name__ == "__main__":
    unittest.main()
