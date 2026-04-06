"""
03_retry_validation.py
结构化输出校验与重试

运行方式：
    python 03_retry_validation.py

依赖：
    pip install openai python-dotenv pydantic
"""

from __future__ import annotations

from typing import Literal

from structured_utils import (
    build_json_fix_prompt,
    format_validation_error,
    get_model_json_schema,
    is_pydantic_available,
    json_dumps,
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
else:  # pragma: no cover
    BaseModel = object  # type: ignore[assignment,misc]

    def Field(*args, **kwargs):  # type: ignore[no-redef]
        return None


TICKET_TEXT = """
工单标题：支付成功但订单状态未更新
工单内容：用户已完成付款，银行卡侧也有扣款记录，但订单页一直显示待支付，不敢重复下单，希望尽快核实。
额外信息：用户是付费专业版客户，今天已经第二次反馈。
""".strip()


class TicketExtraction(BaseModel):
    ticket_title: str = Field(description="工单标题")
    issue_type: Literal["登录", "支付", "数据", "功能", "其他"] = Field(description="问题类型")
    priority: Literal["高", "中", "低"] = Field(description="优先级")
    need_human_follow_up: bool = Field(description="是否需要人工跟进")
    summary: str = Field(min_length=10, description="对问题的简洁总结")


def build_extract_prompt(text: str) -> str:
    return f"""
你是一名售后工单结构化提取助手。

任务：
请根据下面工单提取结构化信息，并只返回 JSON 对象。

工单内容：
{text}

目标 Schema：
{schema_to_prompt_description(TicketExtraction)}

要求：
1. issue_type 只能是 登录 / 支付 / 数据 / 功能 / 其他。
2. priority 只能是 高 / 中 / 低。
3. need_human_follow_up 必须是布尔值。
4. summary 用一句完整中文总结。
""".strip()


class RobustStructuredClient:
    def __init__(self, config, max_retries: int = 3):
        self.config = config
        self.max_retries = max_retries
        self.mock_attempts = [
            """```json
{
  "ticket_title": "支付成功但订单状态未更新",
  "issue_type": "支付",
  "priority": "urgent",
  "need_human_follow_up": "yes",
  "summary": "支付后订单状态没变。"
}
```""",
            json_dumps(
                {
                    "ticket_title": "支付成功但订单状态未更新",
                    "issue_type": "支付",
                    "priority": "高",
                    "need_human_follow_up": True,
                    "summary": "用户已付款但订单仍显示待支付，属于需要人工跟进的支付状态异常。",
                }
            ),
        ]

    def _call(self, prompt: str, attempt_index: int) -> str:
        if not self.config.is_ready:
            return self.mock_attempts[min(attempt_index, len(self.mock_attempts) - 1)]

        result = run_chat(
            self.config,
            messages=[
                {"role": "system", "content": "你是严格返回 JSON 的结构化提取助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=260,
        )
        return result.content

    def extract(self, prompt: str, schema_cls):
        attempts: list[dict[str, object]] = []
        current_prompt = prompt

        for attempt in range(self.max_retries):
            raw_text = self._call(current_prompt, attempt)
            parsed = parse_json_output(raw_text)
            if not parsed.ok:
                error_message = parsed.error or "未知 JSON 解析错误"
                attempts.append(
                    {
                        "attempt": attempt + 1,
                        "stage": "parse",
                        "prompt": current_prompt,
                        "raw_text": raw_text,
                        "error": error_message,
                    }
                )
                current_prompt = build_json_fix_prompt(
                    bad_output=raw_text,
                    error_message=error_message,
                    schema_description=schema_to_prompt_description(schema_cls),
                )
                continue

            try:
                validated = model_validate(schema_cls, parsed.data)
            except Exception as exc:
                error_message = format_validation_error(exc)
                attempts.append(
                    {
                        "attempt": attempt + 1,
                        "stage": "validate",
                        "prompt": current_prompt,
                        "raw_text": raw_text,
                        "parsed_data": parsed.data,
                        "error": error_message,
                    }
                )
                current_prompt = build_json_fix_prompt(
                    bad_output=raw_text,
                    error_message=error_message,
                    schema_description=schema_to_prompt_description(schema_cls),
                )
                continue

            attempts.append(
                {
                    "attempt": attempt + 1,
                    "stage": "success",
                    "prompt": current_prompt,
                    "raw_text": raw_text,
                    "parsed_data": parsed.data,
                    "validated_data": model_dump(validated),
                    "error": None,
                }
            )
            return validated, attempts

        raise RuntimeError(json_dumps({"message": "达到最大重试次数，仍未得到合法结构化输出", "attempts": attempts}))


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()

    if not is_pydantic_available():
        print("未安装 pydantic，请先执行：pip install pydantic")
        return

    prompt = build_extract_prompt(TICKET_TEXT)

    print("当前运行配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- ready: {config.is_ready}")

    print_json("TicketExtraction JSON Schema", get_model_json_schema(TicketExtraction))

    print(f"\n{'=' * 72}")
    print("初始提取 Prompt")
    print("=" * 72)
    print(prompt)

    client = RobustStructuredClient(config=config, max_retries=3)
    validated, attempts = client.extract(prompt, TicketExtraction)

    for row in attempts:
        print_json(f"Attempt {row['attempt']} - {row['stage']}", row)

    print_json("最终校验结果", model_dump(validated))

    print("\n理解重点：")
    print("- 结构化输出失败时，不要只重跑原 Prompt；应该把错误信息显式反馈给模型。")
    print("- 重试不是为了赌概率，而是为了逐步缩小输出空间。")
    print("- 当多次修复仍失败时，工程上应该降级到人工检查或兜底逻辑。")


if __name__ == "__main__":
    main()
