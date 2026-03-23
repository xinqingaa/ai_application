# http_client_class.py
# 练习5：封装 HTTP 客户端类
#
# 依赖：pip install httpx
# 运行方式：python http_client_class.py
#
# 将前面学到的知识封装成一个可复用的 HTTP 客户端，
# 这种模式在实际 AI 应用中非常常见。

import httpx
import time
import json
from dataclasses import dataclass, field


@dataclass
class HttpResponse:
    """统一的响应数据结构"""
    status_code: int
    data: dict | list | None = None
    error: str | None = None
    elapsed_ms: float = 0.0
    headers: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400 and self.error is None


class SimpleHttpClient:
    """
    简单的 HTTP 客户端封装

    特性：
    - 统一的 headers 管理
    - 自动超时配置
    - 统一的错误处理
    - 简单的重试机制
    - 请求日志
    """

    def __init__(
        self,
        base_url: str = "",
        headers: dict | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        debug: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "SimpleHttpClient/1.0",
        }
        if headers:
            self.default_headers.update(headers)
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug = debug

    def _log(self, msg: str) -> None:
        if self.debug:
            print(f"  [DEBUG] {msg}")

    def _build_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def _make_request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_data: dict | None = None,
        headers: dict | None = None,
        retry_on: tuple[int, ...] = (429, 500, 502, 503),
    ) -> HttpResponse:
        """
        发送请求的核心方法，带重试和统一错误处理

        Args:
            method: HTTP 方法
            path: 请求路径（相对 base_url）或完整 URL
            params: 查询参数
            json_data: JSON 请求体
            headers: 额外请求头（会与默认 headers 合并）
            retry_on: 需要重试的状态码
        """
        url = self._build_url(path)

        merged_headers = {**self.default_headers}
        if headers:
            merged_headers.update(headers)

        last_error = ""
        for attempt in range(self.max_retries):
            try:
                self._log(f"请求 {method} {url} (attempt {attempt + 1})")
                start = time.time()

                response = httpx.request(
                    method,
                    url,
                    params=params,
                    json=json_data,
                    headers=merged_headers,
                    timeout=self.timeout,
                )

                elapsed_ms = (time.time() - start) * 1000
                self._log(f"响应 {response.status_code} ({elapsed_ms:.0f}ms)")

                # 需要重试的状态码
                if response.status_code in retry_on and attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    self._log(f"状态码 {response.status_code}，{wait}s 后重试")
                    time.sleep(wait)
                    continue

                # 解析响应
                try:
                    data = response.json()
                except (json.JSONDecodeError, ValueError):
                    data = None

                if response.is_success:
                    return HttpResponse(
                        status_code=response.status_code,
                        data=data,
                        elapsed_ms=elapsed_ms,
                        headers=dict(response.headers),
                    )
                else:
                    return HttpResponse(
                        status_code=response.status_code,
                        data=data,
                        error=f"HTTP {response.status_code}: {response.reason_phrase}",
                        elapsed_ms=elapsed_ms,
                        headers=dict(response.headers),
                    )

            except httpx.TimeoutException:
                last_error = "请求超时"
                self._log(f"超时 (attempt {attempt + 1})")
            except httpx.ConnectError:
                last_error = f"连接失败: {url}"
                self._log(f"连接失败 (attempt {attempt + 1})")
            except httpx.RequestError as e:
                last_error = f"请求错误: {type(e).__name__}"
                self._log(f"请求错误: {e}")

            # 非最后一次尝试，等待后重试
            if attempt < self.max_retries - 1:
                wait = 2 ** attempt
                self._log(f"{wait}s 后重试")
                time.sleep(wait)

        return HttpResponse(status_code=0, error=last_error)

    def get(self, path: str, params: dict | None = None, **kwargs) -> HttpResponse:
        """GET 请求"""
        return self._make_request("GET", path, params=params, **kwargs)

    def post(self, path: str, data: dict | None = None, **kwargs) -> HttpResponse:
        """POST 请求"""
        return self._make_request("POST", path, json_data=data, **kwargs)

    def put(self, path: str, data: dict | None = None, **kwargs) -> HttpResponse:
        """PUT 请求"""
        return self._make_request("PUT", path, json_data=data, **kwargs)

    def delete(self, path: str, **kwargs) -> HttpResponse:
        """DELETE 请求"""
        return self._make_request("DELETE", path, **kwargs)


