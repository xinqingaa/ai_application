"""第 3 步：观察标准 `SourceChunk[]` 的构建流程。

流程：
1. 从目录中发现全部可接受文档。
2. 对每份文档先读取文本，再切成 `ChunkDraft[]`。
3. 在 `ChunkDraft[]` 的基础上补齐 metadata 和 stable id。
4. 汇总成统一的 `SourceChunk[]`。
5. 打印文档级字段、chunk 级字段和稳定性检查结果。

为什么这里不直接 `text -> SourceChunk[]`：
1. “怎么切” 和 “切完后怎么补齐标准字段” 是两件事。
2. `ChunkDraft` 负责保留切分结果和字符范围。
3. `SourceChunk` 再负责补齐 `document_id / chunk_id / metadata`。
4. 这样代码分层更清楚，也更容易调试每一步到底出了什么问题。
"""

from collections import Counter

from document_processing import DATA_DIR, SplitterConfig, build_chunk_corpus, load_and_prepare_chunks


def main() -> None:
    config = SplitterConfig()
    # 第 1 步：做目录级批处理。
    # 这里先不要把注意力放在“最终打印了什么”，而是先记住：
    # 它的本质是把同一条“单文档 -> SourceChunk[]”链路重复应用到所有文档。
    chunks = build_chunk_corpus(DATA_DIR, config)
    chunk_counts = Counter(chunk.metadata["filename"] for chunk in chunks)
    stable_sample_path = DATA_DIR / "faq.txt"

    # 第 2 步：重复执行同一条单文档链路。
    # 这样做不是为了“多跑一遍”，而是为了证明 stable id 的设计没有漂移。
    first_run = load_and_prepare_chunks(stable_sample_path, config)
    second_run = load_and_prepare_chunks(stable_sample_path, config)
    stable_ids = [chunk.chunk_id for chunk in first_run] == [chunk.chunk_id for chunk in second_run]

    print(f"Prepared 已生成 {len(chunks)} 个 chunk 分块。")
    print("Per document 按文档统计：")
    for filename, count in sorted(chunk_counts.items()):
        print(f"- {filename}: {count} 个 chunk 分块")

    print("Stability 稳定性 check 检查：")
    print(f"- faq.txt 的 chunk_ids 分块标识在多次运行间是否稳定: {stable_ids}")

    print("Sample 示例 chunks 分块：")
    for chunk in chunks[:3]:
        # 第 3 步：观察最终产物 `SourceChunk`。
        # 这里故意把文档级 metadata 和 chunk 级 metadata 一起打印，
        # 目的是帮助你区分：
        # - 哪些字段属于整篇文档
        # - 哪些字段属于当前 chunk
        # - 哪些字段是在 prepare 阶段才补齐的
        print(f"- chunk_id 分块标识={chunk.chunk_id}")
        print(f"  document_id 文档标识={chunk.document_id}")
        print(f"  source 来源={chunk.metadata['source']}")
        print(
            f"  filename 文件名={chunk.metadata['filename']} "
            f"suffix 后缀={chunk.metadata['suffix']} loader 加载器={chunk.metadata['loader']} "
            f"chunk_index 分块序号={chunk.metadata['chunk_index']}"
        )
        if "page_count" in chunk.metadata:
            print(f"  page_count 页数={chunk.metadata['page_count']}")
        if chunk.metadata.get("header_path"):
            print(f"  header_path 标题路径={chunk.metadata['header_path']}")
        print(
            f"  range 范围=({chunk.metadata['char_start']}, {chunk.metadata['char_end']}) "
            f"chars 字符数={chunk.metadata['chunk_chars']}"
        )
        preview = chunk.content.replace("\n", " ")[:100]
        print(f"  preview 预览={preview}")


if __name__ == "__main__":
    main()
