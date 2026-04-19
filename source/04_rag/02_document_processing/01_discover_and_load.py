from document_processing import DATA_DIR, discover_documents, load_document


def main() -> None:
    documents = discover_documents(DATA_DIR)
    print(f"Discovered {len(documents)} supported document(s).")

    for path in documents:
        text = load_document(path)
        first_line = text.splitlines()[0] if text else "(empty)"
        print(f"- {path.name}")
        print(f"  chars={len(text)} lines={text.count(chr(10)) + 1 if text else 0}")
        print(f"  preview={first_line}")


if __name__ == "__main__":
    main()
