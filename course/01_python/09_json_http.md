# 09. JSON 与 HTTP 请求

> 本节目标：掌握 JSON 进阶处理和 HTTP 请求，为调用 LLM API 做好准备

---

## 1. 概述

### 学习目标

- 掌握复杂嵌套 JSON 的处理和自定义序列化
- 理解 HTTP 请求方法、请求头、状态码
- 掌握 requests 库的使用
- 掌握 httpx 库的使用（AI 应用推荐）
- 能封装可复用的 HTTP 客户端

### 预计学习时间

- JSON 深入：30 分钟
- HTTP 基础概念：30 分钟
- requests 库：1 小时
- httpx 库：30 分钟
- 练习：1-2 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| 调用 LLM API | HTTP POST 请求、JSON 请求体 |
| 解析模型返回 | JSON 嵌套结构解析 |
| API Key 鉴权 | 请求头 Authorization |
| 错误处理 | 状态码判断、超时重试 |
| 多模型切换 | 封装 HTTP 客户端类 |
| 流式响应 | httpx 异步请求（预览，第 10 节详解） |

> **从这一节开始，你学的东西可以直接用来调用 OpenAI / Claude / DeepSeek 的 API。**

---

## 2. JSON 深入 📌

> 第 7 节已学过 `json.dumps()` / `json.loads()` 基础，本节侧重进阶用法。

### 2.1 复杂嵌套结构处理

LLM API 的请求和响应都是嵌套 JSON，必须熟练处理。

```python
# 模拟 OpenAI API 的响应格式
response = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "你好！有什么可以帮助你的？"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 15,
        "total_tokens": 25
    }
}

# 提取回复内容（多层访问）
content = response["choices"][0]["message"]["content"]
print(content)  # "你好！有什么可以帮助你的？"

# 提取 token 使用
usage = response["usage"]
print(f"消耗 token: {usage['total_tokens']}")
```

### 2.2 安全取值

嵌套层级多的时候，中间任何一层可能缺失，直接访问会 `KeyError`。

```python
# ❌ 不安全：如果 choices 为空会报 IndexError
content = response["choices"][0]["message"]["content"]

# ✅ 安全取值方式一：逐层 get
choices = response.get("choices", [])
if choices:
    content = choices[0].get("message", {}).get("content", "")
else:
    content = ""


# ✅ 安全取值方式二：try/except
def safe_get_content(resp: dict) -> str:
    """从 API 响应中安全提取内容"""
    try:
        return resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""


# ✅ 安全取值方式三：封装工具函数
def get_nested(data: dict, *keys, default=None):
    """安全获取嵌套字典中的值"""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        elif isinstance(current, list) and isinstance(key, int):
            current = current[key] if 0 <= key < len(current) else default
        else:
            return default
        if current is default:
            return default
    return current


content = get_nested(response, "choices", 0, "message", "content", default="")
tokens = get_nested(response, "usage", "total_tokens", default=0)
```

### 2.3 自定义序列化

`json.dumps()` 默认只能序列化基础类型。遇到 `datetime`、`Enum`、`dataclass` 等需要自定义处理。

```python
import json
from datetime import datetime
from enum import StrEnum
from dataclasses import dataclass, asdict


class ModelProvider(StrEnum):
    OPENAI = "openai"
    CLAUDE = "claude"


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime


# ❌ 直接序列化报错
msg = Message(role="user", content="你好", timestamp=datetime.now())
# json.dumps(msg)  # TypeError: Object of type Message is not JSON serializable


# ✅ 方式一：default 参数（推荐，简单场景）
def json_serializer(obj):
    """自定义序列化：处理 json.dumps 不认识的类型"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, StrEnum):
        return obj.value
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"类型 {type(obj)} 无法序列化")


result = json.dumps(
    asdict(msg),
    default=json_serializer,
    ensure_ascii=False,
    indent=2,
)
print(result)


# ✅ 方式二：JSONEncoder 子类（复杂场景）
class AppJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, StrEnum):
            return obj.value
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return super().default(obj)


result = json.dumps(msg, cls=AppJSONEncoder, ensure_ascii=False, indent=2)
```

> **与 JS 对比**：JS 的 `JSON.stringify()` 支持 `replacer` 参数，作用类似 Python 的 `default`。

---

## 3. HTTP 基础概念 📌

> 作为前端开发者你已经熟悉 HTTP，这里从 Python 视角快速复习。

### 3.1 请求方法

