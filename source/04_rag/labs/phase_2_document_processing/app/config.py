from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """Project-level settings used across Phase 2 document processing."""

    project_name: str = "rag_lab"
    data_dir: Path = Path("data")
    evals_dir: Path = Path("evals")
    vector_store_dir: Path = Path(".cache/vector_store")
    default_chunk_size: int = 220
    default_chunk_overlap: int = 40
    default_top_k: int = 5
    supported_suffixes: tuple[str, ...] = field(default_factory=lambda: (".md", ".txt"))


settings = Settings()
