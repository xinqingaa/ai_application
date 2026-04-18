from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """Project-level settings used across Phase 3 embeddings."""

    project_name: str = "rag_lab"
    data_dir: Path = Path("data")
    evals_dir: Path = Path("evals")
    vector_store_dir: Path = Path(".cache/vector_store")
    default_chunk_size: int = 220
    default_chunk_overlap: int = 40
    default_top_k: int = 5
    default_embedding_provider: str = "local_hash"
    default_embedding_model: str = "token-hash-v1"
    default_embedding_dimensions: int = 32
    default_embedding_batch_size: int = 8
    embedding_api_key_env: str = "OPENAI_API_KEY"
    embedding_base_url: str | None = None
    supported_suffixes: tuple[str, ...] = field(default_factory=lambda: (".md", ".txt"))


settings = Settings()
