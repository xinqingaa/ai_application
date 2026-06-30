# 02_llm_streaming_api

`02_llm/04` 的本地 FastAPI SSE 观察入口。它启动一个只在本机运行的轻量服务，把 `llm_core.stream_chat` 产生的统一事件编码成 `text/event-stream`，用于理解 AI 应用前端如何消费模型运行态。

课程正文负责讲 Streaming / Conversation 的原理；本 README 负责运行、读代码和看输出。

## 能力边界

本 app 做：

- LLM token stream → `LLMStreamEvent`
- `LLMStreamEvent` → SSE
- 简单 `session_id` 会话缓存
- 浏览器打字机效果与终端原始 SSE 观察

本 app 不做：

- RAG 检索事件
- Tool / Agent / Workflow 真实运行时
- 生产级会话存储
- 鉴权、限流、取消和重试治理

## 前置

```bash
# 仓库根目录
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # 填写 OPENAI_API_KEY
```

## 启动

```bash
uvicorn main:app --app-dir source/apps/02_llm_streaming_api --reload --port 8004
```

这条命令会在本机启动一个 FastAPI 服务：

| 地址 | 用途 |
| --- | --- |
| `http://127.0.0.1:8004/` | 简单浏览器页面，展示打字机效果 |
| `http://127.0.0.1:8004/api/review/stream` | SSE 接口，前端实际消费的事件流 |
| `http://127.0.0.1:8004/health` | 健康检查 |

健康检查：

```bash
curl http://127.0.0.1:8004/health
```

## 浏览器观察

打开：

```text
http://127.0.0.1:8004/
```

点击 `Start` 后，页面会按 `token.delta` 展示打字机效果。点击 `Stop` 会关闭当前 `EventSource`，前端停止接收后续事件；生产级服务端取消、断点恢复和重试治理放到后续可靠性专题。

建议同时打开浏览器开发者工具：

1. 切到 `Network`。
2. 点击 `Start`。
3. 找到 `/api/review/stream?...` 请求。
4. 观察响应头 `content-type: text/event-stream`，以及持续到达的 `event:` / `data:`。

## 终端观察原始 SSE

终端适合观察协议原文，因此会看到 `id:`、`event:`、`data:` 多行结构；它不是最终用户交互形态。

```bash
curl -N "http://127.0.0.1:8004/api/review/stream?sample_id=S2&session_id=demo"
```

应看到类似事件：

```text
event: message_start
data: {"type": "message_start", ...}

event: token
data: {"type": "token", "delta": "风险", ...}

event: message_done
data: {"type": "message_done", "content": "...", ...}

event: done
data: {"type": "done", ...}
```

## 读代码顺序

1. [`llm_core/streaming.py`](../../packages/llm_core/streaming.py)：`LLMStreamEvent` 与 `encode_sse`。
2. [`llm_core/providers/openai_compat.py`](../../packages/llm_core/providers/openai_compat.py)：OpenAI-compatible chunk 如何转成事件。
3. [`llm_core/client.py`](../../packages/llm_core/client.py)：`LLMClient.stream_chat` 如何保持统一入口。
4. [`main.py`](main.py)：FastAPI `StreamingResponse` 如何返回 SSE。
5. [`index.html`](index.html)：浏览器如何用 `EventSource` 开始、停止和展示打字机效果。
6. [`llm_core/conversation.py`](../../packages/llm_core/conversation.py)：哪些消息进入 history。

## 输出怎么看

| 字段 | 含义 |
| --- | --- |
| `type` | 事件类型。前端按它分发 UI 状态 |
| `run_id` | 一次流式调用的运行 id。一次点击 Start 生成一个新的 run |
| `sequence` | 单次运行内递增序号。用于排查乱序、丢事件和调试日志 |
| `delta` | 单个 token / 文本片段。只在 `token` 常见，用于打字机追加 |
| `content` | 聚合后的最终 assistant 消息。只在 `message_done` 常见，用于保存 history |
| `code` / `message` | 错误事件的错误码和原因。用于展示失败状态和排查 |
| `provider` / `model` / `config_ref` | 实际调用来源。用于确认模型配置是否符合预期 |
| `latency_ms` | 到该事件为止的耗时。常见于 `message_done`、`error`、`done` |

前端可以实时拼接 `delta`，但最终可进入会话历史、数据库或评估样例的内容，应以 `message_done.content` 为准。

## 前端开始与停止

本 demo 使用浏览器原生 `EventSource`：

```js
const source = new EventSource("/api/review/stream?sample_id=S2&session_id=demo");

source.addEventListener("token", (event) => {
  const data = JSON.parse(event.data);
  output.textContent += data.delta || "";
});

source.addEventListener("done", () => {
  source.close();
});
```

开始 = 创建新的 `EventSource`。停止 = 调用 `source.close()`。这能停止前端继续接收；服务端是否能立刻中断模型调用，还需要断连检测、超时和取消传播，后续可靠性专题再展开。

## 常见问题

| 现象 | 优先检查 |
| --- | --- |
| 500：未配置 `OPENAI_API_KEY` | 根目录 `.env` |
| `event: error` | `data.code`，如 `auth`、`rate_limit`、`provider_error` |
| 一次性返回而不是逐 token | 当前供应商或网关可能缓冲了流 |
| 第二次请求带上历史 | `session_id` 相同会复用内存里的 `ConversationBuffer` |
| 想清空会话 | 换一个新的 `session_id` |
| 页面没有反应 | 先看浏览器 Network 中 `/api/review/stream` 的状态码和响应内容 |
