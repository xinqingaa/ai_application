"""
02_cost_counter.py
Token 统计、会话成本估算和不同 provider 成本配置示例

运行方式：
    python 02_cost_counter.py
"""

from __future__ import annotations

from dataclasses import asdict, replace

from reliability_utils import (
    ChatUsage,
    compute_cost_breakdown,
    estimate_messages_tokens,
    estimate_tokens,
    format_cost,
    load_env_if_possible,
    load_provider_config,
    print_json,
)


def build_demo_messages() -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "你是一个面向开发者的 LLM 应用助手。"},
        {"role": "user", "content": "请解释为什么多轮对话会显著提高 token 成本，并给出 3 条优化建议。"},
        {
            "role": "assistant",
            "content": "多轮对话需要把历史消息重复带上，因此输入 token 会随轮次增长。优化建议包括裁剪历史、摘要历史和分层模型。",
        },
        {"role": "user", "content": "请进一步说明为什么摘要历史虽然增加一次调用，但整体仍可能更省。"},
    ]


def session_cost_report(config_name: str, input_price: float, output_price: float) -> dict[str, object]:
    base_config = load_provider_config()
    config = replace(
        base_config,
        provider=config_name,
        input_price_per_million=input_price,
        output_price_per_million=output_price,
    )
    messages = build_demo_messages()
    prompt_tokens = estimate_messages_tokens(messages)
    completion_tokens = estimate_tokens("摘要历史虽然有额外调用，但它能避免后续每轮都重复发送长历史。")
    usage = ChatUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    cost = compute_cost_breakdown(usage, config)
    return {
        "provider": config.provider,
        "input_price_per_million": input_price,
        "output_price_per_million": output_price,
        "usage": asdict(usage),
        "cost": asdict(cost) if cost else None,
        "summary": format_cost(cost),
    }


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()
    messages = build_demo_messages()

    print("当前默认配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- ready: {config.is_ready}")

    print_json("会话消息与 token 估算", {
        "messages": messages,
        "estimated_prompt_tokens": estimate_messages_tokens(messages),
        "latest_user_message_tokens": estimate_tokens(messages[-1]["content"]),
    })

    if config.input_price_per_million is not None and config.output_price_per_million is not None:
        usage = ChatUsage(
            prompt_tokens=estimate_messages_tokens(messages),
            completion_tokens=estimate_tokens("这是一个示例回答，用来估算成本。"),
            total_tokens=estimate_messages_tokens(messages) + estimate_tokens("这是一个示例回答，用来估算成本。"),
        )
        cost = compute_cost_breakdown(usage, config)
        print_json("当前 provider 成本估算", {
            "provider": config.provider,
            "usage": asdict(usage),
            "cost": asdict(cost) if cost else None,
            "summary": format_cost(cost),
        })
    else:
        print("\n当前 .env 未配置价格字段，下面使用教学示例价格做演示，不代表真实官方报价。")

    comparison = [
        session_cost_report("economy-demo", input_price=0.8, output_price=2.0),
        session_cost_report("balanced-demo", input_price=2.0, output_price=8.0),
        session_cost_report("premium-demo", input_price=5.0, output_price=15.0),
    ]
    print_json("不同价格档位下的成本对比（教学示例）", comparison)

    print("\n理解重点：")
    print("- 成本不是只有模型单价，prompt 长度、轮次、max_tokens 都会一起放大支出。")
    print("- 输入 token 在多轮会话中往往增长更快，因为历史消息会反复传输。")
    print("- 如果你没有配置实时价格，也应先把 usage 记下来，至少把成本观测链路搭起来。")


if __name__ == "__main__":
    main()
