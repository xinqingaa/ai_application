from __future__ import annotations

import pytest

from llm_core import EmbeddingResponse, LLMClient, LLMError, LLMErrorCode, TokenUsage
from llm_core.config import CapabilityTags, ModelConfig


class FakeEmbeddingProvider:
    def embed(self, texts, config, **params):
        vectors = tuple((float(index), float(len(text))) for index, text in enumerate(texts))
        return EmbeddingResponse(
            vectors=vectors,
            dimensions=2,
            raw_response={"echo": list(texts), "params": params},
            usage=TokenUsage(prompt_tokens=3, completion_tokens=0, total_tokens=3),
            latency_ms=1.5,
            provider="fake",
            model=config.model,
            config_ref=config.config_ref,
        )


class EmbedRegistry:
    def __init__(self, *, role: str = "embedding") -> None:
        self._role = role
        self._provider = FakeEmbeddingProvider()

    def get_config(self, config_ref: str) -> ModelConfig:
        return ModelConfig(
            config_ref=config_ref,
            role=self._role,  # type: ignore[arg-type]
            provider="fake",
            model="test-embed",
            api_key_env="OPENAI_API_KEY",
            capabilities=CapabilityTags(cost_tier="low"),
        )

    def get_provider(self, provider_name: str) -> FakeEmbeddingProvider:
        assert provider_name == "fake"
        return self._provider


def test_embed_returns_vectors_in_input_order() -> None:
    client = LLMClient(EmbedRegistry())  # type: ignore[arg-type]
    response = client.embed(["售后入口", "source_channel"], "embedding.default_embed")

    assert response.dimensions == 2
    assert response.vectors == ((0.0, 4.0), (1.0, 14.0))
    assert response.model == "test-embed"
    assert response.usage is not None
    assert response.usage.total_tokens == 3


def test_embed_accepts_single_string() -> None:
    client = LLMClient(EmbedRegistry())  # type: ignore[arg-type]
    response = client.embed("仅已支付订单可申请售后", "embedding.default_embed")
    assert len(response.vectors) == 1
    assert response.vectors[0][1] == float(len("仅已支付订单可申请售后"))


def test_embed_rejects_chat_config() -> None:
    client = LLMClient(EmbedRegistry(role="chat"))  # type: ignore[arg-type]
    with pytest.raises(LLMError) as captured:
        client.embed(["hello"], "chat.dev_chat")
    assert captured.value.code is LLMErrorCode.CAPABILITY_MISMATCH


@pytest.mark.parametrize(
    "texts",
    [
        [],
        [""],
        ["  "],
        ["有效文本", ""],
    ],
)
def test_embed_rejects_empty_inputs(texts: list[str]) -> None:
    client = LLMClient(EmbedRegistry())  # type: ignore[arg-type]
    with pytest.raises(LLMError) as captured:
        client.embed(texts, "embedding.default_embed")
    assert captured.value.code is LLMErrorCode.PROVIDER_ERROR