| 方法 | 用途 | AI 应用场景 |
|------|------|------------|
| GET | 获取资源 | 获取模型列表、查询状态 |
| POST | 创建/提交 | **调用 LLM API**（最常用） |
| PUT | 更新资源 | 更新配置 |
| DELETE | 删除资源 | 删除对话 |

### 3.2 请求结构

```
POST /v1/chat/completions HTTP/1.1     ← 请求行
Host: api.openai.com                    ← 请求头
Content-Type: application/json
Authorization: Bearer sk-xxx

{                                       ← 请求体（JSON）
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "你好"}]
}
```

### 3.3 常用请求头

| 请求头 | 说明 | 示例 |
|-------|------|------|
| `Content-Type` | 请求体格式 | `application/json` |
| `Authorization` | 认证信息 | `Bearer sk-xxx` |
| `Accept` | 期望响应格式 | `application/json` |
| `User-Agent` | 客户端标识 | `my-app/1.0` |

### 3.4 状态码

| 状态码 | 含义 | AI API 场景 |
|--------|------|------------|
| 200 | 成功 | 正常响应 |
| 400 | 请求错误 | 参数格式错误 |
| 401 | 未认证 | API Key 无效 |
| 403 | 禁止访问 | 无权限 |
| 404 | 未找到 | 模型不存在 |
| 429 | 请求过多 | **触发速率限制**（很常见） |
| 500 | 服务器错误 | 模型服务异常 |
| 503 | 服务不可用 | 模型过载 |

### 3.5 JSON API 交互流程

```
客户端                                     服务端（LLM API）
  │                                           │
  │  1. 构造请求（headers + JSON body）        │
  │ ─────────────────────────────────────────→ │
  │                                           │
  │  2. 服务端处理（模型推理）                   │
  │                                           │
  │  3. 返回响应（status code + JSON body）     │
  │ ←───────────────────────────────────────── │
  │                                           │
  │  4. 解析响应 JSON，提取内容                  │
  │                                           │
```

---

## 4. requests 库 📌

> `requests` 是 Python 最流行的 HTTP 库，API 简洁直观。

### 4.1 安装

```bash
pip install requests
```

### 4.2 GET 请求

```python
import requests

# 基础 GET
response = requests.get("https://httpbin.org/get")
print(response.status_code)  # 200
print(response.json())       # 解析 JSON 响应

# 带查询参数
response = requests.get(
    "https://httpbin.org/get",
    params={"name": "张三", "page": 1}
)
# 实际请求：https://httpbin.org/get?name=张三&page=1
print(response.json()["args"])  # {"name": "张三", "page": "1"}
```

### 4.3 POST 请求

```python
import requests

# 发送 JSON 数据（最常用）
response = requests.post(
    "https://httpbin.org/post",
    json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "你好"}]
    }
)
data = response.json()
print(data["json"])  # 服务端收到的 JSON 数据

# 自定义请求头
response = requests.post(
    "https://httpbin.org/post",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-test-key",
    },
    json={"prompt": "Hello"}
)
```

> **`json=` vs `data=`**：
> - `json=dict` → 自动序列化为 JSON，自动设置 `Content-Type: application/json`
> - `data=str` → 发送原始字符串/表单数据

### 4.4 响应对象

```python
import requests

response = requests.get("https://httpbin.org/get")

# 常用属性
response.status_code    # 状态码：200
response.ok             # 是否成功（status_code < 400）
response.json()         # 解析 JSON → dict
response.text           # 原始文本
response.headers        # 响应头（dict-like）
response.url            # 实际请求的 URL
response.elapsed        # 请求耗时

print(f"状态: {response.status_code}")
print(f"耗时: {response.elapsed.total_seconds():.2f}s")
```

### 4.5 超时与异常处理

```python
import requests
from requests.exceptions import ConnectionError, Timeout, HTTPError

# 设置超时（秒）
try:
    response = requests.get("https://httpbin.org/delay/5", timeout=3)
except Timeout:
    print("请求超时")

# 完整的异常处理
def safe_request(url: str, **kwargs) -> dict | None:
    """安全地发送请求，统一处理异常"""
    try:
        response = requests.get(url, timeout=10, **kwargs)
        response.raise_for_status()  # 4xx/5xx 会抛出 HTTPError
        return response.json()
    except ConnectionError:
        print(f"连接失败: {url}")
    except Timeout:
        print(f"请求超时: {url}")
    except HTTPError as e:
        print(f"HTTP 错误 {e.response.status_code}: {e}")
    except Exception as e:
        print(f"未知错误: {e}")
    return None
```

### 4.6 Session 复用

多次请求同一个 API 时，用 Session 复用连接和配置：

