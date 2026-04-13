"""
02_few_shot.py
Zero-shot / 坏 Few-shot / 好 Few-shot 的对比实验

运行方式：
    python 02_few_shot.py

依赖：
    pip install openai python-dotenv tiktoken

这个脚本本质上不是“打印三个 Prompt”，而是一个最小 Few-shot 评估器。
它的执行流程是：

1. `load_cases()`：读取评论分类样本集
2. `build_strategy_catalog()`：准备三种待比较的 Prompt 策略
3. `evaluate_strategy()`：用同一批样本评估每个策略
4. `evaluate_case()`：对单条样本执行“构造 Prompt -> 调模型/Mock -> 归一化标签 -> 对比答案”
5. `print_strategy_detail()`：输出每个策略的 Prompt 预览、样本结果和调试信息

建议阅读顺序：
load_cases()
-> build_zero_shot_prompt() / build_bad_few_shot_prompt() / build_good_few_shot_prompt()
-> build_strategy_catalog()
-> evaluate_case()
-> evaluate_strategy()
-> main()
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from prompt_utils import (
    estimate_tokens,
    load_env_if_possible,
    load_provider_config,
    normalize_label,
    print_json,
    print_lines,
    run_chat,
)


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "reviews.json"
ALLOWED_LABELS = ["正面", "负面", "中性"]
DEFAULT_MAX_CASES = 5

PromptBuilder = Callable[[str], str]


@dataclass
class PromptStrategy:
    """单个 Prompt 策略的描述对象。"""

    name: str
    diagnosis: str
    why_it_exists: str
    prompt_builder: PromptBuilder


@dataclass
class CaseResult:
    """单条样本的评估结果。"""

    case_id: str
    text: str
    difficulty: str
    expected: str
    predicted: str
    correct: bool | None
    mocked: bool
    raw_output: str
    error: str | None
    debug_info: dict[str, Any] | None


def load_cases() -> list[dict[str, str]]:
    """作用：
    读取情感分类评估样本，作为 Zero-shot 和 Few-shot 的统一测试集。

    参数：
    无。函数直接读取模块级常量 `DATA_FILE`。

    返回：
    一个评论样本列表，每项包含 id、text、label 和 difficulty 等字段。
    """
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def build_zero_shot_prompt(text: str) -> str:
    """作用：
    构造最基础的 Zero-shot 分类 Prompt，不提供任何示例。

    参数：
    text: 待分类的评论文本。

    返回：
    一个只包含任务说明和输入文本的 Prompt 字符串。
    """
    return f"""
请判断下面评论的情感倾向，只能输出：正面 / 负面 / 中性

评论：{text}
输出：
""".strip()


def build_bad_few_shot_prompt(text: str) -> str:
    """作用：
    构造一个质量较差的 Few-shot Prompt，用来展示标签不一致的副作用。

    参数：
    text: 待分类的评论文本。

    返回：
    一个故意混用“正面 / 差评 / 一般”等标签的 Prompt 字符串。
    """
    return f"""
请做评论分类。

示例1：
输入：这个产品体验绝了，界面很顺手。
输出：正面

示例2：
输入：服务态度很差，根本没人处理。
输出：差评

示例3：
输入：功能比较多，先继续观察。
输出：一般

现在处理：
输入：{text}
输出：
""".strip()


def build_good_few_shot_prompt(text: str) -> str:
    """作用：
    构造一个结构较完整的 Few-shot Prompt，演示高质量示例应如何组织。

    参数：
    text: 待分类的评论文本。

    返回：
    一个包含角色、规则和统一标签示例的 Prompt 字符串。
    """
    return f"""
你是一名评论情感分类助手。

任务：
判断评论的情感倾向，只能输出以下三个标签之一：
- 正面
- 负面
- 中性

