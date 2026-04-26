"""第 2 步：观察文本切分流程。

流程：
1. 读取单个文档的统一文本。
2. 构造切分参数 `chunk_size / chunk_overlap`。
3. 执行 `split_text()` 得到 `TextChunk[]`。
4. 打印每个 chunk 的字符范围和内容预览。
"""

import argparse
from pathlib import Path
import sys

from document_processing import DATA_DIR, SplitterConfig, load_document, split_text


def main() -> None:
    parser = argparse.ArgumentParser(description="观察 document 文档 chunk 切分结果。")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/product_overview.md",
        help="相对当前章节目录的文档路径。",
    )
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--chunk-overlap", type=int, default=00)
    args = parser.parse_args()

    target = Path(args.path)
    if not target.is_absolute():
        target = DATA_DIR.parent / target

    try:
        # 先校验切分参数，再进入真正的 chunk 切分阶段。
        config = SplitterConfig(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    except ValueError as exc:
        print(f"Invalid 无效的 splitter 切分参数: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    # 这一步对应主链路里的 load -> split。
    text = load_document(target)
    chunks = split_text(text, config)

    print(f"document 文档={target.name}")
    print(f"chunk_size 分块大小={config.chunk_size} chunk_overlap 分块重叠={config.chunk_overlap}")
    print(f"total_chunks 总分块数={len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        preview = chunk.content.replace("\n", " ")[:90]
        print(
            f"[{index}] start 起始={chunk.start_index} end 结束={chunk.end_index} "
            f"chars 字符数={chunk.end_index - chunk.start_index}"
        )
        print(f"    {preview}")


if __name__ == "__main__":
    main()
