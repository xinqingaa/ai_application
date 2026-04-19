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
        provider=provider,
        top_k=args.top_k,
        filename=args.filename,
    )

    print(f"Question: {args.question}")
    print(
        "Query embedding space: "
        f"{provider.provider_name}/{provider.model_name}/{provider.dimensions}d"
    )
    current_space = store.embedding_space()
    if current_space is not None:
        print(f"Store embedding space: {current_space.label()}")
    if args.filename:
        print(f"Filename filter: {args.filename} (Chapter 4 currently supports filename-only filtering)")

    for result in results:
        preview = result.chunk.content[:70]
        print(
            f"- score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"document_id={result.chunk.document_id}"
        )
        print(
            "  metadata="
            f"filename={result.chunk.metadata.get('filename')} "
            f"suffix={result.chunk.metadata.get('suffix')} "
            f"source={result.chunk.metadata.get('source')} "
            f"chunk={result.chunk.metadata.get('chunk_index')} "
            f"chars={result.chunk.metadata.get('char_start')}-{result.chunk.metadata.get('char_end')}"
        )
        print(f"  preview={preview}")


if __name__ == "__main__":
    main()
