from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.embeddings.providers import EmbeddingProviderConfig, create_embedding_provider
from app.embeddings.similarity import cosine_similarity, score_query_against_chunks
from app.embeddings.vectorizer import build_embedded_chunk_corpus, embed_chunks
from app.indexing.index_manager import build_chunk_corpus
from app.ingestion.splitters import SplitterConfig
from app.schemas import SourceChunk


class EmbeddingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.split_config = SplitterConfig(
            chunk_size=settings.default_chunk_size,
            chunk_overlap=settings.default_chunk_overlap,
        )
        self.provider = create_embedding_provider(
            EmbeddingProviderConfig(
                provider_name=settings.default_embedding_provider,
                model_name=settings.default_embedding_model,
                dimensions=settings.default_embedding_dimensions,
            )
        )

    def test_local_provider_returns_fixed_dimensions(self) -> None:
        vector = self.provider.embed_query("stable metadata")
        self.assertEqual(len(vector), settings.default_embedding_dimensions)

        norm = sum(value * value for value in vector) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=6)

    def test_query_and_document_paths_are_distinct_but_comparable(self) -> None:
        text = "Stable IDs keep repeated indexing predictable."
        query_vector = self.provider.embed_query(text)
        document_vector = self.provider.embed_documents([text])[0]

        self.assertNotEqual(query_vector, document_vector)
        self.assertGreater(cosine_similarity(query_vector, document_vector), 0.85)

    def test_embed_chunks_keeps_chunk_identity(self) -> None:
        chunks = build_chunk_corpus(
            data_dir=settings.data_dir,
            config=self.split_config,
            supported_suffixes=settings.supported_suffixes,
        )
        embedded_chunks = embed_chunks(
            chunks=chunks,
            provider=self.provider,
            batch_size=settings.default_embedding_batch_size,
        )

        self.assertEqual(len(embedded_chunks), len(chunks))
        self.assertEqual(embedded_chunks[0].chunk.chunk_id, chunks[0].chunk_id)
        self.assertEqual(embedded_chunks[0].provider_name, settings.default_embedding_provider)
        self.assertEqual(embedded_chunks[0].dimensions, settings.default_embedding_dimensions)
        self.assertIsInstance(embedded_chunks[0].chunk, SourceChunk)
        self.assertIn("filename", embedded_chunks[0].chunk.metadata)
        self.assertIn("char_start", embedded_chunks[0].chunk.metadata)
        self.assertIn("char_end", embedded_chunks[0].chunk.metadata)

    def test_build_embedded_chunk_corpus_reuses_phase_2_chunk_ids_and_metadata(self) -> None:
        phase_2_chunks = build_chunk_corpus(
            data_dir=settings.data_dir,
            config=self.split_config,
            supported_suffixes=settings.supported_suffixes,
        )
        phase_3_chunks = build_embedded_chunk_corpus(
            data_dir=settings.data_dir,
            split_config=self.split_config,
            supported_suffixes=settings.supported_suffixes,
            provider=self.provider,
            batch_size=settings.default_embedding_batch_size,
        )

        self.assertEqual(
            [chunk.chunk_id for chunk in phase_2_chunks],
            [item.chunk.chunk_id for item in phase_3_chunks],
        )
        self.assertEqual(
            [chunk.document_id for chunk in phase_2_chunks],
            [item.chunk.document_id for item in phase_3_chunks],
        )
        self.assertEqual(
            phase_2_chunks[0].metadata["source"],
            phase_3_chunks[0].chunk.metadata["source"],
        )
        self.assertEqual(
            phase_2_chunks[0].metadata["filename"],
            phase_3_chunks[0].chunk.metadata["filename"],
        )

    def test_query_scoring_prefers_relevant_chunk(self) -> None:
        embedded_chunks = build_embedded_chunk_corpus(
            data_dir=settings.data_dir,
            split_config=self.split_config,
            supported_suffixes=settings.supported_suffixes,
            provider=self.provider,
            batch_size=settings.default_embedding_batch_size,
        )
        ranked = score_query_against_chunks(
            "Why do stable document IDs matter?",
            embedded_chunks,
            self.provider,
        )

        self.assertGreaterEqual(len(ranked), 1)
        top_chunk, score = ranked[0]
        self.assertGreater(score, 0.2)
        self.assertIn("stable", top_chunk.chunk.content.lower())

    def test_related_documents_score_higher_than_unrelated_documents(self) -> None:
        base = "Stable IDs make repeated indexing predictable."
        related = "Stable IDs make repeated indexing more predictable and consistent."
        unrelated = "Large chunks preserve context, but they may contain unrelated sentences."

        base_vector, related_vector = self.provider.embed_documents([base, related])
        _, unrelated_vector = self.provider.embed_documents([base, unrelated])

        self.assertGreater(
            cosine_similarity(base_vector, related_vector),
            cosine_similarity(base_vector, unrelated_vector),
        )


if __name__ == "__main__":
    unittest.main()
