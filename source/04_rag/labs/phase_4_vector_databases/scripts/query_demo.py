from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.embeddings.providers import EmbeddingProvider, EmbeddingProviderConfig, create_embedding_provider
from app.embeddings.vectorizer import build_embedded_chunk_corpus
from app.ingestion.splitters import SplitterConfig
from app.schemas import RetrievalResult
from app.services.rag_service import RagService
from app.vectorstores.chroma_store import ChromaVectorStore, ChromaVectorStoreConfig


class ChromaDemoRetriever:
    def __init__(self, store: ChromaVectorStore, provider: EmbeddingProvider) -> None:
        self.store = store
        self.provider = provider

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        return self.store.similarity_search(
            question=question,
            provider=self.provider,
            top_k=top_k,
        )


def ensure_index(store: ChromaVectorStore, provider: EmbeddingProvider) -> None:
    if store.count() > 0:
        return

    split_config = SplitterConfig(
        chunk_size=settings.default_chunk_size,
        chunk_overlap=settings.default_chunk_overlap,
    )
    embedded_chunks = build_embedded_chunk_corpus(
        data_dir=settings.data_dir,
        split_config=split_config,
        supported_suffixes=settings.supported_suffixes,
        provider=provider,
        batch_size=settings.default_embedding_batch_size,
    )
    store.upsert(
        embedded_chunks,
        batch_size=settings.default_vector_store_batch_size,
    )


def main() -> None:
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Why do stable document IDs matter?"
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
    store = ChromaVectorStore(
        ChromaVectorStoreConfig(
            persist_directory=settings.vector_store_dir,
            collection_name=settings.default_vector_collection,
            distance_metric=settings.default_vector_distance,
        )
    )
    ensure_index(store, provider)

    service = RagService(retriever=ChromaDemoRetriever(store=store, provider=provider))
    result = service.ask(question)
    print(result.answer)
    print("Sources:")
    for item in result.sources:
        print(
            f"- {item.metadata.get('filename')} "
            f"chunk={item.metadata.get('chunk_index')} "
            f"source={item.metadata.get('source')}"
        )


if __name__ == "__main__":
    main()
