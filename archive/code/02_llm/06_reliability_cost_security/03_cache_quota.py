"""
03_cache_quota.py
缓存命中、重复请求复用和用户配额控制示例

运行方式：
    python 03_cache_quota.py

这个脚本演示的是第六章里“成本控制真正落地”的两条主线：

1. 对相同请求做缓存复用，避免重复付费
2. 对用户调用量做配额控制，避免无限消耗

阅读顺序建议：
1. `fake_llm_call()`
2. `cache_demo()`
3. `quota_demo()`
4. `cache_quota_combined_demo()`
5. `main()`

理解这个脚本时，最重要的是把下面这条链路看清楚：

用户发起请求
-> 先查缓存
-> 未命中时才真正调用模型
-> 调用成功后再消费配额
-> 把结果写入缓存
-> 下次相同请求优先直接命中缓存

也就是说：
缓存负责“避免重复调用”，
配额负责“控制总消耗”，
两者一起工作，才构成真正可落地的成本治理链路。
"""

from __future__ import annotations

from dataclasses import asdict

from reliability_utils import DailyQuotaManager, TTLCache, print_json


def fake_llm_call(question: str) -> dict[str, object]:
    """用本地模拟结果代替真实 LLM 调用。

    这里故意不用真实模型请求，因为当前脚本重点不在模型能力，
    而在“缓存命中后是否还会重复调用”和“调用后如何扣减配额”。
    """

    return {
        "question": question,
        "answer": f"这是对问题《{question}》的模拟回答。",
        "prompt_tokens": len(question) * 2,
        "completion_tokens": 48,
        "total_tokens": len(question) * 2 + 48,
    }


def cache_demo() -> dict[str, object]:
    """单独演示缓存的最小行为：第一次 miss，写入后第二次 hit。

    这一段不讨论配额，只回答一个最基础的问题：
    “如果同一个请求再次到来，系统能不能直接复用已有结果？”
    """

    cache = TTLCache(ttl_seconds=60)
    question = "请总结本周产品例会内容"
    cache_key = "weekly-summary"

    # 第 1 次读取时，缓存还是空的，所以应该是 miss。
    first_hit = cache.get(cache_key)

    # 只有 miss 之后，才需要去“调用模型”拿结果。
    first_result = fake_llm_call(question)

    # 把第一次得到的结果写入缓存，供后续重复请求复用。
    cache.set(cache_key, first_result)

    # 第 2 次读取相同 key，此时应该直接 hit。
    second_hit = cache.get(cache_key)

    return {
        "first_lookup_hit": first_hit.hit,
        "second_lookup_hit": second_hit.hit,
        "cache_size": cache.size(),
        "cached_value": second_hit.value,
    }


def quota_demo() -> dict[str, object]:
    """单独演示配额的最小行为：请求前检查，请求后消费。

    这一段不讨论缓存，只回答另一个问题：
    “系统怎么知道某个用户今天还能不能继续调用？”
    """

    quota = DailyQuotaManager(daily_limit_tokens=600)
    subject = "user-001"

    # 第 1 步：调用前先检查。
    # 这里的 `estimated_tokens` 是“预估本次大概会消耗多少”，
    # 用来提前判断是否还有足够额度。
    before = quota.ensure_available(subject, estimated_tokens=200)

    # 第 2 步：调用成功后再真正消费。
    # 注意这里扣减的是“真实已用量”，而不是上面预估的 200。
    after_first = quota.consume(subject, tokens=220)
    after_second = quota.consume(subject, tokens=260)

    # 第 3 步：连续两次消费后，再检查第 3 次请求是否还能放行。
    blocked = quota.ensure_available(subject, estimated_tokens=180)

    return {
        "before_request": asdict(before),
        "after_first_call": asdict(after_first),
        "after_second_call": asdict(after_second),
        "third_request_check": asdict(blocked),
    }


def cache_quota_combined_demo() -> dict[str, object]:
    """把缓存和配额放到同一条链路里一起观察。

    这一段是整个脚本最关键的示例，因为真实项目里你通常不会只做缓存或只做配额，
    而是需要回答这个更实际的问题：

    “如果第 2 次请求命中了缓存，还应不应该再次扣减用户配额？”

    这个示例给出的答案是：不应该。
    因为第 2 次没有再次触发模型调用，也就不该重复计费。
    """

    cache = TTLCache(ttl_seconds=60)
    quota = DailyQuotaManager(daily_limit_tokens=300)
    subject = "user-002"
    cache_key = "faq:refund"
    question = "退款规则是什么？"

    # 第 1 次读取：先查缓存。
    first_lookup = cache.get(cache_key)
    if first_lookup.hit:
        # 理论上这个分支在当前示例里不会发生，
        # 但真实服务中它代表“请求一进来就直接命中缓存”。
        first_source = "cache"
        first_value = first_lookup.value
    else:
        # 没命中缓存时，才真正去调用模型。
        first_source = "llm"
        first_value = fake_llm_call(question)

        # 只有发生了真实调用，才消费用户配额。
        quota.consume(subject, tokens=int(first_value["total_tokens"]))

        # 调用结果应立即回写缓存，供后续相同请求复用。
        cache.set(cache_key, first_value)

    # 第 2 次读取同一个问题，预期应直接命中缓存。
    second_lookup = cache.get(cache_key)
    second_source = "cache" if second_lookup.hit else "llm"

    # 再取一次配额快照，验证“第二次读取没有再次扣减”。
    snapshot = quota.get_snapshot(subject)

    return {
        "first_source": first_source,
        "first_value": first_value,
        "second_source": second_source,
        "second_value": second_lookup.value,
        "quota_after_two_reads": asdict(snapshot),
    }


def main() -> None:
    """按“先拆开理解，再合起来看”的顺序运行三个示例。"""

    # 第 1 步：先单独看缓存命中行为。
    print_json("缓存命中演示", cache_demo())

    # 第 2 步：再单独看每日配额的检查和消费。
    print_json("每日配额演示", quota_demo())

    # 第 3 步：最后再看缓存和配额放到同一链路里时如何配合。
    print_json("缓存与配额联动演示", cache_quota_combined_demo())

    print("\n理解重点：")
    print("- 缓存的意义不是让模型更聪明，而是避免对相同请求重复付费。")
    print("- 配额检查应该发生在调用之前，消费统计应该发生在调用之后。")
    print("- 如果第二次读取命中缓存，就不应该再次扣减用户 Token 配额。")


if __name__ == "__main__":
    main()
