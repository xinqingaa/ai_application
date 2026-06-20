from embedding_basics import (
    LocalKeywordEmbeddingProvider,
    cosine_similarity,
)


def main() -> None:
    """演示 query path 和 document path 的差异与可比较性。

    作用：
        用同一段文本分别生成 query vector 和 document vector，再用相关、
        不相关文本做对照，说明两个入口语义不同但仍在同一 embedding
        space 中可以比较。
    入参：
        无。示例文本直接写在脚本内。
    流程：
        1. 创建 LocalKeywordEmbeddingProvider。
        2. 准备 base、related、unrelated 三段文本。
        3. base 文本分别走 embed_query() 和 embed_documents()。
        4. related/unrelated 文本走 document path。
        5. 打印 query/document 尾部 mode buckets 和三组相似度。
    """
    provider = LocalKeywordEmbeddingProvider()

    text = "Embedding 会把文本映射成向量。"
    related = "向量化后系统可以计算相似度。"
    unrelated = "课程支持一次 30 分钟免费试学。"

    query_vector = provider.embed_query(text)
    document_vector = provider.embed_documents([text])[0]
    related_vector = provider.embed_documents([related])[0]
    unrelated_vector = provider.embed_documents([unrelated])[0]
    # 最后两个 bucket 刻意编码了 query/document 角色差异，
    # 所以这里专门把尾部切出来观察。
    query_tail = ", ".join(f"{value:.3f}" for value in query_vector[-2:])
    document_tail = ", ".join(f"{value:.3f}" for value in document_vector[-2:])

    print(f"向量空间（提供者/模型）：{provider.provider_name} / {provider.model_name}")
    print(f"查询向量尾部角色桶：[{query_tail}]")
    print(f"文档向量尾部角色桶：[{document_tail}]")

    print(
        "同一文本分别走查询路径和文档路径的相似度："
        f"{cosine_similarity(query_vector, document_vector):.3f}"
    )
    print(
        "相关文档相似度："
        f"{cosine_similarity(document_vector, related_vector):.3f}"
    )
    print(
        "不相关文档相似度："
        f"{cosine_similarity(document_vector, unrelated_vector):.3f}"
    )


if __name__ == "__main__":
    main()
