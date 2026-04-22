import argparse

from chroma_store import ChromaVectorStore, ChromaVectorStoreConfig
from vector_store_basics import (
    LocalKeywordEmbeddingProvider,
    demo_embedded_chunks,
    embedding_space_from_provider,
)


def ensure_index(
    store: ChromaVectorStore,
    provider: LocalKeywordEmbeddingProvider,
) -> None:
    expected_space = embedding_space_from_provider(provider)
    current_space = store.embedding_space()
    if current_space is None:
        inserted = store.replace_document(demo_embedded_chunks(provider))
        print(f"Chroma collection was empty, so a demo index was created first ({inserted} chunks).")
        return

    if current_space != expected_space:
        store.reset()
        inserted = store.replace_document(demo_embedded_chunks(provider))
        print(
            "Chroma embedding space changed from "
            f"{current_space.label()} to {expected_space.label()}, so the collection was rebuilt "
            f"with {inserted} chunks."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Index demo embedded chunks into real Chroma.")
    parser.add_argument("--reset", action="store_true", help="Delete the Chroma collection first.")
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    store = ChromaVectorStore(ChromaVectorStoreConfig())

    if args.reset:
        store.reset()
        print("Existing Chroma collection was reset first.")
    else:
        ensure_index(store, provider)

    inserted = store.replace_document(demo_embedded_chunks(provider))
    current_space = store.embedding_space()
    preview = store.get_chunks(limit=2)

    print(f"Persist dir: {store.persist_directory}")
    print(f"Collection: {store.collection_name} ({store.distance_metric})")
    if current_space is not None:
        print(f"Embedding space: {current_space.label()}")
    print(f"Replaced {inserted} embedded chunk(s) across {len(store.list_document_ids())} document(s).")
    print(f"Current count: {store.count()}")
    print(f"Document IDs: {store.list_document_ids()}")
    print("Preview:")
    for chunk in preview:
        print(
            f"- chunk_id={chunk.chunk_id} document_id={chunk.document_id} "
            f"filename={chunk.metadata.get('filename')}"
        )


if __name__ == "__main__":
    main()
