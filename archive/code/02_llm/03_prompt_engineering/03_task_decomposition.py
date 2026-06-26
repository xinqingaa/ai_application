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


def print_section(title: str, description: str | None = None) -> None:
    """作用：
    打印统一样式的分割线标题，帮助终端里快速识别当前阶段。

    参数：
    title: 当前阶段标题，例如“模式 1：单步方案”。
    description: 可选补充说明，用于解释这一段输出为什么存在。
    """
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)
    if description:
        print(description)


def load_tickets() -> list[dict[str, str]]:
    """作用：
    读取工单样本数据，作为单步 Prompt 和分阶段 Prompt 的共同输入。

    参数：
    无。函数直接读取模块级常量 `DATA_FILE`。

    返回：
    一个工单列表，每项通常包含标题、内容和客户等级等字段。
    """
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def build_single_step_prompt(ticket: dict[str, str]) -> str:
    """作用：
    构造一个把“分析 + 判断 + 回复”都压在同一步里的 Prompt。

    参数：
    ticket: 单条工单数据，至少包含 `title`、`content` 和 `customer_tier`。

    返回：
    一个故意不做任务拆解的 Prompt 字符串。
    """
    return f"""
请阅读下面的用户工单，完成问题分析、优先级判断，并给出客服回复。

工单标题：{ticket['title']}
工单内容：{ticket['content']}
用户等级：{ticket['customer_tier']}

输出尽量完整。
""".strip()


def build_analysis_prompt(ticket: dict[str, str]) -> str:
    """作用：
    构造拆解流程的第一步 Prompt，只负责分析问题和沉淀中间结果。

    参数：
    ticket: 单条工单数据，至少包含 `title`、`content` 和 `customer_tier`。

    返回：
    一个只要求输出分析结构的 Prompt 字符串。
    """
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
    """作用：
    构造拆解流程的第二步 Prompt，基于分析结果生成面向用户的回复。

    参数：
    ticket: 原始工单数据，用于保留上下文。
    analysis_result: 第一步分析阶段产出的中间结果文本。

    返回：
    一个聚焦客服回复生成的 Prompt 字符串。
    """
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
    """作用：
    演示复杂任务拆解前后的差异，依次执行单步方案和两步拆解方案。

    参数：
    无。函数内部会加载环境、读取示例工单并调用模型。
    """
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
    print_section(
        "模式 1：单步方案",
        "这组调用把“问题分析 + 优先级判断 + 客服回复”压成一次模型请求，方便和拆解方案做对照。",
    )

    # 第一组结果故意把多个子任务压成一步，用来和拆解版形成对照。
    single_step_prompt = build_single_step_prompt(ticket)
    single_step_result = run_chat(
        config,
        messages=[
            {"role": "system", "content": "你是一个客服运营助理。"},
            {"role": "user", "content": single_step_prompt},
        ],
        temperature=0.2,
        max_tokens=280,
        debug_label="模式 1 / 单步方案 / 单次调用",
    )

    print_section(
        "模式 2：拆解方案",
        "这组调用拆成两步：先沉淀结构化分析，再基于分析结果生成面向用户的回复。",
    )
    # 第二组结果先沉淀中间分析，再让下一步消费这份分析结果。
    analysis_prompt = build_analysis_prompt(ticket)
    analysis_result = run_chat(
        config,
        messages=[
            {"role": "system", "content": "你擅长先分析事实，再给出结论。"},
            {"role": "user", "content": analysis_prompt},
        ],
        temperature=0.0,
        max_tokens=220,
        debug_label="模式 2 / 拆解方案 / 步骤 1：问题分析",
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
        debug_label="模式 2 / 拆解方案 / 步骤 2：生成回复",
    )

    print_section(
        "结果对比：模式 1 vs 模式 2",
        "你现在可以直接看两种模式的最终输出差异，不需要先在连续 debug 日志里自己找归属。",
    )

    print_section("[模式 1：单步方案的 Prompt]")
    print(single_step_prompt)
    print("\n[模式 1：单步方案的输出：]")
    print(single_step_result.content)

    print_section("[模式 2：步骤 1 分析 Prompt]")
    print(analysis_prompt)
    print("\n[模式 2：步骤 1 分析输出：]")
    print(analysis_result.content)

    print_section("[模式 2：步骤 2 回复 Prompt]")
    print(reply_prompt)
    print("\n[模式 2：步骤 2 最终回复：]")
    print(reply_result.content)

    print_lines(
        "怎么读这次实验",
        [
            "- 看模式 1：如果一次性要求模型同时分析、判断、回复，输出往往更长，也更容易夹带多余承诺。",
            "- 看模式 2 的步骤 1：这里先把“问题类型、影响范围、紧急程度、待确认信息”显式化。",
            "- 看模式 2 的步骤 2：第二次调用只消费分析结果来写回复，所以更容易控制语气、长度和承诺边界。",
            "- 每段 [DEBUG] 日志现在都会带上“模式 / 步骤”标签，对照终端时可以直接知道当前是哪次调用。",
        ],
    )


if __name__ == "__main__":
    main()
