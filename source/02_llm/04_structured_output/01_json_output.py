"""
01_json_output.py
结构化输出入门：自由文本、Prompt JSON、JSON Mode 预览

运行方式：
    python 01_json_output.py

依赖：
    pip install openai python-dotenv
"""

from __future__ import annotations

from structured_utils import load_env_if_possible, load_provider_config, parse_json_output, print_json, run_chat


PERSON_TEXT = "张三，男，28岁，北京人，软件工程师，最近在做 AI 聊天产品。"


def build_free_text_prompt(text: str) -> str:
    return f"""
请从下面文本中提取关键信息，并做一个简洁介绍：

文本：
{text}
""".strip()


def build_json_prompt(text: str) -> str:
    return f"""
请从下面文本中提取信息，并以 JSON 对象输出。

文本：
{text}

输出要求：
1. 只输出 JSON，不要额外解释。
2. 字段必须包含：
   - name: string
   - gender: string
   - age: integer
   - city: string
   - job: string
3. 如果文本里没有对应信息，填 null。

输出示例：
{{
  "name": "",
  "gender": "",
  "age": 0,
  "city": "",
  "job": ""
}}
""".strip()


def build_messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "你是一个结构化信息提取助手，必须尽量按要求返回稳定格式。",
        },
        {"role": "user", "content": prompt},
    ]


def main() -> None:
    load_env_if_possible()
    config = load_provider_config()

    free_text_prompt = build_free_text_prompt(PERSON_TEXT)
    json_prompt = build_json_prompt(PERSON_TEXT)

    print("当前运行配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- base_url: {config.base_url}")
    print(f"- ready: {config.is_ready}")

    print(f"\n{'=' * 72}")
    print("自由文本 Prompt")
    print("=" * 72)
    print(free_text_prompt)

    print(f"\n{'=' * 72}")
    print("JSON Prompt")
    print("=" * 72)
    print(json_prompt)

    free_text_result = run_chat(config, build_messages(free_text_prompt), temperature=0.2, max_tokens=220)
    json_result = run_chat(config, build_messages(json_prompt), temperature=0.0, max_tokens=220)

    print_json("自由文本 request_preview", free_text_result.request_preview)
    print("\n自由文本输出：")
    print(free_text_result.content)

    print_json("JSON Prompt request_preview", json_result.request_preview)
    print("\nJSON Prompt 输出：")
    print(json_result.content)

    parsed = parse_json_output(json_result.content)
    print_json(
        "JSON Prompt 解析结果",
        {
            "ok": parsed.ok,
            "candidate_text": parsed.candidate_text,
            "data": parsed.data,
            "error": parsed.error,
        },
    )

    json_mode_preview = {
        "model": config.model,
        "messages": build_messages(json_prompt),
        "temperature": 0.0,
        "max_tokens": 220,
        "response_format": {"type": "json_object"},
    }
    print_json("JSON Mode 请求预览", json_mode_preview)

    print("\n观察重点：")
    print("- 自由文本结果对人类可读，但对程序不稳定。")
    print("- Prompt 指定 JSON 后，结果更接近可解析格式，但仍可能带解释、代码块或字段错误。")
    print("- JSON Mode 是更强的接口级约束，但不同 provider 的支持程度不完全一致。")


if __name__ == "__main__":
    main()
