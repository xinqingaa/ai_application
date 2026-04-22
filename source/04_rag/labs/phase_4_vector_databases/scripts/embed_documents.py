from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.embeddings.providers import EmbeddingProviderConfig, create_embedding_provider
from app.embeddings.vectorizer import build_embedded_chunk_corpus
from app.ingestion.splitters import SplitterConfig


def print_lineage() -> None:
    print("Lineage:")
    print("- Phase 1 fixed the canonical SourceChunk contract.")
    print("- Phase 2 turned files into stable SourceChunk objects.")
    print("- Phase 3 keeps that chunk identity and adds vectors.")


def main() -> None:
    split_config = SplitterConfig(
        chunk_size=settings.default_chunk_size,
        chunk_overlap=settings.default_chunk_overlap,
    )
    provider = create_embedding_provider(
        EmbeddingProviderConfig(
            provider_name=settings.default_embedding_provider,
            model_name=settings.default_embedding_model,
            dimensions=settings.default_embedding_dimensions,
            api_key_env=settings.embedding_api_key_env,
            base_url=settings.embedding_base_url,
        )
    )
    embedded_chunks = build_embedded_chunk_corpus(
        data_dir=settings.data_dir,
        split_config=split_config,
        supported_suffixes=settings.supported_suffixes,
        provider=provider,
        batch_size=settings.default_embedding_batch_size,
    )

    print_lineage()
    print(
        "Provider: "
        f"{provider.provider_name} / {provider.model_name} / dims={provider.dimensions}"
    )
    print(
        f"Embedded {len(embedded_chunks)} chunk(s) from {settings.data_dir.as_posix()} "
        f"with batch_size={settings.default_embedding_batch_size}."
    )
    for embedded_chunk in embedded_chunks[:5]:
        metadata = embedded_chunk.chunk.metadata
        vector_preview = ", ".join(f"{value:.3f}" for value in embedded_chunk.vector[:6])
        content_preview = embedded_chunk.chunk.content.replace("\n", " ")[:72]
        print(
            f"- chunk_id={embedded_chunk.chunk.chunk_id} "
            f"document_id={embedded_chunk.chunk.document_id}"
        )
        print(
            "    inherited="
            f"source={metadata['source']} "
            f"filename={metadata['filename']} "
            f"chunk={metadata['chunk_index']} "
            f"chars={metadata['char_start']}:{metadata['char_end']}"
        )
        print(
            "    added="
            f"provider={embedded_chunk.provider_name} "
            f"model={embedded_chunk.model_name} "
            f"dims={embedded_chunk.dimensions} "
            f"vector=[{vector_preview}]"
        )
        print(f"    preview={content_preview}")


if __name__ == "__main__":
    main()
