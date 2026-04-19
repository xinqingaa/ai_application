from embedding_basics import LocalKeywordEmbeddingProvider, demo_source_chunks, embed_chunks


def main() -> None:
    provider = LocalKeywordEmbeddingProvider()
    chunks = demo_source_chunks()
    embedded_chunks = embed_chunks(chunks, provider)

    print(
        f"Provider: {provider.provider_name} / {provider.model_name} / dims={provider.dimensions}"
    )
    print(f"Embedded {len(embedded_chunks)} chunk(s).")

    for embedded_chunk in embedded_chunks:
        preview = ", ".join(f"{value:.3f}" for value in embedded_chunk.vector[:6])
        print(f"- chunk_id={embedded_chunk.chunk.chunk_id}")
        print(f"  document_id={embedded_chunk.chunk.document_id}")
        print(
            "  inherited="
            f"source={embedded_chunk.chunk.metadata['source']} "
            f"filename={embedded_chunk.chunk.metadata['filename']} "
            f"chunk={embedded_chunk.chunk.metadata['chunk_index']}"
        )
        print(
            "  added="
            f"provider={embedded_chunk.provider_name} "
            f"model={embedded_chunk.model_name} "
            f"dims={embedded_chunk.dimensions} "
            f"vector=[{preview}]"
        )


if __name__ == "__main__":
    main()
