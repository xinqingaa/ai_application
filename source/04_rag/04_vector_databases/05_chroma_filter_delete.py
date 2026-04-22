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
        store.replace_document(demo_embedded_chunks(provider))
        print("Chroma collection was empty, so a demo index was created first.")
        return

    if current_space != expected_space:
        store.reset()
        store.replace_document(demo_embedded_chunks(provider))
        print(
            "Chroma embedding space changed from "
            f"{current_space.label()} to {expected_space.label()}, so the collection was rebuilt first."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Search and delete against the Chroma collection.")
    parser.add_argument(
        "question",
        nargs="?",
        default="为什么 metadata 很重要？",
        help="Question to search against the Chroma vectors.",
    )
    parser.add_argument("--filename", help="Optional equality filter on filename metadata.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--delete-document-id",
        help="Optional document_id to delete after the search demo finishes.",
    )
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    store = ChromaVectorStore(ChromaVectorStoreConfig())
    ensure_index(store, provider)

    where = {"filename": args.filename} if args.filename else None
    query_vector = provider.embed_query(args.question)
    results = store.similarity_search(
        query_vector=query_vector,
        provider=provider,
        top_k=args.top_k,
        where=where,
    )

    print(f"Question: {args.question}")
    print(
        "Query embedding space: "
        f"{provider.provider_name}/{provider.model_name}/{provider.dimensions}d"
    )
    current_space = store.embedding_space()
    if current_space is not None:
        print(f"Chroma embedding space: {current_space.label()}")
    if where:
        print(f"Metadata filter: {where}")

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
            f"chunk={result.chunk.metadata.get('chunk_index')}"
        )
        print(f"  preview={preview}")

    if args.delete_document_id:
        deleted = store.delete_by_document_id(args.delete_document_id)
        print(f"Deleted {deleted} chunk(s) for document_id={args.delete_document_id}.")
        print(f"Remaining count: {store.count()}")
        print(f"Remaining document IDs: {store.list_document_ids()}")


if __name__ == "__main__":
    main()
