"""
03_retry_validation.py
结构化输出校验与重试

运行方式：
    python 03_retry_validation.py

依赖：
    pip install openai python-dotenv pydantic

这个脚本要解决的不是“多调用几次模型”，而是把一次结构化提取拆成稳定的工程链路：

1. 先根据原始工单生成“初始提取 Prompt”
2. 调模型，拿到原始文本输出
3. 先做 JSON 解析：
   - 如果连 JSON 都提不出来，说明失败发生在 parse 层
4. JSON 解析通过后，再做 Pydantic 校验：
   - 如果字段类型、枚举值、布尔值等不符合 `TicketExtraction`，说明失败发生在 validate 层
5. 一旦失败，不是原样重跑，而是把“上一次错误 + 上一次输出 + 目标 Schema”拼成修复 Prompt
6. 再次调用模型，让模型按明确错误反馈修正输出
7. 某一轮校验成功后立刻返回；超过最大重试次数仍失败则抛错

阅读顺序建议：
build_extract_prompt()
-> RobustStructuredClient._call()
-> RobustStructuredClient.extract()
-> main()

理解重点：
- `run_chat()` 只负责“调一次模型并打印调试日志”
- `parse_json_output()` 只负责“这段文本能不能变成 JSON”
- `model_validate()` 只负责“这个 JSON 是否符合业务 Schema”
- `build_json_fix_prompt()` 才是重试变聪明的关键，因为它会把错误显式反馈给模型
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


def print_section(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)


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
        # `_call()` 只负责“按当前 prompt 发起一次调用并拿回原始文本”。
        # 它不做 JSON 解析，也不做 Schema 校验；这两层都放在 `extract()` 里串起来。
        if not self.config.is_ready:
            return self.mock_attempts[min(attempt_index, len(self.mock_attempts) - 1)]

        attempt_label = "初始提取" if attempt_index == 0 else "错误修复"

        result = run_chat(
            self.config,
            messages=[
                {"role": "system", "content": "你是严格返回 JSON 的结构化提取助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=260,
            debug_label=f"第 {attempt_index + 1} 次尝试：{attempt_label}",
        )
        return result.content

    def extract(self, prompt: str, schema_cls):
        attempts: list[dict[str, object]] = []
        current_prompt = prompt

        for attempt in range(self.max_retries):
            attempt_label = "初始提取" if attempt == 0 else "错误修复"

            # 第一步：基于当前 prompt 调一次模型，拿到最原始的文本返回。
            # 第一轮用的是初始提取 Prompt；后续轮次用的是“带错误反馈的修复 Prompt”。
            raw_text = self._call(current_prompt, attempt)

            # 第二步：先检查“文本是否能被提取成 JSON”。
            # 这层只管 parse，不关心字段是不是符合业务要求。
            parsed = parse_json_output(raw_text)
            if not parsed.ok:
                error_message = parsed.error or "未知 JSON 解析错误"
                attempts.append(
                    {
                        "attempt": attempt + 1,
                        "label": attempt_label,
                        "stage": "parse",
                        "prompt": current_prompt,
                        "raw_text": raw_text,
                        "error": error_message,
                    }
                )

                # 如果 parse 失败，下一轮不会简单重跑原 Prompt，
                # 而是把“错误信息 + 上一次输出 + Schema 描述”拼成修复 Prompt。
                current_prompt = build_json_fix_prompt(
                    bad_output=raw_text,
                    error_message=error_message,
                    schema_description=schema_to_prompt_description(schema_cls),
                )
                continue

            try:
                # 第三步：JSON 解析成功后，再做 Schema 校验。
                # 这里才会检查：
                # - issue_type / priority 是否命中枚举
                # - need_human_follow_up 是否真的是 bool
                # - summary 是否满足长度等约束
                validated = model_validate(schema_cls, parsed.data)
            except Exception as exc:
                error_message = format_validation_error(exc)
                attempts.append(
                    {
                        "attempt": attempt + 1,
                        "label": attempt_label,
                        "stage": "validate",
                        "prompt": current_prompt,
                        "raw_text": raw_text,
                        "parsed_data": parsed.data,
                        "error": error_message,
                    }
                )

                # 如果 validate 失败，说明“JSON 格式没问题，但业务结构不对”。
                # 下一轮会把明确的字段错误反馈给模型，而不是让模型自己猜哪里错了。
                current_prompt = build_json_fix_prompt(
                    bad_output=raw_text,
                    error_message=error_message,
                    schema_description=schema_to_prompt_description(schema_cls),
                )
                continue

            # 只有 parse 和 validate 都通过，才算真正成功。
            # 一旦成功就立刻返回，不再继续消耗额外轮次。
            attempts.append(
                {
                    "attempt": attempt + 1,
                    "label": attempt_label,
                    "stage": "success",
                    "prompt": current_prompt,
                    "raw_text": raw_text,
                    "parsed_data": parsed.data,
                    "validated_data": model_dump(validated),
                    "error": None,
                }
            )
            return validated, attempts

        # 走到这里说明：
        # 1. 已经按顺序尝试了 `max_retries` 轮
        # 2. 每一轮都要么 parse 失败，要么 validate 失败
        # 3. 最终仍没得到合法结构化输出
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
    print("说明：这是 TicketExtraction 自动导出的 JSON Schema，偏程序视角。")
    print("阅读时优先关注 properties、required、enum 和字段约束。")

    print_section("Schema 转 Prompt 描述")
    print(schema_to_prompt_description(TicketExtraction))

    print_section("初始提取 Prompt")
    print(prompt)

    client = RobustStructuredClient(config=config, max_retries=3)
    validated, attempts = client.extract(prompt, TicketExtraction)

    for row in attempts:
        stage_title = {
            "parse": "JSON 解析失败",
            "validate": "Schema 校验失败",
            "success": "提取成功",
        }.get(str(row["stage"]), str(row["stage"]))
        print_json(f"第 {row['attempt']} 次尝试 - {row['label']} - {stage_title}", row)

    print_json("最终校验结果", model_dump(validated))

    print("\n理解重点：")
    print("- 结构化输出失败时，不要只重跑原 Prompt；应该把错误信息显式反馈给模型。")
    print("- 重试不是为了赌概率，而是为了逐步缩小输出空间。")
    print("- 当多次修复仍失败时，工程上应该降级到人工检查或兜底逻辑。")


if __name__ == "__main__":
    main()
