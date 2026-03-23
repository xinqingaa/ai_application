# async_basics.py
# 练习1：asyncio 基础 — async def / await / asyncio.run / sleep
#
# 无额外依赖，使用 Python 标准库 asyncio
# 运行方式：python async_basics.py

import asyncio
import time


# ============================================================
# 1. async def 和 await 基础
# ============================================================

async def say_hello(name: str) -> str:
    """最简单的协程函数"""
    return f"你好，{name}！"


async def demo_basic():
    """async def 和 await 基础"""
    print("=" * 50)
    print("📌 async def / await 基础")
    print("=" * 50)

    # 直接调用 async 函数，得到的是协程对象，不是结果
    coro = say_hello("张三")
    print(f"  直接调用: {coro}")  # <coroutine object ...>
    print(f"  类型: {type(coro).__name__}")

    # 必须 await 才能得到结果
    result = await coro
    print(f"  await 后: {result}")

    # 通常直接 await 调用
    result = await say_hello("李四")
    print(f"  直接 await: {result}")


# ============================================================
# 2. asyncio.sleep vs time.sleep
# ============================================================

async def demo_sleep_difference():
    """对比 asyncio.sleep 和 time.sleep"""
    print("\n" + "=" * 50)
    print("⏱️  asyncio.sleep vs time.sleep")
    print("=" * 50)

    async def async_task(name: str, seconds: float):
        print(f"  {name}: 开始")
        await asyncio.sleep(seconds)  # 非阻塞，其他协程可以执行
        print(f"  {name}: 完成（{seconds}s）")

    # 并发执行 3 个任务
    print("\n  --- asyncio.sleep（非阻塞，并发）---")
    start = time.time()
    await asyncio.gather(
        async_task("任务A", 2),
        async_task("任务B", 1),
        async_task("任务C", 1.5),
    )
    print(f"  总耗时: {time.time() - start:.2f}s（接近最慢的 2s，不是 4.5s）")

    # 对比：如果用 time.sleep（串行阻塞）
    async def blocking_task(name: str, seconds: float):
        print(f"  {name}: 开始")
        time.sleep(seconds)  # 阻塞！整个事件循环卡住
        print(f"  {name}: 完成（{seconds}s）")

    print("\n  --- time.sleep（阻塞，串行）---")
    start = time.time()
    await asyncio.gather(
        blocking_task("任务X", 0.5),
        blocking_task("任务Y", 0.5),
        blocking_task("任务Z", 0.5),
    )
    print(f"  总耗时: {time.time() - start:.2f}s（接近 1.5s，因为被阻塞了）")


# ============================================================
# 3. 协程的执行顺序
# ============================================================

async def demo_execution_order():
    """观察协程的执行顺序"""
    print("\n" + "=" * 50)
    print("🔄 执行顺序观察")
    print("=" * 50)

    async def worker(name: str, steps: int):
        for i in range(steps):
            print(f"  {name}: 步骤 {i + 1}/{steps}")
            await asyncio.sleep(0.3)  # 每次 await 都是一个切换点
        return f"{name} 完成"

    print("\n  3 个 worker 并发执行，观察交错输出：")
    results = await asyncio.gather(
        worker("🅰️ ", 3),
        worker("🅱️ ", 2),
        worker("🅲️ ", 4),
    )
    print(f"\n  结果: {results}")


# ============================================================
# 4. 协程 vs 普通函数
# ============================================================

async def demo_coroutine_vs_function():
    """对比协程和普通函数"""
    print("\n" + "=" * 50)
    print("⚖️  协程 vs 普通函数")
    print("=" * 50)

    def sync_add(a: int, b: int) -> int:
        return a + b

    async def async_add(a: int, b: int) -> int:
        return a + b

    # 普通函数：直接返回结果
    r1 = sync_add(3, 5)
    print(f"  sync_add(3, 5) = {r1}（直接得到结果）")
    print(f"  类型: {type(r1)}")

    # 协程函数：返回协程对象
    r2 = async_add(3, 5)
    print(f"\n  async_add(3, 5) = {r2}（协程对象，还没执行）")
    print(f"  类型: {type(r2)}")

    # await 后才得到结果
    r3 = await r2
    print(f"\n  await 后 = {r3}（真正的结果）")
    print(f"  类型: {type(r3)}")


# ============================================================
# 5. 模拟 AI 应用场景
# ============================================================

async def demo_ai_scenario():
    """模拟 AI 应用中的异步场景"""
    print("\n" + "=" * 50)
    print("🤖 模拟 AI 应用场景")
    print("=" * 50)

    async def call_llm(model: str, delay: float) -> dict:
        """模拟调用 LLM API"""
        print(f"  → 请求 {model}...")
        await asyncio.sleep(delay)
        return {
            "model": model,
            "content": f"来自 {model} 的回复",
            "latency": delay,
        }

    # 场景：同时请求 3 个模型
    print("\n  同时请求 3 个模型：")
    start = time.time()
    results = await asyncio.gather(
        call_llm("GPT-4o", 2.0),
        call_llm("Claude", 1.5),
        call_llm("DeepSeek", 1.0),
    )
    elapsed = time.time() - start

    print(f"\n  全部完成（{elapsed:.2f}s）：")
    for r in results:
        print(f"    {r['model']}: {r['content']}（延迟 {r['latency']}s）")
    print(f"\n  如果串行调用需要 {sum(r['latency'] for r in results):.1f}s，并发只需 {elapsed:.2f}s")


# ============================================================
# 入口
# ============================================================

async def main():
    print("\n🐍 练习1：asyncio 基础\n")

    demos = [
        ("1", "async def / await 基础", demo_basic),
        ("2", "asyncio.sleep vs time.sleep", demo_sleep_difference),
        ("3", "执行顺序观察", demo_execution_order),
        ("4", "协程 vs 普通函数", demo_coroutine_vs_function),
        ("5", "模拟 AI 应用场景", demo_ai_scenario),
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
