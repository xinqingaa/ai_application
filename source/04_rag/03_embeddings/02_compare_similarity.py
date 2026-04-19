from embedding_basics import (
    LocalKeywordEmbeddingProvider,
    demo_source_chunks,
    embed_chunks,
    score_query_against_chunks,
)


def print_ranking(question: str) -> None:
    provider = LocalKeywordEmbeddingProvider()
    embedded_chunks = embed_chunks(demo_source_chunks(), provider)
    ranked = score_query_against_chunks(question, embedded_chunks, provider)

    print(f"Question: {question}")
    for embedded_chunk, score in ranked[:3]:
        preview = embedded_chunk.chunk.content[:60]
        print(
            f"- score={score:.3f} chunk_id={embedded_chunk.chunk.chunk_id} "
            f"source={embedded_chunk.chunk.metadata['filename']}"
        )
        print(f"  preview={preview}")


def main() -> None:
    print_ranking("如何申请退费？")
    print()
    print_ranking("为什么 metadata 很重要？")


if __name__ == "__main__":
    main()
