"""第 5 步：观察目录级 `DocumentPipeline` 总链路。

流程：
1. 扫描目录得到候选文件。
2. 对被接受的文档执行 load。
3. 按文档类型执行 split 和 metadata 补充。
4. 生成 stable id，并汇总成 `DocumentPipelineResult`。
5. 打印批处理摘要和每份文档的治理锚点。
"""

import argparse
from collections import Counter, defaultdict

from document_processing import DATA_DIR, SplitterConfig, run_document_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="观察第二章 document pipeline 文档处理总链路。")
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--chunk-overlap", type=int, default=30)
    args = parser.parse_args()

    # 这里直接运行目录级主链路，观察 discover -> load -> split -> chunk 的总结果。
    result = run_document_pipeline(
        DATA_DIR,
        SplitterConfig(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap),
    )
    chunk_counts = Counter(chunk.metadata["filename"] for chunk in result.chunks)
    document_ids: dict[str, str] = {}
    chunk_samples: dict[str, list[str]] = defaultdict(list)

    for chunk in result.chunks:
        filename = str(chunk.metadata["filename"])
        document_ids.setdefault(filename, chunk.document_id)
        if len(chunk_samples[filename]) < 2:
            chunk_samples[filename].append(chunk.chunk_id)

    print("DocumentPipeline 文档处理流水线")
    print(
        f"summary 摘要: candidates 候选数={len(result.candidates)} accepted 接受数={result.accepted_documents} "
        f"ignored 忽略数={result.ignored_candidates} total_chunks 总分块数={result.total_chunks}"
    )
    print(
        f"config 配置: chunk_size 分块大小={result.config.chunk_size} "
        f"chunk_overlap 分块重叠={result.config.chunk_overlap}"
    )

    print("Per document 按文档统计：")
    for document in result.documents:
        filename = document.path.name
        # 这里重点看 document_id 和 chunk_id 如何成为后续治理锚点。
        print(f"- {filename}")
        print(f"  loader 加载器={document.metadata['loader']}")
        if "page_count" in document.metadata:
            print(f"  page_count 页数={document.metadata['page_count']}")
        print(f"  document_id 文档标识={document_ids[filename]}")
        print(f"  chunk_count 分块数量={chunk_counts[filename]}")
        print(f"  sample_chunk_ids 示例分块标识={chunk_samples[filename]}")
        print("  governance 治理说明=update/delete 应锚定 document_id；upsert 应锚定 chunk_id")


if __name__ == "__main__":
    main()
