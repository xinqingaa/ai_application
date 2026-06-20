"""
02_messages_chat.py
消息格式与多轮对话：角色分工、system prompt、历史管理、裁剪策略

运行方式：
    python 02_messages_chat.py

依赖：
    pip install openai python-dotenv
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from llm_utils import (
    ChatResult,
    call_openai_compatible_chat,
    estimate_messages_tokens,
    export_conversation,
    load_env_if_possible,
    load_provider_config,
    mock_chat_response,
    trim_messages_by_recent_messages,
)


@dataclass
class Conversation:
    # Conversation 是“最小历史管理器”。
    # 它不负责调用模型，只负责在应用侧维护 messages，
    # 用来强调一个核心认知：多轮对话的上下文是应用自己保存和组织的。
    system_prompt: str
    messages: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        # 初始化时先放入 system，是为了保证后续任何一轮请求都带着稳定角色设定。
        self.messages.append({"role": "system", "content": self.system_prompt})

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": text})

    def snapshot(self) -> list[dict[str, str]]:
        # 返回浅拷贝而不是原列表，是为了让调用方拿到“当前快照”，
        # 避免在函数外部直接改坏内部状态。
        return list(self.messages)

    def trim_recent(self, keep_last_messages: int) -> None:
        # 裁剪策略复用 llm_utils 里的公共逻辑：
        # 永远保留 system，再保留最近若干条非 system 消息。
        self.messages = trim_messages_by_recent_messages(self.messages, keep_last_messages)


def print_role_explanation() -> None:
    print("=" * 70)
    print("1. 三种角色的职责")
    print("=" * 70)
    print("| role      | 作用 |")
    print("|-----------|------|")
    print("| system    | 定义长期稳定的角色和规则 |")
    print("| user      | 本轮用户问题或输入材料 |")
    print("| assistant | 模型过去的回复，用于多轮对话 |")
    print()
    print("关键理解：assistant 历史不是模型自己记住的，而是应用侧自己带上的。")


def print_single_vs_multi_turn() -> None:
    single_turn = [
        {"role": "user", "content": "什么是 Python？"},
    ]
    multi_turn = [
        {"role": "system", "content": "你是一个编程助教，回答要简洁。"},
        {"role": "user", "content": "什么是 Python？"},
        {"role": "assistant", "content": "Python 是一种通用编程语言。"},
        {"role": "user", "content": "它适合做 AI 应用开发吗？"},
    ]

    print("\n" + "=" * 70)
    print("2. 单轮 vs 多轮消息结构")
    print("=" * 70)
    print("单轮：")
    print(json.dumps(single_turn, ensure_ascii=False, indent=2))
    print("\n多轮：")
    print(json.dumps(multi_turn, ensure_ascii=False, indent=2))
    print()
    print(f"单轮估算 tokens: {estimate_messages_tokens(single_turn)}")
    print(f"多轮估算 tokens: {estimate_messages_tokens(multi_turn)}")


def print_chat_result_details(title: str, result: ChatResult) -> None:
    # 这个辅助函数专门用来把一次调用的关键返回信息“展开来看”。
    # 对初学者来说，只打印 content 不够，因为你还需要知道：
    # - 这次到底用的是哪个 provider / model
    # - 是真实调用还是 mock
    # - 请求体长什么样
    # - 响应里 finish_reason 是什么
    # - usage 有没有返回
    finish_reason = None
    if result.raw_response_preview:
        choices = result.raw_response_preview.get("choices") or []
        if choices:
            finish_reason = choices[0].get("finish_reason")

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    print(f"provider: {result.provider}")
    print(f"model: {result.model}")
    print(f"mocked: {result.mocked}")
    print(f"finish_reason: {finish_reason or '（未返回）'}")

    print("\nrequest_preview:")
    print(json.dumps(result.request_preview or {}, ensure_ascii=False, indent=2))

    print("\nresponse_preview:")
    print(json.dumps(result.raw_response_preview or {}, ensure_ascii=False, indent=2))

    if result.usage:
        print("\nusage:")
        print(json.dumps(result.usage.__dict__, ensure_ascii=False, indent=2))
    else:
        print("\nusage:")
        print("（当前结果没有 usage，通常是 mock 模式，或者平台未返回 usage）")

    print("\nassistant_content:")
    print(result.content)


def demo_system_prompt_comparison() -> None:
    # 这个演示的重点不是比较“哪个回答更好”，
    # 而是让你直观看到：同一个 user prompt，换一个 system prompt，
    # 请求上下文就变了，模型输出风格也会跟着变。
    config = load_provider_config()
    prompt = "请介绍一下 Python 在 AI 应用开发中的作用。"
    strict_messages = [
        {"role": "system", "content": "你是一个技术助教。回答要简洁，控制在 80 字以内。"},
        {"role": "user", "content": prompt},
    ]
    friendly_messages = [
        {"role": "system", "content": "你是一个友好的技术伙伴。回答可以口语化，并给一个简单建议。"},
        {"role": "user", "content": prompt},
    ]

    print("\n" + "=" * 70)
    print("3. system prompt 如何影响回答风格")
    print("=" * 70)
    print("严格版 system prompt:")
    print(strict_messages[0]["content"])
    print("\n友好版 system prompt:")
    print(friendly_messages[0]["content"])

    if config.is_ready:
        try:
            # 两次调用只改 system prompt 和部分参数，方便观察风格差异来自哪里。
            strict_result = call_openai_compatible_chat(config, strict_messages, temperature=0.3, max_tokens=120)
            friendly_result = call_openai_compatible_chat(config, friendly_messages, temperature=0.6, max_tokens=180)
        except Exception as exc:
            print(f"\n真实调用失败：{type(exc).__name__}: {exc}")
            print("回退到 mock 演示。")
            strict_result = mock_chat_response(config, strict_messages, temperature=0.3, max_tokens=120)
            friendly_result = mock_chat_response(config, friendly_messages, temperature=0.6, max_tokens=180)
    else:
        strict_result = mock_chat_response(config, strict_messages, temperature=0.3, max_tokens=120)
        friendly_result = mock_chat_response(config, friendly_messages, temperature=0.6, max_tokens=180)

    print_chat_result_details("严格版调用结果", strict_result)
    print_chat_result_details("友好版调用结果", friendly_result)


def demo_conversation_manager() -> None:
    # 这一段故意手动构造几轮对话，
    # 让你把注意力集中在“历史如何组织和裁剪”，而不是调用模型本身。
    conversation = Conversation(
        system_prompt="你是一个 AI 学习助手。回答要简洁，优先用应用开发视角解释问题。"
    )
    conversation.add_user("我是前端开发者，刚开始学 AI 应用开发。")
    conversation.add_assistant("很好，你已经有工程经验，下一步重点是把模型接起来。")
    conversation.add_user("我为什么需要关心 messages？")
    conversation.add_assistant("因为多轮对话的历史消息要由应用侧自己管理。")
    conversation.add_user("那 history 越来越长怎么办？")

    print("\n" + "=" * 70)
    print("4. 用 Conversation 管理历史")
    print("=" * 70)
    print("原始历史：")
    print(json.dumps(conversation.snapshot(), ensure_ascii=False, indent=2))
    print(f"原始估算 tokens: {estimate_messages_tokens(conversation.snapshot())}")

    # 裁剪前后对比，是为了让你建立一个工程直觉：
    # 历史不是越完整越好，而是要在“保留上下文”和“控制成本”之间做权衡。
    conversation.trim_recent(keep_last_messages=4)
    print("\n裁剪后历史（裁剪最近四条）：")
    print(json.dumps(conversation.snapshot(), ensure_ascii=False, indent=2))
    print(f"裁剪后估算 tokens: {estimate_messages_tokens(conversation.snapshot())}")

    path = export_conversation(
        provider="demo",
        model="demo-model",
        messages=conversation.snapshot(),
        metadata={"demo": "messages_chat", "note": "示例导出"},
    )
    print(f"\n历史已导出到：{path}")


def main() -> None:
    # 这个脚本按“概念 -> 对比 -> 演示”的顺序组织：
    # 先解释 role，再展示单轮/多轮结构，再展示 system prompt 的影响，
    # 最后落到一个最小历史管理器上。
    load_env_if_possible()
    # print_role_explanation()
    # print_single_vs_multi_turn()
    demo_system_prompt_comparison()
    # demo_conversation_manager()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已手动中断脚本执行。")
