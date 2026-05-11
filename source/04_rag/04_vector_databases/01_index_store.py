"""把演示用的 EmbeddedChunk[] 写入教学版 JSON 向量库。

流程：
1. 解析 --reset 参数。
2. 创建本地 embedding provider 和 PersistentVectorStore。
3. 确认已有 store 没有混用 embedding space。
4. 构造演示用 EmbeddedChunk[]，并按文档维度整体替换写入。
5. 打印持久化状态，方便学习时检查。
"""

import argparse

from vector_store_basics import (
    DEFAULT_STORE_PATH,
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    VectorStoreConfig,
    demo_embedded_chunks,
    embedding_space_from_provider,
)


def prepare_store(store: PersistentVectorStore, provider: LocalKeywordEmbeddingProvider) -> None:
    """写入前清理已经失效或空间不匹配的持久化状态。

    参数：
        store: 当前要准备的 JSON 向量库。
        provider: 定义期望 embedding space 的向量提供器。
    """

    expected_space = embedding_space_from_provider(provider)
    try:
        current_space = store.embedding_space()
    except ValueError:
        store.reset()
        print("Existing store payload was invalid, so it was reset before indexing.")
        return

    if current_space is not None and current_space != expected_space:
        store.reset()
        print(
            "Store embedding space changed from "
            f"{current_space.label()} to {expected_space.label()}, so it was reset."
        )


def main() -> None:
    """JSON 写入演示脚本的命令行入口。"""

    # 1. 读取控制演示状态的命令行参数。
    parser = argparse.ArgumentParser(description="Index demo embedded chunks into the local store.")
    parser.add_argument("--reset", action="store_true", help="Delete the persisted store first.")
    args = parser.parse_args()

    # 2. 创建本章 JSON backend 使用的 provider 和 store。
    store = PersistentVectorStore(VectorStoreConfig())
    provider = LocalKeywordEmbeddingProvider()

    # 3. 如果指定 reset 就清空重建，否则检查旧数据是否失效或空间不匹配。
    if args.reset:
        store.reset()
        print("Existing store was reset first.")
    else:
        prepare_store(store, provider)

    # 4. 将演示语料转成 EmbeddedChunk[]，再用文档级语义安全写入。
    inserted = store.replace_document(demo_embedded_chunks(provider))
    current_space = store.embedding_space()

    # 5. 打印学习时最应该检查的 store 状态。
    print(f"Store path: {DEFAULT_STORE_PATH}")
    if current_space is not None:
        print(f"Embedding space: {current_space.label()}")
    print(f"Replaced {inserted} embedded chunk(s) across {len(store.list_document_ids())} document(s).")
    print(f"Current count: {store.count()}")
    print(f"Document IDs: {store.list_document_ids()}")


if __name__ == "__main__":
    main()
