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


def print_section(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print("=" * 72)


def print_json_parse_result(title: str, content: str) -> None:
    parsed = parse_json_output(content)
    print_json(
        title,
        {
            "ok": parsed.ok,
            "candidate_text": parsed.candidate_text,
            "data": parsed.data,
            "error": parsed.error,
        },
    )


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

    print_section("模式一：自由文本")
    print("Prompt：")
    print(free_text_prompt)

    free_text_result = run_chat(
        config,
        build_messages(free_text_prompt),
        temperature=0.2,
        max_tokens=220,
        debug_label="模式一：自由文本",
    )

    print("\n输出：")
    print(free_text_result.content)

    print_section("模式二：Prompt 约束 JSON")
    print("Prompt：")
    print(json_prompt)

    json_prompt_result = run_chat(
        config,
        build_messages(json_prompt),
        temperature=0.0,
        max_tokens=220,
        debug_label="模式二：Prompt 约束 JSON",
    )

    print("\n输出：")
    print(json_prompt_result.content)
    print_json_parse_result("模式二解析结果", json_prompt_result.content)

    print_section("模式三：JSON Mode 接口约束")
    print("Prompt：")
    print(json_prompt)
    print("\n接口额外约束：response_format = {'type': 'json_object'}")

    try:
        json_mode_result = run_chat(
            config,
            build_messages(json_prompt),
            temperature=0.0,
            max_tokens=220,
            extra_options={"response_format": {"type": "json_object"}},
            debug_label="模式三：JSON Mode 接口约束",
        )
    except Exception as exc:
        print("\n输出：")
        print(f"当前 provider 的 JSON Mode 调用失败：{type(exc).__name__}: {exc}")
        json_mode_result = None

    if json_mode_result is not None:
        print("\n输出：")
        print(json_mode_result.content)
        print_json_parse_result("模式三解析结果", json_mode_result.content)

    print("\n观察重点：")
    print("- 自由文本结果对人类可读，但对程序不稳定。")
    print("- Prompt 里写明 JSON 要求后，结果通常更接近可解析格式，但仍属于依赖模型遵守提示词。")
    print("- JSON Mode 属于接口级约束；如果 provider 支持，通常会比纯 Prompt 约束更稳定。")
    print("- 不同 provider 对 JSON Mode 的支持程度不完全一致，生产里要做兼容判断和失败回退。")


if __name__ == "__main__":
    main()
