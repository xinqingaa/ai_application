from collections import Counter

from document_processing import DATA_DIR, SplitterConfig, build_chunk_corpus, load_and_prepare_chunks


def main() -> None:
    config = SplitterConfig()
    chunks = build_chunk_corpus(DATA_DIR, config)
    chunk_counts = Counter(chunk.metadata["filename"] for chunk in chunks)
    stable_sample_path = DATA_DIR / "faq.txt"
    first_run = load_and_prepare_chunks(stable_sample_path, config)
    second_run = load_and_prepare_chunks(stable_sample_path, config)
    stable_ids = [chunk.chunk_id for chunk in first_run] == [chunk.chunk_id for chunk in second_run]

    print(f"Prepared {len(chunks)} chunk(s).")
    print("Per document:")
    for filename, count in sorted(chunk_counts.items()):
        print(f"- {filename}: {count} chunk(s)")

    print("Stability check:")
    print(f"- faq.txt chunk_ids stable across runs: {stable_ids}")

    print("Sample chunks:")
    for chunk in chunks[:3]:
        print(f"- chunk_id={chunk.chunk_id}")
        print(f"  document_id={chunk.document_id}")
        print(f"  source={chunk.metadata['source']}")
        print(
            f"  filename={chunk.metadata['filename']} "
            f"suffix={chunk.metadata['suffix']} loader={chunk.metadata['loader']} "
            f"chunk_index={chunk.metadata['chunk_index']}"
        )
        if "page_count" in chunk.metadata:
            print(f"  page_count={chunk.metadata['page_count']}")
        if chunk.metadata.get("header_path"):
            print(f"  header_path={chunk.metadata['header_path']}")
        print(
            f"  range=({chunk.metadata['char_start']}, {chunk.metadata['char_end']}) "
            f"chars={chunk.metadata['chunk_chars']}"
        )
        preview = chunk.content.replace("\n", " ")[:100]
        print(f"  preview={preview}")


if __name__ == "__main__":
    main()
