"""Embedding-space and vector-index contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import isfinite
from typing import Sequence

from rag_core.embedding.models import EmbeddingRecord


@dataclass(frozen=True)
class EmbeddingSpace:
    provider: str
    config_ref: str
    model: str
    dimensions: int
    preprocessing_version: str

    def __post_init__(self) -> None:
        values = (
            self.provider,
            self.config_ref,
            self.model,
            self.preprocessing_version,
        )
        if any(not value.strip() for value in values):
            raise ValueError("EmbeddingSpace 的文本身份字段不能为空")
        if self.dimensions <= 0:
            raise ValueError("EmbeddingSpace.dimensions 必须大于 0")

    @classmethod
    def from_record(cls, record: EmbeddingRecord) -> EmbeddingSpace:
        if len(record.vector) != record.dimensions:
            raise ValueError(
                "EmbeddingRecord.vector 长度必须等于 dimensions；"
                f"actual={len(record.vector)} declared={record.dimensions}"
            )
        if any(not isfinite(value) for value in record.vector):
            raise ValueError("EmbeddingRecord.vector 不能包含 NaN 或 Infinity")
        if not any(value != 0.0 for value in record.vector):
            raise ValueError("cosine Dense Retrieval 不接受零向量")
        return cls(
            provider=record.provider,
            config_ref=record.config_ref,
            model=record.model,
            dimensions=record.dimensions,
            preprocessing_version=record.preprocessing_version,
        )

    @classmethod
    def from_records(cls, records: Sequence[EmbeddingRecord]) -> EmbeddingSpace:
        if not records:
            raise ValueError("至少需要一条 EmbeddingRecord")
        expected = cls.from_record(records[0])
        for record in records[1:]:
            actual = cls.from_record(record)
            if actual != expected:
                raise ValueError(
                    "一次向量入库不能混用不同 Embedding 空间；"
                    f"expected={expected.space_ref} actual={actual.space_ref}"
                )
        return expected

    @property
    def fingerprint(self) -> str:
        payload = {
            "provider": self.provider,
            "config_ref": self.config_ref,
            "model": self.model,
            "dimensions": self.dimensions,
            "preprocessing_version": self.preprocessing_version,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return hashlib.sha256(encoded).hexdigest()[:16]

    @property
    def space_ref(self) -> str:
        return f"embedding-space@1:{self.fingerprint}"


@dataclass(frozen=True)
class VectorIndexReport:
    indexed_embeddings: int
    embedding_space: EmbeddingSpace
    latency_ms: float


@dataclass(frozen=True)
class HNSWIndexReport:
    index_name: str
    embedding_space: EmbeddingSpace
    latency_ms: float


@dataclass(frozen=True)
class VectorDeleteReport:
    deleted_embeddings: int
    latency_ms: float


def hnsw_index_name(space: EmbeddingSpace) -> str:
    return f"rag_chunk_embeddings_hnsw_{space.fingerprint}"
