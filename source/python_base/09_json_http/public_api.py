# public_api.py
# 练习4：调用公开 API — 解析响应、错误处理
#
# 依赖：pip install httpx
# 运行方式：python public_api.py
#
# 使用免费公开 API，无需 API Key。

import httpx
import json


def demo_uuid():
    """调用 httpbin.org 生成 UUID"""
    print("=" * 50)
    print("🆔 生成 UUID（httpbin.org/uuid）")
    print("=" * 50)

    response = httpx.get("https://httpbin.org/uuid", timeout=10.0)
    data = response.json()
    print(f"  生成的 UUID: {data['uuid']}")


def demo_ip():
    """获取公网 IP"""
    print("\n" + "=" * 50)
    print("🌐 获取公网 IP（httpbin.org/ip）")
    print("=" * 50)

    response = httpx.get("https://httpbin.org/ip", timeout=10.0)
    data = response.json()
    print(f"  当前 IP: {data['origin']}")


def demo_jsonplaceholder():
    """调用 JSONPlaceholder — 模拟 REST API"""
    print("\n" + "=" * 50)
    print("📋 JSONPlaceholder（模拟 REST API）")
    print("=" * 50)

    base_url = "https://jsonplaceholder.typicode.com"

    # GET 列表
    print("\n  --- GET /posts（前 3 条）---")
    response = httpx.get(f"{base_url}/posts", params={"_limit": 3}, timeout=10.0)
    posts = response.json()
    for post in posts:
        print(f"    [{post['id']}] {post['title'][:30]}...")

    # GET 单条
    print("\n  --- GET /posts/1 ---")
    response = httpx.get(f"{base_url}/posts/1", timeout=10.0)
    post = response.json()
    print(f"    标题: {post['title']}")
    print(f"    内容: {post['body'][:50]}...")

    # POST 创建
    print("\n  --- POST /posts（创建）---")
    new_post = {
        "title": "学习 Python HTTP 请求",
        "body": "使用 httpx 调用公开 API",
        "userId": 1,
    }
    response = httpx.post(f"{base_url}/posts", json=new_post, timeout=10.0)
    created = response.json()
    print(f"    创建成功, id={created.get('id')}, 状态码={response.status_code}")


def demo_headers_inspect():
    """检查响应头"""
    print("\n" + "=" * 50)
    print("📋 检查响应头")
    print("=" * 50)

    response = httpx.get("https://httpbin.org/response-headers",
                         params={"X-Custom": "hello", "X-Model": "gpt-4o"},
                         timeout=10.0)

    print(f"  状态码: {response.status_code}")
    print(f"  响应头:")
    for key in ["Content-Type", "X-Custom", "X-Model"]:
        value = response.headers.get(key, "N/A")
        print(f"    {key}: {value}")


def demo_status_codes():
    """测试不同状态码"""
    print("\n" + "=" * 50)
    print("🔢 状态码测试")
    print("=" * 50)

    codes = [200, 201, 400, 401, 403, 404, 429, 500, 503]

    for code in codes:
        try:
            response = httpx.get(f"https://httpbin.org/status/{code}", timeout=10.0)
            status = "✅" if response.is_success else "❌"
            print(f"  {status} {code} - {response.reason_phrase}")
        except httpx.HTTPStatusError as e:
            print(f"  ❌ {code} - {e}")
        except Exception as e:
            print(f"  ⚠️  {code} - {type(e).__name__}: {e}")


def demo_delay():
    """测试请求延迟和超时"""
    print("\n" + "=" * 50)
    print("⏱️  延迟和超时测试")
    print("=" * 50)

    # 正常延迟
    print("\n  --- 延迟 1 秒 ---")
    response = httpx.get("https://httpbin.org/delay/1", timeout=5.0)
    print(f"  耗时: {response.elapsed.total_seconds():.2f}s")

    # 超时测试
    print("\n  --- 设置 2 秒超时，请求 5 秒延迟 ---")
    try:
        httpx.get("https://httpbin.org/delay/5", timeout=2.0)
        print("  请求完成（不应该走到这里）")
    except httpx.TimeoutException:
        print("  ✅ 正确超时，2 秒后放弃等待")


def demo_error_handling():
    """完整的错误处理示例"""
    print("\n" + "=" * 50)
    print("🛡️  错误处理实战")
    print("=" * 50)

    def fetch_data(url: str) -> dict | None:
        """通用请求函数，统一处理各种错误"""
        try:
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            print(f"    ⏰ 超时: {url}")
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if code == 401:
                print(f"    🔑 认证失败: 请检查 API Key")
            elif code == 429:
                print(f"    🚫 请求过多: 请稍后重试")
            elif code >= 500:
                print(f"    💥 服务器错误: {code}")
            else:
                print(f"    ❌ HTTP 错误: {code}")
        except httpx.RequestError as e:
            print(f"    🔌 连接错误: {type(e).__name__}")
        except json.JSONDecodeError:
            print(f"    📄 响应不是 JSON 格式")
        return None

    # 正常
    print("\n  正常请求:")
    data = fetch_data("https://httpbin.org/uuid")
    if data:
        print(f"    UUID: {data['uuid']}")

    # 401
    print("\n  401 错误:")
    fetch_data("https://httpbin.org/status/401")

    # 429
    print("\n  429 错误:")
    fetch_data("https://httpbin.org/status/429")

    # 500
    print("\n  500 错误:")
    fetch_data("https://httpbin.org/status/500")


if __name__ == "__main__":
    print("\n🐍 练习4：调用公开 API\n")

    demos = [
        ("1", "生成 UUID", demo_uuid),
        ("2", "获取公网 IP", demo_ip),
        ("3", "JSONPlaceholder REST API", demo_jsonplaceholder),
        ("4", "检查响应头", demo_headers_inspect),
        ("5", "状态码测试", demo_status_codes),
        ("6", "延迟和超时", demo_delay),
        ("7", "错误处理实战", demo_error_handling),
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
