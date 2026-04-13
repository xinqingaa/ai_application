"""
01_prompt_basics.py
Prompt 结构、失败模式与基础调试

运行方式：
    python 01_prompt_basics.py

依赖：
    pip install openai python-dotenv tiktoken
"""

from __future__ import annotations

from typing import Any

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

STRUCTURE_CHECKS = [
    ("角色", "has_role"),
    ("任务", "has_task"),
    ("上下文", "has_context"),
    ("约束", "has_constraints"),
    ("输出格式", "has_output_format"),
    ("负向限制", "has_negative_constraints"),
    ("示例", "has_examples"),
]


def build_vague_prompt() -> str:
    """作用：
    构造一个信息不足的示例 Prompt，用来演示“目标太模糊”的失败模式。

    参数：
    无。函数直接使用模块级常量 `REQUIREMENT_TEXT`。

    返回：
    一个刻意保持简短和宽泛的 Prompt 字符串。
    """
    return f"""帮我整理一下这个需求：

{REQUIREMENT_TEXT}
""".strip()


def build_conflicted_prompt() -> str:
    """作用：
    构造一个目标互相冲突的 Prompt，用来演示“要求太多且边界混乱”的问题。

    参数：
    无。函数直接使用模块级常量 `REQUIREMENT_TEXT`。

    返回：
    一个同时混入多种任务诉求的 Prompt 字符串。
    """
    return f"""
你是一个产品经理。

请整理下面的需求，最好顺便给出技术实现、产品规划、商业价值、竞品分析和详细页面文案。
要求尽量详细，但也不要太长。
你可以自由发挥，不一定完全按照原文。

需求：
{REQUIREMENT_TEXT}
""".strip()


def build_structured_prompt() -> str:
    """作用：
    构造一个结构完整的 Prompt，作为本脚本里的对照组。

    参数：
    无。函数直接使用模块级常量 `REQUIREMENT_TEXT`。

    返回：
    一个包含角色、任务、输入、约束和输出格式的 Prompt 字符串。
    """
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
    """作用：
    把单段 Prompt 包装成聊天消息列表，供 `run_chat()` 统一调用。

    参数：
    prompt: 已经构造好的用户提示词文本。

    返回：
    一个包含 system 和 user 两条消息的列表。
    """
    return [
        {
            "role": "system",
            "content": "你是一个严谨的 AI 助教，擅长按要求完成结构化信息整理。",
        },
        {"role": "user", "content": prompt},
    ]


def diagnose_prompt(name: str, audit) -> dict[str, Any]:
    """作用：
    根据 Prompt 名称和审计结果生成更直观的诊断标签、结论和修改建议。

    参数：
    name: 当前 Prompt 版本的显示名称。
    audit: `analyze_prompt()` 返回的结构审计结果。

    返回：
    一个包含诊断标签、一句话反馈和建议动作的字典。
    """
    if "过于模糊" in name:
        return {
            "label": "信息不足",
            "summary": "几乎只给了原始需求，模型需要自己猜角色、任务和输出形式。",
            "actions": [
                "- 先补角色和明确任务，告诉模型到底在为谁输出什么。",
                "- 再加输出格式和长度限制，让结果更稳定、更可消费。",
                "- 如果不允许自由发挥，要显式补充“不要编造”这类负向限制。",
            ],
        }

    if "目标冲突" in name:
        return {
            "label": "目标打架",
            "summary": "信息比模糊版多，但一次塞进太多目标，模型很难判断优先级。",
            "actions": [
                "- 先删掉与当前任务无关的商业分析、竞品分析和页面文案要求。",
                "- 保留单一主目标，例如只输出“前端实现说明”而不是什么都做。",
                "- 再补固定输出格式，否则结果很容易又长又散。",
            ],
        }

    return {
        "label": "结构完整",
        "summary": "角色、任务、约束和输出格式都比较清楚，已经接近可复用版本。",
        "actions": [
            "- 当前版本已经适合作为稳定基线继续微调。",
            "- 如果后续仍有边界漂移，可以补 few-shot 示例而不是继续堆描述。",
            "- 如果要上线，建议再准备一个小评估集验证稳定性。",
        ],
    }


