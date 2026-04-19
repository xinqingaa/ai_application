from collections import Counter

from document_processing import DATA_DIR, SplitterConfig, build_chunk_corpus


def main() -> None:
    chunks = build_chunk_corpus(DATA_DIR, SplitterConfig())
    chunk_counts = Counter(chunk.metadata["filename"] for chunk in chunks)

    print(f"Prepared {len(chunks)} chunk(s).")
    print("Per document:")
    for filename, count in sorted(chunk_counts.items()):
        print(f"- {filename}: {count} chunk(s)")

    print("Sample chunks:")
    for chunk in chunks[:3]:
        print(f"- chunk_id={chunk.chunk_id}")
        print(f"  document_id={chunk.document_id}")
        print(f"  source={chunk.metadata['source']}")
        print(
            f"  range=({chunk.metadata['char_start']}, {chunk.metadata['char_end']}) "
            f"chars={chunk.metadata['chunk_chars']}"
        )
        preview = chunk.content.replace("\n", " ")[:100]
        print(f"  preview={preview}")


if __name__ == "__main__":
    main()