分类规则：
1. 明显表达满意、称赞、推荐，输出 正面。
2. 明显表达抱怨、不满、故障、差评，输出 负面。
3. 既有优点也有缺点、或整体评价平淡，输出 中性。
4. 不要输出解释，不要输出标点，不要输出其他标签。

示例：
输入：客服响应很快，问题当天就解决了。
输出：正面

输入：登录连续失败三次，页面还一直报错。
输出：负面

输入：物流速度一般，但包装比较完整。
输出：中性

输入：价格不算低，不过质量还可以接受。
输出：中性

现在请判断：
输入：{text}
输出：
""".strip()


def build_strategy_catalog() -> list[PromptStrategy]:
    """作用：
    把三种待比较的 Prompt 策略整理成统一清单，供后续评估循环使用。

    参数：
    无。函数内部会绑定三种 Prompt 构造函数。

    返回：
    一个 `PromptStrategy` 列表，每项都描述一种评估策略。
    """
    return [
        PromptStrategy(
            name="Zero-shot",
            diagnosis="基线方案",
            why_it_exists="不放示例，只看纯任务说明能否支撑分类。",
            prompt_builder=build_zero_shot_prompt,
        ),
        PromptStrategy(
            name="坏 Few-shot",
            diagnosis="反例方案",
            why_it_exists="故意制造标签不一致和示例松散的问题，观察错误如何被放大。",
            prompt_builder=build_bad_few_shot_prompt,
        ),
        PromptStrategy(
            name="好 Few-shot",
            diagnosis="改进方案",
            why_it_exists="通过统一标签、补分类规则和边界样本，观察稳定性是否提升。",
            prompt_builder=build_good_few_shot_prompt,
        ),
    ]


def build_classification_messages(prompt: str) -> list[dict[str, str]]:
    """作用：
    把分类 Prompt 包装成统一的聊天消息列表。

    参数：
    prompt: 已经构造好的用户 Prompt。

    返回：
    一个包含 system 和 user 两条消息的列表。
    """
    return [
        {
            "role": "system",
            "content": "你是一个只输出标准标签的分类助手。",
        },
        {"role": "user", "content": prompt},
    ]


def preview_prompt_lines(prompt: str, max_lines: int = 16) -> list[str]:
    """作用：
    生成 Prompt 的预览片段，避免直接打印完整长文本影响阅读节奏。

    参数：
    prompt: 待预览的 Prompt 文本。
    max_lines: 最多展示多少行，默认前 16 行。

    返回：
    带行号的预览文本列表。
    """
    lines = prompt.splitlines()
    preview = [f"{index + 1:>2}. {line}" for index, line in enumerate(lines[:max_lines])]
    if len(lines) > max_lines:
        preview.append(f"... 共 {len(lines)} 行，此处仅展示前 {max_lines} 行")
    return preview


def count_by_field(cases: list[dict[str, str]], field_name: str) -> dict[str, int]:
    """作用：
    统计样本集中某个字段的分布情况，帮助先理解评估数据长什么样。

    参数：
    cases: 评论样本列表。
    field_name: 要统计的字段名，例如 `label` 或 `difficulty`。

    返回：
    一个 `{字段值: 数量}` 形式的统计结果字典。
    """
    counts: dict[str, int] = {}
    for item in cases:
        key = item[field_name]
        counts[key] = counts.get(key, 0) + 1
    return counts


def evaluate_case(
    strategy: PromptStrategy,
    case: dict[str, str],
    config,
) -> CaseResult:
    """作用：
    评估单条样本在某个 Prompt 策略下的表现。

    参数：
    strategy: 当前要评估的 Prompt 策略。
    case: 单条评论样本，至少包含 id、text、label 和 difficulty。
    config: 当前 provider 运行配置。

    返回：
    一个 `CaseResult`，记录这条样本的预测、是否命中、原始输出和调试信息。

    流程位置：
    这是 Few-shot 脚本的核心单元，内部会依次执行：
    `prompt_builder -> run_chat -> 解析预测 -> 对比标准答案`。
    """
    prompt = strategy.prompt_builder(case["text"])
    result = run_chat(
        config,
        messages=build_classification_messages(prompt),
        temperature=0.0,
        max_tokens=10,
    )

    if result.mocked:
        predicted = "MOCK"
        correct = None
    else:
        predicted = normalize_label(result.content, ALLOWED_LABELS)
        correct = predicted == case["label"]

    return CaseResult(
        case_id=case["id"],
        text=case["text"],
        difficulty=case["difficulty"],
        expected=case["label"],
        predicted=predicted,
        correct=correct,
        mocked=result.mocked,
        raw_output=result.content,
        error=result.error,
        debug_info=result.debug_info,
    )


def evaluate_strategy(
    strategy: PromptStrategy,
    cases: list[dict[str, str]],
    config,
    max_cases: int = DEFAULT_MAX_CASES,
) -> dict[str, Any]:
    """作用：
    用同一批样本评估某一组 Prompt 的表现，并整理成统一汇总结果。

    参数：
    strategy: 当前要评估的 Prompt 策略。
    cases: 待评估的数据样本列表。
    config: 当前 provider 运行配置。
    max_cases: 本轮最多评估多少条样本。

    返回：
    一个字典，包含 Prompt 预览、token 成本、逐条样本结果和整体统计信息。
    """
    active_cases = cases[: min(max_cases, len(cases))]
    sample_prompt = strategy.prompt_builder(active_cases[0]["text"])
    rows = [evaluate_case(strategy, item, config) for item in active_cases]
    comparable_rows = [row for row in rows if row.correct is not None]
    correct_count = sum(1 for row in comparable_rows if row.correct)

    if comparable_rows:
        accuracy_text = f"{correct_count}/{len(comparable_rows)}"
    else:
        accuracy_text = "未计算（当前为 Mock 调试模式）"

    return {
        "strategy": strategy,
        "sample_prompt": sample_prompt,
        "sample_prompt_tokens": estimate_tokens(sample_prompt),
        "rows": rows,
        "cases_for_eval": len(active_cases),
        "comparable_cases": len(comparable_rows),
        "correct_count": correct_count,
        "accuracy_text": accuracy_text,
        "mocked_count": sum(1 for row in rows if row.mocked),
        "first_debug_info": rows[0].debug_info if rows else None,
    }


def print_execution_flow() -> None:
    """作用：
    把脚本的执行链路先打印出来，帮助读者带着“流程图”去读代码和输出。

    参数：
    无。
    """
    print_lines(
        "脚本执行流程",
        [
            "1. load_cases()：读取 reviews.json，准备一组带标准答案的评论样本。",
            "2. build_strategy_catalog()：定义 Zero-shot、坏 Few-shot、好 Few-shot 三种策略。",
            "3. evaluate_strategy()：对每个策略循环评估同一批样本。",
            "4. evaluate_case()：单条样本会经历“构造 Prompt -> run_chat() -> 对比标准答案”这条链路。",
            "5. 最后打印策略总览、整体结果对比、每种策略的细节和调试信息。",
        ],
    )


def print_dataset_overview(cases: list[dict[str, str]]) -> None:
    """作用：
    打印评估数据集的规模和标签分布，先让读者知道脚本到底在评估什么。

    参数：
    cases: 评论样本列表。
    """
    label_counts = count_by_field(cases, "label")
    difficulty_counts = count_by_field(cases, "difficulty")
    print_lines(
        "数据集概览",
        [
            f"- 样本总数: {len(cases)}",
            f"- 标签分布: {label_counts}",
            f"- 难度分布: {difficulty_counts}",
            "- 这组数据不是训练集，而是一个小型评估集，用来比较不同 Prompt 策略的稳定性。",
        ],
    )


def print_strategy_catalog(strategies: list[PromptStrategy], cases: list[dict[str, str]]) -> None:
    """作用：
    先横向介绍三种策略的定位和大致成本，便于理解为什么要做三组对比。

    参数：
    strategies: 策略列表。
    cases: 评论样本列表，用于生成一个代表性 Prompt 做 token 估算。
    """
    sample_text = cases[0]["text"]
    lines = []
    for strategy in strategies:
        prompt = strategy.prompt_builder(sample_text)
        lines.append(
            f"- {strategy.name} | {strategy.diagnosis} | "
            f"sample_prompt_tokens={estimate_tokens(prompt)} | "
            f"{strategy.why_it_exists}"
        )
    print_lines("三种策略总览", lines)


def print_evaluation_overview(results: list[dict[str, Any]]) -> None:
    """作用：
    把三种策略的整体评估结果放在同一个总览区里对比。

    参数：
    results: 多个策略的评估结果列表。
    """
    lines = []
    for item in results:
        strategy = item["strategy"]
        lines.append(
            f"- {strategy.name} | {strategy.diagnosis} | "
            f"accuracy={item['accuracy_text']} | "
            f"sample_prompt_tokens={item['sample_prompt_tokens']} | "
            f"mocked_cases={item['mocked_count']}/{item['cases_for_eval']}"
        )
    print_lines("评估结果总览", lines)


def print_strategy_detail(result: dict[str, Any]) -> None:
    """作用：
    打印单个策略的 Prompt 预览、逐条样本结果和代表性调试信息。

    参数：
    result: `evaluate_strategy()` 返回的单个策略结果字典。
    """
    strategy = result["strategy"]
    print(f"\n{'=' * 72}")
    print(f"{strategy.name} | {strategy.diagnosis}")
    print("=" * 72)
    print(f"为什么要有这组策略：{strategy.why_it_exists}")
    print(f"sample_prompt_tokens: {result['sample_prompt_tokens']}")
    print(f"accuracy: {result['accuracy_text']}")
    print(f"mocked_cases: {result['mocked_count']}/{result['cases_for_eval']}")

    print_lines("Prompt 预览", preview_prompt_lines(result["sample_prompt"]))

    row_lines = []
    for row in result["rows"]:
        if row.correct is None:
            status = "未计算"
        else:
            status = "命中" if row.correct else "未命中"
        row_lines.append(
            f"- [{row.case_id}] expected={row.expected} predicted={row.predicted} "
            f"status={status} difficulty={row.difficulty}"
        )
        row_lines.append(f"  text: {row.text}")
        row_lines.append(f"  raw_output: {row.raw_output}")
        if row.error:
            row_lines.append(f"  error: {row.error}")
    print_lines("逐条样本结果", row_lines)

    if result["first_debug_info"]:
        print_json(f"{strategy.name} -> 首条样本 debug_info", result["first_debug_info"])


def main() -> None:
    """作用：
    组织 Few-shot 章节的完整演示：先解释流程，再依次评估三组 Prompt 策略。

    参数：
    无。函数内部会加载环境、读取数据、执行评估并打印结果。
    """
    load_env_if_possible()
    config = load_provider_config()
    cases = load_cases()
    strategies = build_strategy_catalog()

    print("当前运行配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- ready: {config.is_ready}")

    print_execution_flow()
    print_dataset_overview(cases)

    print_lines(
        "Few-shot 设计要点",
        [
            "- Zero-shot 是基线，用来验证“只靠规则是否已经够用”。",
            "- 坏 Few-shot 是反例，用来说明示例本身也可能把任务边界带偏。",
            "- 好 Few-shot 是改进版，用来演示规则、标签一致性和边界样本如何一起工作。",
            "- 评估重点不是单条样本，而是同一批样本在三种策略下的整体差异。",
        ],
    )

    print_strategy_catalog(strategies, cases)

    results = [evaluate_strategy(strategy, cases, config) for strategy in strategies]
    print_evaluation_overview(results)

    for result in results:
        print_strategy_detail(result)


if __name__ == "__main__":
    main()
