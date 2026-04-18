from dataclasses import dataclass, field

from app.schemas import RetrievalResult, SourceChunk


@dataclass(slots=True)
class InMemoryVectorStore:
    """Temporary stand-in used until a real Chroma adapter is added."""

    chunks: list[SourceChunk] = field(default_factory=list)

    def add(self, chunks: list[SourceChunk]) -> None:
        self.chunks.extend(chunks)

    def similarity_search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        ranked = sorted(
            self.chunks,
            key=lambda chunk: abs(len(chunk.content) - len(query)),
        )
        return [RetrievalResult(chunk=item, score=None) for item in ranked[:top_k]]

    def delete(self, document_id: str) -> None:
        self.chunks = [
            chunk for chunk in self.chunks if chunk.document_id != document_id
        ]
