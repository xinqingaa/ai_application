"""
02_few_shot.py
Zero-shot / 坏 Few-shot / 好 Few-shot 的对比实验

运行方式：
    python 02_few_shot.py

依赖：
    pip install openai python-dotenv tiktoken
"""

from __future__ import annotations

import json
from pathlib import Path

from prompt_utils import (
    estimate_tokens,
    load_env_if_possible,
    load_provider_config,
    normalize_label,
    print_lines,
    run_chat,
)


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "reviews.json"
ALLOWED_LABELS = ["正面", "负面", "中性"]


def load_cases() -> list[dict[str, str]]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def build_zero_shot_prompt(text: str) -> str:
    return f"""
请判断下面评论的情感倾向，只能输出：正面 / 负面 / 中性

评论：{text}
输出：
""".strip()


def build_bad_few_shot_prompt(text: str) -> str:
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


def evaluate_prompt_set(
    name: str,
    prompt_builder,
    cases: list[dict[str, str]],
    config,
    max_cases: int = 4,
) -> None:
    print(f"\n{'=' * 72}")
    print(f"{name} 评估")
    print("=" * 72)

    sample_prompt = prompt_builder(cases[0]["text"])
    print(f"- sample_prompt_tokens: {estimate_tokens(sample_prompt)}")
    print(f"- cases_for_live_eval: {min(max_cases, len(cases))}")

    if not config.is_ready:
        print("- 当前未配置 API Key，本轮只展示 Prompt 结构和评估方法。")
        print("\n示例 Prompt：")
        print(sample_prompt)
        return

    rows: list[dict[str, str | bool]] = []
    for item in cases[:max_cases]:
        prompt = prompt_builder(item["text"])
        result = run_chat(
            config,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个只输出标签的分类助手。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=10,
        )
        predicted = normalize_label(result.content, ALLOWED_LABELS)
        rows.append(
            {
                "case_id": item["id"],
                "expected": item["label"],
                "predicted": predicted,
                "correct": predicted == item["label"],
                "text": item["text"],
            }
        )

    correct_count = sum(1 for row in rows if row["correct"])
    print(f"- accuracy@{len(rows)}: {correct_count}/{len(rows)}")
    for row in rows:
        print(
            f"- [{row['case_id']}] expected={row['expected']} "
            f"predicted={row['predicted']} correct={row['correct']}"
        )
        print(f"  text: {row['text']}")


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()
    cases = load_cases()

    print("当前运行配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- ready: {config.is_ready}")

    print_lines(
        "Few-shot 设计要点",
        [
            "- 示例标签必须和真实输出标签完全一致，不能一会儿写“负面”，一会儿写“差评”。",
            "- 示例要覆盖边界样本，尤其是“有好有坏”的中性评论。",
            "- Few-shot 不是越多越好，先用 3-5 个高质量示例把边界讲清楚。",
            "- 评估要看一组样本，而不是只看一条你最满意的案例。",
        ],
    )

    evaluate_prompt_set("Zero-shot", build_zero_shot_prompt, cases, config)
    evaluate_prompt_set("坏 Few-shot", build_bad_few_shot_prompt, cases, config)
    evaluate_prompt_set("好 Few-shot", build_good_few_shot_prompt, cases, config)


if __name__ == "__main__":
    main()
