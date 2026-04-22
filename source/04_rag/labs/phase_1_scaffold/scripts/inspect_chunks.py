from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.splitters import SplitterConfig, split_text
from app.indexing.index_manager import prepare_chunks


def main() -> None:
    sample_path = Path("data/sample.md")
    sample_text = (
        "This is a scaffold document. Replace it with real markdown or text files "
        "when Phase 2 starts."
    )
    chunks = prepare_chunks(sample_path, sample_text, SplitterConfig())
    print(f"Prepared {len(chunks)} chunk(s).")
    for chunk in chunks:
        print(chunk.chunk_id, chunk.metadata)


if __name__ == "__main__":
    main()
