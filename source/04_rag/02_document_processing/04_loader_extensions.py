from document_processing import (
    DATA_DIR,
    discover_documents,
    load_document_record,
    split_markdown_by_headers,
)


def main() -> None:
    print("更真实的 Loader 视角")
    print("说明：第二章现在支持 .txt / .md / .pdf，但仍然只处理本地、可提取文本的输入。")

    for path in discover_documents(DATA_DIR):
        document = load_document_record(path)
        print("=" * 72)
        print(f"document={path.name}")
        print(f"loader={document.metadata['loader']}")
        print(f"chars={len(document.content)}")
        if "page_count" in document.metadata:
            print(f"page_count={document.metadata['page_count']}")
            print("boundary=扫描 PDF / OCR 仍不在第二章范围内")

        if path.suffix.lower() == ".md":
            sections = split_markdown_by_headers(document.content)
            print(f"markdown_sections={len(sections)}")
            for index, section in enumerate(sections, start=1):
                print(
                    f"  [{index}] level={section.header_level} "
                    f"header_path={section.header_path or '(preamble)'} "
                    f"range=({section.start_index}, {section.end_index})"
                )

        preview = document.content.replace("\n", " ")[:120]
        print(f"preview={preview}")


if __name__ == "__main__":
    main()
