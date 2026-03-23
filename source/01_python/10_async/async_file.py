# async_file.py
# 练习4：异步文件操作 — aiofiles
#
# 依赖：pip install aiofiles
# 运行方式：python async_file.py
#
# 大多数场景同步文件操作就够用。
# aiofiles 主要用在异步上下文中（如 FastAPI）需要读写大文件时。

import asyncio
import os
import json
import time

try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    print("⚠️  aiofiles 未安装，请运行: pip install aiofiles")
    print("   部分演示将使用同步替代方案\n")


DEMO_DIR = "demo_async_files"


async def ensure_demo_dir():
    """创建演示用临时目录"""
    os.makedirs(DEMO_DIR, exist_ok=True)


async def cleanup_demo_dir():
    """清理演示用临时目录"""
    if os.path.exists(DEMO_DIR):
        for f in os.listdir(DEMO_DIR):
            os.remove(os.path.join(DEMO_DIR, f))
        os.rmdir(DEMO_DIR)
        print(f"\n  🧹 已清理 {DEMO_DIR}/")


# ============================================================
# 1. aiofiles 基础读写
# ============================================================

async def demo_basic_rw():
    """aiofiles 基础读写"""
    print("=" * 50)
    print("📄 aiofiles 基础读写")
    print("=" * 50)

    if not HAS_AIOFILES:
        print("  ⚠️  需要安装 aiofiles")
        return

    await ensure_demo_dir()
    filepath = os.path.join(DEMO_DIR, "hello.txt")

    # 写入
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write("Hello, 异步文件操作！\n")
        await f.write("这是第二行\n")
        await f.write("这是第三行\n")
    print(f"  ✅ 写入: {filepath}")

    # 读取全部
    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        content = await f.read()
    print(f"  读取全部:\n    {content.strip()}")

    # 逐行读取
    print("  逐行读取:")
    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        line_num = 0
        async for line in f:
            line_num += 1
            print(f"    行 {line_num}: {line.strip()}")


# ============================================================
# 2. 异步 JSON 读写
# ============================================================

async def demo_json_rw():
    """异步 JSON 文件读写"""
    print("\n" + "=" * 50)
    print("📋 异步 JSON 读写")
    print("=" * 50)

    if not HAS_AIOFILES:
        print("  ⚠️  需要安装 aiofiles")
        return

    await ensure_demo_dir()
    filepath = os.path.join(DEMO_DIR, "config.json")

    data = {
        "app": "AI Chat",
        "models": ["gpt-4o-mini", "claude-sonnet", "deepseek-chat"],
        "settings": {"temperature": 0.7, "max_tokens": 1000},
    }

    # 异步写入 JSON
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"  ✅ 写入: {filepath}")

    # 异步读取 JSON
    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        content = await f.read()
        loaded = json.loads(content)
    print(f"  读取: {loaded['app']}，{len(loaded['models'])} 个模型")


# ============================================================
# 3. 并发读写多个文件
# ============================================================

async def demo_concurrent_files():
    """并发读写多个文件"""
    print("\n" + "=" * 50)
    print("🚀 并发读写多个文件")
    print("=" * 50)

    if not HAS_AIOFILES:
        print("  ⚠️  需要安装 aiofiles")
        return

    await ensure_demo_dir()

    # 并发写入 5 个文件
    async def write_file(idx: int):
        filepath = os.path.join(DEMO_DIR, f"file_{idx}.txt")
        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(f"文件 {idx} 的内容\n")
            await f.write(f"创建时间: 模拟\n")
        return filepath

    print("  写入 5 个文件...")
    start = time.time()
    paths = await asyncio.gather(*[write_file(i) for i in range(5)])
    print(f"  ✅ 并发写入 {len(paths)} 个文件（{time.time() - start:.3f}s）")

    # 并发读取
    async def read_file(filepath: str) -> str:
        async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
            return await f.read()

    print("  读取 5 个文件...")
    start = time.time()
    contents = await asyncio.gather(*[read_file(p) for p in paths])
    print(f"  ✅ 并发读取 {len(contents)} 个文件（{time.time() - start:.3f}s）")

    for i, content in enumerate(contents):
        print(f"    [{i}] {content.strip().split(chr(10))[0]}")


# ============================================================
# 4. 同步 vs 异步对比说明
# ============================================================

async def demo_when_to_use():
    """什么时候用 aiofiles"""
    print("\n" + "=" * 50)
    print("💡 什么时候用 aiofiles")
    print("=" * 50)

    print("""
  场景                           推荐方式
  ─────────────────────────────────────────
  脚本中读写配置文件               同步 open()
  脚本中处理数据文件               同步 open()
  FastAPI 中保存上传文件           aiofiles ✅
  FastAPI 中读取模板文件           aiofiles ✅
  异步上下文中写日志               aiofiles ✅
  一次性读取小文件                 同步 open()

  原则：
  - 普通脚本 → 同步够用
  - async def 函数内读写文件 → 用 aiofiles 避免阻塞事件循环
  - FastAPI 路由处理 → 推荐 aiofiles
    """)

    # 同步读写做对比
    await ensure_demo_dir()
    filepath = os.path.join(DEMO_DIR, "sync_test.txt")

    # 同步方式（在 async 函数中用同步 I/O 会阻塞事件循环）
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("同步写入也可以，但在 async 上下文中会阻塞")

    with open(filepath, "r", encoding="utf-8") as f:
        print(f"  同步读取: {f.read()[:30]}...")

    if HAS_AIOFILES:
        async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
            content = await f.read()
        print(f"  异步读取: {content[:30]}...")


# ============================================================
# 入口
# ============================================================

async def main():
    print("\n🐍 练习4：异步文件操作\n")

    demos = [
        ("1", "基础读写", demo_basic_rw),
        ("2", "异步 JSON 读写", demo_json_rw),
        ("3", "并发读写多文件", demo_concurrent_files),
        ("4", "什么时候用 aiofiles", demo_when_to_use),
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
            await cleanup_demo_dir()
            print("\n✅ 全部完成！")
            break
        elif choice in [n for n, _, _ in demos]:
            await demos[int(choice) - 1][2]()
            await cleanup_demo_dir()
        else:
            print(f"  无效输入: '{choice}'")


if __name__ == "__main__":
    asyncio.run(main())
