import argparse
from collections import Counter, defaultdict

from document_processing import DATA_DIR, SplitterConfig, run_document_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the chapter 2 document pipeline.")
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--chunk-overlap", type=int, default=30)
    args = parser.parse_args()

    result = run_document_pipeline(
        DATA_DIR,
        SplitterConfig(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap),
    )
    chunk_counts = Counter(chunk.metadata["filename"] for chunk in result.chunks)
    document_ids: dict[str, str] = {}
    chunk_samples: dict[str, list[str]] = defaultdict(list)

    for chunk in result.chunks:
        filename = str(chunk.metadata["filename"])
        document_ids.setdefault(filename, chunk.document_id)
        if len(chunk_samples[filename]) < 2:
            chunk_samples[filename].append(chunk.chunk_id)

    print("DocumentPipeline")
    print(
        f"summary: candidates={len(result.candidates)} accepted={result.accepted_documents} "
        f"ignored={result.ignored_candidates} total_chunks={result.total_chunks}"
    )
    print(
        f"config: chunk_size={result.config.chunk_size} "
        f"chunk_overlap={result.config.chunk_overlap}"
    )

    print("Per document:")
    for document in result.documents:
        filename = document.path.name
        print(f"- {filename}")
        print(f"  loader={document.metadata['loader']}")
        if "page_count" in document.metadata:
            print(f"  page_count={document.metadata['page_count']}")
        print(f"  document_id={document_ids[filename]}")
        print(f"  chunk_count={chunk_counts[filename]}")
        print(f"  sample_chunk_ids={chunk_samples[filename]}")
        print("  governance=update/delete should anchor on document_id; upsert should anchor on chunk_id")


if __name__ == "__main__":
    main()
