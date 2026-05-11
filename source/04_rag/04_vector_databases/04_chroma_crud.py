"""为演示语料创建并检查真实 Chroma collection。

流程：
1. 解析 --reset 参数。
2. 打开 ChromaVectorStore。
3. 确认 collection 使用当前 embedding space。
4. 替换写入演示文档。
5. 打印 collection 信息和少量预览。
"""

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
    """当 Chroma collection 为空或状态过期时，创建或重建演示索引。"""

    expected_space = embedding_space_from_provider(provider)
    current_space = store.embedding_space()
    if current_space is None:
        inserted = store.replace_document(demo_embedded_chunks(provider))
        print(f"Chroma collection was empty, so a demo index was created first ({inserted} chunks).")
        return

    if current_space != expected_space:
        store.reset()
        inserted = store.replace_document(demo_embedded_chunks(provider))
        print(
            "Chroma embedding space changed from "
            f"{current_space.label()} to {expected_space.label()}, so the collection was rebuilt "
            f"with {inserted} chunks."
        )


def main() -> None:
    """原生 Chroma CRUD 检查脚本的命令行入口。"""

    # 1. 允许学习者重置持久化 Chroma collection。
    parser = argparse.ArgumentParser(description="Index demo embedded chunks into real Chroma.")
    parser.add_argument("--reset", action="store_true", help="Delete the Chroma collection first.")
    args = parser.parse_args()

    # 2. 打开原生 Chroma backend 使用的 provider/store 组合。
    provider = LocalKeywordEmbeddingProvider()
    store = ChromaVectorStore(ChromaVectorStoreConfig())

    # 3. 要么显式重置，要么校验现有 collection 的 embedding space。
    if args.reset:
        store.reset()
        print("Existing Chroma collection was reset first.")
    else:
        ensure_index(store, provider)

    # 4. 通过和 JSON store 相同的文档级契约写入演示语料。
    inserted = store.replace_document(demo_embedded_chunks(provider))
    current_space = store.embedding_space()
    preview = store.get_chunks(limit=2)

    # 5. 打印 Chroma 存储细节，以及恢复后的 SourceChunk metadata。
    print(f"Persist dir: {store.persist_directory}")
    print(f"Collection: {store.collection_name} ({store.distance_metric})")
    if current_space is not None:
        print(f"Embedding space: {current_space.label()}")
    print(f"Replaced {inserted} embedded chunk(s) across {len(store.list_document_ids())} document(s).")
    print(f"Current count: {store.count()}")
    print(f"Document IDs: {store.list_document_ids()}")
    print("Preview:")
    for chunk in preview:
        print(
            f"- chunk_id={chunk.chunk_id} document_id={chunk.document_id} "
            f"filename={chunk.metadata.get('filename')}"
        )


if __name__ == "__main__":
    main()
