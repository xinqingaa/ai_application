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
    """打印某个 provider 在指定问题下的 top-1 检索结果。

    作用：
        用同一套 score_query_against_chunks() 打分逻辑，展示不同 provider
        的最高分 chunk，便于对比 toy keyword 和 semantic provider 的排序差异。
    入参：
        label: 输出时展示的 provider 标签。
        question: 用户查询文本，会被转换为 query vector。
        provider: 实现 EmbeddingProvider 契约的向量提供者。
        embedded_chunks: 已经用同一 provider 向量化过的 document chunks。
    流程：
        1. 调用 score_query_against_chunks() 完成 query 向量化、空间校验和排序。
        2. 取排序后的第一条结果。
        3. 打印 top chunk 的 id、分数、来源文件和完整内容。
    """
    ranked = score_query_against_chunks(question, embedded_chunks, provider)
    # 这里只取 top-1，是为了把第三章的 known gap / semantic 修正现象直接暴露出来。
    top_chunk, score = ranked[0]
    print(f"{label}：最高匹配文档块={top_chunk.chunk.chunk_id} 相似度分数={score:.3f}")
    print(f"  来源文件：{top_chunk.chunk.metadata['filename']}")
    print(f"  内容预览：{top_chunk.chunk.content}")


def main() -> None:
    """对比本地 toy provider 和语义 provider 的检索结果。

    作用：
        读取 search_cases.json 中标记为 known_gap 的问题，展示关键词
        toy provider 的已知缺口，以及真实或 mock semantic provider 如何
        更自然地把问题桥接到 metadata chunk。
    入参：
        命令行参数 --force-mock:
            强制使用内置 mock semantic client，方便不配置真实 endpoint 时演示。
    流程：
        1. 解析命令行参数。
        2. 从 search cases 中取出 known_gap 样例和 question。
        3. 分别构建 local_provider 与 semantic_provider。
        4. 用各自 provider 对同一批 demo chunks 做 document embedding。
        5. 打印问题背景，再分别打印两个 provider 的 top-1 结果。
    """
    parser = argparse.ArgumentParser(description="对比本地关键词向量和语义向量的排序结果。")
    parser.add_argument(
        "--force-mock",
        action="store_true",
        help="强制使用内置模拟语义客户端，不调用真实向量服务。",
    )
    args = parser.parse_args()

    bridge_case = next(case for case in load_search_cases() if "known_gap" in case)
    question = str(bridge_case["question"])

    local_provider = LocalKeywordEmbeddingProvider()
    local_chunks = embed_chunks(demo_source_chunks(), local_provider)

    semantic_provider, mode = build_openai_provider_or_mock(force_mock=args.force_mock)
    semantic_chunks = embed_chunks(demo_source_chunks(), semantic_provider)

    print(f"问题：{question}")
    mode_label = "真实 endpoint" if mode == "real" else "内置 mock"
    print(f"语义向量模式：{mode_label}（{mode}）")
    if mode == "mock":
        print("说明：当前用内置模拟语义客户端演示桥接效果；配置好向量服务环境变量后会自动切到真实向量提供者。")
    print(f"已知缺口说明：{bridge_case['known_gap']}")
    print()

    print_top_result("本地关键词向量", question, local_provider, local_chunks)
    print()
    print_top_result(
        f"语义向量（{semantic_provider.provider_name}/{semantic_provider.model_name}）",
        question,
        semantic_provider,
        semantic_chunks,
    )


if __name__ == "__main__":
    main()
