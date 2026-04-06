# 05. 流式输出与 FastAPI - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/02_llm/05_streaming_fastapi.md) 一步步完成第五章实践

---

## 核心原则

```text
先理解流式输出为什么有用 -> 再跑最小流式脚本 -> 再启动普通聊天 API -> 最后启动 SSE 流式接口
```

- 在 `source/02_llm/05_streaming_fastapi/` 目录下操作
- 这一章的重点不是“把结果拆成几段打印出来”，而是理解流式输出如何改善用户体验，以及服务端应该怎样把流式事件稳定地暴露给前端
- 没有 API Key 时，也可以用 mock 模式完成大部分学习，包括首字延迟、SSE 事件格式、心跳事件和会话管理
- 有真实模型时，优先用百炼 / 通义、DeepSeek、GLM 做实验，重点观察首字返回时间和总耗时差异
- 流式章节默认你已经理解第 1 章的 `messages`、第 2 章的 provider 配置，以及第 4 章的 Pydantic / FastAPI 基础

---

## 项目结构

```text
05_streaming_fastapi/
├── README.md                 ← 你正在读的这个文件
├── .env.example              ← 第五章环境变量模板
├── streaming_utils.py        ← 公共工具：provider 配置、异步聊天、流式输出、SSE 编码、会话状态
├── 01_stream_basic.py        ← 第 1 步：最小流式调用（文档第 2-3 章）
├── 02_fastapi_chat.py        ← 第 2 步：普通 FastAPI 聊天接口（文档第 4-5 章）
└── 03_fastapi_stream.py      ← 第 3 步：SSE 流式聊天接口（文档第 4-6 章）
```

---

## 前置准备

### 1. 安装依赖

推荐先进入虚拟环境，再安装：

```bash
pip install openai python-dotenv fastapi uvicorn
```

如果你想更准确地观察 token 估算，可以额外安装：

```bash
pip install tiktoken
```

### 2. 配置环境变量

把 `.env.example` 复制为 `.env`，按你当前可用的平台填写。

第五章建议优先完成两类实验：

1. 用 mock 模式理解流式事件链路和 FastAPI 接口结构
2. 用真实 provider 对比“首字到达时间”和“整段返回时间”

### 3. 运行方式

```bash
cd source/02_llm/05_streaming_fastapi

python 01_stream_basic.py

uvicorn 02_fastapi_chat:app --reload --port 8000
uvicorn 03_fastapi_stream:app --reload --port 8000
```

---

## 第 1 步：最小流式调用（文档第 2-3 章）

**对应文件**：`01_stream_basic.py`  
**对应文档**：第 2 章「为什么流式输出能改善体验」+ 第 3 章「OpenAI 风格流式调用」

### 这一步要解决什么

很多人知道 `stream=True` 可以流式输出，但没有真正看过：

1. token 是怎么一段段到达的
2. 为什么用户会感觉“更快”
3. 什么叫首字耗时和整段耗时

### 操作流程

1. 先读文档第 2-3 章。
2. 打开 `01_stream_basic.py`，重点看：
   - `stream_chat_events()`
   - `StreamSummary`
3. 运行：

```bash
python 01_stream_basic.py
```

### 重点观察

- 输出是否是一段段出现，而不是整段一次返回
- `first_token_ms` 和 `elapsed_ms` 分别代表什么
- 为什么即使总耗时差不多，流式输出仍然显得更快
- mock 模式下的 chunk 粒度是什么样

### 建议主动修改

- 改 `USER_PROMPT`
- 改 `temperature`
- 让输出更长一些，观察 chunk 数变化
- 真 key 环境下对比不同 provider 的首字耗时

---

## 第 2 步：普通 FastAPI 聊天接口（文档第 4-5 章）

**对应文件**：`02_fastapi_chat.py`  
**对应文档**：第 4 章「为什么要先有非流式 API」+ 第 5 章「FastAPI 中的聊天请求与会话状态」

### 这一步要解决什么

流式接口不是凭空出现的。在工程上，通常应该先有一个普通聊天接口，先把这些事情稳定下来：

- 请求体长什么样
- 会话历史怎么保存
- 如何切换 provider
- 如何返回元信息

### 操作流程

1. 先读文档第 4-5 章。
2. 启动服务：

```bash
uvicorn 02_fastapi_chat:app --reload --port 8000
```

3. 浏览器打开：

```text
http://localhost:8000/docs
```

4. 在 `/docs` 里重点测试：
   - `GET /health`
   - `POST /chat`
   - `GET /sessions/{session_id}`

### 重点观察

