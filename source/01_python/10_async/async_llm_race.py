# async_llm_race.py
# 练习5：实战 — 并发调用多个 LLM API，返回最快结果
#
# 依赖：pip install httpx
# 运行方式：python async_llm_race.py
#
# 用 httpbin.org/delay/{n} 模拟不同模型的响应速度。
# 这种"多模型竞速"模式在实际 AI 应用中可以用来：
# - 降低延迟（选最快的响应）
# - 提高可用性（一个挂了另一个顶上）
# - A/B 测试（对比不同模型的输出）

import httpx
import asyncio
import time
import json


# ============================================================
# 模拟的 LLM 模型配置
# ============================================================

MODELS = [
    {"name": "GPT-4o", "provider": "OpenAI", "delay": 3, "base_url": "https://httpbin.org"},
    {"name": "Claude Sonnet", "provider": "Anthropic", "delay": 1, "base_url": "https://httpbin.org"},
    {"name": "DeepSeek Chat", "provider": "DeepSeek", "delay": 2, "base_url": "https://httpbin.org"},
]


async def call_model(
    client: httpx.AsyncClient,
    model: dict,
    prompt: str,
) -> dict:
    """
    模拟调用 LLM API

    用 httpbin.org/delay/{n} 模拟延迟，
    用 httpbin.org/post 模拟请求和响应。
    """
    start = time.time()
    try:
        response = await client.post(
            f"{model['base_url']}/delay/{model['delay']}",
            json={
                "model": model["name"],
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={"Authorization": f"Bearer sk-{model['provider'].lower()}-test"},
        )
        elapsed = time.time() - start
        return {
            "model": model["name"],
            "provider": model["provider"],
            "status": response.status_code,
            "latency": round(elapsed, 2),
            "content": f"来自 {model['name']} 的模拟回复：{prompt}的答案",
            "ok": True,
        }
    except httpx.TimeoutException:
        return {
            "model": model["name"],
            "provider": model["provider"],
            "latency": round(time.time() - start, 2),
            "error": "超时",
            "ok": False,
        }
    except httpx.RequestError as e:
        return {
            "model": model["name"],
            "provider": model["provider"],
            "latency": round(time.time() - start, 2),
            "error": str(type(e).__name__),
            "ok": False,
        }


# ============================================================
# 场景1：全部请求，等最快的
# ============================================================

async def demo_race():
    """竞速模式：返回最快的响应"""
    print("=" * 50)
    print("🏁 竞速模式（返回最快的）")
    print("=" * 50)

    prompt = "用一句话介绍 Python"
    print(f"\n  Prompt: {prompt}")
    print(f"  同时请求 {len(MODELS)} 个模型...\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = {
            asyncio.create_task(call_model(client, m, prompt)): m["name"]
            for m in MODELS
        }

        start = time.time()
        done, pending = await asyncio.wait(
            tasks.keys(),
            return_when=asyncio.FIRST_COMPLETED,
        )

        # 最快的结果
        winner_task = done.pop()
        result = winner_task.result()
        elapsed = time.time() - start

        print(f"  🏆 最快: {result['model']}（{result['latency']}s）")
        print(f"  回复: {result['content']}")
        print(f"  总耗时: {elapsed:.2f}s")

        # 取消剩余
        cancelled = 0
        for t in pending:
            t.cancel()
            cancelled += 1
        print(f"  已取消 {cancelled} 个未完成请求（节省资源）")


# ============================================================
# 场景2：全部请求，收集所有结果
# ============================================================

async def demo_all():
    """全部模式：请求所有模型，对比结果"""
    print("\n" + "=" * 50)
    print("📊 全部模式（对比所有结果）")
    print("=" * 50)

    prompt = "Python 的优势是什么"
    print(f"\n  Prompt: {prompt}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        start = time.time()
        tasks = [call_model(client, m, prompt) for m in MODELS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total = time.time() - start

    print(f"\n  全部完成（{total:.2f}s）：")
    for r in results:
        if isinstance(r, Exception):
            print(f"    ❌ 异常: {r}")
        elif r["ok"]:
            print(f"    ✅ {r['model']:15s} → {r['latency']}s")
        else:
            print(f"    ❌ {r['model']:15s} → {r['error']}")

    # 排序
    valid = [r for r in results if not isinstance(r, Exception) and r["ok"]]
    if valid:
        fastest = min(valid, key=lambda x: x["latency"])
        print(f"\n  最快: {fastest['model']}（{fastest['latency']}s）")


# ============================================================
# 场景3：带超时的竞速
# ============================================================

async def demo_race_with_timeout():
    """带超时的竞速：超时后使用 fallback"""
    print("\n" + "=" * 50)
    print("⏰ 带超时的竞速（2.5s 超时）")
    print("=" * 50)

    prompt = "什么是异步编程"
    timeout_seconds = 2.5
    print(f"\n  超时: {timeout_seconds}s")
    print(f"  模型延迟: {', '.join(f'{m['name']}={m['delay']}s' for m in MODELS)}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            asyncio.create_task(call_model(client, m, prompt))
            for m in MODELS
        ]

        start = time.time()
        done, pending = await asyncio.wait(
            tasks,
            timeout=timeout_seconds,
            return_when=asyncio.FIRST_COMPLETED,
        )
        elapsed = time.time() - start

        if done:
            winner = done.pop()
            result = winner.result()
            print(f"\n  ✅ {result['model']} 在 {result['latency']}s 内响应")
        else:
            print(f"\n  ⚠️  {timeout_seconds}s 内没有模型响应")
            print(f"  使用 fallback 回复...")

        # 取消剩余
        for t in pending:
            t.cancel()
        # 等待取消操作完成
        if pending:
            await asyncio.wait(pending)

        print(f"  已取消 {len(pending)} 个未完成请求")


# ============================================================
# 场景4：按完成顺序流式处理
# ============================================================

async def demo_stream_results():
    """按完成顺序逐个处理结果"""
    print("\n" + "=" * 50)
    print("📋 按完成顺序处理")
    print("=" * 50)

    prompt = "解释什么是 RAG"

    async with httpx.AsyncClient(timeout=30.0) as client:
        coros = [call_model(client, m, prompt) for m in MODELS]

        print(f"\n  按完成顺序输出：")
        start = time.time()
        for i, coro in enumerate(asyncio.as_completed(coros)):
            result = await coro
            elapsed = time.time() - start
            if result["ok"]:
                print(f"  [{elapsed:.2f}s] 第 {i+1} 个: {result['model']}（延迟 {result['latency']}s）")
            else:
                print(f"  [{elapsed:.2f}s] 第 {i+1} 个: {result['model']} 失败 → {result['error']}")


# ============================================================
# 场景5：Semaphore 限速 + 批量请求
# ============================================================

async def demo_batch_with_limit():
    """批量请求多个 prompt，限制并发数"""
    print("\n" + "=" * 50)
    print("🚦 批量请求 + 并发限制")
    print("=" * 50)

    prompts = [
        "什么是 Python",
        "什么是 JavaScript",
        "什么是 Rust",
        "什么是 Go",
        "什么是 TypeScript",
    ]

    model = MODELS[1]  # Claude（最快）
    semaphore = asyncio.Semaphore(2)  # 最多同时 2 个请求

    async def limited_call(client: httpx.AsyncClient, prompt: str) -> dict:
        async with semaphore:
            return await call_model(client, model, prompt)

    async with httpx.AsyncClient(timeout=30.0) as client:
        start = time.time()
        tasks = [limited_call(client, p) for p in prompts]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

    print(f"\n  {len(results)} 个请求完成（最多同时 2 个），总耗时 {elapsed:.2f}s")
    for r in results:
        status = "✅" if r["ok"] else "❌"
        print(f"    {status} {r['content'][:40]}...（{r['latency']}s）")


# ============================================================
# 入口
# ============================================================

async def main():
    print("\n🐍 练习5：并发 LLM API 竞速实战\n")

    demos = [
        ("1", "竞速（返回最快）", demo_race),
        ("2", "全部请求（对比结果）", demo_all),
        ("3", "带超时的竞速", demo_race_with_timeout),
        ("4", "按完成顺序处理", demo_stream_results),
        ("5", "批量请求 + 并发限制", demo_batch_with_limit),
    ]

    print("选择要运行的演示（编号 / a=全部 / q=退出）:\n")
    for num, name, _ in demos:
        print(f"  [{num}] {name}")
    print("  [a] 全部运行")
    print("  [q] 退出")

    while True:
        choice = input("\n👉 请输入: ").strip().lower()
        if choice == "q":
            break
        elif choice == "a":
            for _, _, fn in demos:
                await fn()
            print("\n✅ 全部完成！")
            break
        elif choice in [n for n, _, _ in demos]:
            await demos[int(choice) - 1][2]()
        else:
            print(f"  无效输入: '{choice}'")


if __name__ == "__main__":
    asyncio.run(main())
