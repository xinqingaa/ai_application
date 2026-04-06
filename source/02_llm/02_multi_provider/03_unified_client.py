"""
03_unified_client.py
统一客户端：messages 级接口、统一响应对象、debug、retry、扩展位

运行方式：
    python 03_unified_client.py

依赖：
    pip install openai python-dotenv
"""

from __future__ import annotations

import json

from provider_utils import (
    ChatRequest,
    UnifiedLLMClient,
    load_env_if_possible,
)


def demo_default_client() -> None:
    client = UnifiedLLMClient(provider=None, timeout=20.0, max_retries=2, debug=True)
    request = ChatRequest(
        messages=[
            {"role": "system", "content": "你是一个 AI 工程顾问，回答要简洁。"},
            {"role": "user", "content": "请解释：统一客户端为什么比散落的 if/else 更适合长期维护？"},
        ],
        temperature=0.3,
        max_tokens=260,
        metadata={"demo": "default_client"},
    )
    result = client.chat(request)

    print("\n" + "=" * 70)
    print("1. 默认 provider 的统一客户端结果")
    print("=" * 70)
    print("client.describe():")
    print(json.dumps(client.describe(), ensure_ascii=False, indent=2))
    print("\nresult.request_preview:")
    print(json.dumps(result.request_preview or {}, ensure_ascii=False, indent=2))
    print("\nresult.raw_response_preview:")
    print(json.dumps(result.raw_response_preview or {}, ensure_ascii=False, indent=2))
    print("\nresult.content:")
    print(result.content)
    print(f"\nmocked={result.mocked} elapsed_ms={result.elapsed_ms} error={result.error}")
    if result.usage:
        print(json.dumps(result.usage.__dict__, ensure_ascii=False, indent=2))


def demo_switch_provider() -> None:
    client = UnifiedLLMClient(provider="bailian", debug=False)
    request = ChatRequest(
        messages=[
            {"role": "system", "content": "你是一个平台选型顾问。"},
            {"role": "user", "content": "比较一下统一接口设计对后续 RAG 和流式输出的帮助。"},
        ],
        temperature=0.2,
        max_tokens=220,
    )

    print("\n" + "=" * 70)
    print("2. switch_provider 演示")
    print("=" * 70)
    for provider in ["bailian", "deepseek", "glm", "claude"]:
        client.switch_provider(provider)
        result = client.chat(request)
        print(f"\nprovider={provider}")
        print(f"describe={json.dumps(client.describe(), ensure_ascii=False)}")
        print(f"mocked={result.mocked}")
        print(f"content={result.content}")


def demo_messages_level_api() -> None:
    client = UnifiedLLMClient(provider="openai", debug=False)
    request = ChatRequest(
        messages=[
            {"role": "system", "content": "你是一个聊天机器人。"},
            {"role": "user", "content": "第一轮：什么是多平台统一抽象？"},
            {"role": "assistant", "content": "多平台统一抽象是把差异收敛到底层接口层。"},
            {"role": "user", "content": "第二轮：为什么不能只传一个 prompt 字符串？"},
        ],
        temperature=0.3,
        max_tokens=180,
    )
    result = client.chat(request)

    print("\n" + "=" * 70)
    print("3. 为什么统一客户端必须接受 messages，而不是 prompt 字符串")
    print("=" * 70)
    print("request.messages:")
    print(json.dumps(request.messages, ensure_ascii=False, indent=2))
    print("\nresult.content:")
    print(result.content)
    print("\n关键理解：")
    print("1. 第二章的统一抽象不能把能力降级成 chat(prompt: str)")
    print("2. 真正的聊天抽象应该以 messages 为核心输入")
    print("3. 这样后续做多轮、结构化输出、流式才不会返工")


def main() -> None:
    load_env_if_possible()
    demo_default_client()
    demo_switch_provider()
    demo_messages_level_api()


if __name__ == "__main__":
    main()
