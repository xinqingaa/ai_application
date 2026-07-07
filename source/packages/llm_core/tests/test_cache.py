from __future__ import annotations

from llm_core import CacheEvent, CacheKeyParts, CacheStats, InMemoryLLMCache, build_cache_key


def _parts(**overrides: object) -> CacheKeyParts:
    data = {
        "config_ref": "chat.dev_chat",
        "model": "fake-model",
        "messages": [{"role": "user", "content": "订单详情页新增申请售后入口"}],
        "prompt_id": "review.risk_review",
        "prompt_version": "v4",
        "structured_mode": "json_object",
        "schema_version": "review_risk_list@1",
        "temperature": 0,
        "context_fingerprint": "ctx-a",
    }
    data.update(overrides)
    return CacheKeyParts(**data)  # type: ignore[arg-type]


def test_cache_key_changes_when_prompt_schema_or_context_changes() -> None:
    base = build_cache_key(_parts())

    assert build_cache_key(_parts(prompt_version="v5")) != base
    assert build_cache_key(_parts(schema_version="review_risk_list@2")) != base
    assert build_cache_key(_parts(context_fingerprint="ctx-b")) != base
    assert build_cache_key(_parts(messages=[{"role": "user", "content": "优惠券叠加"}])) != base


def test_in_memory_cache_hit_avoids_second_call() -> None:
    calls = 0
    cache: InMemoryLLMCache[str] = InMemoryLLMCache()
    key = build_cache_key(_parts())

    def expensive_call() -> str:
        nonlocal calls
        cached = cache.get(key)
        if cached is not None:
            return cached
        calls += 1
        value = "model result"
        cache.set(key, value)
        return value

    assert expensive_call() == "model result"
    assert expensive_call() == "model result"
    assert calls == 1
    assert cache.size == 1


def test_cache_stats_summarize_hits_and_savings() -> None:
    stats = CacheStats.from_events(
        [
            CacheEvent("S1", hit=True, cache_key="k1", saved_tokens=120, saved_estimated_cost=0.001, saved_latency_ms=30),
            CacheEvent("S2", hit=False, cache_key="k2"),
        ]
    )

    assert stats.total == 2
    assert stats.hit_count == 1
    assert stats.miss_count == 1
    assert stats.hit_rate == 0.5
    assert stats.saved_tokens == 120
    assert stats.saved_estimated_cost == 0.001
    assert stats.saved_latency_ms == 30
