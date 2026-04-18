from math import sqrt

from app.embeddings.providers import EmbeddingProvider
from app.schemas import EmbeddedChunk


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for two equal-length vectors."""

    if len(left) != len(right):
        raise ValueError("Cosine similarity requires vectors with the same dimensions.")

    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)


def score_query_against_chunks(
    question: str,
    chunks: list[EmbeddedChunk],
    provider: EmbeddingProvider,
) -> list[tuple[EmbeddedChunk, float]]:
    """Rank embedded chunks by cosine similarity against a query vector."""

    if not chunks:
        return []

    query_vector = provider.embed_query(question)
    scored = [
        (chunk, cosine_similarity(query_vector, chunk.vector))
        for chunk in chunks
    ]
    return sorted(scored, key=lambda item: item[1], reverse=True)
