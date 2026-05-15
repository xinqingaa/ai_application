"""查询教学版 JSON 向量库，并打印 RetrievalResult[]。

流程：
1. 解析问题、过滤条件和 top_k。
2. 确保当前存在兼容的演示索引。
3. 将问题向量化成 query vector。
4. 调用 PersistentVectorStore.similarity_search(...)。
5. 打印分数、chunk 身份和 metadata。
"""

import argparse

from vector_store_basics import (
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    VectorStoreConfig,
    demo_embedded_chunks,
    embedding_space_from_provider,
)


def ensure_index(store: PersistentVectorStore, provider: LocalKeywordEmbeddingProvider) -> None:
    """当 JSON 演示索引缺失或不兼容时，创建或重建索引。"""

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
    """JSON 相似度查询演示脚本的命令行入口。"""

    # 1. 收集查询文本和可选 filename 过滤条件。
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

    # 2. 准备 provider/store，并确保 store 里有可查询数据。
    provider = LocalKeywordEmbeddingProvider()
    store = PersistentVectorStore(VectorStoreConfig())
    ensure_index(store, provider)

    # 3. query 必须使用和 store 相同身份的 provider 进行向量化。
    query_vector = provider.embed_query(args.question)

    # 4. 查询返回 RetrievalResult[]，而不是脱离 chunk 的裸向量或裸分数。
    results = store.similarity_search(
        query_vector=query_vector,
        provider=provider,
        top_k=args.top_k,
        filename=args.filename,
    )

    # 5. 打印足够的 metadata，方便把终端结果对应回已存储的 chunk。
    print(f"Question: {args.question}")
    print(
        "Query embedding space: "
        "provider_name: " f"{provider.provider_name};model_name: {provider.model_name};dimensions: {provider.dimensions}d"
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
