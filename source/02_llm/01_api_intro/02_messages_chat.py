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
    system_prompt: str
    messages: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.messages.append({"role": "system", "content": self.system_prompt})

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": text})

    def snapshot(self) -> list[dict[str, str]]:
        return list(self.messages)

    def trim_recent(self, keep_last_messages: int) -> None:
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


def demo_system_prompt_comparison() -> None:
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
            strict_result = call_openai_compatible_chat(config, strict_messages, temperature=0.2, max_tokens=120)
            friendly_result = call_openai_compatible_chat(config, friendly_messages, temperature=0.6, max_tokens=180)
        except Exception as exc:
            print(f"\n真实调用失败：{type(exc).__name__}: {exc}")
            print("回退到 mock 演示。")
            strict_result = mock_chat_response(config, strict_messages, temperature=0.2, max_tokens=120)
            friendly_result = mock_chat_response(config, friendly_messages, temperature=0.6, max_tokens=180)
    else:
        strict_result = mock_chat_response(config, strict_messages, temperature=0.2, max_tokens=120)
        friendly_result = mock_chat_response(config, friendly_messages, temperature=0.6, max_tokens=180)

    print("\n严格版输出：")
    print(strict_result.content)
    print("\n友好版输出：")
    print(friendly_result.content)


def demo_conversation_manager() -> None:
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

    conversation.trim_recent(keep_last_messages=4)
    print("\n裁剪后历史：")
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
    load_env_if_possible()
    print_role_explanation()
    print_single_vs_multi_turn()
    demo_system_prompt_comparison()
    demo_conversation_manager()


if __name__ == "__main__":
    main()
