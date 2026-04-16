"""
01_stream_basic.py
最小流式调用演示：逐段接收、首字耗时、完整结果拼接

运行方式：
    python 01_stream_basic.py

依赖：
    pip install openai python-dotenv

这个脚本是第五章最小、最直接的“流式消费示例”。
它不引入 FastAPI，也不引入 SSE，只做一件事：

1. 调 `stream_chat_events()`
2. 用 `async for` 逐个消费事件
3. 遇到 `token` 就立即打印
4. 遇到 `done` 就拿到整次流式调用的统计汇总

所以阅读这个脚本时，重点不是业务逻辑，而是理解：
- 为什么 token 会一段段出现
- 为什么 `first_token_ms` 和 `elapsed_ms` 要分开看
- 为什么流式接口通常同时需要“增量输出”和“最终汇总”

关于这个脚本里的异步，可以先抓住 4 个点：
- `async def main()` 表示：`main()` 调用后不会立刻执行完，而是先返回一个 coroutine。
- `asyncio.run(main())` 负责在普通 Python 脚本里启动事件循环，并把这个 coroutine 跑完。
- 这里虽然没有单独写一行 `await xxx`，但 `async for` 本身就在“反复等待下一段结果到来”。
- 真正的网络等待，发生在 `stream_chat_events()` 内部，例如它会 `await client.chat.completions.create(...)`，
  或者在 mock 模式下 `await asyncio.sleep(...)`。
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
    # `load_env_if_possible()` 和 `load_provider_config()` 都是普通同步函数，
    # 它们只是读取环境变量、组装配置，不涉及异步 IO，所以这里不需要 `await`。
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

    summary = None
    # 为什么这里没有显式 `await`，却还能写在 `async def` 里？
    #
    # 因为 `stream_chat_events(...)` 返回的是“异步生成器”：
    # - 普通 `for` 是立刻从本地迭代器里拿下一个值
    # - `async for` 是“等下一个值准备好以后再继续”
    #
    # 可以把它粗略理解成下面这种效果（概念上）：
    #
    #     iterator = stream_chat_events(...)
    #     while True:
    #         event = await iterator.__anext__()
    #
    # 也就是说，`await` 并没有消失，而是被 `async for` 这个语法糖包起来了。
    #
    # 这里之所以必须把 `main()` 定义成 `async def`，
    # 正是因为 `async for` 只能出现在异步上下文中。
    # `stream_chat_events()` 会不断产出事件。
    # 这个最小示例只关心两类：
    # 1. token: 一段新增文本，立即打印给用户
    # 2. done: 流式结束后的汇总信息，包含首字耗时、总耗时、chunk 数等
    async for event in stream_chat_events(
        config,
        messages=messages,
        temperature=0.3,
        max_tokens=280,
        debug_label="最小流式调用",
    ):
        if event["type"] == "token":
            print(event["delta"], end="", flush=True)
        elif event["type"] == "done":
            summary = event["summary"]

    print()
    if summary:
        # `summary` 不是新的模型输出，而是对刚才整次流式过程的汇总。
        # 这里把“用户体感速度”和“整段完成速度”一起打印出来，便于对比。
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
    # 在普通 `.py` 脚本的最外层，不能直接写 `await main()`，
    # 所以要用 `asyncio.run(main())` 来做两件事：
    # 1. 创建并启动事件循环（event loop）
    # 2. 执行 `main()` 返回的 coroutine，直到它结束
    #
    # 可以把事件循环理解成“异步任务调度器”：
    # 当 `main()` 运行到 `async for` 时，它会把控制权交还给事件循环；
    # 等网络数据到了，事件循环再继续往下执行。
    asyncio.run(main())
