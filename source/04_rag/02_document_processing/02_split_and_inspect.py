import argparse
from pathlib import Path
import sys

from document_processing import DATA_DIR, SplitterConfig, load_document, split_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect document chunks.")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/product_overview.md",
        help="Document path relative to the chapter directory.",
    )
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--chunk-overlap", type=int, default=30)
    args = parser.parse_args()

    target = Path(args.path)
    if not target.is_absolute():
        target = DATA_DIR.parent / target

    try:
        config = SplitterConfig(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    except ValueError as exc:
        print(f"Invalid splitter config: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    text = load_document(target)
    chunks = split_text(text, config)

    print(f"document={target.name}")
    print(f"chunk_size={config.chunk_size} chunk_overlap={config.chunk_overlap}")
    print(f"total_chunks={len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        preview = chunk.content.replace("\n", " ")[:90]
        print(
            f"[{index}] start={chunk.start_index} end={chunk.end_index} "
            f"chars={chunk.end_index - chunk.start_index}"
        )
        print(f"    {preview}")


if __name__ == "__main__":
    main()
