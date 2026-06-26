"""
04_extractor.py
通用结构化数据提取器：根据 Schema 自动生成 Prompt，批量提取并导出结果

运行方式：
    python 04_extractor.py

依赖：
    pip install openai python-dotenv pydantic
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from structured_utils import (
    format_validation_error,
    get_model_json_schema,
    is_pydantic_available,
    load_env_if_possible,
    load_provider_config,
    model_dump,
    model_validate,
    parse_json_output,
    print_json,
    run_chat,
    schema_to_prompt_description,
    timestamp_slug,
    write_json_export,
)

if is_pydantic_available():
    from pydantic import BaseModel, Field
else:  # pragma: no cover
    BaseModel = object  # type: ignore[assignment,misc]

    def Field(*args, **kwargs):  # type: ignore[no-redef]
        return None


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "customer_notes.json"


class SalesLead(BaseModel):
    name: str = Field(description="联系人姓名")
    company: str = Field(description="公司名称")
    city: str = Field(description="所在城市")
    intent_level: Literal["high", "medium", "low"] = Field(description="购买意向等级")
    budget: int | None = Field(default=None, ge=0, description="预算金额，单位元")
    next_action: str = Field(description="建议的下一步动作")


def print_section(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)


class StructuredExtractor:
    def __init__(self, config, schema_cls):
        self.config = config
        self.schema_cls = schema_cls

    def build_prompt(self, text: str) -> str:
        return f"""
你是一名销售线索提取助手。

任务：
请从下面的销售跟进记录中提取结构化信息，并只返回一个 JSON 对象。

销售记录：
{text}

目标 Schema：
{schema_to_prompt_description(self.schema_cls)}

要求：
1. intent_level 只能是 high / medium / low。
2. budget 没提到时输出 null。
3. next_action 必须是一个可以执行的动作短句。
4. 不要输出解释、代码块或额外字段。
""".strip()

    def extract_one(self, case: dict[str, str]) -> dict[str, object]:
        prompt = self.build_prompt(case["text"])
        result = run_chat(
            self.config,
            messages=[
                {"role": "system", "content": "你是一个结构化销售线索提取助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=260,
            debug_label=f"样本 {case['id']}：结构化提取",
        )
        parsed = parse_json_output(result.content)
        if not parsed.ok:
            return {
                "id": case["id"],
                "ok": False,
                "stage": "parse",
                "error": parsed.error,
                "raw_output": result.content,
            }
        try:
            validated = model_validate(self.schema_cls, parsed.data)
        except Exception as exc:
            return {
                "id": case["id"],
                "ok": False,
                "stage": "validate",
                "error": format_validation_error(exc),
                "raw_output": result.content,
                "parsed_data": parsed.data,
            }

        return {
            "id": case["id"],
            "ok": True,
            "stage": "success",
            "validated_data": model_dump(validated),
            "raw_output": result.content,
        }

    def extract_batch(self, cases: list[dict[str, str]]) -> dict[str, object]:
        rows = [self.extract_one(case) for case in cases]
        success_count = sum(1 for row in rows if row["ok"])
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "total": len(rows),
            "success": success_count,
            "failed": len(rows) - success_count,
            "rows": rows,
        }


def load_cases() -> list[dict[str, str]]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()

    if not is_pydantic_available():
        print("未安装 pydantic，请先执行：pip install pydantic")
        return

    cases = load_cases()
    extractor = StructuredExtractor(config=config, schema_cls=SalesLead)

    print("当前运行配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- ready: {config.is_ready}")
    print(f"- batch_size: {len(cases)}")

    print_json("SalesLead JSON Schema", get_model_json_schema(SalesLead))
    print("说明：这是 SalesLead 自动导出的 JSON Schema，偏程序视角。")
    print("批量提取时，Prompt 生成和最终校验都围绕这份结构定义展开。")

    print_section("Schema 转 Prompt 描述")
    print(schema_to_prompt_description(SalesLead))

    preview_prompt = extractor.build_prompt(cases[0]["text"])
    print_section("首条样本 Prompt 预览")
    print(preview_prompt)

    report = extractor.extract_batch(cases)
    print_json("批量提取报告", report)

    export_path = write_json_export(
        f"extractor_report_{timestamp_slug()}.json",
        report,
    )
    print(f"\n已导出提取结果：{export_path}")

    print("\n理解重点：")
    print("- 提取器真正复用的核心不是某条 Prompt，而是 Schema 驱动的提取流程。")
    print("- 批量处理时必须把 parse 错误和 validate 错误分开统计。")
    print("- 一旦 Schema 变化，Prompt、校验和导出结构都会跟着变化，这就是 Schema 驱动的价值。")


if __name__ == "__main__":
    main()
