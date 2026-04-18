from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.embeddings.providers import EmbeddingProviderConfig, create_embedding_provider
from app.embeddings.vectorizer import build_embedded_chunk_corpus
from app.ingestion.splitters import SplitterConfig
from app.vectorstores.chroma_store import ChromaVectorStore, ChromaVectorStoreConfig


def main() -> None:
    reset = "--reset" in sys.argv or "--rebuild" in sys.argv
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
    store = ChromaVectorStore(
        ChromaVectorStoreConfig(
            persist_directory=settings.vector_store_dir,
            collection_name=settings.default_vector_collection,
            distance_metric=settings.default_vector_distance,
        )
    )

    if reset:
        store.reset()

    store.upsert(
        embedded_chunks,
        batch_size=settings.default_vector_store_batch_size,
    )

    filenames = sorted({item.chunk.metadata["filename"] for item in embedded_chunks})

    print("Lineage:")
    print("- Phase 2 turned source files into stable SourceChunk objects.")
    print("- Phase 3 attached vectors and provider metadata.")
    print("- Phase 4 writes those EmbeddedChunk objects into real Chroma storage.")
    print(
        f"Collection: {store.collection_name} ({settings.default_vector_distance})"
    )
    print(f"Persist dir: {store.persist_directory.as_posix()}")
    print(
        f"Provider: {provider.provider_name} / {provider.model_name} / "
        f"dims={provider.dimensions}"
    )
    print(
        f"Upserted {len(embedded_chunks)} chunk(s) from {len(filenames)} document(s). "
        f"Collection count={store.count()}."
    )
    print(f"Documents: {', '.join(filenames)}")


if __name__ == "__main__":
    main()
