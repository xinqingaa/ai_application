# httpx_client.py
# 练习3：httpx 同步请求 + 异步预览
#
# 依赖：pip install httpx
# 运行方式：python httpx_client.py
#
# httpx 的同步 API 与 requests 几乎一致，额外支持原生 async。
# AI 应用开发推荐使用 httpx。

import httpx
import asyncio
import time


def demo_sync_get():
    """httpx 同步 GET 请求"""
    print("=" * 50)
    print("📥 httpx 同步 GET")
    print("=" * 50)

    response = httpx.get("https://httpbin.org/get", timeout=10.0)

    print(f"  状态码: {response.status_code}")
    print(f"  耗时: {response.elapsed.total_seconds():.2f}s")
    print(f"  HTTP 版本: {response.http_version}")

    data = response.json()
    print(f"  来源 IP: {data.get('origin', 'unknown')}")

    # 带参数
    response = httpx.get(
        "https://httpbin.org/get",
        params={"model": "gpt-4o-mini", "limit": 10},
        timeout=10.0,
    )
    print(f"  带参数 URL: {response.url}")


def demo_sync_post():
    """httpx 同步 POST 请求"""
    print("\n" + "=" * 50)
    print("📤 httpx 同步 POST")
    print("=" * 50)

    response = httpx.post(
        "https://httpbin.org/post",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "你好"}],
        },
        headers={"Authorization": "Bearer sk-httpx-test"},
        timeout=10.0,
    )

    data = response.json()
    print(f"  状态码: {response.status_code}")
    print(f"  模型: {data['json']['model']}")
    print(f"  Auth: {data['headers']['Authorization'][:25]}...")


def demo_client():
    """httpx.Client（类似 requests.Session）"""
    print("\n" + "=" * 50)
    print("🔄 httpx.Client 复用")
    print("=" * 50)

    with httpx.Client(
        base_url="https://httpbin.org",
        headers={"Authorization": "Bearer sk-client-test"},
        timeout=10.0,
    ) as client:
        # base_url 生效，只需写路径
        r1 = client.get("/get")
        r2 = client.post("/post", json={"action": "test"})

        print(f"  GET  状态: {r1.status_code}")
        print(f"  POST 状态: {r2.status_code}")
        print(f"  base_url 生效: 只需写 /get、/post")


def demo_error_handling():
    """httpx 异常处理"""
    print("\n" + "=" * 50)
    print("🛡️  httpx 异常处理")
    print("=" * 50)

    # 1. 超时
    print("\n  --- 超时 ---")
    try:
        httpx.get("https://httpbin.org/delay/5", timeout=2.0)
    except httpx.TimeoutException:
        print("  ✅ 捕获 TimeoutException")

    # 2. HTTP 状态码错误
    print("\n  --- 状态码错误 ---")
    response = httpx.get("https://httpbin.org/status/404", timeout=10.0)
    print(f"  状态码: {response.status_code}")
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"  ✅ 捕获 HTTPStatusError: {e.response.status_code}")

    # 3. 连接错误
    print("\n  --- 连接错误 ---")
    try:
        httpx.get("https://this-domain-does-not-exist-12345.com", timeout=3.0)
    except httpx.ConnectError:
        print("  ✅ 捕获 ConnectError")
    except httpx.RequestError as e:
        print(f"  ✅ 捕获 RequestError: {type(e).__name__}")


def demo_timeout_config():
    """httpx 超时细粒度配置"""
    print("\n" + "=" * 50)
    print("⏱️  超时配置")
    print("=" * 50)

    # 简单超时
    print("  简单超时: timeout=30.0（所有阶段共 30 秒）")

    # 细粒度超时（AI 应用推荐）
    timeout = httpx.Timeout(
        connect=5.0,   # 连接超时 5 秒
        read=60.0,     # 读取超时 60 秒（LLM 推理可能较慢）
        write=10.0,    # 写入超时 10 秒
        pool=5.0,      # 连接池等待 5 秒
    )
    print(f"  细粒度超时: connect={timeout.connect}s, read={timeout.read}s")
    print(f"  LLM API 推荐: read 设为 60s+（模型推理需要时间）")

    response = httpx.get("https://httpbin.org/get", timeout=timeout)
    print(f"  请求成功: {response.status_code}")


# ============================================================
# 异步预览（第 10 节会详细学习 async/await）
# ============================================================

async def async_get(url: str) -> dict:
    """异步 GET 请求"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        return response.json()


async def async_concurrent():
    """并发请求多个 URL"""
    urls = [
        "https://httpbin.org/get?id=1",
        "https://httpbin.org/get?id=2",
        "https://httpbin.org/get?id=3",
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        # asyncio.gather 并发执行
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)

    return [r.json()["args"]["id"] for r in responses]


def demo_async_preview():
    """异步预览（简单了解）"""
    print("\n" + "=" * 50)
    print("⚡ 异步预览")
    print("=" * 50)

    # 单个异步请求
    print("\n  --- 单个异步请求 ---")
    result = asyncio.run(async_get("https://httpbin.org/get"))
    print(f"  结果类型: {type(result).__name__}")

    # 并发请求
    print("\n  --- 并发 3 个请求 ---")
    start = time.time()
    ids = asyncio.run(async_concurrent())
    elapsed = time.time() - start
    print(f"  结果: {ids}")
    print(f"  耗时: {elapsed:.2f}s（3 个请求并发执行，比串行快）")
    print(f"\n  💡 异步详细内容将在第 10 节学习")


# ============================================================
# requests vs httpx 对比
# ============================================================

def demo_comparison():
    """requests vs httpx 对比演示"""
    print("\n" + "=" * 50)
    print("⚖️  requests vs httpx 对比")
    print("=" * 50)

    import requests as req

    url = "https://httpbin.org/post"
    payload = {"model": "gpt-4o-mini", "prompt": "test"}
    headers = {"Authorization": "Bearer sk-compare-test"}

    # requests
    start = time.time()
    r1 = req.post(url, json=payload, headers=headers, timeout=10)
    t1 = time.time() - start

    # httpx
    start = time.time()
    r2 = httpx.post(url, json=payload, headers=headers, timeout=10.0)
    t2 = time.time() - start

    print(f"  requests: {r1.status_code} ({t1:.3f}s)")
    print(f"  httpx   : {r2.status_code} ({t2:.3f}s)")
    print(f"\n  API 几乎一致，httpx 额外支持 async 和 HTTP/2")


if __name__ == "__main__":
    print("\n🐍 练习3：httpx 库\n")

    demos = [
        ("1", "同步 GET", demo_sync_get),
        ("2", "同步 POST", demo_sync_post),
        ("3", "Client 复用", demo_client),
        ("4", "异常处理", demo_error_handling),
        ("5", "超时配置", demo_timeout_config),
        ("6", "异步预览", demo_async_preview),
        ("7", "requests vs httpx 对比", demo_comparison),
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
                fn()
            print("\n✅ 全部完成！")
            break
        elif choice in [n for n, _, _ in demos]:
            demos[int(choice) - 1][2]()
        else:
            print(f"  无效输入: '{choice}'")
