"""RAG-side embedding records and similarity observations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt
from typing import Sequence

from llm_core import EmbeddingResponse, LLMClient


class SimilarityMetric(str, Enum):
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"


@dataclass(frozen=True)
class EmbeddingRecord:
    text: str
    vector: tuple[float, ...]
    model: str
    dimensions: int
    config_ref: str
    provider: str
    text_id: str | None = None
    preprocessing_version: str = "raw-v1"


@dataclass(frozen=True)
class SimilarityObservation:
    left_text: str
    right_text: str
    left_id: str | None
    right_id: str | None
    score: float
    metric: SimilarityMetric
    higher_is_closer: bool
    provider: str
    config_ref: str
    model: str
    dimensions: int
    preprocessing_version: str


@dataclass(frozen=True)
class EmbeddingBatchResult:
    records: tuple[EmbeddingRecord, ...]
    response: EmbeddingResponse


def embed_texts(
    texts: Sequence[str],
    *,
    client: LLMClient | None = None,
    config_ref: str = "embedding.default_embed",
    text_ids: Sequence[str] | None = None,
    preprocessing_version: str = "raw-v1",
    debug: bool = False,
) -> EmbeddingBatchResult:
    if text_ids is not None and len(text_ids) != len(texts):
        raise ValueError("text_ids 数量必须与 texts 一致")
    if not preprocessing_version.strip():
        raise ValueError("preprocessing_version 不能为空")

    llm = client or LLMClient.from_default_config()
    response = llm.embed(list(texts), config_ref, debug=debug)
    records = tuple(
        EmbeddingRecord(
            text=text,
            vector=vector,
            model=response.model,
            dimensions=response.dimensions,
            config_ref=response.config_ref,
            provider=response.provider,
            text_id=None if text_ids is None else text_ids[index],
            preprocessing_version=preprocessing_version,
        )
        for index, (text, vector) in enumerate(zip(texts, response.vectors, strict=True))
    )
    return EmbeddingBatchResult(records=records, response=response)


def similarity(
    left: Sequence[float] | EmbeddingRecord,
    right: Sequence[float] | EmbeddingRecord,
    *,
    metric: SimilarityMetric = SimilarityMetric.COSINE,
) -> float:
    left_vector = left.vector if isinstance(left, EmbeddingRecord) else tuple(left)
    right_vector = right.vector if isinstance(right, EmbeddingRecord) else tuple(right)
    if len(left_vector) != len(right_vector):
        raise ValueError(
            f"向量维度不一致：{len(left_vector)} vs {len(right_vector)}"
        )
    if metric is SimilarityMetric.DOT:
        return _dot(left_vector, right_vector)
    if metric is SimilarityMetric.EUCLIDEAN:
        return sqrt(sum((a - b) ** 2 for a, b in zip(left_vector, right_vector, strict=True)))
    return _cosine(left_vector, right_vector)


def pairwise_similarity(
    records: Sequence[EmbeddingRecord],
    *,
    metric: SimilarityMetric = SimilarityMetric.COSINE,
) -> tuple[SimilarityObservation, ...]:
    if len(records) < 2:
        raise ValueError("pairwise_similarity 至少需要两条 EmbeddingRecord")

    higher_is_closer = metric is not SimilarityMetric.EUCLIDEAN
    observations: list[SimilarityObservation] = []
    for left_index, left in enumerate(records):
        for right in records[left_index + 1 :]:
            left_space = _space_identity(left)
            right_space = _space_identity(right)
            if left_space != right_space:
                raise ValueError(
                    "不能比较不同 Embedding 空间的 EmbeddingRecord；"
                    f"left={left_space} right={right_space}"
                )
            observations.append(
                SimilarityObservation(
                    left_text=left.text,
                    right_text=right.text,
                    left_id=left.text_id,
                    right_id=right.text_id,
                    score=similarity(left, right, metric=metric),
                    metric=metric,
                    higher_is_closer=higher_is_closer,
                    provider=left.provider,
                    config_ref=left.config_ref,
                    model=left.model,
                    dimensions=left.dimensions,
                    preprocessing_version=left.preprocessing_version,
                )
            )
    return tuple(observations)


def _space_identity(record: EmbeddingRecord) -> tuple[str, str, str, int, str]:
    return (
        record.provider,
        record.config_ref,
        record.model,
        record.dimensions,
        record.preprocessing_version,
    )


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    left_norm = sqrt(_dot(left, left))
    right_norm = sqrt(_dot(right, right))
    if left_norm == 0.0 or right_norm == 0.0:
        raise ValueError("零向量无法计算 cosine 相似度")
    return _dot(left, right) / (left_norm * right_norm)
