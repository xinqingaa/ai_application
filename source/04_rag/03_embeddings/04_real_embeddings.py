import argparse
import json

from embedding_basics import build_openai_provider_or_mock, demo_source_chunks, embed_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a real or mock embedding provider.")
    parser.add_argument(
        "--force-mock",
        action="store_true",
        help="Use the built-in mock semantic client instead of a real embeddings endpoint.",
    )
    args = parser.parse_args()

    provider, mode = build_openai_provider_or_mock(force_mock=args.force_mock)
    chunks = demo_source_chunks()
    embedded_chunks = embed_chunks(chunks, provider)
    query = "为什么文档块要记录出处？"
    query_vector = provider.embed_query(query)

    print(f"embedding_mode={mode}")
    if mode == "mock":
        print("note=未检测到可用的 embedding 环境变量，当前回退到 mock semantic client，只演示 embeddings 接口形状。")

    print("provider.describe():")
    print(json.dumps(provider.describe(), ensure_ascii=False, indent=2))

    print("Same contract, different endpoint:")
    print("- 第三章仍然保留 embed_query / embed_documents 两个入口。")
    print("- 对 OpenAI-compatible embeddings 来说，这两个入口会映射到同一个 embeddings API。")
    print("- 差异不在 chat.completions，而在向量维度、批量输入和同一 embedding space 的稳定性。")

    print(f"Embedded {len(embedded_chunks)} chunk(s).")
    print(f"query={query}")
    print(f"query_vector_dims={len(query_vector)}")
    print(f"query_vector_preview={[round(value, 3) for value in query_vector[:6]]}")

    for embedded_chunk in embedded_chunks[:3]:
        print(f"- chunk_id={embedded_chunk.chunk.chunk_id}")
        print(
            f"  provider={embedded_chunk.provider_name} model={embedded_chunk.model_name} "
            f"dims={embedded_chunk.dimensions}"
        )
        print(
            f"  inherited=source={embedded_chunk.chunk.metadata['source']} "
            f"filename={embedded_chunk.chunk.metadata['filename']}"
        )
        print(f"  vector_preview={[round(value, 3) for value in embedded_chunk.vector[:6]]}")


if __name__ == "__main__":
    main()
