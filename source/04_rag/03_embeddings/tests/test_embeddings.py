from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from embedding_basics import (
    DEFAULT_DIMENSIONS,
    LocalKeywordEmbeddingProvider,
    cosine_similarity,
    demo_source_chunks,
    embed_chunks,
    score_query_against_chunks,
)


class EmbeddingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = LocalKeywordEmbeddingProvider()
        self.source_chunks = demo_source_chunks()
        self.embedded_chunks = embed_chunks(self.source_chunks, self.provider)

    def test_local_provider_returns_fixed_dimensions(self) -> None:
        vector = self.provider.embed_query("为什么稳定 id 很重要？")
        self.assertEqual(len(vector), DEFAULT_DIMENSIONS)

        norm = sum(value * value for value in vector) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=6)

    def test_query_and_document_paths_are_distinct_but_comparable(self) -> None:
        text = "Embedding 会把文本映射成向量。"
        query_vector = self.provider.embed_query(text)
        document_vector = self.provider.embed_documents([text])[0]

        self.assertNotEqual(query_vector, document_vector)
        self.assertGreater(cosine_similarity(query_vector, document_vector), 0.95)

    def test_embed_chunks_keeps_chunk_identity(self) -> None:
        self.assertEqual(len(self.embedded_chunks), len(self.source_chunks))
        self.assertEqual(self.embedded_chunks[0].chunk.chunk_id, self.source_chunks[0].chunk_id)
        self.assertEqual(
            self.embedded_chunks[0].chunk.metadata["filename"],
            self.source_chunks[0].metadata["filename"],
        )
        self.assertEqual(self.embedded_chunks[0].provider_name, "local_keyword")
        self.assertEqual(self.embedded_chunks[0].dimensions, DEFAULT_DIMENSIONS)

    def test_query_scoring_prefers_relevant_chunk(self) -> None:
        ranked = score_query_against_chunks("如何申请退费？", self.embedded_chunks, self.provider)
        top_chunk, score = ranked[0]
        self.assertGreater(score, 0.5)
        self.assertEqual(top_chunk.chunk.chunk_id, "refund:0")

    def test_related_documents_score_higher_than_unrelated_documents(self) -> None:
        base = "Embedding 会把文本映射成向量。"
        related = "向量化后系统可以计算相似度。"
        unrelated = "课程支持一次 30 分钟免费试学。"

        base_vector = self.provider.embed_documents([base])[0]
        related_vector = self.provider.embed_documents([related])[0]
        unrelated_vector = self.provider.embed_documents([unrelated])[0]

        self.assertGreater(
            cosine_similarity(base_vector, related_vector),
            cosine_similarity(base_vector, unrelated_vector),
        )


if __name__ == "__main__":
    unittest.main()
