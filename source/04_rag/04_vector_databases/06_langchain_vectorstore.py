import argparse

from langchain_adapter import (
    LangChainChromaConfig,
    build_documents,
    create_langchain_chroma,
    create_langchain_chroma_from_documents,
    reset_langchain_chroma,
    retrieval_results_from_scored_documents,
    similarity_results_from_documents,
)
from vector_store_basics import LocalKeywordEmbeddingProvider


def ensure_index(vectorstore) -> int:
    if vectorstore._collection.count() > 0:
        return 0

    documents = build_documents()
    ids = [str(document.metadata["chunk_id"]) for document in documents]
    vectorstore.add_documents(documents=documents, ids=ids)
    return len(ids)


def create_or_load_vectorstore(
    *,
    provider: LocalKeywordEmbeddingProvider,
    config: LangChainChromaConfig,
    init_mode: str,
):
    if init_mode == "from_documents":
        existing = create_langchain_chroma(provider, config)
        if existing._collection.count() > 0:
            return existing, "Existing collection reused; `from_documents` was skipped because data already existed."
        created = create_langchain_chroma_from_documents(provider, config)
        return created, "Collection was initialized through `Chroma.from_documents(...)`."

    vectorstore = create_langchain_chroma(provider, config)
    inserted = ensure_index(vectorstore)
    if inserted > 0:
        return vectorstore, f"Collection was initialized through `add_documents(...)` with {inserted} chunk(s)."
    return vectorstore, "Existing collection reused; `add_documents(...)` was not needed."


def print_plain_results(title: str, results) -> None:
    print(title)
    for result in results:
        print(
            f"- chunk_id={result.chunk.chunk_id} document_id={result.chunk.document_id} "
            f"filename={result.chunk.metadata.get('filename')}"
        )
        print(f"  preview={result.chunk.content[:70]}")


def print_scored_results(title: str, results) -> None:
    print(title)
    for result in results:
        print(
            f"- score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"document_id={result.chunk.document_id} filename={result.chunk.metadata.get('filename')}"
        )
        print(f"  preview={result.chunk.content[:70]}")


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
    parser.add_argument(
        "--init-mode",
        choices=("add_documents", "from_documents"),
        default="add_documents",
        help="How to initialize LangChain Chroma for the demo.",
    )
    parser.add_argument(
        "--retriever-search-type",
        choices=("similarity", "mmr"),
        default="similarity",
        help="Expose the `as_retriever()` API surface. Strategy details are covered in Chapter 5.",
    )
    parser.add_argument("--reset", action="store_true", help="Delete the LangChain persist directory first.")
    args = parser.parse_args()

    provider = LocalKeywordEmbeddingProvider()
    config = LangChainChromaConfig()
    if args.reset:
        reset_langchain_chroma(config)
        print("Existing LangChain Chroma persist directory was reset first.")

    vectorstore, init_message = create_or_load_vectorstore(
        provider=provider,
        config=config,
        init_mode=args.init_mode,
    )

    search_kwargs: dict[str, object] = {"k": args.top_k}
    if args.filename:
        search_kwargs["filter"] = {"filename": args.filename}

    plain_results = similarity_results_from_documents(
        vectorstore.similarity_search(args.question, **search_kwargs)
    )
    scored_results = retrieval_results_from_scored_documents(
        vectorstore.similarity_search_with_score(args.question, **search_kwargs)
    )
    retriever = vectorstore.as_retriever(
        search_type=args.retriever_search_type,
        search_kwargs=search_kwargs,
    )
    retriever_results = similarity_results_from_documents(retriever.invoke(args.question))

    print(f"Persist dir: {config.persist_directory}")
    print(f"Collection: {config.collection_name}")
    print(f"Init mode: {args.init_mode}")
    print(
        "Embedding adapter: "
        f"{provider.provider_name}/{provider.model_name}/{provider.dimensions}d"
    )
    print(init_message)
    print(f"Question: {args.question}")
    if args.filename:
        print(f"Metadata filter: filename={args.filename}")
    if args.retriever_search_type == "mmr":
        print("Retriever API note: `as_retriever(search_type=\"mmr\")` is shown here only as an interface demo; strategy details are covered in Chapter 5.")
    print()
    print_plain_results("[similarity_search]", plain_results)
    print()
    print_scored_results("[similarity_search_with_score]", scored_results)
    print()
    print_plain_results(f"[as_retriever search_type={args.retriever_search_type}]", retriever_results)


if __name__ == "__main__":
    main()
