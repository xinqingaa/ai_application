from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.indexing.index_manager import build_chunk_corpus
from app.ingestion.splitters import SplitterConfig
from app.vectorstores.chroma_store import ChromaVectorStore, ChromaVectorStoreConfig


def main() -> None:
    target_name = sys.argv[1] if len(sys.argv) > 1 else "faq.txt"
    split_config = SplitterConfig(
        chunk_size=settings.default_chunk_size,
        chunk_overlap=settings.default_chunk_overlap,
    )
    chunks = build_chunk_corpus(
        data_dir=settings.data_dir,
        config=split_config,
        supported_suffixes=settings.supported_suffixes,
    )
    document_ids = sorted(
        {
            chunk.document_id
            for chunk in chunks
            if chunk.metadata.get("filename") == target_name
            or chunk.metadata.get("source") == target_name
        }
    )
    if not document_ids:
        raise SystemExit(
            f"Could not find a source document named {target_name!r} under {settings.data_dir}."
        )

    document_id = document_ids[0]
    store = ChromaVectorStore(
        ChromaVectorStoreConfig(
            persist_directory=settings.vector_store_dir,
            collection_name=settings.default_vector_collection,
            distance_metric=settings.default_vector_distance,
        )
    )
    if store.count() == 0:
        print("Chroma collection is empty. Run `python scripts/index_chroma.py --reset` first.")
        return

    before = store.count()
    store.delete_by_document_id(document_id)
    after = store.count()
    remaining = store.get_chunks(where={"filename": target_name})

    print(f"Deleted document: {target_name}")
    print(f"document_id={document_id}")
    print(f"Collection count: {before} -> {after}")
    print(f"Remaining chunks for {target_name}: {len(remaining)}")


if __name__ == "__main__":
    main()
