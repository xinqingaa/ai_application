# 09. JSON 与 HTTP 请求 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/01_python/09_json_http.md) 一步步动手操作

---

## 核心原则

```
读文档 → 看对应代码 → 运行验证 → 理解原理
```

- 在 `source/01_python/09_json_http/` 目录下操作
- 每个练习文件独立可运行，无包依赖关系
- 练习 1 纯本地，练习 2-5 需要联网（访问 httpbin.org）

---

## 项目结构

```
09_json_http/
├── README.md                ← 你正在读的这个文件
├── json_advanced.py         ← 第 1 步：JSON 深入（文档第 2 章）
├── http_requests.py         ← 第 2 步：requests 库（文档第 4 章）
├── httpx_client.py          ← 第 3 步：httpx 库（文档第 5 章）
├── public_api.py            ← 第 4 步：调用公开 API（文档第 4-5 章综合）
└── http_client_class.py     ← 第 5 步：封装 HTTP 客户端（文档第 6 章）
```

---

## 前置准备

### 1. 安装依赖

```bash
pip install requests httpx
```

### 2. 运行方式

```bash
cd source/01_python/09_json_http

# 每个文件独立运行，都有交互式菜单
python json_advanced.py       # 选 a 运行全部
python http_requests.py
python httpx_client.py
python public_api.py
python http_client_class.py
```

---

## 第 1 步：JSON 深入（文档第 2 章）

**对应文件**：`json_advanced.py`
**对应文档**：第 2 章「JSON 深入」

不需要联网，纯本地运行。

### 操作流程

1. 读文档 2.1 节「复杂嵌套结构处理」，理解 LLM API 返回的 JSON 结构

2. 打开 `json_advanced.py`，看 `MOCK_API_RESPONSE`（第 17 行），这是模拟的 OpenAI 响应格式

3. 看 `demo_nested_access()` 函数，对比文档中的三种安全取值方式：
   - 直接访问：`resp["choices"][0]["message"]["content"]`
   - get_nested 工具函数：`get_nested(resp, "choices", 0, "message", "content", default="")`
   - try/except：文档中的 `safe_get_content()`

4. 看 `demo_data_extraction()`，从嵌套数据中提取和统计（列表推导式、Counter）

5. 读文档 2.3 节「自定义序列化」

6. 看 `demo_custom_serialization()`，对比两种方式：
   - `json.dumps(data, default=json_serializer)` — default 参数
   - `json.dumps(data, cls=AppJSONEncoder)` — JSONEncoder 子类

7. 运行验证：

```bash
python json_advanced.py
```

---

## 第 2 步：requests 库（文档第 4 章）

**对应文件**：`http_requests.py`
**对应文档**：第 4 章「requests 库」

需要联网（httpbin.org）。

### 操作流程

1. 读文档 4.1 节「安装」，确保 `pip install requests` 完成

2. 读文档 4.2 节「GET 请求」，打开 `http_requests.py` 看 `demo_get_basic()` 和 `demo_get_with_params()`

3. 读文档 4.3 节「POST 请求」，看 `demo_post_json()`——重点理解：
   - `json=payload` 自动序列化 + 设置 Content-Type
   - `headers={"Authorization": "Bearer sk-test-key"}` 鉴权

4. 读文档 4.4 节「响应对象」，看 `demo_response_details()`

5. 读文档 4.5 节「超时与异常处理」，看 `demo_error_handling()` 和 `safe_request()` 函数

6. 读文档 4.6 节「Session 复用」，看 `demo_session()`

7. 运行验证（需要联网）：

```bash
python http_requests.py
# 输入 a 运行全部
```

---

## 第 3 步：httpx 库（文档第 5 章）

**对应文件**：`httpx_client.py`
**对应文档**：第 5 章「httpx 库（推荐）」

需要联网。

### 操作流程

1. 读文档 5.1-5.2 节，理解 httpx 和 requests 的区别：
   - API 几乎一致
   - httpx 原生支持异步
   - httpx 支持 HTTP/2

2. 看 `demo_sync_get()` 和 `demo_sync_post()`，和 requests 对比——写法几乎一样

3. 看 `demo_client()`——httpx.Client 类似 requests.Session：
   - `base_url` 统一前缀
   - `headers` 统一请求头
   - `timeout` 统一超时

4. 看 `demo_error_handling()`——httpx 的异常类型：
   - `httpx.TimeoutException` 超时
   - `httpx.HTTPStatusError` 状态码错误
   - `httpx.ConnectError` 连接失败
   - `httpx.RequestError` 所有请求错误的父类

5. 看 `demo_timeout_config()`——细粒度超时配置（AI 应用推荐）：
   ```python
   httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)
   ```
   LLM API 推理可能需要几十秒，`read` 要设长一点。

