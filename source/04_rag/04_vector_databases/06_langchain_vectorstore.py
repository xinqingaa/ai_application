import argparse

from langchain_adapter import (
    LangChainChromaConfig,
    build_documents,
    create_langchain_chroma,
    reset_langchain_chroma,
)
from vector_store_basics import LocalKeywordEmbeddingProvider


def ensure_index(vectorstore, *, provider: LocalKeywordEmbeddingProvider) -> None:
    if vectorstore._collection.count() > 0:
        return

    documents = build_documents()
    ids = [str(document.metadata["chunk_id"]) for document in documents]
    vectorstore.add_documents(documents=documents, ids=ids)
    print(f"LangChain Chroma collection was empty, so a demo index was created first ({len(ids)} chunks).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the same Chapter 4 flow through LangChain Chroma.")
    parser.add_argument(
        "question",
        nargs="?",
        default="为什么 metadata 很重要？",
        help="Question to search against the LangChain vector store.",
    )
    parser.add_argument("--filename", help="Optional equality filter on filename metadata.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--reset", action="store_true", help="Delete the LangChain persist directory first.")
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    config = LangChainChromaConfig()
    if args.reset:
        reset_langchain_chroma(config)
        print("Existing LangChain Chroma persist directory was reset first.")

    vectorstore = create_langchain_chroma(provider, config)
    ensure_index(vectorstore, provider=provider)

    search_kwargs: dict[str, object] = {"k": args.top_k}
    if args.filename:
        search_kwargs["filter"] = {"filename": args.filename}

    results = vectorstore.similarity_search_with_score(args.question, **search_kwargs)

    print(f"Persist dir: {config.persist_directory}")
    print(f"Collection: {config.collection_name}")
    print(
        "Embedding adapter: "
        f"{provider.provider_name}/{provider.model_name}/{provider.dimensions}d"
    )
    print(f"Question: {args.question}")
    if args.filename:
        print(f"Metadata filter: filename={args.filename}")
    print("Top results:")
    for document, distance in results:
        metadata = document.metadata
        print(
            f"- distance={float(distance):.3f} chunk_id={metadata.get('chunk_id')} "
            f"document_id={metadata.get('document_id')}"
        )
        print(
            "  metadata="
            f"filename={metadata.get('filename')} "
            f"source={metadata.get('source')} "
            f"chunk={metadata.get('chunk_index')}"
        )
        print(f"  preview={document.page_content[:70]}")


if __name__ == "__main__":
    main()
