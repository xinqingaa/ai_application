from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.indexing.index_manager import load_and_prepare_chunks
from app.ingestion.splitters import SplitterConfig


def main() -> None:
    sample_path = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/product_overview.md")
    )
    config = SplitterConfig(
        chunk_size=settings.default_chunk_size,
        chunk_overlap=settings.default_chunk_overlap,
    )
    chunks = load_and_prepare_chunks(sample_path, config)

    print(f"Inspecting: {sample_path.as_posix()}")
    print(f"Prepared {len(chunks)} chunk(s).")
    for chunk in chunks:
        preview = chunk.content.replace("\n", " ")[:80]
        print(
            f"[{chunk.metadata['chunk_index']}] {chunk.chunk_id} "
            f"chars={chunk.metadata['char_start']}:{chunk.metadata['char_end']} "
            f"len={chunk.metadata['chunk_chars']}"
        )
        print(f"    source={chunk.metadata['source']}")
        print(f"    preview={preview}")


if __name__ == "__main__":
    main()