```python
import requests

# 不用 Session：每次请求都要写 headers
requests.get("https://api.example.com/a", headers={"Authorization": "Bearer sk-xxx"})
requests.get("https://api.example.com/b", headers={"Authorization": "Bearer sk-xxx"})

# 用 Session：配置一次，所有请求共享
session = requests.Session()
session.headers.update({
    "Authorization": "Bearer sk-xxx",
    "Content-Type": "application/json",
})

response = session.get("https://api.example.com/a")
response = session.get("https://api.example.com/b")

# 推荐用 with 语句自动关闭
with requests.Session() as session:
    session.headers.update({"Authorization": "Bearer sk-xxx"})
    response = session.post("https://api.example.com/chat", json={...})
```

---

## 5. httpx 库（推荐） 📌

> `httpx` 是现代 Python HTTP 库，API 与 requests 几乎一致，但**原生支持异步**。AI 应用开发推荐使用。

### 5.1 安装

```bash
pip install httpx
```

### 5.2 requests vs httpx 对比

| 特性 | requests | httpx |
|------|---------|-------|
| 同步请求 | ✅ | ✅ |
| 异步请求 | ❌ | ✅（原生支持） |
| API 风格 | 经典 | 与 requests 几乎一致 |
| HTTP/2 | ❌ | ✅ |
| 超时默认值 | 无（可能无限等待） | 无（但推荐显式设置） |
| 生态 | 最广泛 | 快速增长 |
| AI 应用推荐 | 了解 | **推荐** |

### 5.3 同步用法

```python
import httpx

# 基础 GET — 和 requests 几乎一样
response = httpx.get("https://httpbin.org/get")
print(response.status_code)
print(response.json())

# POST JSON
response = httpx.post(
    "https://httpbin.org/post",
    json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "你好"}]},
    headers={"Authorization": "Bearer sk-test"},
    timeout=30.0,
)

# Client（类似 requests.Session）
with httpx.Client(
    base_url="https://httpbin.org",
    headers={"Authorization": "Bearer sk-test"},
    timeout=30.0,
) as client:
    r1 = client.get("/get")
    r2 = client.post("/post", json={"key": "value"})
```

### 5.4 异步预览

> 异步详细内容在第 10 节学习，这里先了解基本写法。

```python
import httpx
import asyncio


async def fetch_data():
    """异步请求示例"""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://httpbin.org/get")
        return response.json()


# 运行异步函数
result = asyncio.run(fetch_data())
print(result)
```

> **为什么 AI 应用推荐 httpx？**
>
> LLM API 调用通常需要等待几秒到几十秒。如果用同步请求，程序只能傻等。用异步请求，等待时可以做别的事（比如同时请求多个模型、处理其他用户请求）。httpx 原生支持异步，不需要装额外的库。

---

## 6. 实战：模拟 LLM API 调用 📌 🔗

用 httpbin.org 模拟一次完整的 LLM API 调用流程。

### 6.1 构造请求

```python
import httpx

api_url = "https://httpbin.org/post"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-test-key-12345",
}

# 模拟 OpenAI Chat Completion 请求格式
request_body = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "你是一个有用的助手"},
        {"role": "user", "content": "用一句话介绍 Python"},
    ],
    "temperature": 0.7,
    "max_tokens": 100,
}

response = httpx.post(api_url, headers=headers, json=request_body, timeout=30.0)
```

### 6.2 解析响应

```python
if response.status_code == 200:
    data = response.json()

    # httpbin.org 会把我们发送的 JSON 放在 data["json"] 中
    sent_data = data["json"]
    print(f"模型: {sent_data['model']}")
    print(f"消息数: {len(sent_data['messages'])}")

    # 验证 Authorization 头是否正确发送
    auth = data["headers"].get("Authorization", "")
    print(f"认证头: {auth[:20]}...")
else:
    print(f"请求失败: {response.status_code}")
```

### 6.3 完整封装

```python
import httpx


def call_llm_api(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    api_key: str = "sk-test",
    base_url: str = "https://httpbin.org/post",
) -> dict | None:
    """
    模拟调用 LLM API

    Args:
        messages: 消息列表 [{"role": "user", "content": "..."}]
        model: 模型名称
        api_key: API Key
        base_url: API 地址

    Returns:
        响应 dict 或 None（失败时）
    """
    try:
        response = httpx.post(
            base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "model": model,
                "messages": messages,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        print("⏰ 请求超时")
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP 错误: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"❌ 请求失败: {e}")
    return None


# 使用
result = call_llm_api(
    messages=[{"role": "user", "content": "你好"}],
    model="gpt-4o-mini",
)
if result:
    print("调用成功")
```

