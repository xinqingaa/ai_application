from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.indexing.index_manager import load_and_prepare_chunks
from app.ingestion.loaders import discover_documents
from app.ingestion.splitters import SplitterConfig


def main() -> None:
    config = SplitterConfig(
        chunk_size=settings.default_chunk_size,
        chunk_overlap=settings.default_chunk_overlap,
    )
    documents = discover_documents(settings.data_dir, settings.supported_suffixes)

    print(f"Discovered {len(documents)} document(s) under {settings.data_dir}.")
    total_chunks = 0
    for path in documents:
        chunks = load_and_prepare_chunks(path, config)
        total_chunks += len(chunks)
        print(f"- {path.as_posix()}: {len(chunks)} chunk(s)")

    print(f"Chunk config: size={config.chunk_size}, overlap={config.chunk_overlap}")
    print(f"Prepared {total_chunks} chunk(s) in total.")


if __name__ == "__main__":
    main()
