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
    parser = argparse.ArgumentParser(description="Search the local vector store.")
    parser.add_argument(
        "question",
        nargs="?",
        default="如何申请退费？",
        help="Question to search against the stored vectors.",
    )
    parser.add_argument("--filename", help="Optional filename filter.")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    store = PersistentVectorStore(VectorStoreConfig())
    ensure_index(store, provider)

    query_vector = provider.embed_query(args.question)
    results = store.similarity_search(
        query_vector=query_vector,
        top_k=args.top_k,
        filename=args.filename,
    )

    print(f"Question: {args.question}")
    if args.filename:
        print(f"Filename filter: {args.filename}")

    for result in results:
        preview = result.chunk.content[:70]
        print(
            f"- score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"document_id={result.chunk.document_id}"
        )
        print(
            "  metadata="
            f"filename={result.chunk.metadata['filename']} "
            f"source={result.chunk.metadata['source']} "
            f"chunk={result.chunk.metadata['chunk_index']}"
        )
        print(f"  preview={preview}")


if __name__ == "__main__":
    main()
