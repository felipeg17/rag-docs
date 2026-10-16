import unittest

from chromadb.api.types import validate_where
from langchain_postgres.v2.async_vectorstore import AsyncPGVectorStore

from app.infrastructure.vector_db.filters import build_document_filter


TITLE_CLAUSE = {"titulo": {"$eq": "doc-a"}}


def _has_title_scope(result: dict) -> bool:
    if result == TITLE_CLAUSE:
        return True
    return TITLE_CLAUSE in result.get("$and", [])


class TestBuildDocumentFilter(unittest.TestCase):
    def setUp(self):
        self.pg_store = object.__new__(AsyncPGVectorStore)

    def test_all_shapes_are_scoped_and_valid_on_both_backends(self):
        cases = {
            "title_only": None,
            "single_key": {"pagina": 1},
            "multi_key": {"pagina": 1, "autor": "x"},
            "and_expr": {"$and": [{"pagina": 1}, {"autor": "x"}]},
            "or_expr": {"$or": [{"pagina": 1}, {"pagina": 2}]},
            "tipo_documento": {"tipo_documento": "x"},
        }
        for name, metadata_filter in cases.items():
            with self.subTest(case=name):
                result = build_document_filter("doc-a", metadata_filter)

                self.assertTrue(_has_title_scope(result))
                validate_where(result)
                self.pg_store._create_filter_clause(result)
                self.assertEqual("tipo_documento" in repr(result), name == "tipo_documento")

    def test_multi_key_filter_is_split_into_one_clause_per_key(self):
        result = build_document_filter("doc-a", {"pagina": 1, "autor": "x"})

        self.assertEqual(result, {"$and": [TITLE_CLAUSE, {"pagina": 1}, {"autor": "x"}]})

    def test_title_only_is_single_condition_without_and(self):
        for empty in (None, {}):
            with self.subTest(metadata_filter=empty):
                self.assertEqual(build_document_filter("doc-a", empty), TITLE_CLAUSE)

    def test_client_filter_cannot_replace_title_scope(self):
        result = build_document_filter("doc-a", {"titulo": "other-doc"})

        self.assertIn(TITLE_CLAUSE, result["$and"])
        self.assertIn({"titulo": "other-doc"}, result["$and"])


if __name__ == "__main__":
    unittest.main()
