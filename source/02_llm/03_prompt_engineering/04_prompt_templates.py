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
    """作用：
    管理 `prompts/` 目录下的模板文件，统一提供列出、读取、描述和渲染能力。

    这个类的定位是“轻量模板仓库”：
    上层脚本不直接散落读文件，而是通过它集中访问模板资产。
    """

    def __init__(self, prompt_dir: Path):
        """作用：
        初始化模板库实例，记录模板目录位置。

        参数：
        prompt_dir: 存放 `.txt` Prompt 模板的目录路径。
        """
        self.prompt_dir = prompt_dir

    def list_templates(self) -> list[str]:
        """作用：
        列出模板目录下的全部模板文件名。

        参数：
        无。函数直接扫描初始化时传入的模板目录。

        返回：
        一个按名称排序的模板文件名列表。
        """
        return sorted(path.name for path in self.prompt_dir.glob("*.txt"))

    def load_text(self, name: str) -> str:
        """作用：
        根据模板文件名读取对应模板文本。

        参数：
        name: 模板文件名，例如 `support_reply.txt`。

        返回：
        模板原始文本内容。
        """
        return read_text(self.prompt_dir / name)

    def describe(self, name: str) -> dict[str, object]:
        """作用：
        输出某个模板的基础说明，方便快速查看变量和预览内容。

        参数：
        name: 待查看的模板文件名。

        返回：
        一个包含模板名、变量列表和前几行预览内容的字典。
        """
        text = self.load_text(name)
        return {
            "name": name,
            "variables": extract_template_variables(text),
            "preview_lines": text.splitlines()[:10],
        }

    def render(self, name: str, variables: dict[str, object]) -> tuple[str, dict[str, object]]:
        """作用：
        渲染指定模板，并把变量校验结果一起整理成上层更易打印的结构。

        参数：
        name: 待渲染的模板文件名。
        variables: 传给模板的变量字典。

        返回：
        一个二元组：`(渲染后的 Prompt, 变量校验摘要字典)`。
        """
        text = self.load_text(name)
        rendered, check = render_template_text(text, variables)
        return rendered, {
            "variables": check.variables,
            "missing_variables": check.missing_variables,
            "unused_variables": check.unused_variables,
        }


def load_json(path: Path) -> list[dict[str, str]]:
    """作用：
    读取本章示例使用的 JSON 数据文件。

    参数：
    path: 待读取的 JSON 文件路径。

    返回：
    反序列化后的列表数据。
    """
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    """作用：
    演示模板库的完整用法：列模板、看变量、渲染模板、导出预览并执行一次调用。

    参数：
    无。函数内部会加载环境、准备样本数据并组织整条模板工程化流程。
    """
    load_env_if_possible()
    config = load_provider_config()
    library = PromptLibrary(PROMPTS_DIR)
    review = load_json(REVIEWS_FILE)[2]
    ticket = load_json(TICKETS_FILE)[1]

    print("模板列表：")
    for name in library.list_templates():
        print(f"- {name}")

    for name in ["requirement_summary_v2.txt", "sentiment_few_shot.txt", "support_reply.txt"]:
        description = library.describe(name)
        print(f"\n{name}")
        print(f"- variables: {description['variables']}")
        for line in description["preview_lines"]:
            print(f"  {line}")

    # 先渲染三种不同用途的模板，展示变量替换和校验结果。
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

    # 把渲染结果固化到 exports 目录，方便回看当前模板版本的实际展开内容。
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
