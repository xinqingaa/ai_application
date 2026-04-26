"""第 3 步：观察标准 `SourceChunk[]` 的构建流程。

流程：
1. 从目录中发现全部可接受文档。
2. 对每份文档执行 load -> split -> metadata -> stable id。
3. 汇总成统一的 `SourceChunk[]`。
4. 打印文档级字段、chunk 级字段和稳定性检查结果。
"""

from collections import Counter

from document_processing import DATA_DIR, SplitterConfig, build_chunk_corpus, load_and_prepare_chunks


def main() -> None:
    config = SplitterConfig()
    # 这一步对应目录级批处理：把全部文档收束成统一 chunk 语料。
    chunks = build_chunk_corpus(DATA_DIR, config)
    chunk_counts = Counter(chunk.metadata["filename"] for chunk in chunks)
    stable_sample_path = DATA_DIR / "faq.txt"
    # 重复执行同一条单文档链路，用来观察 stable id 是否保持一致。
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
        # 这里把文档级 metadata 和 chunk 级 metadata 一起展示出来。
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
