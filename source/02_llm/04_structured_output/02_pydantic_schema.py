"""
02_pydantic_schema.py
使用 Pydantic Schema 约束 LLM 结构化输出

运行方式：
    python 02_pydantic_schema.py

依赖：
    pip install openai python-dotenv pydantic
"""

from __future__ import annotations

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
)

if is_pydantic_available():
    from pydantic import BaseModel, Field
else:  # pragma: no cover - 只为缺依赖时脚本能打印说明
    BaseModel = object  # type: ignore[assignment,misc]

    def Field(*args, **kwargs):  # type: ignore[no-redef]
        return None


NOTE_TEXT = """
销售记录：
客户王敏来自杭州的华星零售，计划给 30 人团队采购 AI 知识库产品。
她说预算大概 5 万，最关心的是权限管理和多轮问答效果。
希望下周安排一次线上演示，目前主要通过邮箱和企业微信联系。
""".strip()


class ContactChannel(BaseModel):
    email: str | None = Field(default=None, description="客户邮箱，未知时为 null")
    wecom: bool = Field(description="是否提到企业微信沟通")


class LeadRecord(BaseModel):
    name: str = Field(description="客户姓名")
    company: str = Field(description="客户所属公司")
    city: str = Field(description="客户所在城市")
    team_size: int | None = Field(default=None, ge=1, description="计划使用产品的团队人数")
    budget: int | None = Field(default=None, ge=0, description="预算，单位为人民币元")
    intent_level: Literal["high", "medium", "low"] = Field(description="购买意向等级")
    requested_features: list[str] = Field(default_factory=list, description="明确提到的关注功能")
    need_demo: bool = Field(description="是否明确提出演示需求")
    contact: ContactChannel = Field(description="已知联系方式信息")


def build_schema_prompt(text: str) -> str:
    schema_description = schema_to_prompt_description(LeadRecord)
    return f"""
你是一名销售线索结构化提取助手。

任务：
请根据下面的销售记录提取结构化数据，并只输出 JSON 对象。

销售记录：
{text}

目标 Schema：
{schema_description}

要求：
1. 只输出一个 JSON 对象，不要解释。
2. 字段类型必须符合 Schema。
3. 如果文本未提到具体值，使用 null、空数组或合理的布尔值。
4. intent_level 只能是 high / medium / low。
""".strip()


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()

    if not is_pydantic_available():
        print("未安装 pydantic，请先执行：pip install pydantic")
        return

    schema = get_model_json_schema(LeadRecord)
    prompt = build_schema_prompt(NOTE_TEXT)

    print("当前运行配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- ready: {config.is_ready}")

    print_json("LeadRecord JSON Schema", schema)

    print(f"\n{'=' * 72}")
    print("Schema 转 Prompt 描述")
    print("=" * 72)
    print(schema_to_prompt_description(LeadRecord))

    print(f"\n{'=' * 72}")
    print("提取 Prompt")
    print("=" * 72)
    print(prompt)

    result = run_chat(
        config,
        messages=[
            {"role": "system", "content": "你是严格遵守 Schema 的结构化提取助手。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=280,
    )

    print_json("request_preview", result.request_preview)
    print("\n模型输出：")
    print(result.content)

    parsed = parse_json_output(result.content)
    print_json(
        "JSON 解析结果",
        {
            "ok": parsed.ok,
            "data": parsed.data,
            "error": parsed.error,
        },
    )
    if not parsed.ok:
        return

    try:
        validated = model_validate(LeadRecord, parsed.data)
    except Exception as exc:
        print_json(
            "Pydantic 校验错误",
            {
                "error": format_validation_error(exc),
                "parsed_data": parsed.data,
            },
        )
        return
    print_json("Pydantic 校验后的对象", model_dump(validated))

    print("\n理解重点：")
    print("- JSON 只是文本格式；Pydantic 才真正把字段、类型和约束落成程序规则。")
    print("- Schema 一旦确定，后续调用、存储和 API 返回值都能共享同一份结构定义。")
    print("- 当 provider 原生 structured outputs 不稳定或不可用时，JSON + Pydantic 是最稳的回退方案。")


if __name__ == "__main__":
    main()