def get_hit_items(audit) -> list[str]:
    """作用：
    返回当前 Prompt 已命中的结构项名称，便于做横向比较。

    参数：
    audit: `analyze_prompt()` 返回的结构审计结果。

    返回：
    已命中结构项的名称列表。
    """
    return [label for label, field in STRUCTURE_CHECKS if getattr(audit, field)]


def get_missing_items(audit) -> list[str]:
    """作用：
    返回当前 Prompt 缺失的结构项名称，便于快速定位问题。

    参数：
    audit: `analyze_prompt()` 返回的结构审计结果。

    返回：
    缺失结构项的名称列表。
    """
    return [label for label, field in STRUCTURE_CHECKS if not getattr(audit, field)]


def build_prompt_entries() -> list[dict[str, Any]]:
    """作用：
    预先整理三种 Prompt 的文本、审计结果和诊断信息，作为后续展示的统一数据源。

    参数：
    无。函数内部会构造本脚本的三种 Prompt。

    返回：
    一个列表，每项都包含标题、Prompt 文本、审计结果和诊断说明。
    """
    prompts = [
        ("坏 Prompt：过于模糊", build_vague_prompt()),
        ("坏 Prompt：目标冲突", build_conflicted_prompt()),
        ("好 Prompt：结构化版本", build_structured_prompt()),
    ]
    entries: list[dict[str, Any]] = []
    for title, prompt in prompts:
        audit = analyze_prompt(prompt)
        entries.append(
            {
                "title": title,
                "prompt": prompt,
                "audit": audit,
                "diagnosis": diagnose_prompt(title, audit),
                "hit_items": get_hit_items(audit),
                "missing_items": get_missing_items(audit),
            }
        )
    return entries


def preview_prompt_lines(prompt: str, max_lines: int = 12) -> list[str]:
    """作用：
    生成 Prompt 的行级预览，避免完整大段文本影响比较体验。

    参数：
    prompt: 待预览的 Prompt 文本。
    max_lines: 最多展示多少行，默认显示前 12 行。

    返回：
    带行号的预览文本列表。
    """
    lines = prompt.splitlines()
    preview = [f"{index + 1:>2}. {line}" for index, line in enumerate(lines[:max_lines])]
    if len(lines) > max_lines:
        preview.append(f"... 共 {len(lines)} 行，此处仅展示前 {max_lines} 行")
    return preview


def print_prompt_overview(entries: list[dict[str, Any]]) -> None:
    """作用：
    先从总览视角展示三种 Prompt 的差异，让读者一眼看出结构好坏。

    参数：
    entries: 由 `build_prompt_entries()` 生成的 Prompt 信息列表。
    """
    lines = []
    for entry in entries:
        audit = entry["audit"]
        lines.append(
            f"- {entry['title']} | 诊断={entry['diagnosis']['label']} | "
            f"score={audit.score}/7 | tokens={audit.estimated_tokens} | "
            f"命中={' / '.join(entry['hit_items']) or '无'} | "
            f"缺失={' / '.join(entry['missing_items']) or '无'}"
        )
    print_lines("三种 Prompt 总览", lines)


def print_prompt_detail(entry: dict[str, Any]) -> None:
    """作用：
    按单个 Prompt 输出更细的分析，包括诊断、预览、优点和风险。

    参数：
    entry: 单个 Prompt 的整理结果字典。
    """
    audit = entry["audit"]
    print(f"\n{'=' * 72}")
    print(entry["title"])
    print("=" * 72)
    print(f"诊断标签：{entry['diagnosis']['label']}")
    print(f"一句话反馈：{entry['diagnosis']['summary']}")
    print(f"结构分：{audit.score}/7")
    print(f"估算 tokens：{audit.estimated_tokens}")
    print_lines("命中结构", [f"- {item}" for item in entry["hit_items"]] or ["- 无"])
    print_lines("缺失结构", [f"- {item}" for item in entry["missing_items"]] or ["- 无"])
    print_lines("建议先改什么", entry["diagnosis"]["actions"])
    print_lines("Prompt 预览", preview_prompt_lines(entry["prompt"]))
    print_lines("优点", [f"- {item}" for item in audit.strengths] or ["- 无"])
    print_lines("风险", [f"- {item}" for item in audit.risks] or ["- 无"])


