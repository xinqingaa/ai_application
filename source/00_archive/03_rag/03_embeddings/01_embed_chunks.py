from embedding_basics import LocalKeywordEmbeddingProvider, demo_source_chunks, embed_chunks


def main() -> None:
    """演示 SourceChunk 到 EmbeddedChunk 的最小流转。

    作用：
        读取本章内置的 demo chunks，用本地 toy embedding provider 批量生成
        document vectors，并打印向量化前后字段的继承关系。
    入参：
        无。脚本直接从 data/source_chunks.json 加载演示数据。
    流程：
        1. 创建 LocalKeywordEmbeddingProvider，确定 provider/model/dimensions。
        2. 读取 demo_source_chunks()，得到稳定的 SourceChunk 列表。
        3. 调用 embed_chunks() 走 document path 生成 EmbeddedChunk。
        4. 逐条打印原始 chunk metadata 和新增 embedding 信息。
    """
    provider = LocalKeywordEmbeddingProvider()
    chunks = demo_source_chunks()
    embedded_chunks = embed_chunks(chunks, provider)

    print(
        f"向量提供者：{provider.provider_name} / 模型：{provider.model_name} / 维度：{provider.dimensions}"
    )
    print(f"已向量化文档块数量：{len(embedded_chunks)}")

    for embedded_chunk in embedded_chunks:
        # 这里故意并排打印“继承字段”和“新增字段”，帮助对照 SourceChunk -> EmbeddedChunk。
        preview = ", ".join(f"{value:.3f}" for value in embedded_chunk.vector[:6])
        print(f"- 文档块 ID（chunk_id）：{embedded_chunk.chunk.chunk_id}")
        print(f"  文档 ID（document_id）：{embedded_chunk.chunk.document_id}")
        print(
            "  继承自原始文档块："
            f"来源={embedded_chunk.chunk.metadata['source']} "
            f"文件名={embedded_chunk.chunk.metadata['filename']} "
            f"后缀={embedded_chunk.chunk.metadata['suffix']} "
            f"分块序号={embedded_chunk.chunk.metadata['chunk_index']} "
            f"字符范围=({embedded_chunk.chunk.metadata['char_start']}, {embedded_chunk.chunk.metadata['char_end']})"
        )
        print(
            "  向量化后新增："
            f"向量提供者={embedded_chunk.provider_name} "
            f"模型={embedded_chunk.model_name} "
            f"维度={embedded_chunk.dimensions} "
            f"向量预览=[{preview}]"
        )


if __name__ == "__main__":
    main()
