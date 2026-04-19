import argparse

from vector_store_basics import (
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    VectorStoreConfig,
    demo_embedded_chunks,
    embedding_space_from_provider,
)


def ensure_index(store: PersistentVectorStore, provider: LocalKeywordEmbeddingProvider) -> None:
    expected_space = embedding_space_from_provider(provider)
    try:
        current_space = store.embedding_space()
    except ValueError:
        store.reset()
        store.replace_document(demo_embedded_chunks(provider))
        print("Store payload was invalid, so a demo index was rebuilt first.")
        return

    if current_space is None:
        store.replace_document(demo_embedded_chunks(provider))
        print("Store was empty, so a demo index was created first.")
        return

    if current_space != expected_space:
        store.reset()
        store.replace_document(demo_embedded_chunks(provider))
        print(
            "Store embedding space changed from "
            f"{current_space.label()} to {expected_space.label()}, so the demo index was rebuilt first."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete every chunk for a document id.")
    parser.add_argument(
        "document_id",
        nargs="?",
        default="trial",
        help="Stable document id to delete from the store.",
    )
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    store = PersistentVectorStore(VectorStoreConfig())
    ensure_index(store, provider)

    deleted = store.delete_by_document_id(args.document_id)
    current_space = store.embedding_space()
    print(f"Deleted {deleted} chunk(s) for document_id={args.document_id}.")
    if current_space is not None:
        print(f"Store embedding space: {current_space.label()}")
    print("Document updates should use replace_document() to avoid stale chunks.")
    print(f"Remaining count: {store.count()}")
    print(f"Remaining document IDs: {store.list_document_ids()}")


if __name__ == "__main__":
    main()
