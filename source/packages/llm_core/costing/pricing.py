"""Learning-only price table for cost estimation.

Real provider prices change over time. The values here are intentionally a
local learning baseline, used to teach where cost math enters the application.
Production code should load current prices from configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ModelPrice:
    input_per_1m_tokens: float
    output_per_1m_tokens: float
    currency: str = "USD"
    label: str = "learning_estimate"


PriceTable = dict[str, ModelPrice]


DEFAULT_LEARNING_PRICES: PriceTable = {
    "chat.dev_chat": ModelPrice(0.15, 0.60, label="learning_low"),
    "chat.fallback_chat": ModelPrice(0.15, 0.60, label="learning_low"),
    "chat.structured_chat": ModelPrice(2.50, 10.00, label="learning_medium"),
    "gpt-4o-mini": ModelPrice(0.15, 0.60, label="learning_low"),
    "gpt-4o": ModelPrice(2.50, 10.00, label="learning_medium"),
    "fake-model": ModelPrice(0.15, 0.60, label="learning_fake"),
}


def get_learning_price(
    *,
    config_ref: Optional[str] = None,
    model: Optional[str] = None,
    price_table: Optional[PriceTable] = None,
) -> Optional[ModelPrice]:
    table = price_table or DEFAULT_LEARNING_PRICES
    if config_ref and config_ref in table:
        return table[config_ref]
    if model and model in table:
        return table[model]
    return None
