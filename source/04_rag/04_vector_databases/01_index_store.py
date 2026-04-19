import argparse

from vector_store_basics import (
    DEFAULT_STORE_PATH,
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    VectorStoreConfig,
    demo_embedded_chunks,
    embedding_space_from_provider,
)


def prepare_store(store: PersistentVectorStore, provider: LocalKeywordEmbeddingProvider) -> None:
    expected_space = embedding_space_from_provider(provider)
    try:
        current_space = store.embedding_space()
    except ValueError:
        store.reset()
        print("Existing store payload was invalid, so it was reset before indexing.")
        return

    if current_space is not None and current_space != expected_space:
        store.reset()
        print(
            "Store embedding space changed from "
            f"{current_space.label()} to {expected_space.label()}, so it was reset."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Index demo embedded chunks into the local store.")
    parser.add_argument("--reset", action="store_true", help="Delete the persisted store first.")
    args = parser.parse_args()

    store = PersistentVectorStore(VectorStoreConfig())
    provider = LocalKeywordEmbeddingProvider()
    if args.reset:
        store.reset()
        print("Existing store was reset first.")
    else:
        prepare_store(store, provider)

    inserted = store.replace_document(demo_embedded_chunks(provider))
    current_space = store.embedding_space()

    print(f"Store path: {DEFAULT_STORE_PATH}")
    if current_space is not None:
        print(f"Embedding space: {current_space.label()}")
    print(f"Replaced {inserted} embedded chunk(s) across {len(store.list_document_ids())} document(s).")
    print(f"Current count: {store.count()}")
    print(f"Document IDs: {store.list_document_ids()}")


if __name__ == "__main__":
    main()
