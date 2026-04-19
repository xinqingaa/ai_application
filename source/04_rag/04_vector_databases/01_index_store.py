import argparse

from vector_store_basics import (
    DEFAULT_STORE_PATH,
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    VectorStoreConfig,
    demo_embedded_chunks,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Index demo embedded chunks into the local store.")
    parser.add_argument("--reset", action="store_true", help="Delete the persisted store first.")
    args = parser.parse_args()

    store = PersistentVectorStore(VectorStoreConfig())
    if args.reset:
        store.reset()

    provider = LocalKeywordEmbeddingProvider()
    inserted = store.upsert(demo_embedded_chunks(provider))

    print(f"Store path: {DEFAULT_STORE_PATH}")
    print(f"Inserted {inserted} embedded chunk(s).")
    print(f"Current count: {store.count()}")
    print(f"Document IDs: {store.list_document_ids()}")


if __name__ == "__main__":
    main()
