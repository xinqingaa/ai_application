from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.embeddings.providers import EmbeddingProviderConfig, create_embedding_provider
from app.vectorstores.chroma_store import ChromaVectorStore, ChromaVectorStoreConfig


def main() -> None:
    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Why do stable document IDs matter?"
    )
    filename_filter = sys.argv[2] if len(sys.argv) > 2 else None
    where = {"filename": filename_filter} if filename_filter else None

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

    if store.count() == 0:
        print("Chroma collection is empty. Run `python scripts/index_chroma.py --reset` first.")
        return

    results = store.similarity_search(
        question=question,
        provider=provider,
        top_k=settings.default_top_k,
        where=where,
    )

    print(f"Question: {question}")
    if where:
        print(f"Filter: {where}")
    print(f"Collection count: {store.count()}")
    print("Top results:")
    for item in results:
        preview = item.chunk.content.replace("\n", " ")[:88]
        print(
            f"- score={item.score:.3f} "
            f"chunk_id={item.chunk.chunk_id} "
            f"document_id={item.chunk.document_id}"
        )
        print(
            "  metadata="
            f"source={item.chunk.metadata.get('source')} "
            f"filename={item.chunk.metadata.get('filename')} "
            f"chunk={item.chunk.metadata.get('chunk_index')}"
        )
        print(f"  preview={preview}")


if __name__ == "__main__":
    main()
