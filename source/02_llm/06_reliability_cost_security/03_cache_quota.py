"""
03_cache_quota.py
缓存命中、重复请求复用和用户配额控制示例

运行方式：
    python 03_cache_quota.py
"""

from __future__ import annotations

from dataclasses import asdict

from reliability_utils import DailyQuotaManager, TTLCache, print_json


def fake_llm_call(question: str) -> dict[str, object]:
    return {
        "question": question,
        "answer": f"这是对问题《{question}》的模拟回答。",
        "prompt_tokens": len(question) * 2,
        "completion_tokens": 48,
        "total_tokens": len(question) * 2 + 48,
    }


def cache_demo() -> dict[str, object]:
    cache = TTLCache(ttl_seconds=60)
    question = "请总结本周产品例会内容"
    cache_key = "weekly-summary"

    first_hit = cache.get(cache_key)
    first_result = fake_llm_call(question)
    cache.set(cache_key, first_result)
    second_hit = cache.get(cache_key)

    return {
        "first_lookup_hit": first_hit.hit,
        "second_lookup_hit": second_hit.hit,
        "cache_size": cache.size(),
        "cached_value": second_hit.value,
    }


def quota_demo() -> dict[str, object]:
    quota = DailyQuotaManager(daily_limit_tokens=600)
    subject = "user-001"

    before = quota.ensure_available(subject, estimated_tokens=200)
    after_first = quota.consume(subject, tokens=220)
    after_second = quota.consume(subject, tokens=260)
    blocked = quota.ensure_available(subject, estimated_tokens=180)

    return {
        "before_request": asdict(before),
        "after_first_call": asdict(after_first),
        "after_second_call": asdict(after_second),
        "third_request_check": asdict(blocked),
    }


def cache_quota_combined_demo() -> dict[str, object]:
    cache = TTLCache(ttl_seconds=60)
    quota = DailyQuotaManager(daily_limit_tokens=300)
    subject = "user-002"
    cache_key = "faq:refund"
    question = "退款规则是什么？"

    first_lookup = cache.get(cache_key)
    if first_lookup.hit:
        first_source = "cache"
        first_value = first_lookup.value
    else:
        first_source = "llm"
        first_value = fake_llm_call(question)
        quota.consume(subject, tokens=int(first_value["total_tokens"]))
        cache.set(cache_key, first_value)

    second_lookup = cache.get(cache_key)
    second_source = "cache" if second_lookup.hit else "llm"
    snapshot = quota.get_snapshot(subject)

    return {
        "first_source": first_source,
        "first_value": first_value,
        "second_source": second_source,
        "second_value": second_lookup.value,
        "quota_after_two_reads": asdict(snapshot),
    }


def main() -> None:
    print_json("缓存命中演示", cache_demo())
    print_json("每日配额演示", quota_demo())
    print_json("缓存与配额联动演示", cache_quota_combined_demo())

    print("\n理解重点：")
    print("- 缓存的意义不是让模型更聪明，而是避免对相同请求重复付费。")
    print("- 配额检查应该发生在调用之前，消费统计应该发生在调用之后。")
    print("- 如果第二次读取命中缓存，就不应该再次扣减用户 Token 配额。")


if __name__ == "__main__":
    main()
