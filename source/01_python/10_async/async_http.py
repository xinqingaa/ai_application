# async_http.py
# 练习3：异步 HTTP — httpx.AsyncClient + 并发请求
#
# 依赖：pip install httpx
# 运行方式：python async_http.py

import httpx
import asyncio
import time


# ============================================================
# 1. AsyncClient 基础
# ============================================================

async def demo_basic():
    """AsyncClient 基础 GET/POST"""
    print("=" * 50)
    print("📥 AsyncClient 基础")
    print("=" * 50)

    # async with 是异步版 with：
    # 1. 进入代码块前创建并打开 AsyncClient
    # 2. as client 把对象绑定给变量 client
    # 3. 代码块结束后自动 await client.aclose()
    # 所以它本质上很像：
    # client = httpx.AsyncClient(...)
    # try:
    #     ...
    # finally:
    #     await client.aclose()
    async with httpx.AsyncClient(timeout=10.0) as client:
        # GET
        response = await client.get("https://httpbin.org/get", params={"hello": "async"})
        print(f"  GET  状态: {response.status_code}")
        print(f"  参数: {response.json()['args']}")

        # POST
        response = await client.post(
            "https://httpbin.org/post",
            json={"model": "gpt-4o-mini", "content": "你好"},
            headers={"Authorization": "Bearer sk-async-test"},
        )
        data = response.json()
        print(f"  POST 状态: {response.status_code}")
        print(f"  发送: {data['json']}")


# ============================================================
# 2. 并发请求多个 URL
# ============================================================

async def demo_concurrent_requests():
    """并发请求多个 URL"""
    print("\n" + "=" * 50)
    print("🚀 并发请求多个 URL")
    print("=" * 50)

    urls = [f"https://httpbin.org/get?id={i}" for i in range(5)]

    async with httpx.AsyncClient(timeout=10.0) as client:
        # async with 负责管理 client 的生命周期
        # asyncio.gather 负责并发执行任务
        # 这两个是两件不同的事：
        # - async with：资源打开 / 关闭
        # - gather：并发调度
        start = time.time()
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        elapsed = time.time() - start

    for r in responses:
        args = r.json()["args"]
        print(f"  id={args['id']} → 状态 {r.status_code}")
    print(f"\n  5 个请求并发耗时: {elapsed:.2f}s")


# ============================================================
# 3. 串行 vs 并发性能对比
# ============================================================

async def demo_serial_vs_concurrent():
    """串行 vs 并发性能对比"""
    print("\n" + "=" * 50)
    print("⚡ 串行 vs 并发对比")
    print("=" * 50)

    urls = [f"https://httpbin.org/delay/1?id={i}" for i in range(3)]

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 串行
        print("\n  --- 串行（逐个请求）---")
        start = time.time()
        for url in urls:
            await client.get(url)
        serial_time = time.time() - start
        print(f"  串行耗时: {serial_time:.2f}s")

        # 并发
        print("\n  --- 并发（同时请求）---")
        start = time.time()
        await asyncio.gather(*[client.get(url) for url in urls])
        concurrent_time = time.time() - start
        print(f"  并发耗时: {concurrent_time:.2f}s")

    print(f"\n  提速: {serial_time / concurrent_time:.1f}x")


# ============================================================
# 4. Semaphore 控制并发数
# ============================================================

async def demo_semaphore():
    """用 Semaphore 控制并发数（防止触发 API 限速）"""
    print("\n" + "=" * 50)
    print("🚦 Semaphore 控制并发数")
    print("=" * 50)

    semaphore = asyncio.Semaphore(2)  # 最多同时 2 个请求

    async def fetch_with_limit(client: httpx.AsyncClient, url: str, idx: int):
        # Semaphore 也支持 async with：
        # 进入代码块时获取一个名额，退出时自动归还名额
        async with semaphore:
            print(f"  [{idx}] 开始请求...")
            response = await client.get(url, timeout=10.0)
            print(f"  [{idx}] 完成 → {response.status_code}")
            return response.status_code

    urls = [f"https://httpbin.org/get?id={i}" for i in range(6)]

    async with httpx.AsyncClient() as client:
        start = time.time()
        tasks = [fetch_with_limit(client, url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

    print(f"\n  {len(results)} 个请求完成（最多同时 2 个），耗时 {elapsed:.2f}s")


# ============================================================
# 5. 异步错误处理
# ============================================================

async def demo_error_handling():
    """异步请求的错误处理"""
    print("\n" + "=" * 50)
    print("🛡️  异步错误处理")
    print("=" * 50)

    async def safe_fetch(client: httpx.AsyncClient, url: str) -> dict:
        """安全的异步请求"""
        try:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            return {"url": url, "status": response.status_code, "ok": True}
        except httpx.TimeoutException:
            return {"url": url, "error": "超时", "ok": False}
        except httpx.HTTPStatusError as e:
            return {"url": url, "error": f"HTTP {e.response.status_code}", "ok": False}
        except httpx.RequestError as e:
            return {"url": url, "error": str(type(e).__name__), "ok": False}

    urls = [
        "https://httpbin.org/get",            # 正常
        "https://httpbin.org/status/404",      # 404
        "https://httpbin.org/status/500",      # 500
        "https://httpbin.org/delay/10",        # 超时
    ]

    async with httpx.AsyncClient() as client:
        tasks = [safe_fetch(client, url) for url in urls]
        results = await asyncio.gather(*tasks)

    for r in results:
        if r["ok"]:
            print(f"  ✅ {r['url'].split('/')[-1]} → {r['status']}")
        else:
            print(f"  ❌ {r['url'].split('/')[-1]} → {r['error']}")


# ============================================================
# 6. Client 配置复用
# ============================================================

async def demo_client_config():
    """AsyncClient 配置复用"""
    print("\n" + "=" * 50)
    print("⚙️  AsyncClient 配置复用")
    print("=" * 50)

    async with httpx.AsyncClient(
        base_url="https://httpbin.org",
        headers={
            "Authorization": "Bearer sk-config-test",
            "User-Agent": "ai-app/1.0",
        },
        timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
    ) as client:
        # base_url 生效，只需写路径
        r1 = await client.get("/get")
        r2 = await client.post("/post", json={"msg": "hello"})

        print(f"  GET  → Auth: {r1.json()['headers']['Authorization'][:25]}...")
        print(f"  POST → 数据: {r2.json()['json']}")
        print(f"  base_url、headers、timeout 所有请求共享")


# ============================================================
# 入口
# ============================================================

async def main():
    print("\n🐍 练习3：异步 HTTP\n")

    demos = [
        ("1", "AsyncClient 基础", demo_basic),
        ("2", "并发请求多个 URL", demo_concurrent_requests),
        ("3", "串行 vs 并发对比", demo_serial_vs_concurrent),
        ("4", "Semaphore 限速", demo_semaphore),
        ("5", "异步错误处理", demo_error_handling),
        ("6", "Client 配置复用", demo_client_config),
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
