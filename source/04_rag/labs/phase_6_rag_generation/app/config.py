from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """Project-level settings used across Phase 6 RAG generation."""

    project_name: str = "rag_lab"
    data_dir: Path = Path("data")
    evals_dir: Path = Path("evals")
    vector_store_dir: Path = Path(".cache/chroma")
    default_vector_collection: str = "course_chunks"
    default_vector_distance: str = "cosine"
    default_vector_store_batch_size: int = 32
    default_chunk_size: int = 220
    default_chunk_overlap: int = 40
    default_top_k: int = 5
    default_retrieval_strategy: str = "similarity"
    default_retrieval_candidate_k: int = 8
    default_retrieval_score_threshold: float = 0.70
    default_retrieval_mmr_lambda: float = 0.35
    default_embedding_provider: str = "local_hash"
    default_embedding_model: str = "token-hash-v1"
    default_embedding_dimensions: int = 32
    default_embedding_batch_size: int = 8
    embedding_api_key_env: str = "OPENAI_API_KEY"
    embedding_base_url: str | None = None
    default_generation_provider: str = "mock"
    default_generation_model: str = "gpt-4o-mini"
    generation_api_key_env: str = "OPENAI_API_KEY"
    generation_base_url_env: str = "OPENAI_BASE_URL"
    default_generation_base_url: str | None = None
    default_generation_temperature: float = 0.0
    default_generation_max_tokens: int = 280
    default_generation_min_score: float = 0.60
    default_context_max_chunks: int = 4
    default_context_max_chars_per_chunk: int = 320
    supported_suffixes: tuple[str, ...] = field(default_factory=lambda: (".md", ".txt"))


settings = Settings()
