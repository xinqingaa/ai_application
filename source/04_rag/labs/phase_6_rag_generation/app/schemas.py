from dataclasses import dataclass, field


@dataclass(slots=True)
class SourceChunk:
    """Canonical chunk object shared by ingestion, indexing, and retrieval."""

    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(slots=True)
class EmbeddedChunk:
    """Phase 3 object: keep the canonical SourceChunk and add vector payload."""

    chunk: SourceChunk
    vector: list[float]
    provider_name: str
    model_name: str
    dimensions: int


@dataclass(slots=True)
class RetrievalResult:
    """A retrieved chunk plus optional retrieval score."""

    chunk: SourceChunk
    score: float | None = None


@dataclass(slots=True)
class AnswerResult:
    """Minimal response structure returned by the RAG service."""

    answer: str
    sources: list[SourceChunk] = field(default_factory=list)


@dataclass(slots=True)
class EvalSample:
    """Golden set item used by the evaluation layer."""

    question: str
    expected_answer: str
    expected_sources: list[str] = field(default_factory=list)
