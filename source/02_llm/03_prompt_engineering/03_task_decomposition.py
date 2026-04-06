"""
03_task_decomposition.py
复杂任务拆解：单步 Prompt vs 分阶段 Prompt

运行方式：
    python 03_task_decomposition.py

依赖：
    pip install openai python-dotenv tiktoken
"""

from __future__ import annotations

import json
from pathlib import Path

from prompt_utils import load_env_if_possible, load_provider_config, print_lines, run_chat


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "support_tickets.json"


def load_tickets() -> list[dict[str, str]]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def build_single_step_prompt(ticket: dict[str, str]) -> str:
    return f"""
请阅读下面的用户工单，完成问题分析、优先级判断，并给出客服回复。

工单标题：{ticket['title']}
工单内容：{ticket['content']}
用户等级：{ticket['customer_tier']}

输出尽量完整。
""".strip()


def build_analysis_prompt(ticket: dict[str, str]) -> str:
    return f"""
你是一名售后问题分析助手。

任务：
先只做问题分析，不要直接写客服回复。

工单标题：{ticket['title']}
工单内容：{ticket['content']}
用户等级：{ticket['customer_tier']}

输出格式：
问题类型：<登录 / 支付 / 数据 / 功能 / 其他>
影响范围：<单个用户 / 多个用户 / 未知>
紧急程度：<高 / 中 / 低>
已知事实：
- ...
待确认信息：
- ...
""".strip()


def build_reply_prompt(ticket: dict[str, str], analysis_result: str) -> str:
    return f"""
你是一名面向用户的一线客服助手。

任务：
基于下面已经完成的问题分析，写一段发给用户的回复。

原始工单：
标题：{ticket['title']}
内容：{ticket['content']}
用户等级：{ticket['customer_tier']}

分析结果：
{analysis_result}

约束：
1. 先确认用户遇到的问题，再说明我们会怎么跟进。
2. 不要承诺系统一定在多久恢复，除非分析结果里明确给出。
3. 语气专业、克制、简洁。
4. 控制在 120 字以内。
""".strip()


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()
    ticket = load_tickets()[0]

    print("当前工单：")
    print(f"- id: {ticket['id']}")
    print(f"- title: {ticket['title']}")
    print(f"- customer_tier: {ticket['customer_tier']}")
    print(f"- content: {ticket['content']}")

    print_lines(
        "拆解原则",
        [
            "- 一个 Prompt 同时做“抽取 + 判断 + 生成”时，失败点很难定位。",
            "- 先把中间结果显式化，可以判断到底是分析错了，还是生成回复时跑偏了。",
            "- 拆解后的每一步都应该有独立输入、独立输出、独立校验标准。",
        ],
    )

    single_step_prompt = build_single_step_prompt(ticket)
    single_step_result = run_chat(
        config,
        messages=[
            {"role": "system", "content": "你是一个客服运营助理。"},
            {"role": "user", "content": single_step_prompt},
        ],
        temperature=0.2,
        max_tokens=280,
    )

    analysis_prompt = build_analysis_prompt(ticket)
    analysis_result = run_chat(
        config,
        messages=[
            {"role": "system", "content": "你擅长先分析事实，再给出结论。"},
            {"role": "user", "content": analysis_prompt},
        ],
        temperature=0.0,
        max_tokens=220,
    )

    reply_prompt = build_reply_prompt(ticket, analysis_result.content)
    reply_result = run_chat(
        config,
        messages=[
            {"role": "system", "content": "你是客服回复助手。"},
            {"role": "user", "content": reply_prompt},
        ],
        temperature=0.2,
        max_tokens=180,
    )

    print(f"\n{'=' * 72}")
    print("单步 Prompt")
    print("=" * 72)
    print(single_step_prompt)
    print("\n输出：")
    print(single_step_result.content)

    print(f"\n{'=' * 72}")
    print("拆解步骤 1：分析 Prompt")
    print("=" * 72)
    print(analysis_prompt)
    print("\n输出：")
    print(analysis_result.content)

    print(f"\n{'=' * 72}")
    print("拆解步骤 2：回复 Prompt")
    print("=" * 72)
    print(reply_prompt)
    print("\n输出：")
    print(reply_result.content)


if __name__ == "__main__":
    main()
