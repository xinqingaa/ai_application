# async_concurrency.py
# 练习2：并发执行 — gather / create_task / wait / as_completed / wait_for
#
# 无额外依赖，使用 Python 标准库 asyncio
# 运行方式：python async_concurrency.py

import asyncio
import time


async def task(name: str, seconds: float) -> str:
    """模拟一个耗时任务"""
    print(f"  {name}: 开始（需要 {seconds}s）")
    await asyncio.sleep(seconds)
    print(f"  {name}: 完成")
    return f"{name} 的结果"


# ============================================================
# 1. asyncio.gather — 并发等待全部完成
# ============================================================

async def demo_gather():
    """gather：并发执行，等待全部完成"""
    print("=" * 50)
    print("📦 asyncio.gather（等待全部完成）")
    print("=" * 50)

    start = time.time()
    results = await asyncio.gather(
        task("A", 2),
        task("B", 1),
        task("C", 3),
    )
    elapsed = time.time() - start

    print(f"\n  结果: {results}")
    print(f"  总耗时: {elapsed:.2f}s（≈ 最慢的 3s，不是 2+1+3=6s）")


# ============================================================
# 2. asyncio.create_task — 创建并调度任务
# ============================================================

async def demo_create_task():
    """create_task：立即开始，后续 await 拿结果"""
    print("\n" + "=" * 50)
    print("🚀 asyncio.create_task（创建并调度）")
    print("=" * 50)

    # 创建任务（立即开始在后台执行）
    task_a = asyncio.create_task(task("后台A", 2))
    task_b = asyncio.create_task(task("后台B", 1))

    print("  任务已创建，主线程继续...")
    await asyncio.sleep(0.5)
    print("  0.5s 后：任务在后台运行中")

    # 等待任务完成
    result_a = await task_a
    result_b = await task_b
    print(f"\n  结果: {result_a}, {result_b}")


# ============================================================
# 3. asyncio.wait + FIRST_COMPLETED — 竞速
# ============================================================

async def demo_wait_first():
    """wait + FIRST_COMPLETED：谁先完成拿谁"""
    print("\n" + "=" * 50)
    print("🏁 asyncio.wait（FIRST_COMPLETED 竞速）")
    print("=" * 50)

    tasks = [
        asyncio.create_task(task("OpenAI", 3)),
        asyncio.create_task(task("Claude", 1)),
        asyncio.create_task(task("DeepSeek", 2)),
    ]

    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.FIRST_COMPLETED,
    )

    # 最快完成的
    winner = done.pop()
    print(f"\n  最快: {winner.result()}")
    print(f"  未完成: {len(pending)} 个")

    # 取消剩余任务
    for t in pending:
        t.cancel()
    print(f"  已取消未完成的任务")


# ============================================================
# 4. asyncio.as_completed — 按完成顺序处理
# ============================================================

async def demo_as_completed():
    """as_completed：按完成顺序逐个处理"""
    print("\n" + "=" * 50)
    print("📋 asyncio.as_completed（按完成顺序）")
    print("=" * 50)

    coros = [
        task("慢任务", 3),
        task("快任务", 1),
        task("中任务", 2),
    ]

    print("\n  按完成顺序输出：")
    for i, coro in enumerate(asyncio.as_completed(coros)):
        result = await coro
        print(f"  第 {i + 1} 个完成: {result}")


# ============================================================
# 5. asyncio.wait_for — 单任务超时
# ============================================================

async def demo_wait_for():
    """wait_for：给单个任务设置超时"""
    print("\n" + "=" * 50)
    print("⏰ asyncio.wait_for（超时控制）")
    print("=" * 50)

    async def slow_api():
        await asyncio.sleep(5)
        return "终于完成了"

    # 正常完成
    print("\n  --- 2 秒超时，任务需要 1 秒 ---")
    try:
        result = await asyncio.wait_for(task("快任务", 1), timeout=2.0)
        print(f"  结果: {result}")
    except asyncio.TimeoutError:
        print("  超时！")

    # 超时
    print("\n  --- 2 秒超时，任务需要 5 秒 ---")
    try:
        result = await asyncio.wait_for(slow_api(), timeout=2.0)
        print(f"  结果: {result}")
    except asyncio.TimeoutError:
        print("  ✅ 超时！（2 秒内未完成，任务被取消）")


# ============================================================
# 6. 错误处理：return_exceptions
# ============================================================

async def demo_error_handling():
    """gather 中的错误处理"""
    print("\n" + "=" * 50)
    print("🛡️  gather 错误处理（return_exceptions）")
    print("=" * 50)

    async def success_task(name: str) -> str:
        await asyncio.sleep(0.5)
        return f"{name} 成功"

    async def fail_task(name: str) -> str:
        await asyncio.sleep(0.5)
        raise ValueError(f"{name} 出错了")

    # 默认：一个失败全部中断
    print("\n  --- 默认行为（一个失败就抛异常）---")
    try:
        results = await asyncio.gather(
            success_task("A"),
            fail_task("B"),
            success_task("C"),
        )
    except ValueError as e:
        print(f"  捕获异常: {e}")

    # return_exceptions=True：异常作为返回值
    print("\n  --- return_exceptions=True（收集所有结果）---")
    results = await asyncio.gather(
        success_task("A"),
        fail_task("B"),
        success_task("C"),
        return_exceptions=True,
    )

    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"  [{i}] 异常: {type(r).__name__}: {r}")
        else:
            print(f"  [{i}] 成功: {r}")


# ============================================================
# 7. 串行 vs 并发对比
# ============================================================

async def demo_serial_vs_concurrent():
    """对比串行和并发的耗时"""
    print("\n" + "=" * 50)
    print("⚡ 串行 vs 并发")
    print("=" * 50)

    delays = [1.0, 1.5, 0.5, 2.0]

    # 串行
    start = time.time()
    serial_results = []
    for i, d in enumerate(delays):
        r = await task(f"串行-{i}", d)
        serial_results.append(r)
    serial_time = time.time() - start

    print()

    # 并发
    start = time.time()
    concurrent_results = await asyncio.gather(
        *[task(f"并发-{i}", d) for i, d in enumerate(delays)]
    )
    concurrent_time = time.time() - start

    print(f"\n  串行耗时: {serial_time:.2f}s")
    print(f"  并发耗时: {concurrent_time:.2f}s")
    print(f"  提速: {serial_time / concurrent_time:.1f}x")


# ============================================================
# 入口
# ============================================================

async def main():
    print("\n🐍 练习2：并发执行\n")

    demos = [
        ("1", "gather（全部完成）", demo_gather),
        ("2", "create_task（后台调度）", demo_create_task),
        ("3", "wait（FIRST_COMPLETED 竞速）", demo_wait_first),
        ("4", "as_completed（按完成顺序）", demo_as_completed),
        ("5", "wait_for（超时控制）", demo_wait_for),
        ("6", "gather 错误处理", demo_error_handling),
        ("7", "串行 vs 并发对比", demo_serial_vs_concurrent),
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
