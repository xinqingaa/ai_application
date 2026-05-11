"""从教学版 JSON 向量库中删除某个 document_id 对应的全部 chunk。

流程：
1. 解析目标 document_id。
2. 确保演示索引存在。
3. 调用 delete_by_document_id(...)。
4. 打印删除后的 store 状态。
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
    """执行删除演示前，确保 JSON 演示索引存在且兼容。"""

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
    """JSON store 文档级删除演示脚本的命令行入口。"""

    # 1. 选择要删除的逻辑文档，默认删除 trial 文档。
    parser = argparse.ArgumentParser(description="Delete every chunk for a document id.")
    parser.add_argument(
        "document_id",
        nargs="?",
        default="trial",
        help="Stable document id to delete from the store.",
    )
    args = parser.parse_args()

    # 2. 删除前准备有效 store，保证演示可以重复运行。
    provider = LocalKeywordEmbeddingProvider()
    store = PersistentVectorStore(VectorStoreConfig())
    ensure_index(store, provider)

    # 3. 按 document_id 删除，确保多 chunk 文档能作为整体移除。
    deleted = store.delete_by_document_id(args.document_id)
    current_space = store.embedding_space()

    # 4. 打印剩余 id，让 stale chunk 残留问题可以被直接看见。
    print(f"Deleted {deleted} chunk(s) for document_id={args.document_id}.")
    if current_space is not None:
        print(f"Store embedding space: {current_space.label()}")
    print("Document updates should use replace_document() to avoid stale chunks.")
    print(f"Remaining count: {store.count()}")
    print(f"Remaining document IDs: {store.list_document_ids()}")


if __name__ == "__main__":
    main()
