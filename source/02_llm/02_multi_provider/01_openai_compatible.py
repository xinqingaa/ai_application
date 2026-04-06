"""
01_openai_compatible.py
OpenAI SDK 为什么能成为统一入口：同一套调用方式切换不同平台

运行方式：
    python 01_openai_compatible.py

依赖：
    pip install openai python-dotenv
"""

from __future__ import annotations

import json

from provider_utils import (
    ChatRequest,
    build_provider_preview,
    call_openai_compatible_chat,
    list_registered_providers,
    load_env_if_possible,
    load_provider_config,
    mock_chat_response,
)


def build_demo_request() -> ChatRequest:
    return ChatRequest(
        messages=[
            {"role": "system", "content": "你是一个 AI 应用开发助教，回答要简洁。"},
            {"role": "user", "content": "请解释为什么 OpenAI-compatible 平台适合学习 LLM API 调用。"},
        ],
        temperature=0.3,
        max_tokens=220,
    )


def print_registered_providers() -> None:
    print("=" * 70)
    print("1. 当前注册的 provider")
    print("=" * 70)
    for key in list_registered_providers():
        config = load_provider_config(key)
        print(f"{key:9s} | type={config.provider_type:18s} | ready={config.is_ready}")
        print(f"         display_name={config.display_name}")
        print(f"         base_url={config.base_url}")
        print(f"         model={config.model}")


def print_same_sdk_different_configs() -> None:
    request = build_demo_request()
    print("\n" + "=" * 70)
    print("2. 同一套 OpenAI SDK，切换不同配置")
    print("=" * 70)
    for key in ["openai", "deepseek", "bailian", "glm"]:
        config = load_provider_config(key)
        payload = build_provider_preview(config, request)
        print(f"\n[{key}]")
        print(f"display_name={config.display_name}")
        print(f"base_url={config.base_url}")
        print(f"model={config.model}")
        print("request_preview:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    print("\n关键理解：")
    print("1. request shape 基本一致")
    print("2. 差异主要集中在 api_key / base_url / model")
    print("3. 这就是 OpenAI-compatible 平台对学习和工程实践的价值")


def run_default_provider_demo() -> None:
    config = load_provider_config()
    request = build_demo_request()

    print("\n" + "=" * 70)
    print("3. 当前默认 provider 的真实或 mock 调用")
    print("=" * 70)
    print(f"default_provider={config.key}")
    print(f"ready={config.is_ready}")

    if config.is_ready:
        try:
            result = call_openai_compatible_chat(config, request)
        except Exception as exc:
            print(f"真实调用失败：{type(exc).__name__}: {exc}")
            result = mock_chat_response(config, request, error=str(exc))
    else:
        result = mock_chat_response(config, request, error="未配置真实环境变量")

    print("request_preview:")
    print(json.dumps(result.request_preview or {}, ensure_ascii=False, indent=2))
    print("\nresponse_preview:")
    print(json.dumps(result.raw_response_preview or {}, ensure_ascii=False, indent=2))
    print("\ncontent:")
    print(result.content)
    if result.usage:
        print("\nusage:")
        print(json.dumps(result.usage.__dict__, ensure_ascii=False, indent=2))
    if result.error:
        print(f"\nerror_note: {result.error}")


def main() -> None:
    load_env_if_possible()
    print_registered_providers()
    print_same_sdk_different_configs()
    run_default_provider_demo()


if __name__ == "__main__":
    main()
