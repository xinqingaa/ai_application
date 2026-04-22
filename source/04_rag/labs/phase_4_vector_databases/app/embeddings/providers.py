from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b
from math import sqrt
from os import getenv
import re
from typing import Protocol

TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]+", re.IGNORECASE)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "do",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "not",
    "of",
    "on",
    "or",
    "the",
    "they",
    "this",
    "to",
    "we",
    "what",
    "when",
    "where",
    "why",
}


class EmbeddingProvider(Protocol):
    """Common interface for query/document embeddings."""

    provider_name: str
    model_name: str
    dimensions: int

    def embed_query(self, text: str) -> list[float]:
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        ...


@dataclass(slots=True)
class EmbeddingProviderConfig:
    """Minimal configuration required to construct an embedding provider."""

    provider_name: str
    model_name: str
    dimensions: int
    api_key_env: str | None = None
    base_url: str | None = None


class LocalHashEmbeddingProvider:
    """Deterministic local provider used for offline study and tests."""

    def __init__(self, model_name: str = "token-hash-v1", dimensions: int = 32) -> None:
        if dimensions <= 0:
            raise ValueError("Embedding dimensions must be positive.")

        self.provider_name = "local_hash"
        self.model_name = model_name
        self.dimensions = dimensions

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text, kind="query")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text, kind="document") for text in texts]

    def _embed(self, text: str, kind: str) -> list[float]:
        vector = [0.0] * self.dimensions
        features = self._collect_features(text)

        for feature, weight in features:
            primary_index, primary_sign = self._project(feature)
            secondary_index, secondary_sign = self._project(f"{feature}:secondary")
            vector[primary_index] += primary_sign * weight
            vector[secondary_index] += secondary_sign * weight * 0.5

        # Keep query/document interfaces distinct without breaking comparability.
        mode_index, mode_sign = self._project(f"kind:{kind}")
        vector[mode_index] += mode_sign * 0.15

        return _normalize(vector)

    def _collect_features(self, text: str) -> list[tuple[str, float]]:
        normalized = " ".join(text.lower().split())
        compact = normalized.replace(" ", "")
        tokens = [
            token
            for token in TOKEN_PATTERN.findall(normalized)
            if token not in STOPWORDS
        ]
        features: list[tuple[str, float]] = []

        for token in tokens:
            token_weight = 1.2 + min(len(token), 10) * 0.05
            features.append((f"token:{token}", token_weight))

        for first, second in zip(tokens, tokens[1:]):
            features.append((f"pair:{first}->{second}", 0.45))

        if compact and tokens:
            for index in range(max(0, len(compact) - 2)):
                trigram = compact[index : index + 3]
                if len(trigram) == 3:
                    features.append((f"gram:{trigram}", 0.08))
        elif compact:
            if len(compact) < 3:
                features.append((f"chars:{compact}", 0.15))
            else:
                for index in range(len(compact) - 2):
                    trigram = compact[index : index + 3]
                    features.append((f"gram:{trigram}", 0.08))
        else:
            features.append(("__empty__", 1.0))

        return features

    def _project(self, feature: str) -> tuple[int, float]:
        digest = blake2b(feature.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % self.dimensions
        # The local teaching provider favors intuitive overlap scores over
        # high-variance random projections, so collisions stay additive.
        sign = 1.0
        return index, sign


class OpenAICompatibleEmbeddingProvider:
    """Optional provider for OpenAI-compatible embedding APIs."""

    def __init__(
        self,
        model_name: str,
        dimensions: int,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI-compatible embeddings require the `openai` package."
            ) from exc

        api_key = getenv(api_key_env)
        if not api_key:
            raise RuntimeError(
                f"Environment variable `{api_key_env}` is required for provider "
                "`openai_compatible`."
            )

        self.provider_name = "openai_compatible"
        self.model_name = model_name
        self.dimensions = dimensions
        self._client = OpenAI(api_key=api_key, base_url=base_url or None)

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_batch(texts)

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        request_kwargs: dict[str, object] = {
            "model": self.model_name,
            "input": texts,
        }
        if self.dimensions > 0:
            request_kwargs["dimensions"] = self.dimensions

        response = self._client.embeddings.create(**request_kwargs)
        return [item.embedding for item in response.data]


def create_embedding_provider(config: EmbeddingProviderConfig) -> EmbeddingProvider:
    """Factory used by scripts and later vector store layers."""

    if config.provider_name == "local_hash":
        return LocalHashEmbeddingProvider(
            model_name=config.model_name,
            dimensions=config.dimensions,
        )

    if config.provider_name == "openai_compatible":
        return OpenAICompatibleEmbeddingProvider(
            model_name=config.model_name,
            dimensions=config.dimensions,
            api_key_env=config.api_key_env or "OPENAI_API_KEY",
            base_url=config.base_url,
        )

    raise ValueError(f"Unsupported embedding provider: {config.provider_name}")


def _normalize(vector: list[float]) -> list[float]:
    norm = sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]