6. 看 `demo_async_preview()`——异步预览（第 10 节详细学），先了解：
   - `httpx.AsyncClient` 异步客户端
   - `asyncio.gather()` 并发请求

7. 看 `demo_comparison()`——requests vs httpx 同场对比

8. 运行验证：

```bash
python httpx_client.py
# 输入 a 运行全部
```

---

## 第 4 步：调用公开 API（文档第 4-5 章综合）

**对应文件**：`public_api.py`

需要联网。用免费公开 API 实战，不需要 API Key。

### 操作流程

1. 看 `demo_uuid()` 和 `demo_ip()`——最简单的 GET 请求，热身

2. 看 `demo_jsonplaceholder()`——完整 CRUD 演示：
   - GET 列表（带 `_limit` 参数）
   - GET 单条
   - POST 创建
   - 这就是调用 REST API 的标准流程

3. 看 `demo_status_codes()`——一次性测试 200-503 各种状态码，直观理解

4. 看 `demo_delay()`——延迟和超时测试：
   - 正常延迟 1 秒
   - 设置 2 秒超时，请求 5 秒延迟 → 必定超时

5. 看 `demo_error_handling()`——完整的错误处理实战，统一处理各种异常

6. 运行验证：

```bash
python public_api.py
# 输入 a 运行全部
```

---

## 第 5 步：封装 HTTP 客户端（文档第 6 章）

**对应文件**：`http_client_class.py`
**对应文档**：第 6 章「实战：模拟 LLM API 调用」

需要联网。这是本节最重要的练习——封装一个可复用的 HTTP 客户端。

### 操作流程

1. 看 `HttpResponse` dataclass（第 17 行）——统一的响应结构：
   - `status_code`、`data`、`error`、`elapsed_ms`、`headers`
   - `ok` property 判断是否成功

2. 看 `SimpleHttpClient` 类——核心设计：
   - `__init__`：配置 base_url、headers、timeout、重试次数
   - `_make_request`：核心方法，统一处理重试（指数退避）、错误、超时
   - `get/post/put/delete`：对外暴露的简洁 API

3. 重点看 `_make_request` 的重试逻辑：
   ```python
   if response.status_code in retry_on and attempt < self.max_retries - 1:
       wait = 2 ** attempt  # 指数退避：1s, 2s, 4s
       time.sleep(wait)
       continue
   ```
   429（限速）和 500/502/503（服务器错误）会自动重试。

4. 看 `demo_simulate_llm_api()`——模拟 LLM API 调用：
   - 构造类似 OpenAI 的请求体
   - 设置 Authorization 头
   - 如果把 `base_url` 改成 `https://api.openai.com/v1`，path 改成 `/chat/completions`，就是真正的 API 调用

5. 运行验证：

```bash
python http_client_class.py
# 输入 a 运行全部
```

**关键理解**：这个 `SimpleHttpClient` 的设计模式和后续调用真实 LLM API 的方式完全一致——base_url + headers + json body + timeout + 重试。

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 | 是否联网 |
|---------|---------|---------|---------|
| 第 2 章：JSON 深入 | 嵌套取值、自定义序列化 | `json_advanced.py` | 否 |
| 第 3 章：HTTP 基础 | 方法、状态码、请求结构 | 结合 `public_api.py` 的状态码测试理解 | 是 |
| 第 4 章：requests | GET/POST、异常、Session | `http_requests.py` | 是 |
| 第 5 章：httpx | 同步/异步、Client | `httpx_client.py` | 是 |
| 第 6 章：实战 | 模拟 LLM API 调用 | `http_client_class.py` | 是 |

---

## 学习顺序总结

| 顺序 | 文件 | 核心内容 | 联网 | 运行命令 |
|-----|------|---------|------|---------|
| 1 | `json_advanced.py` | JSON 嵌套、自定义序列化 | 否 | `python json_advanced.py` |
| 2 | `http_requests.py` | requests 库全套用法 | 是 | `python http_requests.py` |
| 3 | `httpx_client.py` | httpx + 异步预览 | 是 | `python httpx_client.py` |
| 4 | `public_api.py` | 真实 API 调用实战 | 是 | `python public_api.py` |
| 5 | `http_client_class.py` | 封装可复用客户端 | 是 | `python http_client_class.py` |

---

## 注意事项

- **练习 1 可以离线完成**，其余都需要联网
- **httpbin.org 偶尔会慢**，耐心等待或稍后重试
- **httpbin.org 是调试用的**——它会把你的请求原样返回，方便查看 headers 和 body 是否正确
- **`json=` vs `data=`**：调用 LLM API 时永远用 `json=`，自动序列化 + 设置 Content-Type
- **超时设置**：LLM API 推理可能需要 10-60 秒，`timeout` 要设长一点（推荐 60 秒）
- **429 限速**：LLM API 很容易触发，需要做重试（指数退避）
