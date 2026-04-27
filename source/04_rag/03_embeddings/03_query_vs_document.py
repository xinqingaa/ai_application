from embedding_basics import (
    LocalKeywordEmbeddingProvider,
    cosine_similarity,
)


def main() -> None:
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

    print(f"Provider/model space: {provider.provider_name} / {provider.model_name}")
    print(f"Query tail buckets: [{query_tail}]")
    print(f"Document tail buckets: [{document_tail}]")

    print(
        "Same text via query/document paths: "
        f"{cosine_similarity(query_vector, document_vector):.3f}"
    )
    print(
        "Related document similarity: "
        f"{cosine_similarity(document_vector, related_vector):.3f}"
    )
    print(
        "Unrelated document similarity: "
        f"{cosine_similarity(document_vector, unrelated_vector):.3f}"
    )


if __name__ == "__main__":
    main()
