from embedding_basics import (
    LocalKeywordEmbeddingProvider,
    demo_source_chunks,
    embed_chunks,
    score_query_against_chunks,
)


def print_ranking(question: str) -> None:
    """打印一个问题和所有 demo chunks 的相似度排序。

    作用：
        把用户问题转换成 query vector，再和已经向量化的 document chunks
        逐一计算 cosine similarity，展示 top-3 排序结果。
    入参：
        question: 用户查询文本，会走 provider.embed_query() 生成 query vector。
    流程：
        1. 创建本地 toy provider。
        2. 加载 demo chunks，并通过 embed_chunks() 得到 document vectors。
        3. 单独生成 query vector，打印前几个维度帮助观察。
        4. 调用 score_query_against_chunks() 完成校验、打分、排序。
        5. 打印分数、chunk_id、来源文件和内容预览。
    """
    provider = LocalKeywordEmbeddingProvider()
    embedded_chunks = embed_chunks(demo_source_chunks(), provider)
    query_vector = provider.embed_query(question)
    ranked = score_query_against_chunks(question, embedded_chunks, provider)

    preview = ", ".join(f"{value:.3f}" for value in query_vector[:6])
    print(f"问题：{question}")
    print(
        f"向量提供者：{provider.provider_name} / 模型：{provider.model_name} / 维度：{provider.dimensions}"
    )
    print(f"查询向量预览：[{preview}]")
    for embedded_chunk, score in ranked[:3]:
        preview = embedded_chunk.chunk.content[:60]
        print(
            f"- 相似度分数={score:.3f} 文档块ID={embedded_chunk.chunk.chunk_id} "
            f"来源文件={embedded_chunk.chunk.metadata['filename']}"
        )
        print(f"  内容预览：{preview}")


def main() -> None:
    """按固定问题运行两次排序示例。

    作用：
        让脚本一次性展示两个查询：一个偏业务问题，一个偏 metadata
        问题，从而观察关键词 toy provider 的排序行为。
    入参：
        无。问题文本在脚本内固定，便于学习和回归。
    流程：
        1. 调用 print_ranking("如何申请退费？")。
        2. 输出空行分隔两组结果。
        3. 调用 print_ranking("为什么 metadata 很重要？")。
    """
    print_ranking("如何申请退费？")
    print()
    print_ranking("为什么 metadata 很重要？")


if __name__ == "__main__":
    main()
