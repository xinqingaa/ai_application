# http_requests.py
# 练习2：requests 库基础 — GET/POST、httpbin.org
#
# 依赖：pip install requests
# 运行方式：python http_requests.py
#
# httpbin.org 是一个免费的 HTTP 测试服务，会把你的请求原样返回，
# 非常适合学习和调试 HTTP 请求。

import json
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError


def demo_get_basic():
    """GET 请求基础"""
    print("=" * 50)
    print("📥 GET 请求基础")
    print("=" * 50)

    response = requests.get("https://httpbin.org/get", timeout=10)

    print(f"  状态码: {response.status_code}")
    print(f"  是否成功: {response.ok}")
    print(f"  耗时: {response.elapsed.total_seconds():.2f}s")
    print(f"  URL: {response.url}")

    data = response.json()
    print(f"  来源 IP: {data.get('origin', 'unknown')}")


def demo_get_with_params():
    """GET 请求带查询参数"""
    print("\n" + "=" * 50)
    print("📥 GET 带查询参数")
    print("=" * 50)

    response = requests.get(
        "https://httpbin.org/get",
        params={"name": "张三", "page": 1, "limit": 10},
        timeout=10,
    )

    data = response.json()
    print(f"  实际 URL: {response.url}")
    print(f"  服务端收到的参数: {data['args']}")


def demo_post_json():
    """POST 请求发送 JSON"""
    print("\n" + "=" * 50)
    print("📤 POST 发送 JSON")
    print("=" * 50)

    # 模拟 LLM API 请求
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "你是一个有用的助手"},
            {"role": "user", "content": "你好"},
        ],
        "temperature": 0.7,
    }

    response = requests.post(
        "https://httpbin.org/post",
        json=payload,  # 自动序列化 + 设置 Content-Type
        headers={"Authorization": "Bearer sk-test-key"},
        timeout=10,
    )

    data = response.json()
    print(f"  状态码: {response.status_code}")
    print(f"  服务端收到的 JSON:")
    print(f"    model: {data['json']['model']}")
    print(f"    messages: {len(data['json']['messages'])} 条")
    print(f"  请求头 Content-Type: {data['headers'].get('Content-Type')}")
    print(f"  请求头 Authorization: {data['headers'].get('Authorization')[:20]}...")


def demo_response_details():
    """响应对象详解"""
    print("\n" + "=" * 50)
    print("📋 响应对象详解")
    print("=" * 50)

    response = requests.get("https://httpbin.org/get", timeout=10)

    print(f"  status_code  : {response.status_code}")
    print(f"  ok           : {response.ok}")
    print(f"  encoding     : {response.encoding}")
    print(f"  headers 类型 : {type(response.headers).__name__}")
    print(f"  Content-Type : {response.headers.get('Content-Type')}")
    print(f"  text 前 80 字: {response.text[:80]}...")
    print(f"  json() 类型  : {type(response.json()).__name__}")


def demo_error_handling():
    """异常处理"""
    print("\n" + "=" * 50)
    print("🛡️  异常处理")
    print("=" * 50)

    # 1. 状态码错误
    print("\n  --- 404 错误 ---")
    response = requests.get("https://httpbin.org/status/404", timeout=10)
    print(f"  状态码: {response.status_code}, ok: {response.ok}")
    try:
        response.raise_for_status()
    except HTTPError as e:
        print(f"  ✅ 捕获 HTTPError: {e}")

    # 2. 超时
    print("\n  --- 超时 ---")
    try:
        requests.get("https://httpbin.org/delay/5", timeout=2)
    except Timeout:
        print("  ✅ 捕获 Timeout: 请求在 2 秒内未完成")

    # 3. 连接错误
    print("\n  --- 连接错误 ---")
    try:
        requests.get("https://this-domain-does-not-exist-12345.com", timeout=3)
    except ConnectionError:
        print("  ✅ 捕获 ConnectionError: 域名无法解析")

    # 4. 安全请求函数
    print("\n  --- safe_request 函数 ---")
    result = safe_request("https://httpbin.org/get")
    print(f"  正常请求: 返回了 {type(result).__name__}")

    result = safe_request("https://httpbin.org/status/500")
    print(f"  500 错误: 返回了 {result}")


def safe_request(url: str, method: str = "GET", **kwargs) -> dict | None:
    """安全地发送请求，统一处理异常"""
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        response.raise_for_status()
        return response.json()
    except ConnectionError:
        print(f"    ⚠️  连接失败: {url}")
    except Timeout:
        print(f"    ⚠️  请求超时: {url}")
    except HTTPError as e:
        print(f"    ⚠️  HTTP {e.response.status_code}: {url}")
    except Exception as e:
        print(f"    ⚠️  未知错误: {e}")
    return None


def demo_session():
    """Session 复用"""
    print("\n" + "=" * 50)
    print("🔄 Session 复用")
    print("=" * 50)

    with requests.Session() as session:
        # 设置公共配置
        session.headers.update({
            "Authorization": "Bearer sk-test-session",
            "User-Agent": "my-ai-app/1.0",
        })

        # 多次请求共享 headers
        r1 = session.get("https://httpbin.org/get", timeout=10)
        r2 = session.post("https://httpbin.org/post", json={"msg": "hello"}, timeout=10)

        print(f"  GET  - Auth: {r1.json()['headers'].get('Authorization', '')[:25]}...")
        print(f"  POST - Auth: {r2.json()['headers'].get('Authorization', '')[:25]}...")
        print(f"  两次请求共享了 Authorization 和 User-Agent 请求头")


if __name__ == "__main__":
    print("\n🐍 练习2：requests 库\n")

    demos = [
        ("1", "GET 基础", demo_get_basic),
        ("2", "GET 带参数", demo_get_with_params),
        ("3", "POST JSON", demo_post_json),
        ("4", "响应详解", demo_response_details),
        ("5", "异常处理", demo_error_handling),
        ("6", "Session 复用", demo_session),
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
