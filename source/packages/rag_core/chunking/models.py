"""Data contracts for traceable document chunking."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from rag_core.ingestion.models import (
    EvidenceEligibility,
    FileFormat,
    SourceLocator,
    SourceRole,
)


class ChunkKind(str, Enum):
    STANDALONE = "standalone"
    PARENT = "parent"
    CHILD = "child"


class ChunkStrategy(str, Enum):
    ELEMENT = "element"
    FIXED_WINDOW = "fixed_window"
    STRUCTURE_AWARE = "structure_aware"
    PARENT_CHILD = "parent_child"


@dataclass(frozen=True)
class ChunkPolicy:
    name: str
    version: str
    strategy: ChunkStrategy
    max_tokens: int = 96
    overlap_tokens: int = 0
    parent_max_tokens: int = 192
    tokenizer: str = "o200k_base"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("ChunkPolicy.name 不能为空")
        if not self.version.strip():
            raise ValueError("ChunkPolicy.version 不能为空")
        if self.max_tokens <= 0:
            raise ValueError("ChunkPolicy.max_tokens 必须大于 0")
        if self.overlap_tokens < 0:
            raise ValueError("ChunkPolicy.overlap_tokens 不能小于 0")
        if self.overlap_tokens >= self.max_tokens:
            raise ValueError("ChunkPolicy.overlap_tokens 必须小于 max_tokens")
        if (
            self.strategy is ChunkStrategy.PARENT_CHILD
            and self.parent_max_tokens < self.max_tokens
        ):
            raise ValueError("ChunkPolicy.parent_max_tokens 不能小于 max_tokens")
        if not self.tokenizer.strip():
            raise ValueError("ChunkPolicy.tokenizer 不能为空")

    @property
    def fingerprint(self) -> str:
        payload = {
            "name": self.name,
            "version": self.version,
            "strategy": self.strategy.value,
            "max_tokens": self.max_tokens,
            "overlap_tokens": self.overlap_tokens,
            "parent_max_tokens": self.parent_max_tokens,
            "tokenizer": self.tokenizer,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return hashlib.sha256(encoded).hexdigest()[:16]


@dataclass(frozen=True)
class ChunkSourceSpan:
    element_id: str
    locator: SourceLocator
    start_char: int
    end_char: int
    text: str

    def __post_init__(self) -> None:
        if not self.element_id:
            raise ValueError("ChunkSourceSpan.element_id 不能为空")
        if self.start_char < 0 or self.end_char <= self.start_char:
            raise ValueError("ChunkSourceSpan 字符范围无效")
        if not self.text:
            raise ValueError("ChunkSourceSpan.text 不能为空")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    kind: ChunkKind
    document_id: str
    document_version: str
    original_filename: str
    file_format: FileFormat
    source_role: SourceRole
    evidence_eligibility: EvidenceEligibility
    text: str
    ordinal: int
    token_count: int
    source_spans: tuple[ChunkSourceSpan, ...]
    policy_name: str
    policy_version: str
    policy_fingerprint: str
    parent_chunk_id: str | None = None
    business_metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ChunkReport:
    document_id: str
    document_version: str
    policy_name: str
    policy_version: str
    policy_fingerprint: str
    strategy: ChunkStrategy
    chunk_count: int
    standalone_count: int
    parent_count: int
    child_count: int
    source_span_count: int
    min_tokens: int
    median_tokens: int
    p95_tokens: int
    max_tokens: int
    total_chunk_tokens: int
    source_tokens: int
    repeated_tokens: int
    repetition_ratio: float


@dataclass(frozen=True)
class ChunkResult:
    chunks: tuple[Chunk, ...]
    report: ChunkReport

    @property
    def retrieval_chunks(self) -> tuple[Chunk, ...]:
        return tuple(
            chunk for chunk in self.chunks if chunk.kind is not ChunkKind.PARENT
        )

    @property
    def parent_chunks(self) -> tuple[Chunk, ...]:
        return tuple(chunk for chunk in self.chunks if chunk.kind is ChunkKind.PARENT)
