"""
01_first_call.py
第一条 LLM 请求：从配置、请求体、响应结构到错误排查

运行方式：
    python 01_first_call.py

依赖：
    pip install openai python-dotenv
"""

from __future__ import annotations

import json

from llm_utils import (
    ProviderConfig,
    call_openai_compatible_chat,
    load_env_if_possible,
    load_provider_config,
    mock_chat_response,
)


def print_config_summary(config: ProviderConfig) -> None:
    print("=" * 70)
    print("1. 当前运行配置")
    print("=" * 70)
    print(f"provider: {config.provider}")
    print(f"base_url: {config.base_url or '(SDK 默认)'}")
    print(f"model: {config.model}")
    print(f"api_key: {'已配置' if config.api_key else '未配置'}")
    print()
    print("关键理解：")
    print("1. provider 决定你在用哪个平台")
    print("2. base_url 决定请求发往哪个兼容端点")
    print("3. model 决定具体调用哪个模型")


def build_demo_messages() -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "你是一个有帮助的 AI 助手，回答要简洁。"},
        {"role": "user", "content": "你好，请用 3 句话介绍一下你自己，并说明你能帮助我做什么。"},
    ]


def print_request_anatomy(config: ProviderConfig, messages: list[dict[str, str]]) -> None:
    print("\n" + "=" * 70)
    print("2. 请求体结构拆解")
    print("=" * 70)
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 256,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print()
    print("关键理解：")
    print("- model: 这次调用使用哪个模型")
    print("- messages: 本次请求的全部上下文")
    print("- temperature: 输出发散程度")
    print("- max_tokens: 输出长度上限")


def print_response_anatomy() -> None:
    print("\n" + "=" * 70)
    print("3. 响应对象应该关注什么")
    print("=" * 70)
    sample = {
        "id": "chatcmpl-abc123",
        "model": "demo-model",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "这是一个示例回复。",
                },
            }
        ],
        "usage": {
            "prompt_tokens": 35,
            "completion_tokens": 42,
            "total_tokens": 77,
        },
    }
    print(json.dumps(sample, ensure_ascii=False, indent=2))
    print()
    print("你通常最关心这四部分：")
    print("1. choices[0].message.content -> 实际文本内容")
    print("2. choices[0].finish_reason -> 为什么停止")
    print("3. model -> 最终实际使用的模型")
    print("4. usage -> 输入 / 输出 / 总 token 消耗")


def run_call_demo(config: ProviderConfig, messages: list[dict[str, str]]) -> None:
    print("\n" + "=" * 70)
    print("4. 发起一次真实或模拟调用")
    print("=" * 70)

    if config.is_ready:
        try:
            result = call_openai_compatible_chat(
                config=config,
                messages=messages,
                temperature=0.3,
                max_tokens=256,
            )
        except Exception as exc:
            print(f"真实调用失败：{type(exc).__name__}: {exc}")
            print("回退到 mock 模式，继续看完整链路。")
            result = mock_chat_response(config, messages, temperature=0.3, max_tokens=256)
    else:
        print("未检测到 API Key，自动进入 mock 模式。")
        result = mock_chat_response(config, messages, temperature=0.3, max_tokens=256)

    print("request_preview:")
    print(json.dumps(result.request_preview or {}, ensure_ascii=False, indent=2))
    print("\nresponse_preview:")
    print(json.dumps(result.raw_response_preview or {}, ensure_ascii=False, indent=2))
    print("\nassistant_content:")
    print(result.content)
    if result.usage:
        print("\nusage:")
        print(json.dumps(result.usage.__dict__, ensure_ascii=False, indent=2))


def print_common_failures(config: ProviderConfig) -> None:
    print("\n" + "=" * 70)
    print("5. 常见失败点与排查顺序")
    print("=" * 70)
    print("常见错误类型：")
    print("- API Key 未配置或无效")
    print("- base_url 写错，指向了不兼容的地址")
    print("- model 名称写错")
    print("- 请求字段不被平台支持")
    print("- 网络问题 / 速率限制 / 服务端异常")
    print()
    print("建议排查顺序：")
    print(f"1. 先确认 provider={config.provider} 是否符合预期")
    print(f"2. 再确认 base_url={config.base_url or '(SDK 默认)'} 是否正确")
    print(f"3. 再确认 model={config.model} 是否存在")
    print("4. 最后再看是不是请求参数、网络、限流问题")


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()
    messages = build_demo_messages()

    print("第一条 LLM 请求：完整教学示例")
    print_config_summary(config)
    print_request_anatomy(config, messages)
    print_response_anatomy()
    run_call_demo(config, messages)
    print_common_failures(config)


if __name__ == "__main__":
    main()
