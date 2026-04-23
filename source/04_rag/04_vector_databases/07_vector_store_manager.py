import argparse

from vector_store_basics import LocalKeywordEmbeddingProvider
from vector_store_manager import VectorStoreManager


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Chapter 4 vector store manager demo.")
    parser.add_argument(
        "--backend",
        choices=["json", "chroma", "langchain"],
        default="json",
        help="Which backend to run for the Chapter 4 demo.",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default="如何申请退费？",
        help="Question to search against the selected backend.",
    )
    parser.add_argument("--filename", help="Optional filename filter.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--reset", action="store_true", help="Reset the selected backend before indexing.")
    parser.add_argument("--add-document-id", help="Optional document_id to add before search.")
    parser.add_argument("--add-text", help="Optional raw document text to add before search.")
    parser.add_argument("--replace-document-id", help="Optional document_id to replace before search.")
    parser.add_argument("--replace-text", help="Optional raw document text to use during replacement.")
    parser.add_argument("--delete-document-id", help="Optional document_id to delete before search.")
    args = parser.parse_args()

    if bool(args.add_document_id) != bool(args.add_text):
        parser.error("--add-document-id and --add-text must be provided together.")
    if bool(args.replace_document_id) != bool(args.replace_text):
        parser.error("--replace-document-id and --replace-text must be provided together.")

    manager = VectorStoreManager(
        backend=args.backend,
        provider=LocalKeywordEmbeddingProvider(),
    )
    if args.reset:
        manager.reset()
        print(f"Backend `{args.backend}` was reset first.")
    manager.ensure_index()

    if args.add_document_id and args.add_text:
        added = manager.add_documents(
            [args.add_text],
            ids=[args.add_document_id],
        )
        print(f"Added {added} document(s) through VectorStoreManager.")

    if args.replace_document_id and args.replace_text:
        replaced = manager.replace_document(
            args.replace_document_id,
            args.replace_text,
        )
        print(f"Replaced {replaced} document chunk(s) through VectorStoreManager.")

    if args.delete_document_id:
        deleted = manager.delete_document(args.delete_document_id)
        print(f"Deleted {deleted} document chunk(s) for document_id={args.delete_document_id}.")

    results = manager.search(
        args.question,
        top_k=args.top_k,
        filename=args.filename,
    )

    print(f"Backend: {args.backend}")
    print(f"Question: {args.question}")
    if args.filename:
        print(f"Filename filter: {args.filename}")
    print(f"Count: {manager.count()}")
    print(f"Document IDs: {manager.list_document_ids()}")
    for result in results:
        print(
            f"- score={result.score:.3f} chunk_id={result.chunk.chunk_id} "
            f"document_id={result.chunk.document_id} "
            f"filename={result.chunk.metadata.get('filename')}"
        )


if __name__ == "__main__":
    main()
