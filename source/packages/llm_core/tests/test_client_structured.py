from llm_core import LLMClient
from llm_core.config import LLMResponse, ModelConfig


class DummyRegistry:
    def get_config(self, config_ref: str) -> ModelConfig:
        return ModelConfig(
            config_ref=config_ref,
            role="chat",
            provider="openai_compat",
            model="test-model",
            api_key_env="OPENAI_API_KEY",
            default_params={"temperature": 0.2, "max_tokens": 2048},
        )


def test_chat_structured_passes_request_params_once():
    client = LLMClient(DummyRegistry())  # type: ignore[arg-type]
    captured: dict = {}

    def fake_chat(
        messages: list[dict[str, str]],
        config_ref: str,
        *,
        debug: bool = False,
        **kwargs,
    ) -> LLMResponse:
        captured.update(kwargs)
        return LLMResponse(
            content='{"risks":[{"title":"t","category":"api","level":"high","rationale":"r"}]}',
            raw_response={},
            usage=None,
            latency_ms=1.0,
            provider="test",
            model="test-model",
            config_ref=config_ref,
        )

    client.chat = fake_chat  # type: ignore[method-assign]

    result = client.chat_structured(
        [{"role": "user", "content": "x"}],
        "chat.dev_chat",
        structured_mode="json_object",
        temperature=0,
        max_tokens=128,
    )

    assert result.parse.ok
    assert captured["temperature"] == 0
    assert captured["max_tokens"] == 128
    assert captured["response_format"] == {"type": "json_object"}
