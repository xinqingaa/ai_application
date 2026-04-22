from document_processing import (
    DATA_DIR,
    discover_documents,
    inspect_document_candidates,
    load_document_record,
)


def main() -> None:
    candidates = inspect_document_candidates(DATA_DIR)
    documents = discover_documents(DATA_DIR)
    print(f"Found {len(candidates)} file candidate(s) under data/.")
    print(f"Accepted {len(documents)} supported document(s).")

    print("Discovery decisions:")
    for candidate in candidates:
        status = "accepted" if candidate.accepted else "ignored"
        print(f"- {candidate.path.name}: {status} ({candidate.reason})")

    print("Loaded documents:")
    for path in documents:
        document = load_document_record(path)
        text = document.content
        first_line = text.splitlines()[0] if text else "(empty)"
        print(f"- {path.name}")
        print(f"  loader={document.metadata['loader']}")
        if "page_count" in document.metadata:
            print(f"  pages={document.metadata['page_count']}")
        print(f"  chars={len(text)} lines={text.count(chr(10)) + 1 if text else 0}")
        print(f"  preview={first_line}")


if __name__ == "__main__":
    main()
