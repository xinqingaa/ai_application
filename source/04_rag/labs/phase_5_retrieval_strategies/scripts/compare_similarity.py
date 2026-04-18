from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.embeddings.providers import EmbeddingProviderConfig, create_embedding_provider
from app.embeddings.similarity import cosine_similarity, score_query_against_chunks
from app.embeddings.vectorizer import build_embedded_chunk_corpus
from app.ingestion.splitters import SplitterConfig


def main() -> None:
    split_config = SplitterConfig(
        chunk_size=settings.default_chunk_size,
        chunk_overlap=settings.default_chunk_overlap,
    )
    provider = create_embedding_provider(
        EmbeddingProviderConfig(
            provider_name=settings.default_embedding_provider,
            model_name=settings.default_embedding_model,
            dimensions=settings.default_embedding_dimensions,
            api_key_env=settings.embedding_api_key_env,
            base_url=settings.embedding_base_url,
        )
    )
    embedded_chunks = build_embedded_chunk_corpus(
        data_dir=settings.data_dir,
        split_config=split_config,
        supported_suffixes=settings.supported_suffixes,
        provider=provider,
        batch_size=settings.default_embedding_batch_size,
    )

    question = "Why do stable document IDs matter?"
    ranked = score_query_against_chunks(question, embedded_chunks, provider)

    print("Lineage check: ranking uses Phase 3 vectors on top of Phase 2 chunk identity.")
    print(f"Question: {question}")
    print("Top similar chunks:")
    for embedded_chunk, score in ranked[:3]:
        metadata = embedded_chunk.chunk.metadata
        preview = embedded_chunk.chunk.content.replace("\n", " ")[:88]
        print(
            f"- score={score:.3f} "
            f"chunk_id={embedded_chunk.chunk.chunk_id} "
            f"document_id={embedded_chunk.chunk.document_id}"
        )
        print(
            "  inherited="
            f"source={metadata['source']} "
            f"filename={metadata['filename']} "
            f"chunk={metadata['chunk_index']}"
        )
        print(f"  preview={preview}")

    text = "Stable IDs make repeated indexing predictable."
    related = "Stable IDs make repeated indexing more predictable and consistent."
    unrelated = "Large chunks preserve context, but they may contain unrelated sentences."

    query_vector = provider.embed_query(text)
    document_vector = provider.embed_documents([text])[0]
    related_vectors = provider.embed_documents([text, related])
    unrelated_vectors = provider.embed_documents([text, unrelated])

    print()
    print(
        "Same text via query/document paths: "
        f"{cosine_similarity(query_vector, document_vector):.3f}"
    )
    print(
        "Related document similarity: "
        f"{cosine_similarity(related_vectors[0], related_vectors[1]):.3f}"
    )
    print(
        "Unrelated document similarity: "
        f"{cosine_similarity(unrelated_vectors[0], unrelated_vectors[1]):.3f}"
    )


if __name__ == "__main__":
    main()
