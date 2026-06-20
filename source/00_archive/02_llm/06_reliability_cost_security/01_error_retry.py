"""
01_error_retry.py
错误分类、指数退避、有限重试和备用模型降级示例

运行方式：
    python 01_error_retry.py

这个脚本先不依赖真实模型，而是用可控场景模拟高频失败类型，
目的不是复刻某个平台的全部异常细节，而是先把下面这条主链路看清楚：

错误发生
-> `classify_exception()` 分类
-> `retry_call()` 判断是否值得重试
-> 记录每次退避等待
-> 超过边界后决定是否切备用 provider

阅读顺序建议：
1. `ScenarioTransport`
2. `explain_outcome()`
3. `fallback_demo()`
4. `main()`

调试建议：
1. 先直接运行一次，看 `attempts / retries / error.category`
2. 再修改 `max_retries / base_delay`
3. 最后回头对照 `reliability_utils.py` 里的 `classify_exception()` 和 `retry_call()`
"""

from __future__ import annotations

from dataclasses import asdict

from reliability_utils import (
    RetryOutcome,
    classify_exception,
    load_env_if_possible,
    load_provider_config,
    print_json,
    retry_call,
)


class ScenarioTransport:
    """用可重复的本地场景模拟不同错误类型。

    这一层故意不用真实网络请求，这样你在学习第六章时不会被平台波动干扰，
    可以更专注地观察：哪些错误会立即失败，哪些错误会先退避再重试。
    """

    def __init__(self, scenario: str) -> None:
        self.scenario = scenario
        self.calls = 0

    def call(self) -> str:
        # 每次调用都累加计数，方便演示“第几次尝试成功”。
        self.calls += 1
        if self.scenario == "auth_error":
            raise RuntimeError("Authentication failed: invalid_api_key")
        if self.scenario == "request_error":
            raise RuntimeError("400 invalid request: messages must be a list")
        if self.scenario == "rate_limit_then_success":
            if self.calls < 3:
                raise RuntimeError("429 rate limit exceeded")
            return "主模型在第 3 次尝试后成功返回。"
        if self.scenario == "rate_limit_always_fail":
            raise RuntimeError("429 rate limit exceeded")
        if self.scenario == "network_then_success":
            if self.calls < 2:
                raise ConnectionError("temporary network connection reset")
            return "网络恢复后，当前请求已成功。"
        if self.scenario == "timeout_then_success":
            if self.calls < 2:
                raise TimeoutError("request timeout after 30 seconds")
            return "超时重试后成功。"
        return "未命名场景，直接成功。"


def explain_outcome(name: str, outcome: RetryOutcome) -> dict[str, object]:
    """把结构化重试结果整理成更适合打印和文档讲解的字典。"""

    return {
        "scenario": name,
        "ok": outcome.ok,
        "attempts": outcome.attempts,
        "retries": [asdict(item) for item in outcome.retries],
        "value": outcome.value,
        "error": asdict(outcome.error) if outcome.error else None,
    }


def fallback_demo(primary_provider: str, backup_provider: str) -> dict[str, object]:
    """演示“主链路失败后切备用 provider”的最小流程。

    这里主 provider 被设定成“持续限流”，这样更符合真实降级场景：
    它属于可恢复但短时间内未恢复的错误，所以先有限重试，再决定切换备用链路。
    """

    primary_transport = ScenarioTransport("rate_limit_always_fail")
    backup_transport = ScenarioTransport("network_then_success")

    primary_outcome = retry_call(primary_transport.call, max_retries=2, base_delay=0.2, max_delay=0.5)
    backup_outcome: RetryOutcome | None = None

    if primary_outcome.ok:
        selected = primary_provider
        content = primary_outcome.value
        fallback_reason = None
    else:
        fallback_reason = primary_outcome.error.category if primary_outcome.error else None
        backup_outcome = retry_call(backup_transport.call, max_retries=2, base_delay=0.2, max_delay=0.5)
        selected = backup_provider if backup_outcome.ok else None
        content = backup_outcome.value
    # 这里同时保留主链路和备用链路的结果，方便你对照：
    # “谁失败了”“为什么失败”“备用链路是否又发生了重试”。

    return {
        "primary_provider": primary_provider,
        "backup_provider": backup_provider,
        "selected_provider": selected,
        "used_fallback": backup_outcome is not None,
        "fallback_reason": fallback_reason,
        "content": content,
        "primary_outcome": explain_outcome("rate_limit_always_fail", primary_outcome),
        "backup_outcome": explain_outcome("network_then_success", backup_outcome) if backup_outcome else None,
    }


def main() -> None:
    """按“配置 -> 分类 -> 重试 -> 降级”的顺序串起整个示例。"""

    # 第 1 步：读取当前 provider 配置。
    # 这里不是为了真的发模型请求，而是让“主 provider / 备用 provider”这两个概念具体化。
    load_env_if_possible()
    config = load_provider_config()
    backup_provider = config.backup_provider or "deepseek"

    print("当前 provider 配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- backup_provider: {backup_provider}")
    print(f"- api_key: {config.masked_api_key}")

    # 第 2 步：先不做重试，直接看“异常文本会被分到什么错误类别”。
    # 这一步的重点是建立分类心智模型：哪些错误天然不该重试，哪些错误适合退避重试。
    direct_examples = [
        RuntimeError("Authentication failed: invalid_api_key"),
        RuntimeError("429 rate limit exceeded"),
        RuntimeError("400 invalid request: messages must be a list"),
        TimeoutError("request timeout after 30 seconds"),
        ConnectionError("temporary network connection reset"),
        RuntimeError("content policy violation: blocked by safety system"),
    ]
    print_json(
        "常见错误分类示例",
        [asdict(classify_exception(item)) for item in direct_examples],
    )

    # 第 3 步：用一组可控场景跑 `retry_call()`，观察 attempts 和 retries 如何变化。
    # 这里的 `attempts` 表示真实调用次数，`retries` 只记录“失败后等待再试”的那几次退避动作。
    scenarios = [
        "auth_error",
        "request_error",
        "rate_limit_then_success",
        "network_then_success",
        "timeout_then_success",
    ]
    reports = []
    for scenario in scenarios:
        transport = ScenarioTransport(scenario)
        outcome = retry_call(transport.call, max_retries=3, base_delay=0.2, max_delay=0.8)
        reports.append(explain_outcome(scenario, outcome))

    print_json("重试场景结果", reports)

    # 第 4 步：单独看“主 provider 失败后切备用 provider”的流程。
    # 这一步不是为了说明备用模型一定更好，而是说明服务层可以用它提升可用性。
    print_json("主备模型降级演示", fallback_demo(config.provider, backup_provider))

    print("\n理解重点：")
    print("- auth_error 和 request_error 通常不该重试，因为重试不会修复错误参数或无效凭证。")
    print("- rate_limit、network_error、timeout 才是典型的可重试错误。")
    print("- 降级到备用模型不是为了隐藏错误，而是为了在服务层提供更高可用性。")


if __name__ == "__main__":
    main()