---

## 7. 小结

### 核心知识

| 知识点 | 优先级 | 一句话总结 |
|--------|-------|-----------|
| JSON 嵌套处理 | 📌 | 多层 `get()` 安全取值，或 try/except 兜底 |
| 自定义序列化 | 📌 | `default` 参数处理 datetime/Enum/dataclass |
| HTTP 方法 | 📌 | POST + JSON 是调用 LLM API 的核心方式 |
| 状态码 | 📌 | 200 成功、401 无权限、429 限速、500 服务器错误 |
| requests | 📌 | `requests.post(url, json=data, headers=h, timeout=t)` |
| httpx | 📌 | API 同 requests + 原生 async，AI 应用推荐 |
| Session / Client | 📌 | 复用连接和配置，多次请求时使用 |
| 超时与重试 | 📌 | 永远设置 timeout，异常用 try/except 处理 |

### 与 JavaScript 关键差异

| 差异点 | JavaScript | Python |
|--------|-----------|--------|
| HTTP 请求 | `fetch()` / `axios` | `requests` / `httpx` |
| JSON 解析 | `JSON.parse(str)` | `json.loads(str)` |
| JSON 序列化 | `JSON.stringify(obj, replacer)` | `json.dumps(obj, default=fn)` |
| 响应解析 | `await resp.json()` | `response.json()` |
| 异步请求 | `fetch` 天然异步 | `httpx.AsyncClient` + `await` |
| 超时设置 | `AbortController` + `signal` | `timeout=30` 参数 |
| Session | axios `create()` 实例 | `requests.Session()` / `httpx.Client()` |

### 下一节预告

下一节 **异步编程**（第 10 节）将深入 `async/await`，学习并发调用多个 API 和异步 HTTP 请求。

---

## 8. 常见问题

### Q: requests 和 httpx 选哪个？

**学习阶段两个都写一遍**，理解它们 API 几乎一致。实际项目中：
- 简单脚本、没有异步需求 → requests（生态更广）
- AI 应用、需要异步 → httpx（原生 async）
- 面试准备 → 两个都要了解

### Q: json= 和 data= 有什么区别？

```python
# json= ：自动序列化 + 自动设 Content-Type
requests.post(url, json={"key": "value"})
# 等价于：
requests.post(url, data=json.dumps({"key": "value"}),
              headers={"Content-Type": "application/json"})

# data= ：发送原始数据
requests.post(url, data="raw string")
requests.post(url, data={"field": "value"})  # 表单格式
```

调用 LLM API 时**永远用 `json=`**。

### Q: 为什么请求总是超时？

常见原因：
1. **没设置代理**：国内访问 OpenAI 等需要代理
2. **timeout 太短**：LLM API 推理可能需要 10-60 秒
3. **网络问题**：先用 `httpbin.org` 测试网络是否通

```python
# 建议设置较长的超时
response = httpx.post(url, json=data, timeout=60.0)

# 或分别设置连接超时和读取超时
response = httpx.post(url, json=data, timeout=httpx.Timeout(5.0, read=60.0))
```

### Q: response.json() 报错怎么办？

说明响应内容不是合法 JSON，先检查原始内容：

```python
response = httpx.get(url)
print(response.status_code)
print(response.text[:200])  # 先看前 200 字符

# 确认是 JSON 再解析
if "application/json" in response.headers.get("content-type", ""):
    data = response.json()
else:
    print(f"响应不是 JSON: {response.text[:100]}")
```

### Q: 如何处理 429（速率限制）？

LLM API 很容易触发 429，需要做重试：

```python
import time
import httpx

def request_with_retry(url, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        response = httpx.post(url, **kwargs)
        if response.status_code == 429:
            wait = 2 ** attempt  # 指数退避：1s, 2s, 4s
            print(f"触发限速，{wait}s 后重试...")
            time.sleep(wait)
            continue
        return response
    raise Exception(f"重试 {max_retries} 次后仍然失败")
```

### Q: 怎么看请求到底发了什么？

用 httpbin.org 调试——它会把你的请求原样返回：

```python
# httpbin.org 会回显你发送的所有内容
response = httpx.post(
    "https://httpbin.org/post",
    headers={"Authorization": "Bearer test"},
    json={"model": "gpt-4o-mini"},
)
data = response.json()
print(data["headers"])  # 你发送的请求头
print(data["json"])     # 你发送的 JSON 数据
```
