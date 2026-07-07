"""Process-local exact-match cache used by learning demos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class InMemoryLLMCache(Generic[T]):
    _items: dict[str, T] = field(default_factory=dict)

    def get(self, key: str) -> Optional[T]:
        return self._items.get(key)

    def set(self, key: str, value: T) -> None:
        self._items[key] = value

    def clear(self) -> None:
        self._items.clear()

    @property
    def size(self) -> int:
        return len(self._items)