def build_result_summary(entry: dict[str, Any], result) -> str:
    """作用：
    生成一行结果摘要，便于在三个 Prompt 之间横向比较模型反馈。

    参数：
    entry: 单个 Prompt 的整理结果字典。
    result: `run_chat()` 返回的统一聊天结果。

    返回：
    一行适合打印到总览区的摘要文本。
    """
    first_line = result.content.splitlines()[0] if result.content else "（空输出）"
    fallback_reason = None
    if result.debug_info:
        fallback_reason = (result.debug_info.get("chat") or {}).get("fallback_reason")
    return (
        f"- {entry['title']} | 模式={'MOCK' if result.mocked else '真实'} | "
        f"fallback={fallback_reason or '无'} | "
        f"error={result.error or '无'} | "
        f"输出摘要={first_line}"
    )


def print_result_detail(entry: dict[str, Any], result) -> None:
    """作用：
    打印单个 Prompt 的模型输出和完整调试信息。

    参数：
    entry: 单个 Prompt 的整理结果字典。
    result: `run_chat()` 返回的统一聊天结果。
    """
    finish_reason = None
    if result.raw_response_preview:
        choices = result.raw_response_preview.get("choices") or []
        if choices:
            finish_reason = choices[0].get("finish_reason")

    print(f"\n{'=' * 72}")
    print(f"{entry['title']} -> {'MOCK' if result.mocked else '真实'}输出")
    print("=" * 72)
    print(f"- 调用模式: {'MOCK' if result.mocked else '真实'}")
    print(f"- elapsed_ms: {result.elapsed_ms}")
    print(f"- finish_reason: {finish_reason or '（未返回）'}")
    print(f"- error: {result.error or '无'}")
    print("\n模型输出：")
    print(result.content)

    if result.debug_info:
        print_json(f"{entry['title']} -> debug_info", result.debug_info)


def run_comparison() -> None:
    """作用：
    串联本脚本完整演示流程，比较三类 Prompt 的结构分和模型输出。

    参数：
    无。函数内部会自行加载环境变量、provider 配置并执行对比。
    """
    load_env_if_possible()
    config = load_provider_config()
    entries = build_prompt_entries()
    results: list[tuple[dict[str, Any], Any]] = []

    print("当前运行配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- base_url: {config.base_url}")
    print(f"- ready: {config.is_ready}")
    print(f"- debug: True")

    print_lines("原始需求", [line for line in REQUIREMENT_TEXT.splitlines()])
    print_prompt_overview(entries)

    print_lines(
        "先看结论",
        [
            "- 模糊版几乎只给了原始需求，模型会自行决定回答角色、边界和格式。",
            "- 冲突版虽然信息更多，但因为目标混杂，结果通常会变得冗长、发散且不聚焦。",
            "- 结构化版本把角色、任务、约束和输出格式都写清楚了，更容易得到稳定结果。",
        ],
    )

    for entry in entries:
        print_prompt_detail(entry)

    print_lines(
        "调试原则",
        [
            "- 先修任务边界，再谈措辞是否漂亮。",
            "- 一次只改一个变量，例如只增加输出格式，不要同时改角色和约束。",
            "- 如果输出不稳定，先检查是否缺了上下文、约束、负向限制和格式说明。",
            "- 如果 Prompt 已经很长但结果仍差，优先考虑任务拆解，而不是继续堆说明文字。",
        ],
    )

    for entry in entries:
        result = run_chat(
            config,
            build_messages(entry["prompt"]),
            temperature=0.2,
            max_tokens=280,
        )
        results.append((entry, result))

    print_lines("模型反馈总览", [build_result_summary(entry, result) for entry, result in results])

    for entry, result in results:
        print_result_detail(entry, result)


if __name__ == "__main__":
    run_comparison()