# ============================================================
# 演示
# ============================================================

def demo_basic_usage():
    """基础使用"""
    print("=" * 50)
    print("📦 基础使用")
    print("=" * 50)

    client = SimpleHttpClient(
        base_url="https://httpbin.org",
        debug=True,
    )

    # GET
    resp = client.get("/get", params={"name": "test"})
    print(f"\n  GET 结果: ok={resp.ok}, status={resp.status_code}, "
          f"耗时={resp.elapsed_ms:.0f}ms")
    if resp.ok:
        print(f"  参数: {resp.data['args']}")

    # POST
    resp = client.post("/post", data={"model": "gpt-4o-mini"})
    print(f"\n  POST 结果: ok={resp.ok}, status={resp.status_code}")
    if resp.ok:
        print(f"  发送的数据: {resp.data['json']}")


def demo_with_auth():
    """带认证的请求"""
    print("\n" + "=" * 50)
    print("🔐 带认证的请求")
    print("=" * 50)

    client = SimpleHttpClient(
        base_url="https://httpbin.org",
        headers={"Authorization": "Bearer sk-my-api-key"},
    )

    resp = client.post("/post", data={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "你好"}],
    })

    if resp.ok:
        auth = resp.data["headers"].get("Authorization", "")
        print(f"  Auth 头已发送: {auth[:25]}...")
        print(f"  模型: {resp.data['json']['model']}")


def demo_error_and_retry():
    """错误处理和重试"""
    print("\n" + "=" * 50)
    print("🔄 错误处理和重试")
    print("=" * 50)

    client = SimpleHttpClient(
        base_url="https://httpbin.org",
        max_retries=2,
        timeout=3.0,
        debug=True,
    )

    # 404 — 不重试（不在 retry_on 列表中）
    print("\n  --- 404 错误（不重试）---")
    resp = client.get("/status/404")
    print(f"  结果: ok={resp.ok}, error={resp.error}")

    # 超时 — 重试
    print("\n  --- 超时（重试 2 次）---")
    resp = client.get("/delay/10")
    print(f"  结果: ok={resp.ok}, error={resp.error}")


def demo_simulate_llm_api():
    """模拟 LLM API 调用"""
    print("\n" + "=" * 50)
    print("🤖 模拟 LLM API 调用")
    print("=" * 50)

    # 模拟一个 LLM API 客户端
    llm_client = SimpleHttpClient(
        base_url="https://httpbin.org",
        headers={
            "Authorization": "Bearer sk-fake-key",
            "Content-Type": "application/json",
        },
        timeout=60.0,
    )

    # 构造类似 OpenAI 的请求
    request_body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "你是一个有用的助手"},
            {"role": "user", "content": "用一句话介绍 Python"},
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }

    resp = llm_client.post("/post", data=request_body)

    if resp.ok:
        sent = resp.data["json"]
        print(f"  模型: {sent['model']}")
        print(f"  消息数: {len(sent['messages'])}")
        print(f"  temperature: {sent['temperature']}")
        print(f"  耗时: {resp.elapsed_ms:.0f}ms")
        print(f"\n  💡 将 base_url 改为 https://api.openai.com/v1")
        print(f"     path 改为 /chat/completions")
        print(f"     就是真正的 OpenAI API 调用了！")
    else:
        print(f"  请求失败: {resp.error}")


def demo_response_dataclass():
    """HttpResponse 数据结构演示"""
    print("\n" + "=" * 50)
    print("📊 HttpResponse 数据结构")
    print("=" * 50)

    client = SimpleHttpClient(base_url="https://httpbin.org")

    resp = client.get("/uuid")
    print(f"  ok          : {resp.ok}")
    print(f"  status_code : {resp.status_code}")
    print(f"  data        : {resp.data}")
    print(f"  error       : {resp.error}")
    print(f"  elapsed_ms  : {resp.elapsed_ms:.0f}ms")
    print(f"  headers 数量: {len(resp.headers)}")


if __name__ == "__main__":
    print("\n🐍 练习5：封装 HTTP 客户端类\n")

    demos = [
        ("1", "基础使用", demo_basic_usage),
        ("2", "带认证的请求", demo_with_auth),
        ("3", "错误处理和重试", demo_error_and_retry),
        ("4", "模拟 LLM API 调用", demo_simulate_llm_api),
        ("5", "HttpResponse 数据结构", demo_response_dataclass),
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
