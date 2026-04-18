from typing import Protocol

from app.schemas import RetrievalResult


class Retriever(Protocol):
    """Stable retrieval interface consumed by the RAG service."""

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        ...
