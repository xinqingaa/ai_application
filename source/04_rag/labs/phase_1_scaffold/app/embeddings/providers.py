from typing import Protocol


class EmbeddingProvider(Protocol):
    """Common interface for query/document embeddings."""

    def embed_query(self, text: str) -> list[float]:
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...


class MockEmbeddingProvider:
    """A placeholder provider that keeps Phase 1 importable without external deps."""

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text))] for text in texts]
