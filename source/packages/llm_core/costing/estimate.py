"""Token cost estimation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from llm_core.config import TokenUsage
from llm_core.costing.pricing import ModelPrice, PriceTable, get_learning_price


@dataclass(frozen=True)
class CostEstimate:
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]
    input_cost: Optional[float]
    output_cost: Optional[float]
    total_cost: Optional[float]
    currency: str = "USD"
    price_label: str = "unknown"

    @property
    def known(self) -> bool:
        return self.total_cost is not None


def estimate_usage_cost(
    usage: Optional[TokenUsage],
    *,
    config_ref: Optional[str] = None,
    model: Optional[str] = None,
    price_table: Optional[PriceTable] = None,
) -> CostEstimate:
    if usage is None:
        return CostEstimate(
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            input_cost=None,
            output_cost=None,
            total_cost=None,
        )
    return estimate_token_cost(
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        config_ref=config_ref,
        model=model,
        price_table=price_table,
    )


def estimate_token_cost(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    config_ref: Optional[str] = None,
    model: Optional[str] = None,
    price_table: Optional[PriceTable] = None,
) -> CostEstimate:
    total_tokens = prompt_tokens + completion_tokens
    price = get_learning_price(config_ref=config_ref, model=model, price_table=price_table)
    if price is None:
        return CostEstimate(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            input_cost=None,
            output_cost=None,
            total_cost=None,
        )
    return _estimate_with_price(prompt_tokens, completion_tokens, total_tokens, price)


def _estimate_with_price(
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    price: ModelPrice,
) -> CostEstimate:
    input_cost = prompt_tokens / 1_000_000 * price.input_per_1m_tokens
    output_cost = completion_tokens / 1_000_000 * price.output_per_1m_tokens
    return CostEstimate(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=input_cost + output_cost,
        currency=price.currency,
        price_label=price.label,
    )
