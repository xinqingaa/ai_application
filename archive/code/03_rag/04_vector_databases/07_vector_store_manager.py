"""在选定 backend 上运行统一的 VectorStoreManager。

流程：
1. 解析 backend、查询文本，以及可选 add/replace/delete 操作。
2. 使用选定 backend 构造 VectorStoreManager。
3. 确保演示数据存在。
4. 执行可选写入/删除操作。
5. 查询并打印归一后的 RetrievalResult[] 输出。
"""

import argparse

from vector_store_basics import LocalKeywordEmbeddingProvider
from vector_store_manager import VectorStoreManager


def main() -> None:
    """跨 backend manager 演示脚本的命令行入口。"""

    # 1. 解析 backend 选择，以及搜索前可选的数据变更操作。
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

    # 2. 校验成对 CLI 参数，避免 add/replace 操作只提供一半信息。
    if bool(args.add_document_id) != bool(args.add_text):
        parser.error("--add-document-id and --add-text must be provided together.")
    if bool(args.replace_document_id) != bool(args.replace_text):
        parser.error("--replace-document-id and --replace-text must be provided together.")

    # 3. 创建 manager，并确保选定 backend 中已有演示数据。
    manager = VectorStoreManager(
        backend=args.backend,
        provider=LocalKeywordEmbeddingProvider(),
    )
    if args.reset:
        manager.reset()
        print(f"Backend `{args.backend}` was reset first.")
    manager.ensure_index()

    # 4. 可选添加路径：在这个 manager 中，一段原始文本会变成一个 SourceChunk。
    if args.add_document_id and args.add_text:
        added = manager.add_documents(
            [args.add_text],
            ids=[args.add_document_id],
        )
        print(f"Added {added} document(s) through VectorStoreManager.")

    # 5. 可选替换路径：保持文档级整体替换语义。
    if args.replace_document_id and args.replace_text:
        replaced = manager.replace_document(
            args.replace_document_id,
            args.replace_text,
        )
        print(f"Replaced {replaced} document chunk(s) through VectorStoreManager.")

    # 6. 可选删除路径：搜索前移除一个逻辑文档。
    if args.delete_document_id:
        deleted = manager.delete_document(args.delete_document_id)
        print(f"Deleted {deleted} document chunk(s) for document_id={args.delete_document_id}.")

    # 7. 通过选定 backend 查询，并获得归一后的结果。
    results = manager.search(
        args.question,
        top_k=args.top_k,
        filename=args.filename,
    )

    # 8. 打印 backend 状态和 RetrievalResult 中的身份字段。
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