- `ChatRequest` 如何承载 `message / session_id / provider / system_prompt`
- `POST /chat` 返回了哪些对调试有用的信息
- 为什么接口返回里保留了 `request_preview`
- `session_estimated_tokens` 会随着历史增长而增加

### 建议主动修改

- 连续向同一个 `session_id` 发两轮消息
- 切换不同 `system_prompt`
- 故意把 `keep_last_messages` 调小，观察历史裁剪
- 切不同 provider，看 `request_preview` 是否变化

---

## 第 3 步：SSE 流式聊天接口（文档第 6 章）

**对应文件**：`03_fastapi_stream.py`  
**对应文档**：第 6 章「SSE 流式接口、事件格式与心跳保活」

### 这一步要解决什么

真正前端对接流式体验时，服务端不只是“把 token 打印出来”，还要解决：

- 如何编码 SSE 事件
- 如何逐条返回给前端
- 如何在等待阶段发送心跳
- 如何在流结束时返回统计信息

### 操作流程

1. 先读文档第 6 章。
2. 启动服务：

```bash
uvicorn 03_fastapi_stream:app --reload --port 8000
```

3. 浏览器打开 `/docs`，先测试：
   - `POST /chat`
   - `GET /sessions/{session_id}`

4. 再用 `curl` 测试 SSE：

```bash
curl -N http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "message": "请解释流式输出为什么能提升聊天体验",
    "heartbeat_seconds": 1.5
  }'
```

### 重点观察

- `event: start / token / ping / done` 的区别
- 为什么 `StreamingResponse` 返回的是异步生成器
- 心跳事件在什么情况下会出现
- `done` 事件里为什么要返回 `first_token_ms / elapsed_ms / chunk_count`

### 建议主动修改

- 把 `heartbeat_seconds` 调大或调小
- 使用同一个 `session_id` 连续发两次流式请求
- 把 `system_prompt` 改成更严格的助手风格
- 自己写一个前端 `fetch + ReadableStream` 或 `EventSource` 客户端去消费 SSE

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 |
|---------|---------|---------|
| 第 2-3 章 | 流式输出价值、最小流式调用、首字耗时 | `01_stream_basic.py`, `streaming_utils.py` |
| 第 4-5 章 | 普通聊天 API、会话状态、请求体验证 | `02_fastapi_chat.py`, `streaming_utils.py` |
| 第 6 章 | SSE、StreamingResponse、心跳、done 事件 | `03_fastapi_stream.py`, `streaming_utils.py` |

---

## 建议的学习顺序

1. 先跑 `01_stream_basic.py`
2. 再启动 `02_fastapi_chat.py`
3. 最后启动 `03_fastapi_stream.py`

这个顺序对应的能力递进是：

1. 先理解流式是什么
2. 再理解聊天接口怎么组织
3. 最后理解如何把流式结果变成前后端都能消费的 SSE 服务

---

## 常见问题

### 1. 第五章是不是只要学 `stream=True` 就够了？

不够。`stream=True` 只是模型 SDK 这一层。真正上线时，你还需要解决：

- 服务端怎么把 chunk 转成 SSE
- 前端怎么消费
- 怎么处理心跳和中断
- 怎么保存完整响应

### 2. 为什么先写普通 `/chat` 再写 `/chat/stream`？

因为流式接口应该建立在稳定的普通聊天接口之上。请求体、会话管理、provider 切换这些基础不稳定时，直接上流式只会让排错更难。

### 3. 没有真实 API Key 能学吗？

能。mock 模式已经足够帮你理解：

- chunk 到达
- SSE 事件编码
- 心跳事件
- 会话保存

真实 API 主要用来观察不同 provider 的首字速度和总耗时差异。

### 4. `EventSource` 能直接发 POST 吗？

不能。浏览器原生 `EventSource` 主要是 GET。真实项目里如果你要带请求体，前端更常用的是 `fetch + ReadableStream`。课程里先用 `curl -N` 和服务端生成器把核心链路讲透。

---

## 建议你自己追加的练习

1. 在 `03_fastapi_stream.py` 里给 `done` 事件增加 `request_preview`。
2. 自己写一个最小前端页面，用 `fetch` 消费 `/chat/stream`。
3. 给会话状态增加“导出 JSON”功能。
4. 记录每次流式请求的首字耗时和总耗时，做一个简单对比表。
5. 尝试增加“客户端主动取消流式请求”的处理逻辑。

如果你把这五件事做完，第五章就不只是“知道 SSE 是什么”，而是真正具备把流式聊天接口接给前端的能力。
