from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
import hashlib
import json
import os
import re
from typing import Any, Protocol


CHAPTER_ROOT = Path(__file__).resolve().parent
DATA_DIR = CHAPTER_ROOT / "data"
SOURCE_CHUNKS_PATH = DATA_DIR / "source_chunks.json"
SEARCH_CASES_PATH = DATA_DIR / "search_cases.json"

TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]", re.IGNORECASE)
STOPWORDS = {"the", "a", "an", "is", "are", "to", "of", "and", "how", "why", "do"}
CONCEPT_GROUPS = [
    ("refund", ("退款", "退费", "refund")),
    ("trial", ("试学", "预约", "trial")),
    ("metadata", ("metadata", "source", "filename", "来源")),
    ("stable_id", ("stable", "id", "document_id", "chunk_id", "稳定")),
    ("embedding", ("embedding", "向量", "vector")),
    ("similarity", ("similarity", "相似度", "检索", "retrieve")),
    ("support", ("答疑", "support", "工作日")),
]
HASH_BUCKETS = 4
MODE_BUCKETS = 2
DEFAULT_DIMENSIONS = len(CONCEPT_GROUPS) + HASH_BUCKETS + MODE_BUCKETS

SEMANTIC_CONCEPT_GROUPS = [
    ("refund", ("退款", "退费", "退钱", "退回来", "refund")),
    ("trial", ("试学", "预约", "trial")),
    ("metadata", ("metadata", "source", "filename", "header_path", "来源", "出处", "引用", "出处字段")),
    ("stable_id", ("stable", "id", "document_id", "chunk_id", "更新", "删除", "稳定")),
    ("embedding", ("embedding", "向量", "向量化")),
    ("similarity", ("similarity", "相似度", "检索", "召回")),
    ("support", ("答疑", "support", "工作日", "助教")),
]
SEMANTIC_DIMENSIONS = len(SEMANTIC_CONCEPT_GROUPS)
EMBEDDING_API_KEY_ENV_KEYS = ("EMBEDDING_API_KEY", "OPENAI_API_KEY")
EMBEDDING_BASE_URL_ENV_KEYS = ("EMBEDDING_BASE_URL", "OPENAI_BASE_URL")
EMBEDDING_MODEL_ENV_KEYS = ("EMBEDDING_MODEL", "OPENAI_EMBEDDING_MODEL")


@dataclass(frozen=True)
class SourceChunk:
    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk: SourceChunk
    vector: list[float]
    provider_name: str
    model_name: str
    dimensions: int


@dataclass(frozen=True)
class MockEmbeddingData:
    index: int
    embedding: list[float]


@dataclass(frozen=True)
class MockEmbeddingResponse:
    data: list[MockEmbeddingData]
    model: str


class EmbeddingProvider(Protocol):
    provider_name: str
    model_name: str
    dimensions: int

    def embed_query(self, text: str) -> list[float]:
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...


class LocalKeywordEmbeddingProvider:
    def __init__(
        self,
        model_name: str = "concept-space-v1",
        dimensions: int = DEFAULT_DIMENSIONS,
    ) -> None:
        if dimensions != DEFAULT_DIMENSIONS:
            raise ValueError(
                f"LocalKeywordEmbeddingProvider expects dimensions={DEFAULT_DIMENSIONS}."
            )

        self.provider_name = "local_keyword"
        self.model_name = model_name
        self.dimensions = dimensions

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, kind="query")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text, kind="document") for text in texts]

    def _embed(self, text: str, kind: str) -> list[float]:
        normalized = " ".join(text.lower().split())
        vector = [0.0] * self.dimensions

        for index, (_, keywords) in enumerate(CONCEPT_GROUPS):
            hits = sum(1 for keyword in keywords if keyword in normalized)
            vector[index] = float(hits)

        hash_offset = len(CONCEPT_GROUPS)
        for token in TOKEN_PATTERN.findall(normalized):
            if token in STOPWORDS:
                continue
            bucket = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % HASH_BUCKETS
            vector[hash_offset + bucket] += 0.25

        query_mode_index = self.dimensions - 2
        document_mode_index = self.dimensions - 1
        if kind == "query":
            vector[query_mode_index] = 0.30
        else:
            vector[document_mode_index] = 0.30

        return normalize(vector)


class OpenAICompatibleEmbeddingProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str = "text-embedding-3-small",
        expected_dimensions: int | None = None,
        client: Any | None = None,
    ) -> None:
        self.provider_name = "openai_compatible"
        self.model_name = model_name
        self.dimensions = expected_dimensions or 0
        self.api_key = api_key
        self.base_url = base_url
        self._client = client

    @classmethod
    def from_env(
        cls,
        *,
        model_name: str | None = None,
        expected_dimensions: int | None = None,
        client: Any | None = None,
    ) -> OpenAICompatibleEmbeddingProvider:
        configured_dimensions = expected_dimensions
        dimensions_text = os.getenv("EMBEDDING_DIMENSIONS")
        if configured_dimensions is None and dimensions_text:
            configured_dimensions = int(dimensions_text)

        return cls(
            api_key=first_env(*EMBEDDING_API_KEY_ENV_KEYS),
            base_url=first_env(*EMBEDDING_BASE_URL_ENV_KEYS),
            model_name=(
                model_name
                or first_env(*EMBEDDING_MODEL_ENV_KEYS)
                or "text-embedding-3-small"
            ),
            expected_dimensions=configured_dimensions,
            client=client,
        )

    @property
    def is_ready(self) -> bool:
        return self._client is not None or bool(self.api_key)

    def describe(self) -> dict[str, str | int | bool | None]:
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "dimensions": self.dimensions or None,
            "ready": self.is_ready,
            "client_type": type(self._client).__name__ if self._client else None,
        }

    def embed_query(self, text: str) -> list[float]:
        vectors = self._embed_many([text])
        return vectors[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_many(texts)

    def _embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        client = self._ensure_client()
        response = client.embeddings.create(model=self.model_name, input=texts)
        data = getattr(response, "data", None)
        if not isinstance(data, list):
            raise ValueError("Embedding response must expose a list-like `data` field.")

        vectors: list[list[float]] = []
        for index, item in enumerate(data):
            raw_vector = getattr(item, "embedding", None)
            if not isinstance(raw_vector, list):
                raise ValueError(f"Embedding item at index {index} is missing a vector.")
            self._record_dimensions(raw_vector)
            vectors.append(normalize([float(value) for value in raw_vector]))

        if len(vectors) != len(texts):
            raise ValueError("Embedding provider returned an unexpected vector count.")
        return vectors

    def _record_dimensions(self, vector: list[float]) -> None:
        if self.dimensions == 0:
            self.dimensions = len(vector)
            return
        if len(vector) != self.dimensions:
            raise ValueError(
                f"Embedding vector has dimensions={len(vector)}, expected {self.dimensions}."
            )

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise ValueError(
                "Missing embedding API key. Set EMBEDDING_API_KEY or OPENAI_API_KEY."
            )

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on local env
            raise ImportError(
                "openai is required for real embedding calls. Run `python -m pip install -r requirements.txt`."
            ) from exc

        kwargs: dict[str, str] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = OpenAI(**kwargs)
        return self._client


class MockSemanticOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = _MockSemanticEmbeddingsResource()


class _MockSemanticEmbeddingsResource:
    def create(self, *, model: str, input: list[str] | str) -> MockEmbeddingResponse:
        texts = [input] if isinstance(input, str) else list(input)
        return MockEmbeddingResponse(
            data=[
                MockEmbeddingData(index=index, embedding=build_mock_semantic_vector(text))
                for index, text in enumerate(texts)
            ],
            model=model,
        )


def first_env(*keys: str) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return None


def demo_chunk_metadata(source: str, content: str, chunk_index: int = 0) -> dict[str, str | int]:
    filename = source.rsplit("/", maxsplit=1)[-1]
    suffix = f".{filename.rsplit('.', maxsplit=1)[-1]}" if "." in filename else ""
    char_count = len(content)
    line_count = 0 if not content else content.count("\n") + 1
    return {
        "source": source,
        "filename": filename,
        "suffix": suffix,
        "char_count": char_count,
        "line_count": line_count,
        "chunk_index": chunk_index,
        "char_start": 0,
        "char_end": char_count,
        "chunk_chars": char_count,
    }


def load_demo_source_chunk_specs(path: Path | None = None) -> list[dict[str, Any]]:
    target_path = path or SOURCE_CHUNKS_PATH
    with target_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise TypeError("source chunk specs must be a list")
    return data


def load_search_cases(path: Path | None = None) -> list[dict[str, Any]]:
    target_path = path or SEARCH_CASES_PATH
    with target_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise TypeError("search cases must be a list")
    return data


def build_openai_provider_or_mock(
    *,
    force_mock: bool = False,
    model_name: str | None = None,
) -> tuple[OpenAICompatibleEmbeddingProvider, str]:
    if force_mock:
        return (
            OpenAICompatibleEmbeddingProvider(
                client=MockSemanticOpenAIClient(),
                model_name=model_name or "mock-semantic-bridge",
                expected_dimensions=SEMANTIC_DIMENSIONS,
            ),
            "mock",
        )

    provider = OpenAICompatibleEmbeddingProvider.from_env(model_name=model_name)
    if provider.is_ready:
        return provider, "real"

    return (
        OpenAICompatibleEmbeddingProvider(
            client=MockSemanticOpenAIClient(),
            model_name=model_name or "mock-semantic-bridge",
            expected_dimensions=SEMANTIC_DIMENSIONS,
        ),
        "mock",
    )


def demo_source_chunks(path: Path | None = None) -> list[SourceChunk]:
    chunks: list[SourceChunk] = []
    for spec in load_demo_source_chunk_specs(path):
        source = str(spec["source"])
        content = str(spec["content"])
        chunk_index = int(spec.get("chunk_index", 0))
        metadata = demo_chunk_metadata(source, content, chunk_index)

        extra_metadata = spec.get("metadata")
        if isinstance(extra_metadata, dict):
            metadata.update(extra_metadata)

        chunks.append(
            SourceChunk(
                chunk_id=str(spec["chunk_id"]),
                document_id=str(spec["document_id"]),
                content=content,
                metadata=metadata,
            )
        )
    return chunks


def ensure_vector_dimensions(
    vector: list[float],
    expected_dimensions: int,
    context: str,
) -> None:
    if len(vector) != expected_dimensions:
        raise ValueError(
            f"{context} has dimensions={len(vector)}, expected {expected_dimensions}."
        )


def ensure_same_embedding_space(
    chunk: EmbeddedChunk,
    provider: EmbeddingProvider,
) -> None:
    if chunk.provider_name != provider.provider_name or chunk.model_name != provider.model_name:
        raise ValueError("Query and document vectors must come from the same provider/model.")

    if chunk.dimensions != provider.dimensions:
        raise ValueError("Embedded chunk dimensions do not match provider dimensions.")

    ensure_vector_dimensions(
        chunk.vector,
        chunk.dimensions,
        context=f"embedded chunk {chunk.chunk.chunk_id}",
    )


def embed_chunks(
    chunks: list[SourceChunk],
    provider: EmbeddingProvider,
) -> list[EmbeddedChunk]:
    if not chunks:
        return []

    vectors = provider.embed_documents([chunk.content for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Embedding provider returned an unexpected vector count.")

    embedded_chunks: list[EmbeddedChunk] = []
    for chunk, vector in zip(chunks, vectors):
        ensure_vector_dimensions(
            vector,
            provider.dimensions,
            context=f"document vector for {chunk.chunk_id}",
        )
        embedded_chunks.append(
            EmbeddedChunk(
                chunk=chunk,
                vector=vector,
                provider_name=provider.provider_name,
                model_name=provider.model_name,
                dimensions=provider.dimensions,
            )
        )
    return embedded_chunks


def cosine_similarity(left: list[float], right: list[float]) -> float:
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
    if not chunks:
        return []

    query_vector = provider.embed_query(question)
    ensure_vector_dimensions(query_vector, provider.dimensions, context="query vector")
    scored: list[tuple[EmbeddedChunk, float]] = []
    for chunk in chunks:
        ensure_same_embedding_space(chunk, provider)
        scored.append((chunk, cosine_similarity(query_vector, chunk.vector)))
    return sorted(scored, key=lambda item: item[1], reverse=True)


def build_mock_semantic_vector(text: str) -> list[float]:
    normalized = " ".join(text.lower().split())
    vector = [0.0] * SEMANTIC_DIMENSIONS

    for index, (_, keywords) in enumerate(SEMANTIC_CONCEPT_GROUPS):
        hits = sum(1.0 for keyword in keywords if keyword in normalized)
        vector[index] = hits

    return normalize(vector)


def normalize(vector: list[float]) -> list[float]:
    norm = sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]
