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
