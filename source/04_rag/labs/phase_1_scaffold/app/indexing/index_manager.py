from pathlib import Path

from app.ingestion.metadata import build_base_metadata
from app.ingestion.splitters import SplitterConfig, split_text
from app.indexing.id_generator import stable_chunk_id, stable_document_id
from app.schemas import SourceChunk


def prepare_chunks(path: Path, text: str, config: SplitterConfig) -> list[SourceChunk]:
    """Convert raw text into canonical chunks for downstream indexing."""

    document_id = stable_document_id(str(path))
    base_metadata = build_base_metadata(path)
    chunks: list[SourceChunk] = []

    for index, chunk_text in enumerate(split_text(text, config)):
        chunks.append(
            SourceChunk(
                chunk_id=stable_chunk_id(document_id, index, chunk_text),
                document_id=document_id,
                content=chunk_text,
                metadata={**base_metadata, "chunk_index": index},
            )
        )

    return chunks
