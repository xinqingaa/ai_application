from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest
from openai import APIStatusError

from llm_core import EmbeddingResponse, LLMClient, LLMError, LLMErrorCode, TokenUsage
from llm_core.config import CapabilityTags, ModelConfig
from llm_core.providers.openai_compat import OpenAICompatProvider


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
    assert captured.value.code is LLMErrorCode.INPUT_VALIDATION


def _embedding_config() -> ModelConfig:
    return ModelConfig(
        config_ref="embedding.default_embed",
        role="embedding",
        provider="openai_compat",
        model="test-embed",
        api_key_env="OPENAI_EMBEDDING_API_KEY",
    )


def test_embedding_requires_its_declared_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_EMBEDDING_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "chat-only-key")

    with pytest.raises(LLMError) as captured:
        OpenAICompatProvider()._client_for_config(_embedding_config())

    assert captured.value.code is LLMErrorCode.AUTH
    assert "OPENAI_EMBEDDING_API_KEY" in captured.value.message


def test_provider_orders_embedding_response_and_records_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = SimpleNamespace(
        data=[
            SimpleNamespace(index=1, embedding=[0.3, 0.4]),
            SimpleNamespace(index=0, embedding=[0.1, 0.2]),
        ],
        usage=SimpleNamespace(prompt_tokens=4, total_tokens=4),
        model="resolved-embed",
    )
    fake_client = SimpleNamespace(
        embeddings=SimpleNamespace(create=lambda **_: response),
    )
    provider = OpenAICompatProvider()
    monkeypatch.setattr(provider, "_client_for_config", lambda _: fake_client)

    result = provider.embed(["a", "b"], _embedding_config())

    assert result.vectors == ((0.1, 0.2), (0.3, 0.4))
    assert result.dimensions == 2
    assert result.model == "resolved-embed"
    assert result.usage is not None
    assert result.usage.total_tokens == 4


def test_provider_maps_embedding_404_with_endpoint_hint() -> None:
    response = httpx.Response(
        404,
        request=httpx.Request("POST", "https://example.test/v1/embeddings"),
    )
    error = OpenAICompatProvider()._map_exception(
        APIStatusError("not found", response=response, body=None),
        _embedding_config(),
    )

    assert error.code is LLMErrorCode.PROVIDER_ERROR
    assert "Embedding 端点不存在或模型不可用" in error.message


@pytest.mark.parametrize(
    ("data", "expected_message"),
    [
        (
            [SimpleNamespace(index=0, embedding=[0.1, 0.2])],
            "与输入文本数 2 不一致",
        ),
        (
            [
                SimpleNamespace(index=0, embedding=[0.1, 0.2]),
                SimpleNamespace(index=1, embedding=[0.3]),
            ],
            "向量维度为空或不一致",
        ),
    ],
)
def test_provider_rejects_invalid_embedding_response_contract(
    monkeypatch: pytest.MonkeyPatch,
    data: list[SimpleNamespace],
    expected_message: str,
) -> None:
    response = SimpleNamespace(data=data, usage=None, model="resolved-embed")
    fake_client = SimpleNamespace(
        embeddings=SimpleNamespace(create=lambda **_: response),
    )
    provider = OpenAICompatProvider()
    monkeypatch.setattr(provider, "_client_for_config", lambda _: fake_client)

    with pytest.raises(LLMError, match=expected_message) as captured:
        provider.embed(["a", "b"], _embedding_config())

    assert captured.value.code is LLMErrorCode.PROVIDER_ERROR
