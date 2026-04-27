import argparse

from embedding_basics import (
    LocalKeywordEmbeddingProvider,
    build_openai_provider_or_mock,
    demo_source_chunks,
    embed_chunks,
    load_search_cases,
    score_query_against_chunks,
)


def print_top_result(label: str, question: str, provider, embedded_chunks) -> None:
    ranked = score_query_against_chunks(question, embedded_chunks, provider)
    # 这里只取 top-1，是为了把第三章的 known gap / semantic 修正现象直接暴露出来。
    top_chunk, score = ranked[0]
    print(f"{label}: top_chunk={top_chunk.chunk.chunk_id} score={score:.3f}")
    print(f"  source={top_chunk.chunk.metadata['filename']}")
    print(f"  preview={top_chunk.chunk.content}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare toy and semantic embedding rankings.")
    parser.add_argument(
        "--force-mock",
        action="store_true",
        help="Use the built-in mock semantic client instead of a real embeddings endpoint.",
    )
    args = parser.parse_args()

    bridge_case = next(case for case in load_search_cases() if "known_gap" in case)
    question = str(bridge_case["question"])

    local_provider = LocalKeywordEmbeddingProvider()
    local_chunks = embed_chunks(demo_source_chunks(), local_provider)

    semantic_provider, mode = build_openai_provider_or_mock(force_mock=args.force_mock)
    semantic_chunks = embed_chunks(demo_source_chunks(), semantic_provider)

    print(f"question={question}")
    print(f"semantic_mode={mode}")
    if mode == "mock":
        print("note=当前用 mock semantic client 演示桥接效果；配置好 embeddings 环境变量后会自动切到真实 provider。")
    print(f"known_gap={bridge_case['known_gap']}")
    print()

    print_top_result("local_keyword", question, local_provider, local_chunks)
    print()
    print_top_result(
        f"{semantic_provider.provider_name}/{semantic_provider.model_name}",
        question,
        semantic_provider,
        semantic_chunks,
    )


if __name__ == "__main__":
    main()
