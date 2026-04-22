from typing import Protocol

from app.schemas import RetrievalResult


class Retriever(Protocol):
    """Minimal retriever protocol for the scaffold."""

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        ...
