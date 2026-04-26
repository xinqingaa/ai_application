"""第 4 步：观察不同 loader 和 Markdown 扩展切分流程。

流程：
1. 发现目录里的可接受文档。
2. 根据文件类型选择不同 loader。
3. 对 Markdown 额外执行按标题切分。
4. 打印 loader 差异、页数信息和标题层级信息。
"""

from document_processing import (
    DATA_DIR,
    discover_documents,
    load_document_record,
    split_markdown_by_headers,
)


def main() -> None:
    print("更真实的 Loader 加载器 视角")
    print("说明：第二章现在支持 .txt / .md / .pdf，但仍然只处理本地、可提取文本的 input 输入。")

    for path in discover_documents(DATA_DIR):
        # 同样是 load，这里重点看不同文件类型的 loader 差异。
        document = load_document_record(path)
        print("=" * 72)
        print(f"document 文档={path.name}")
        print(f"loader 加载器={document.metadata['loader']}")
        print(f"chars 字符数={len(document.content)}")
        if "page_count" in document.metadata:
            print(f"page_count 页数={document.metadata['page_count']}")
            print("boundary 边界=扫描 PDF / OCR 仍不在第二章范围内")

        if path.suffix.lower() == ".md":
            # Markdown 不是直接平铺切分，而是先按标题结构拆成 section。
            sections = split_markdown_by_headers(document.content)
            print(f"markdown_sections Markdown 分段数={len(sections)}")
            for index, section in enumerate(sections, start=1):
                print(
                    f"  [{index}] level 标题级别={section.header_level} "
                    f"header_path 标题路径={section.header_path or '(preamble 前言)'} "
                    f"range 范围=({section.start_index}, {section.end_index})"
                )

        preview = document.content.replace("\n", " ")[:120]
        print(f"preview 预览={preview}")


if __name__ == "__main__":
    main()
