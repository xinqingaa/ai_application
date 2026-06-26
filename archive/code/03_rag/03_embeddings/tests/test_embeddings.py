from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from embedding_basics import (
    DEFAULT_DIMENSIONS,
    EmbeddedChunk,
    LocalKeywordEmbeddingProvider,
    MockEmbeddingData,
    MockEmbeddingResponse,
    MockSemanticOpenAIClient,
    OpenAICompatibleEmbeddingProvider,
    SourceChunk,
    cosine_similarity,
    demo_source_chunks,
    embed_chunks,
    load_search_cases,
    score_query_against_chunks,
)

SEARCH_CASES = load_search_cases()


class WrongCountProvider:
    provider_name = "broken"
    model_name = "wrong-count-v1"
    dimensions = DEFAULT_DIMENSIONS

    def embed_query(self, text: str) -> list[float]:
        return [0.0] * self.dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self.dimensions]


class WrongDimensionProvider:
    provider_name = "broken"
    model_name = "wrong-dim-v1"
    dimensions = DEFAULT_DIMENSIONS

    def embed_query(self, text: str) -> list[float]:
        return [0.0] * (self.dimensions - 1)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * (self.dimensions - 1) for _ in texts]


class BrokenClient:
    class Embeddings:
        def create(self, *, model: str, input):
            return object()

    def __init__(self) -> None:
        self.embeddings = self.Embeddings()


class WrongCountClient:
    class Embeddings:
        def create(self, *, model: str, input):
            return MockEmbeddingResponse(
                data=[MockEmbeddingData(index=0, embedding=[1.0, 0.0, 0.0])],
                model=model,
            )

    def __init__(self) -> None:
        self.embeddings = self.Embeddings()


class WrongDimensionClient:
    class Embeddings:
        def create(self, *, model: str, input):
            texts = [input] if isinstance(input, str) else list(input)
            data = []
            for index, _ in enumerate(texts):
                dims = 4 if index == 0 else 3
                data.append(MockEmbeddingData(index=index, embedding=[1.0] * dims))
            return MockEmbeddingResponse(data=data, model=model)

    def __init__(self) -> None:
        self.embeddings = self.Embeddings()


class EmbeddingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.local_provider = LocalKeywordEmbeddingProvider()
        self.source_chunks = demo_source_chunks()
        self.local_embedded_chunks = embed_chunks(self.source_chunks, self.local_provider)
        self.semantic_provider = OpenAICompatibleEmbeddingProvider(
            client=MockSemanticOpenAIClient(),
            model_name="mock-semantic-bridge",
        )
        self.semantic_embedded_chunks = embed_chunks(self.source_chunks, self.semantic_provider)

    def test_demo_source_chunks_keep_chapter_two_style_metadata(self) -> None:
        first_chunk = self.source_chunks[0]
        self.assertIn("source", first_chunk.metadata)
        self.assertIn("filename", first_chunk.metadata)
        self.assertIn("suffix", first_chunk.metadata)
        self.assertIn("char_count", first_chunk.metadata)
        self.assertIn("line_count", first_chunk.metadata)
        self.assertIn("chunk_index", first_chunk.metadata)
        self.assertIn("char_start", first_chunk.metadata)
        self.assertIn("char_end", first_chunk.metadata)
        self.assertIn("chunk_chars", first_chunk.metadata)
        self.assertEqual(
            first_chunk.metadata["char_end"] - first_chunk.metadata["char_start"],
            first_chunk.metadata["chunk_chars"],
        )

    def test_local_provider_returns_fixed_dimensions(self) -> None:
        vector = self.local_provider.embed_query("为什么稳定 id 很重要？")
        self.assertEqual(len(vector), DEFAULT_DIMENSIONS)

        norm = sum(value * value for value in vector) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=6)

    def test_query_and_document_paths_are_distinct_but_comparable_for_local_provider(self) -> None:
        text = "Embedding 会把文本映射成向量。"
        query_vector = self.local_provider.embed_query(text)
        document_vector = self.local_provider.embed_documents([text])[0]

        self.assertNotEqual(query_vector, document_vector)
        similarity = cosine_similarity(query_vector, document_vector)
        self.assertGreater(similarity, 0.85)
        self.assertLess(similarity, 0.99)

    def test_openai_compatible_provider_uses_same_embedding_contract_for_query_and_documents(self) -> None:
        text = "为什么文档块要记录出处？"
        query_vector = self.semantic_provider.embed_query(text)
        document_vector = self.semantic_provider.embed_documents([text])[0]
        self.assertEqual(query_vector, document_vector)
        self.assertEqual(len(query_vector), self.semantic_provider.dimensions)

    def test_embed_chunks_keeps_chunk_identity(self) -> None:
        self.assertEqual(len(self.local_embedded_chunks), len(self.source_chunks))
        self.assertEqual(self.local_embedded_chunks[0].chunk.chunk_id, self.source_chunks[0].chunk_id)
        self.assertEqual(
            self.local_embedded_chunks[0].chunk.metadata["filename"],
            self.source_chunks[0].metadata["filename"],
        )
        self.assertEqual(self.local_embedded_chunks[0].provider_name, "local_keyword")
        self.assertEqual(self.local_embedded_chunks[0].dimensions, DEFAULT_DIMENSIONS)

    def test_local_search_cases(self) -> None:
        for case in SEARCH_CASES:
            with self.subTest(question=case["question"]):
                ranked = score_query_against_chunks(
                    str(case["question"]),
                    self.local_embedded_chunks,
                    self.local_provider,
                )
                self.assertEqual(ranked[0][0].chunk.chunk_id, case["local_expected_top_chunk"])

    def test_semantic_provider_fixes_known_gap_case(self) -> None:
        bridge_case = next(case for case in SEARCH_CASES if "known_gap" in case)
        ranked = score_query_against_chunks(
            str(bridge_case["question"]),
            self.semantic_embedded_chunks,
            self.semantic_provider,
        )
        self.assertEqual(ranked[0][0].chunk.chunk_id, bridge_case["semantic_expected_top_chunk"])

    def test_related_documents_score_higher_than_unrelated_documents(self) -> None:
        base = "Embedding 会把文本映射成向量。"
        related = "向量化后系统可以计算相似度。"
        unrelated = "课程支持一次 30 分钟免费试学。"

        base_vector = self.local_provider.embed_documents([base])[0]
        related_vector = self.local_provider.embed_documents([related])[0]
        unrelated_vector = self.local_provider.embed_documents([unrelated])[0]

        self.assertGreater(
            cosine_similarity(base_vector, related_vector),
            cosine_similarity(base_vector, unrelated_vector),
        )

    def test_cosine_similarity_returns_zero_for_zero_vector(self) -> None:
        self.assertEqual(cosine_similarity([0.0, 0.0], [1.0, 0.0]), 0.0)

    def test_embed_chunks_rejects_wrong_vector_count(self) -> None:
        with self.assertRaises(ValueError):
            embed_chunks(self.source_chunks, WrongCountProvider())

    def test_embed_chunks_rejects_wrong_vector_dimensions(self) -> None:
        with self.assertRaises(ValueError):
            embed_chunks(self.source_chunks, WrongDimensionProvider())

    def test_score_query_against_chunks_rejects_query_dimension_mismatch(self) -> None:
        embedded_chunks = embed_chunks(self.source_chunks, self.local_provider)
        with self.assertRaises(ValueError):
            score_query_against_chunks("如何申请退费？", embedded_chunks, WrongDimensionProvider())

    def test_score_query_against_chunks_rejects_provider_space_mismatch(self) -> None:
        mismatched_provider = LocalKeywordEmbeddingProvider(model_name="concept-space-v2")
        with self.assertRaises(ValueError):
            score_query_against_chunks("如何申请退费？", self.local_embedded_chunks, mismatched_provider)

    def test_openai_provider_rejects_missing_api_key_without_client(self) -> None:
        with self.assertRaises(ValueError):
            OpenAICompatibleEmbeddingProvider().embed_query("hi")

    def test_openai_provider_rejects_broken_response_shape(self) -> None:
        provider = OpenAICompatibleEmbeddingProvider(client=BrokenClient(), model_name="broken")
        with self.assertRaises(ValueError):
            provider.embed_query("hi")

    def test_openai_provider_rejects_wrong_vector_count(self) -> None:
        provider = OpenAICompatibleEmbeddingProvider(client=WrongCountClient(), model_name="broken")
        with self.assertRaises(ValueError):
            provider.embed_documents(["a", "b"])

    def test_openai_provider_rejects_dimension_drift(self) -> None:
        provider = OpenAICompatibleEmbeddingProvider(client=WrongDimensionClient(), model_name="broken")
        with self.assertRaises(ValueError):
            provider.embed_documents(["a", "b"])

    def test_embed_chunks_returns_empty_for_empty_input(self) -> None:
        self.assertEqual(embed_chunks([], self.local_provider), [])

    def test_score_query_against_chunks_returns_empty_for_empty_input(self) -> None:
        self.assertEqual(score_query_against_chunks("如何申请退费？", [], self.local_provider), [])


if __name__ == "__main__":
    unittest.main()
