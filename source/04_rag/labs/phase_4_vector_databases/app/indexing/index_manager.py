from pathlib import Path

from app.ingestion.loaders import discover_documents, load_document
from app.ingestion.metadata import build_base_metadata, build_chunk_metadata
from app.ingestion.splitters import SplitterConfig, split_text
from app.indexing.id_generator import stable_chunk_id, stable_document_id
from app.schemas import SourceChunk


def prepare_chunks(path: Path, text: str, config: SplitterConfig) -> list[SourceChunk]:
    """Convert raw text into canonical chunks for downstream indexing."""

    resolved_path = path.resolve()
    document_id = stable_document_id(resolved_path.as_posix())
    base_metadata = build_base_metadata(path, text)
    chunks: list[SourceChunk] = []

    for index, chunk in enumerate(split_text(text, config)):
        chunks.append(
            SourceChunk(
                chunk_id=stable_chunk_id(document_id, index, chunk.content),
                document_id=document_id,
                content=chunk.content,
                metadata=build_chunk_metadata(
                    base_metadata=base_metadata,
                    chunk_index=index,
                    start_index=chunk.start_index,
                    end_index=chunk.end_index,
                ),
            )
        )

    return chunks


def load_and_prepare_chunks(path: Path, config: SplitterConfig) -> list[SourceChunk]:
    """Load a document from disk and convert it into canonical chunks."""

    text = load_document(path)
    return prepare_chunks(path, text, config)


def build_chunk_corpus(
    data_dir: Path, config: SplitterConfig, supported_suffixes: tuple[str, ...]
) -> list[SourceChunk]:
    """Load every supported document under data_dir and return one flat chunk list."""

    chunks: list[SourceChunk] = []
    for path in discover_documents(data_dir, supported_suffixes):
        chunks.extend(load_and_prepare_chunks(path, config))
    return chunks
