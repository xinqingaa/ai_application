from __future__ import annotations

from llm_core import estimate_token_cost, estimate_usage_cost
from llm_core.config import TokenUsage


def test_estimate_usage_cost_handles_missing_usage() -> None:
    estimate = estimate_usage_cost(None, config_ref="chat.dev_chat", model="fake-model")

    assert estimate.prompt_tokens is None
    assert estimate.total_cost is None
    assert estimate.known is False


def test_estimate_token_cost_uses_learning_price_table() -> None:
    estimate = estimate_token_cost(
        prompt_tokens=1_000,
        completion_tokens=500,
        config_ref="chat.dev_chat",
        model="fake-model",
    )

    assert estimate.known
    assert estimate.prompt_tokens == 1_000
    assert estimate.completion_tokens == 500
    assert estimate.total_tokens == 1_500
    assert estimate.total_cost == 0.00045


def test_estimate_usage_cost_reports_unknown_price_without_crashing() -> None:
    estimate = estimate_usage_cost(
        TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        config_ref="chat.unknown",
        model="unknown-model",
    )

    assert estimate.prompt_tokens == 100
    assert estimate.total_tokens == 150
    assert estimate.total_cost is None
    assert estimate.known is False
