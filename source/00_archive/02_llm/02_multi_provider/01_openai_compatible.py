"""
01_openai_compatible.py
OpenAI SDK 为什么能成为统一入口：同一套调用方式切换不同平台

这个脚本主要回答两个问题：
1. 为什么很多平台可以复用同一套 OpenAI SDK 调用方式
2. 这些平台的差异为什么主要收敛在配置层，而不是业务层

阅读顺序建议：
print_registered_providers()
-> print_same_sdk_different_configs()
-> run_default_provider_demo()

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
    """作用：
    构造一个最小聊天请求，作为整份脚本的统一演示输入。

    参数：
    无。函数内部固定写入一组 system + user 消息，以及基础采样参数。

    返回：
    一个 `ChatRequest` 对象，后续会被不同 provider 复用。
    """
    return ChatRequest(
        messages=[
            {"role": "system", "content": "你是一个 AI 应用开发助教，回答要简洁。"},
            {"role": "user", "content": "请解释为什么 OpenAI-compatible 平台适合学习 LLM API 调用。"},
        ],
        temperature=0.3,
        max_tokens=220,
    )


def print_registered_providers() -> None:
    """作用：
    打印当前注册表里的 provider 清单，先建立“有哪些平台可以参与统一抽象”的整体视角。

    参数：
    无。函数会遍历 `provider_utils.PROVIDER_REGISTRY` 对应的配置。
    """
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
    """作用：
    用同一份 `ChatRequest` 对比多个 OpenAI-compatible provider 的请求预览。

    参数：
    无。函数内部会固定比较 `openai`、`deepseek`、`bailian`、`glm` 四个平台。
    """
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
    """作用：
    使用当前默认 provider 跑一次真实或 mock 调用，把“配置 -> 请求 -> 响应”的完整链路串起来。

    参数：
    无。函数会自动读取默认 provider 配置，并根据环境是否就绪决定走真实调用还是 mock。
    """
    config = load_provider_config()
    request = build_demo_request()

    print("\n" + "=" * 70)
    print("3. 当前默认 provider 的真实或 mock 调用")
    print("=" * 70)
    print(f"default_provider={config.key}")
    print(f"ready={config.is_ready}")

    if config.is_ready:
        try:
            # 环境已就绪时，优先真实调用，方便观察统一响应对象长什么样。
            result = call_openai_compatible_chat(config, request)
        except Exception as exc:
            print(f"真实调用失败：{type(exc).__name__}: {exc}")
            # 教学示例保留自动回退，是为了避免环境问题打断主流程理解。
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
    """主流程：
    1. 先加载环境变量，拿到默认 provider
    2. 再看注册表里有哪些平台
    3. 再比较同一份请求在不同平台上的预览
    4. 最后跑一次默认 provider 的真实或 mock 调用
    """
    # 这个 main 的组织顺序是：
    # 先建立 provider 全局视角，再看同构请求，最后落到一次实际调用。
    load_env_if_possible()
    print_registered_providers()
    print_same_sdk_different_configs()
    run_default_provider_demo()


if __name__ == "__main__":
    main()
