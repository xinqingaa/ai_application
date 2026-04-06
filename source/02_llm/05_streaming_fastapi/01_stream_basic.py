"""
01_stream_basic.py
最小流式调用演示：逐段接收、首字耗时、完整结果拼接

运行方式：
    python 01_stream_basic.py

依赖：
    pip install openai python-dotenv
"""

from __future__ import annotations

import asyncio

from streaming_utils import (
    load_env_if_possible,
    load_provider_config,
    stream_chat_events,
)


USER_PROMPT = "请用 5 个要点解释为什么流式输出能改善 AI 聊天产品的体验。"


async def main() -> None:
    load_env_if_possible()
    config = load_provider_config()
    messages = [
        {"role": "system", "content": "你是一个面向开发者的 AI 技术讲师，回答清楚、简洁。"},
        {"role": "user", "content": USER_PROMPT},
    ]

    print("当前运行配置：")
    print(f"- provider: {config.provider}")
    print(f"- model: {config.model}")
    print(f"- base_url: {config.base_url}")
    print(f"- ready: {config.is_ready}")

    print(f"\n{'=' * 72}")
    print("当前 Prompt")
    print("=" * 72)
    print(USER_PROMPT)

    print(f"\n{'=' * 72}")
    print("流式输出")
    print("=" * 72)

    summary = None
    async for event in stream_chat_events(
        config,
        messages=messages,
        temperature=0.3,
        max_tokens=280,
    ):
        if event["type"] == "token":
            print(event["delta"], end="", flush=True)
        elif event["type"] == "done":
            summary = event["summary"]

    print()
    if summary:
        print(f"\n{'=' * 72}")
        print("流式统计")
        print("=" * 72)
        print(f"- mocked: {summary.mocked}")
        print(f"- first_token_ms: {summary.first_token_ms}")
        print(f"- elapsed_ms: {summary.elapsed_ms:.2f}")
        print(f"- chunk_count: {summary.chunk_count}")
        print(f"- input_tokens_estimate: {summary.input_tokens_estimate}")
        print(f"- output_tokens_estimate: {summary.output_tokens_estimate}")
        print("\n完整结果：")
        print(summary.full_text)


if __name__ == "__main__":
    asyncio.run(main())
