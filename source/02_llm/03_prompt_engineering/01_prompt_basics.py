"""
01_prompt_basics.py
Prompt 结构、失败模式与基础调试

运行方式：
    python 01_prompt_basics.py

依赖：
    pip install openai python-dotenv tiktoken
"""

from __future__ import annotations

from prompt_utils import (
    analyze_prompt,
    load_env_if_possible,
    load_provider_config,
    print_json,
    print_lines,
    run_chat,
)


REQUIREMENT_TEXT = """
我们要做一个 AI 聊天页面，需求如下：
1. 左侧展示历史会话列表，支持新建、重命名、删除。
2. 中间是对话区，支持多轮上下文。
3. 回答过程中要支持流式输出。
4. 用户希望能看到本轮大概消耗了多少 Token。
5. 后端先不做复杂权限，只做单用户版本。
""".strip()


def build_vague_prompt() -> str:
    return f"""帮我整理一下这个需求：

{REQUIREMENT_TEXT}
""".strip()


def build_conflicted_prompt() -> str:
    return f"""
你是一个产品经理。

请整理下面的需求，最好顺便给出技术实现、产品规划、商业价值、竞品分析和详细页面文案。
要求尽量详细，但也不要太长。
你可以自由发挥，不一定完全按照原文。

需求：
{REQUIREMENT_TEXT}
""".strip()


def build_structured_prompt() -> str:
    return f"""
你是一名资深 AI 产品需求分析助手，主要服务对象是前端开发者。

任务：
请根据下面的原始需求，整理一份「前端实现说明」。

输入材料：
{REQUIREMENT_TEXT}

约束：
1. 只整理和前端实现直接相关的信息。
2. 不要补充商业分析、竞品分析、市场背景。
3. 如果原始需求没有提到，就明确标注“待确认”，不要自行编造。
4. 用简洁中文输出，控制在 350 字以内。

输出格式：
## 页面目标
- ...

## 核心功能
- ...

## 前端状态
- ...

## 待确认问题
- ...
""".strip()


def build_messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "你是一个严谨的 AI 助教，擅长按要求完成结构化信息整理。",
        },
        {"role": "user", "content": prompt},
    ]


def print_audit(name: str, prompt: str) -> None:
    audit = analyze_prompt(prompt)
    print(f"\n{'=' * 72}")
    print(name)
    print("=" * 72)
    print(prompt)
    print("\n结构审计：")
    print(f"- score: {audit.score}/7")
    print(f"- estimated_tokens: {audit.estimated_tokens}")
    print(f"- has_role: {audit.has_role}")
    print(f"- has_task: {audit.has_task}")
    print(f"- has_context: {audit.has_context}")
    print(f"- has_constraints: {audit.has_constraints}")
    print(f"- has_output_format: {audit.has_output_format}")
    print(f"- has_negative_constraints: {audit.has_negative_constraints}")
    print(f"- has_examples: {audit.has_examples}")
    print_lines("优点", [f"- {item}" for item in audit.strengths] or ["- 无"])
    print_lines("风险", [f"- {item}" for item in audit.risks] or ["- 无"])


def run_comparison() -> None:
    load_env_if_possible()
    config = load_provider_config()
    prompts = [
        ("坏 Prompt：过于模糊", build_vague_prompt()),
        ("坏 Prompt：目标冲突", build_conflicted_prompt()),
        ("好 Prompt：结构化版本", build_structured_prompt()),
    ]

    print("当前运行配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- base_url: {config.base_url}")
    print(f"- ready: {config.is_ready}")

    for title, prompt in prompts:
        print_audit(title, prompt)

    print_lines(
        "调试原则",
        [
            "- 先修任务边界，再谈措辞是否漂亮。",
            "- 一次只改一个变量，例如只增加输出格式，不要同时改角色和约束。",
            "- 如果输出不稳定，先检查是否缺了上下文、约束、负向限制和格式说明。",
            "- 如果 Prompt 已经很长但结果仍差，优先考虑任务拆解，而不是继续堆说明文字。",
        ],
    )

    for title, prompt in prompts:
        result = run_chat(config, build_messages(prompt), temperature=0.2, max_tokens=280)
        print_json(
            f"{title} -> request_preview",
            result.request_preview,
        )
        print(f"\n{title} -> {'MOCK' if result.mocked else '真实'}输出：")
        print(result.content)


if __name__ == "__main__":
    run_comparison()
