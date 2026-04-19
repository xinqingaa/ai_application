import argparse

from vector_store_basics import (
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    VectorStoreConfig,
    demo_embedded_chunks,
)


def ensure_index(store: PersistentVectorStore, provider: LocalKeywordEmbeddingProvider) -> None:
    if store.count() == 0:
        store.upsert(demo_embedded_chunks(provider))
        print("Store was empty, so a demo index was created first.")


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
    print(f"Deleted {deleted} chunk(s) for document_id={args.document_id}.")
    print(f"Remaining count: {store.count()}")
    print(f"Remaining document IDs: {store.list_document_ids()}")


if __name__ == "__main__":
    main()
