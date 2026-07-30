from __future__ import annotations

from math import isclose

import pytest

from llm_core import EmbeddingResponse, LLMClient, TokenUsage
from llm_core.config import CapabilityTags, ModelConfig
from rag_core import (
    EmbeddingRecord,
    SimilarityMetric,
    embed_texts,
    pairwise_similarity,
    similarity,
)


class FakeEmbeddingProvider:
    def embed(self, texts, config, **params):
        # Fixed 2D directions so cosine relations are deterministic.
        mapping = {
            "申请售后": (1.0, 0.0),
            "发起逆向服务": (0.95, 0.05),
            "虚拟商品除外": (0.9, 0.1),
            "售前活动规则": (0.0, 1.0),
        }
        vectors = tuple(mapping[text] for text in texts)
        return EmbeddingResponse(
            vectors=vectors,
            dimensions=2,
            raw_response=None,
            usage=TokenUsage(prompt_tokens=len(texts), completion_tokens=0, total_tokens=len(texts)),
            latency_ms=0.5,
            provider="fake",
            model=config.model,
            config_ref=config.config_ref,
        )


class FakeRegistry:
    def get_config(self, config_ref: str) -> ModelConfig:
        return ModelConfig(
            config_ref=config_ref,
            role="embedding",
            provider="fake",
            model="fake-embed",
            api_key_env="OPENAI_API_KEY",
            capabilities=CapabilityTags(cost_tier="low"),
        )

    def get_provider(self, provider_name: str) -> FakeEmbeddingProvider:
        return FakeEmbeddingProvider()


def test_embed_texts_preserves_order_and_identity() -> None:
    client = LLMClient(FakeRegistry())  # type: ignore[arg-type]
    batch = embed_texts(
        ["申请售后", "售前活动规则"],
        client=client,
        text_ids=["q1", "noise"],
    )

    assert [record.text_id for record in batch.records] == ["q1", "noise"]
    assert batch.records[0].vector == (1.0, 0.0)
    assert batch.records[1].vector == (0.0, 1.0)
    assert batch.response.dimensions == 2


def test_similarity_metrics_and_pairwise_observations() -> None:
    left = EmbeddingRecord(
        text="申请售后",
        vector=(1.0, 0.0),
        model="fake-embed",
        dimensions=2,
        config_ref="embedding.default_embed",
        provider="fake",
        text_id="a",
    )
    right = EmbeddingRecord(
        text="发起逆向服务",
        vector=(0.95, 0.05),
        model="fake-embed",
        dimensions=2,
        config_ref="embedding.default_embed",
        provider="fake",
        text_id="b",
    )

    cosine = similarity(left, right, metric=SimilarityMetric.COSINE)
    dot = similarity(left, right, metric=SimilarityMetric.DOT)
    distance = similarity(left, right, metric=SimilarityMetric.EUCLIDEAN)

    assert cosine > 0.99
    assert isclose(dot, 0.95)
    assert distance < 0.1

    observations = pairwise_similarity([left, right])
    assert len(observations) == 1
    assert observations[0].higher_is_closer is True
    assert observations[0].left_id == "a"
    assert observations[0].right_id == "b"


def test_pairwise_rejects_mixed_models() -> None:
    left = EmbeddingRecord(
        text="a",
        vector=(1.0, 0.0),
        model="m1",
        dimensions=2,
        config_ref="embedding.default_embed",
        provider="fake",
    )
    right = EmbeddingRecord(
        text="b",
        vector=(0.0, 1.0),
        model="m2",
        dimensions=2,
        config_ref="embedding.default_embed",
        provider="fake",
    )
    with pytest.raises(ValueError, match="不同模型"):
        pairwise_similarity([left, right])
