"""第 1 步：观察文档发现和加载流程。

流程：
1. 扫描 `data/` 下的全部文件候选。
2. 判断每个文件是否应该进入系统。
3. 对被接受的文件选择 loader 并读取内容。
4. 打印发现结果、loader 选择和文本预览。
"""

from document_processing import (
    DATA_DIR,
    discover_documents,
    inspect_document_candidates,
    load_document_record,
)


def main() -> None:
    # 先看“哪些文件能进系统”，再看“进来以后怎么被读取”。
    candidates = inspect_document_candidates(DATA_DIR)
    documents = discover_documents(DATA_DIR)
    print(f"Found 找到 {len(candidates)} 个 file 文件 candidate 候选项，位置在 data/ 下。")
    print(f"Accepted 接受了 {len(documents)} 个 supported 支持的 document 文档。")

    print("Discovery 发现阶段 decisions 判断结果：")
    for candidate in candidates:
        status = "accepted" if candidate.accepted else "ignored"
        print(f"- 文件名：{candidate.path.name} , status: {status} , reason: ({candidate.reason})")

    print("Loaded 已加载 documents 文档：")
    for path in documents:
        # 这一步对应主链路里的 load：把文件统一读取成文本和 metadata。
        document = load_document_record(path)
        text = document.content
        first_line = text.splitlines()[0] if text else "(empty 空内容)"
        print(f"- {path.name}")
        print(f"  loader ={document.metadata['loader']}")
        if "page_count" in document.metadata:
            print(f"  pages 页数={document.metadata['page_count']}")
        print(f"  chars 字符数={len(text)} lines 行数={text.count(chr(10)) + 1 if text else 0}")
        print(f"  preview 预览={first_line}")


if __name__ == "__main__":
    main()
