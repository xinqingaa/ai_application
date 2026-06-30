from llm_core import LLMClient
from llm_core.config import CapabilityTags, ModelConfig
from llm_core.streaming import LLMStreamEvent, StreamEventBuilder, encode_sse


class FakeProvider:
    def stream_chat(self, messages, config, **params):
        builder = StreamEventBuilder(run_id=params.get("_run_id"))
        yield builder.event("message_start", model=config.model, config_ref=config.config_ref)
        yield builder.event("token", delta="你", model=config.model, config_ref=config.config_ref)
        yield builder.event("token", delta="好", model=config.model, config_ref=config.config_ref)
        yield builder.event("message_done", content="你好", model=config.model, config_ref=config.config_ref)
        yield builder.event("done", model=config.model, config_ref=config.config_ref)


class DummyRegistry:
    def get_config(self, config_ref: str) -> ModelConfig:
        return ModelConfig(
            config_ref=config_ref,
            role="chat",
            provider="fake",
            model="test-model",
            api_key_env="OPENAI_API_KEY",
            capabilities=CapabilityTags(streaming=True),
        )

    def get_provider(self, provider_name: str) -> FakeProvider:
        return FakeProvider()


def test_stream_chat_event_order_and_content():
    client = LLMClient(DummyRegistry())  # type: ignore[arg-type]
    events = list(
        client.stream_chat(
            [{"role": "user", "content": "hello"}],
            "chat.dev_chat",
            run_id="run-test",
        )
    )

    assert [event.type for event in events] == [
        "message_start",
        "token",
        "token",
        "message_done",
        "done",
    ]
    assert "".join(event.delta or "" for event in events) == "你好"
    assert events[-2].content == "你好"
    assert all(event.run_id == "run-test" for event in events)
    assert [event.sequence for event in events] == [1, 2, 3, 4, 5]


def test_encode_sse_contains_event_and_json_data():
    event = LLMStreamEvent(type="token", run_id="r1", sequence=2, delta="x")
    text = encode_sse(event)
    assert "id: r1:2" in text
    assert "event: token" in text
    assert '"delta": "x"' in text
    assert text.endswith("\n\n")
