"""
04_prompt_templates.py
Prompt 模板库、变量校验与渲染预览

运行方式：
    python 04_prompt_templates.py
"""

from __future__ import annotations

import json
from pathlib import Path

from prompt_utils import (
    extract_template_variables,
    load_env_if_possible,
    load_provider_config,
    read_text,
    render_template_text,
    run_chat,
    timestamp_slug,
    write_json_export,
)


BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
REVIEWS_FILE = BASE_DIR / "data" / "reviews.json"
TICKETS_FILE = BASE_DIR / "data" / "support_tickets.json"


class PromptLibrary:
    def __init__(self, prompt_dir: Path):
        self.prompt_dir = prompt_dir

    def list_templates(self) -> list[str]:
        return sorted(path.name for path in self.prompt_dir.glob("*.txt"))

    def load_text(self, name: str) -> str:
        return read_text(self.prompt_dir / name)

    def describe(self, name: str) -> dict[str, object]:
        text = self.load_text(name)
        return {
            "name": name,
            "variables": extract_template_variables(text),
            "preview_lines": text.splitlines()[:10],
        }

    def render(self, name: str, variables: dict[str, object]) -> tuple[str, dict[str, object]]:
        text = self.load_text(name)
        rendered, check = render_template_text(text, variables)
        return rendered, {
            "variables": check.variables,
            "missing_variables": check.missing_variables,
            "unused_variables": check.unused_variables,
        }


def load_json(path: Path) -> list[dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()
    library = PromptLibrary(PROMPTS_DIR)
    review = load_json(REVIEWS_FILE)[2]
    ticket = load_json(TICKETS_FILE)[1]

    print("模板列表：")
    for name in library.list_templates():
        print(f"- {name}")

    for name in ["requirement_summary_v2.txt", "support_reply.txt"]:
        description = library.describe(name)
        print(f"\n{name}")
        print(f"- variables: {description['variables']}")
        for line in description["preview_lines"]:
            print(f"  {line}")

    rendered_summary, summary_check = library.render(
        "requirement_summary_v2.txt",
        {
            "role": "前端需求整理助手",
            "task": "根据原始需求输出面向前端开发的功能说明",
            "source_text": (
                "我们要做一个带历史会话、流式输出和 token 统计的 AI 聊天页面，"
                "当前阶段先支持单用户使用。"
            ),
            "max_length": 280,
        },
    )

    rendered_sentiment, sentiment_check = library.render(
        "sentiment_few_shot.txt",
        {
            "input_text": review["text"],
        },
    )

    rendered_reply, reply_check = library.render(
        "support_reply.txt",
        {
            "ticket_title": ticket["title"],
            "ticket_content": ticket["content"],
            "customer_tier": ticket["customer_tier"],
            "analysis_result": (
                "问题类型：支付\n"
                "影响范围：单个用户\n"
                "紧急程度：中\n"
                "已知事实：用户付款后页面卡住，订单状态未更新。"
            ),
            "max_length": 120,
            "unused_demo_var": "这个变量会被检测为未使用",
        },
    )

    print(f"\n{'=' * 72}")
    print("渲染后的 requirement_summary_v2.txt")
    print("=" * 72)
    print(rendered_summary)
    print(f"- variable_check: {summary_check}")

    print(f"\n{'=' * 72}")
    print("渲染后的 sentiment_few_shot.txt")
    print("=" * 72)
    print(rendered_sentiment)
    print(f"- variable_check: {sentiment_check}")

    print(f"\n{'=' * 72}")
    print("渲染后的 support_reply.txt")
    print("=" * 72)
    print(rendered_reply)
    print(f"- variable_check: {reply_check}")

    export_path = write_json_export(
        f"template_preview_{timestamp_slug()}.json",
        {
            "summary": {
                "template": "requirement_summary_v2.txt",
                "check": summary_check,
                "rendered_prompt": rendered_summary,
            },
            "sentiment": {
                "template": "sentiment_few_shot.txt",
                "check": sentiment_check,
                "rendered_prompt": rendered_sentiment,
            },
            "reply": {
                "template": "support_reply.txt",
                "check": reply_check,
                "rendered_prompt": rendered_reply,
            },
        },
    )
    print(f"\n已导出模板预览：{export_path}")

    result = run_chat(
        config,
        messages=[
            {
                "role": "system",
                "content": "你是一个会严格遵守输出格式的助手。",
            },
            {"role": "user", "content": rendered_summary},
        ],
        temperature=0.2,
        max_tokens=240,
    )
    print(f"\n{'=' * 72}")
    print("模板调用结果")
    print("=" * 72)
    print(result.content)


if __name__ == "__main__":
    main()
