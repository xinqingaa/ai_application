"""
01_error_retry.py
错误分类、指数退避、有限重试和备用模型降级示例

运行方式：
    python 01_error_retry.py
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
    def __init__(self, scenario: str) -> None:
        self.scenario = scenario
        self.calls = 0

    def call(self) -> str:
        self.calls += 1
        if self.scenario == "auth_error":
            raise RuntimeError("Authentication failed: invalid_api_key")
        if self.scenario == "rate_limit_then_success":
            if self.calls < 3:
                raise RuntimeError("429 rate limit exceeded")
            return "主模型在第 3 次尝试后成功返回。"
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
    return {
        "scenario": name,
        "ok": outcome.ok,
        "attempts": outcome.attempts,
        "retries": [asdict(item) for item in outcome.retries],
        "value": outcome.value,
        "error": asdict(outcome.error) if outcome.error else None,
    }


def fallback_demo(primary_provider: str, backup_provider: str) -> dict[str, object]:
    primary_transport = ScenarioTransport("auth_error")
    backup_transport = ScenarioTransport("network_then_success")

    primary_outcome = retry_call(primary_transport.call, max_retries=2, base_delay=0.2, max_delay=0.5)
    if primary_outcome.ok:
        selected = primary_provider
        content = primary_outcome.value
        retries = [asdict(item) for item in primary_outcome.retries]
    else:
        backup_outcome = retry_call(backup_transport.call, max_retries=2, base_delay=0.2, max_delay=0.5)
        selected = backup_provider
        content = backup_outcome.value
        retries = [asdict(item) for item in backup_outcome.retries]

    return {
        "primary_provider": primary_provider,
        "backup_provider": backup_provider,
        "selected_provider": selected,
        "content": content,
        "retries": retries,
    }


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()
    backup_provider = config.backup_provider or "deepseek"

    print("当前 provider 配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- backup_provider: {backup_provider}")
    print(f"- api_key: {config.masked_api_key}")

    direct_examples = [
        RuntimeError("Authentication failed: invalid_api_key"),
        RuntimeError("429 rate limit exceeded"),
        TimeoutError("request timeout after 30 seconds"),
        ConnectionError("temporary network connection reset"),
    ]
    print_json(
        "常见错误分类示例",
        [asdict(classify_exception(item)) for item in direct_examples],
    )

    scenarios = [
        "auth_error",
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
    print_json("主备模型降级演示", fallback_demo(config.provider, backup_provider))

    print("\n理解重点：")
    print("- auth_error 和 request_error 通常不该重试，因为重试不会修复错误参数或无效凭证。")
    print("- rate_limit、network_error、timeout 才是典型的可重试错误。")
    print("- 降级到备用模型不是为了隐藏错误，而是为了在服务层提供更高可用性。")


if __name__ == "__main__":
    main()
