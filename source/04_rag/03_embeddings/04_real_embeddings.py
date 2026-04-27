import argparse
import json

from embedding_basics import build_openai_provider_or_mock, demo_source_chunks, embed_chunks


def main() -> None:
    """检查真实或 mock embeddings provider 的接口形态。

    作用：
        演示 OpenAI-compatible embedding provider 如何承接本章同一套
        embed_query / embed_documents 契约；没有真实环境变量时自动用
        mock semantic client 保持脚本可运行。
    入参：
        命令行参数 --force-mock:
            强制使用内置 mock semantic client，不读取真实 endpoint。
    流程：
        1. 解析命令行参数。
        2. 通过 build_openai_provider_or_mock() 选择 real 或 mock provider。
        3. 加载 demo chunks 并批量生成 document vectors。
        4. 用固定问题生成 query vector。
        5. 打印 provider 描述、契约说明、query 维度和 chunk 向量预览。
    """
    parser = argparse.ArgumentParser(description="查看真实或内置模拟向量提供者的接口形态。")
    parser.add_argument(
        "--force-mock",
        action="store_true",
        help="强制使用内置模拟语义客户端，不调用真实向量服务。",
    )
    args = parser.parse_args()

    provider, mode = build_openai_provider_or_mock(force_mock=args.force_mock)
    chunks = demo_source_chunks()
    embedded_chunks = embed_chunks(chunks, provider)
    query = "为什么文档块要记录出处？"
    # 第三章保留 query/document 两个入口，即使真实 provider 底层可能映射到同一个 endpoint。
    query_vector = provider.embed_query(query)

    mode_label = "真实 endpoint" if mode == "real" else "内置 mock"
    print(f"向量模式：{mode_label}（{mode}）")
    if mode == "mock":
        print("说明：未检测到可用的向量服务环境变量，当前回退到内置模拟语义客户端，只演示向量接口形状。")

    print("向量提供者信息：")
    provider_info = provider.describe()
    print(
        json.dumps(
            {
                "提供者名称": provider_info["provider_name"],
                "模型名称": provider_info["model_name"],
                "服务地址": provider_info["base_url"],
                "向量维度": provider_info["dimensions"],
                "是否可调用": provider_info["ready"],
                "客户端类型": provider_info["client_type"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    print("同一套调用契约，不同的底层服务：")
    print("- 第三章仍然保留 embed_query / embed_documents 两个入口。")
    print("- 对 OpenAI-compatible 向量服务来说，这两个入口会映射到同一个 embeddings API。")
    print("- 差异不在聊天补全接口，而在向量维度、批量输入和同一向量空间的稳定性。")

    print(f"已向量化文档块数量：{len(embedded_chunks)}")
    print(f"查询问题：{query}")
    print(f"查询向量维度：{len(query_vector)}")
    print(f"查询向量预览：{[round(value, 3) for value in query_vector[:6]]}")

    for embedded_chunk in embedded_chunks[:3]:
        print(f"- 文档块 ID（chunk_id）：{embedded_chunk.chunk.chunk_id}")
        print(
            f"  向量提供者={embedded_chunk.provider_name} 模型={embedded_chunk.model_name} "
            f"维度={embedded_chunk.dimensions}"
        )
        print(
            f"  继承自原始文档块：来源={embedded_chunk.chunk.metadata['source']} "
            f"文件名={embedded_chunk.chunk.metadata['filename']}"
        )
        print(f"  向量预览：{[round(value, 3) for value in embedded_chunk.vector[:6]]}")


if __name__ == "__main__":
    main()
