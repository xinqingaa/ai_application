"""
03_unified_client.py
统一客户端：messages 级接口、统一响应对象、debug、retry、扩展位

这个脚本重点演示统一客户端的三个核心价值：
1. 业务侧统一只调用 `client.chat(request)`
2. provider 差异尽量收敛到客户端内部
3. 输入必须保持在 `messages` 级，而不是退化成单个 prompt 字符串

阅读顺序建议：
demo_default_client()
-> demo_switch_provider()
-> demo_messages_level_api()

运行方式：
    python 03_unified_client.py

依赖：
    pip install openai python-dotenv
"""

from __future__ import annotations

import json

from provider_utils import (
    ChatRequest,
    NormalizedChatResponse,
    UnifiedLLMClient,
    load_env_if_possible,
)


def print_section_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def demo_default_client() -> None:
    """作用：
    演示默认 provider 下统一客户端的完整结果结构，包括 describe、request_preview 和响应对象。

    参数：
    无。函数内部会创建一个开启 debug 的 `UnifiedLLMClient`。
    """
    print_section_header("1. 默认 provider 的统一客户端结果")
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

    print("client.describe():")
    print(json.dumps(client.describe(), ensure_ascii=False, indent=2))
    if client.debug:
        print("\nrequest_preview 已在 debug 日志中打印，这里不重复展开。")
    else:
        print("\nresult.request_preview:")
        print(json.dumps(result.request_preview or {}, ensure_ascii=False, indent=2))
    if client.debug:
        print("\nraw_response_preview 已在 debug 日志中打印，这里不重复展开。")
    else:
        print("\nresult.raw_response_preview:")
        print(json.dumps(result.raw_response_preview or {}, ensure_ascii=False, indent=2))
    print("\nresult.content:")
    print(result.content)
    print(
        f"\nmocked={result.mocked} "
        f"finish_reason={result.finish_reason or '（未返回）'} "
        f"elapsed_ms={result.elapsed_ms} "
        f"error={result.error}"
    )
    if result.usage:
        print("\nusage:")
        print(json.dumps(result.usage.__dict__, ensure_ascii=False, indent=2))


def print_switch_provider_result(
    client: UnifiedLLMClient,
    result: NormalizedChatResponse,
) -> None:
    """作用：
    按统一模板打印 `switch_provider` 场景下的结果，便于横向比较不同 provider。

    参数：
    client: 当前统一客户端实例，用于读取 `describe()` 结果。
    result: 当前 provider 对应的统一响应对象。
    """
    # debug 打开时，调用前信息已经打印过；
    # 这里主要展示“本轮调用结果”，避免重复堆叠同一份配置。
    if not client.debug:
        print("client.describe():")
        print(json.dumps(client.describe(), ensure_ascii=False, indent=2))
    print(
        f"model={result.model} "
        f"mocked={result.mocked} "
        f"finish_reason={result.finish_reason or '（未返回）'} "
        f"elapsed_ms={result.elapsed_ms} "
        f"error={result.error}"
    )
    if result.usage:
        print("\nusage:")
        print(json.dumps(result.usage.__dict__, ensure_ascii=False, indent=2))
    if result.finish_reason == "length":
        print("\n提示：finish_reason=length，说明本轮输出可能因为 max_tokens 上限被截断。")
    print("\ncontent:")
    print(result.content)


def demo_switch_provider() -> None:
    """作用：
    演示同一个客户端实例如何切换不同 provider，并保持统一的调用入口。

    参数：
    无。函数内部会依次切换 `bailian`、`deepseek`、`glm`、`claude`。
    """
    print_section_header("2. switch_provider 演示")
    client = UnifiedLLMClient(provider="bailian")
    request = ChatRequest(
        messages=[
            {"role": "system", "content": "你是一个平台选型顾问。"},
            {"role": "user", "content": "比较一下统一接口设计对后续 RAG 和流式输出的帮助。"},
        ],
        temperature=0.2,
        max_tokens=220,
    )
    for provider in ["bailian", "deepseek", "glm", "claude"]:
        print("\n" + "-" * 70)
        print(f"[{provider}]")
        print("-" * 70)
        # 循环里只切换 provider，其余调用入口保持不变，
        # 方便把注意力集中在“统一客户端如何收敛平台差异”上。
        client.switch_provider(provider)
        result = client.chat(request)
        print_switch_provider_result(client, result)


def demo_messages_level_api() -> None:
    """作用：
    用一段多轮消息历史说明统一客户端为什么必须接受 `messages`，而不是只接受单个 prompt。

    参数：
    无。函数内部会构造包含 assistant 历史的多轮 `ChatRequest`。
    """
    print_section_header("3. 为什么统一客户端必须接受 messages，而不是 prompt 字符串")
    client = UnifiedLLMClient(provider="bailian")
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

    print("request.messages:")
    print(json.dumps(request.messages, ensure_ascii=False, indent=2))
    print(
        f"\nmocked={result.mocked} "
        f"finish_reason={result.finish_reason or '（未返回）'} "
        f"elapsed_ms={result.elapsed_ms} "
        f"error={result.error}"
    )
    if result.usage:
        print("\nusage:")
        print(json.dumps(result.usage.__dict__, ensure_ascii=False, indent=2))
    print("\nresult.content:")
    print(result.content)
    print("\n关键理解：")
    print("1. 第二章的统一抽象不能把能力降级成 chat(prompt: str)")
    print("2. 真正的聊天抽象应该以 messages 为核心输入")
    print("3. 这样后续做多轮、结构化输出、流式才不会返工")


def main() -> None:
    """主流程：
    1. 先用默认 provider 看统一客户端的完整返回结构
    2. 再切换不同 provider，观察业务调用入口如何保持不变
    3. 最后用多轮消息说明为什么统一抽象必须保留 messages 级输入
    """
    # 这个脚本按“统一结果 -> 切换 provider -> 理解输入形态”的顺序组织。
    load_env_if_possible()
    demo_default_client()
    demo_switch_provider()
    demo_messages_level_api()


if __name__ == "__main__":
    main()
