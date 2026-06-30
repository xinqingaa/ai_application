# 04. Streaming 与 Conversation

> 前三节已经解决了「能调用模型」「能稳定组织 Prompt」「能把输出变成结构化契约」。本篇回答：**模型生成过程如何变成前端可消费的实时状态**，以及多轮对话里哪些内容应该进入 history，哪些只是一次运行中的中间态。

---

## 真实问题

在 00–03 中，我们主要观察的是一次模型调用的最终结果。`LLMClient.chat` 返回 `LLMResponse`，`chat_structured` 返回 `StructuredLLMResponse`。这对后端验证很方便，但真实 AI 应用不会只在终端里等待最终文本。

需求评审助手面对的是一个持续运行的任务：用户提交 PRD 后，系统可能需要读材料、分析风险、生成建议、等待人工确认。即使本节还没有接入 RAG、Tool Calling 或 Workflow，前端也已经不能只显示一个 loading 圈，然后等 20 秒把最终回答一次性贴出来。用户需要知道：系统已经开始处理了吗？现在是否有内容生成？失败发生在调用前、生成中，还是生成后？最终进入会话历史的是哪段内容？

本节要建立的直觉是：**Streaming 不是把字符串切碎发送，Conversation 也不是把所有过程都塞进 messages**。AI 应用需要一层事件协议，把模型增量、最终消息、错误和完成状态分开；同时需要一条会话边界，只把稳定的用户消息和最终 assistant 消息放进 history。

### 学习者真实问题

如果你有前端 / Flutter / 客户端背景，流式输出很容易被理解成「后端边生成边返回文字，前端 append 到屏幕上」。这个理解能跑通最小 demo，但不足以支撑 AI Native 应用。

真实工程里，前端不是只接收一串字符，而是在维护 UI 状态机：

- 当前 run 是否开始。
- 是否正在收到 token。
- 是否已经拿到最终 assistant message。
- 错误是否发生，错误码是什么。
- 这次结果是否应该进入会话历史。
- 用户刷新、取消或重试时，应该从哪个状态恢复。

如果后端只返回裸文本流，前端很快会遇到问题：不知道第一段内容是 token 还是错误；不知道最终消息什么时候稳定；不知道一次任务是否真正完成；不知道同一个页面里多个 run 的事件是否串在一起。

所以本节不只讲 OpenAI SDK 的 `stream=True`。我们会把它放进 FastAPI SSE 中，形成更接近真实产品的链路：

```text
模型 token stream
→ llm_core 统一事件
→ FastAPI text/event-stream
→ 前端按事件更新 UI
```

### 产品真实问题

产品同学小周打开需求评审助手，选择 S2 样例：订单详情页新增「申请售后」按钮，对接售后接口 v2。她点击「开始评审」后，希望系统不要一直空白等待，而是先出现「正在分析需求」，随后风险分析内容逐步显示。

第一次做原型时，后端只提供普通 HTTP 接口。前端点击按钮后，页面进入 loading，直到模型完整生成后才显示 Markdown。这个体验有三个问题：第一，模型调用慢时用户不知道系统是否卡死；第二，网络中断时前端只能得到一个失败提示，无法知道模型是否已经生成了一部分；第三，后续要展示「正在检索知识库」「正在调用接口文档工具」「等待人工确认」时，普通最终响应无法表达这些中间状态。

于是团队决定改成流式接口。最直观的做法是后端直接把模型 token 原样转发给前端。但联调时又出现新问题：前端拿到 token 可以实时拼接文本，却不知道什么时候该把拼接结果保存为一条 assistant message；某次模型中途失败，页面上已经显示了半段风险分析，刷新后这半段到底算不算历史记录？另一次用户连续点击两次评审，两个请求的 token 混在一起，UI 无法判断哪个 token 属于哪个 run。

这些问题说明：产品需要的不只是「快一点显示文字」，而是一个稳定的运行态协议。一次评审至少要有开始、增量、最终消息、错误、结束几个状态；每个事件要带 `run_id` 和递增 `sequence`；前端可以实时展示 `delta`，但只有 `message_done.content` 才能进入会话历史或后续评估。这样用户看到的是持续反馈，工程上也能判断这次 AI 运行到底完成到了哪一步。

### 工程真实问题

从工程角度看，Streaming 与 Conversation 至少要拆开四件事：

| 概念 | 解决什么 | 本节边界 |
| --- | --- | --- |
| Token stream | 模型供应商返回的增量文本 | `OpenAICompatProvider.stream_chat` |
| Event stream | 应用暴露给前端的运行态协议 | `LLMStreamEvent` + SSE |
| Conversation history | 多轮对话中稳定的用户/assistant 消息 | `ConversationBuffer` |
| Task state | 检索、工具、工作流等中间状态 | 本节只预留思想，真实实现 defer |

这里最容易出错的是把四者混在一起：把 token 当事件，把事件当 history，把检索结果当用户消息，把工具调用过程当 assistant 最终回答。短 demo 里看不出问题，项目一旦进入 RAG、Agent 和 Workflow，这种混用会直接污染上下文，导致模型后续回答越来越乱。

---

## 基础原理

### 本节方案性质

Streaming 与 Conversation 也没有唯一标准答案。不同产品可以使用 SSE、WebSocket、HTTP chunk、移动端长连接或框架自带事件流；会话历史也可能存内存、Redis、数据库或浏览器本地缓存。本节给的是需求评审助手当前阶段的一套**推荐工程实践**，不是要求所有项目都照搬目录和字段名。

需要区分四层：

| 层级 | 本节怎么理解 |
| --- | --- |
| **通用原则** | token 流不等于业务事件流；最终可保存内容以 `message_done` 为准；history 只保存稳定消息；错误必须作为事件显式传给前端 |
| **工程实践** | 用 `LLMStreamEvent` 统一事件，用 FastAPI `StreamingResponse` 输出 SSE，用 `ConversationBuffer` 管理最小 history |
| **项目取舍** | 本节只做 LLM streaming + SSE + 内存 conversation，不做 RAG / Tool / Agent / Workflow 真实事件 |
| **非目标** | 不把 SSE 说成唯一选择；不把内存会话当生产方案；不把流式输出误认为可靠性、取消、重试都已完成 |

选择 FastAPI SSE 的原因很直接：本仓库的学习者已经有 Python 基础，后续又要做 AI Native 前端体验。与只在终端打印 token 相比，SSE 更接近真实产品中前后端的协作边界，也更适合解释「事件协议」这个核心概念。

### Streaming 是什么

**输入**：`messages` + `config_ref` + 模型参数。  
**输出**：一串有序事件，而不是一次性 `LLMResponse`。

在普通调用中，应用发出请求，然后等待最终文本：

```text
request → 等待 → LLMResponse(content="完整回答")
```

在流式调用中，应用拿到的是过程：

```text
message_start
token(delta="第一段")
token(delta="第二段")
...
message_done(content="完整回答")
done
```

注意这里的核心变化不是「返回更快」，而是**应用从最终结果模型变成运行态模型**。前端可以在 `token` 到达时增量渲染，但仍然要等待 `message_done` 才能认为 assistant message 稳定。

### Token Stream 与 Event Stream

Token stream 是模型供应商给应用的东西，event stream 是应用给前端的东西。两者不能简单画等号。

模型供应商的 chunk 通常只关心「本次 delta 是什么」。它可能不带业务状态，不保证字段形态适合前端，也不关心你的 UI 是风险卡片、时间线还是工作流面板。

应用事件则要回答前端真正需要的问题：

- 这是哪个 run 的事件？
- 事件顺序是多少？
- 这是 token、最终消息、错误，还是完成信号？
- 如果是 token，增量文本是什么？
- 如果是最终消息，完整内容是什么？
- 如果是错误，错误码和可展示原因是什么？

本节定义的 `LLMStreamEvent` 就是这层应用事件。它不是为了包装而包装，而是把供应商差异挡在后端，把前端需要的状态明确化。

### 流式事件字段如何被前端使用

前端消费 SSE 时，真正拿到的是一条条 JSON 事件。每个字段都应该服务 UI 状态或调试，而不是随便透传。

| 字段 | 前端怎么用 |
| --- | --- |
| `type` | 决定分发逻辑：开始、追加 token、保存最终消息、展示错误、结束 run |
| `run_id` | 区分一次模型运行；同一个页面同时有多个任务时，避免事件串线 |
| `sequence` | 单次 run 内递增；用于排查乱序、丢包、重复事件和日志对齐 |
| `delta` | `token` 事件里的增量文本；用于打字机效果，不应直接入库 |
| `content` | `message_done` 里的最终文本；用于保存 assistant history 或后续评估 |
| `code` / `message` | `error` 事件里的错误信息；用于展示失败状态和排查 |
| `provider` / `model` / `config_ref` | 调试模型配置是否命中预期 |
| `latency_ms` | 观察首包、完成耗时和错误发生时机 |

一个典型前端状态流是：

```text
点击 Start
→ 创建 EventSource
→ message_start：进入 running 状态
→ token：不断 append delta
→ message_done：用 content 覆盖最终文本并允许保存
→ done：关闭 EventSource，进入 completed 状态
```

点击 Stop 时，浏览器侧调用 `EventSource.close()`，前端停止接收后续事件。注意：这只保证**客户端停止消费**。生产级「用户取消后模型调用也立刻停止」还需要服务端检测断连、向 provider 传播取消、记录取消状态，这些属于 06 可靠性与后续产品工程，本节只讲最小边界。

### 为什么选择 SSE

SSE，即 Server-Sent Events，是服务端向客户端持续推送文本事件的 HTTP 协议形态。它很适合本节这种「客户端发起一次请求，服务端持续返回生成过程」的场景。

与普通 JSON 响应相比，SSE 可以让前端尽早收到 token；与 WebSocket 相比，SSE 更轻，天然是单向服务端推送，适合模型生成、检索进度和工作流运行状态这类场景。

本节不说 SSE 是唯一最佳方案。更准确地说：

- **单向生成状态**：SSE 通常足够清晰。
- **双向实时协作**：WebSocket 可能更合适。
- **移动端或网关复杂场景**：还要考虑代理缓冲、断线重连、心跳和超时。

当前需求评审助手先用 SSE，是因为它能用最少工程复杂度讲清 AI 应用的事件边界。

### 为什么本节要写一个本地服务

本节不是只给 `llm_core` 加一个 `stream_chat` 方法就结束。`llm_core` 解决的是**后端内部如何获得统一流式事件**；但学习 AI 应用时，还必须看到这些事件如何通过 HTTP 暴露给前端。因此本节额外写了一个很小的本地 FastAPI 服务。

这个服务不是完整产品后端，也不是另起一个主项目。它的职责只有三件事：

1. 接收浏览器或 `curl` 发来的评审请求。
2. 调用 `LLMClient.stream_chat`，把模型生成过程转成 `LLMStreamEvent`。
3. 通过 SSE 返回给前端，让前端能按事件更新 UI。

启动 `uvicorn main:app --app-dir source/apps/02_llm_streaming_api --reload --port 8004` 后，本机就多了一个临时服务：

| 地址 | 作用 |
| --- | --- |
| `http://127.0.0.1:8004/` | 浏览器页面，展示打字机效果 |
| `http://127.0.0.1:8004/api/review/stream` | SSE 接口，返回 `message_start / token / message_done / done` |
| `http://127.0.0.1:8004/health` | 健康检查 |

所以这条命令不是“运行一个脚本”，而是“启动一个本地 AI 应用接口”。这也是从模型调用底座走向 AI Native 前端体验的第一步。

### Conversation 不是上下文垃圾桶

Conversation 的职责是保存稳定的对话消息，不是保存所有中间过程。

本节的最小原则：

```text
进入 history：
- system prompt
- user message
- assistant 最终消息

不进入 history：
- token delta
- message_start / done
- 错误事件
- 检索过程日志
- 工具调用原始输入输出
- workflow 节点运行细节
```

为什么这么严格？因为 history 会进入下一次模型调用。只要把中间 token、工具日志或错误栈混进去，模型就可能把过程噪声当成用户意图或事实依据。

反例很常见：某次流式生成到一半失败，前端已经显示了半段「接口 v2 可能存在兼容风险」。如果后端把这半段 token 存进 history，下一轮用户问「继续分析」时，模型会把未完成内容当成已确认结论。正确做法是：中间 token 可以展示，但只有 `message_done.content` 才能进入 history。

### 从弱到强的机制递进

Streaming 与 Conversation 的工程设计可以按下面这条链理解：

**第 1 步 · 普通 HTTP 最终响应**

后端一次性返回完整文本。实现简单，但用户等待期间没有反馈，失败时也无法表达生成到了哪一步。**反例**：模型 20 秒后超时，前端只知道失败，不知道是否已经生成过部分内容。

**第 2 步 · 裸 token 流**

后端边收到模型 chunk 边转发文本。体验变好，但前端不知道事件类型、run 边界和最终完成状态。**反例**：两个请求并发时，前端无法判断 token 属于哪次 run。

**第 3 步 · 应用事件流**

后端把 chunk 转成 `message_start / token / message_done / error / done`。前端可以基于事件更新 UI 状态。**仍遗留**：事件通过什么协议传输？如何给浏览器或客户端消费？

**第 4 步 · FastAPI SSE**

应用事件用 `text/event-stream` 输出，每条事件有 `event:` 和 `data:`。浏览器、curl、移动端 HTTP 客户端都能逐步读取。**仍遗留**：取消、断线恢复、重试、持久化属于可靠性和产品工程问题，本节不展开。

**第 5 步 · Conversation 边界**

流式展示不等于全部入历史。用户消息立即进入 history，assistant 最终消息在 `message_done` 后进入 history。**仍遗留**：history 太长时如何裁剪、摘要和压缩，放到 05 Context Engineering。

这条递进的重点是：不要停在“能流式显示”。真正可维护的 AI 应用，要让前端知道事件状态，让后端知道哪些内容稳定，让后续上下文不被中间过程污染。

### 本节数据流

```text
用户选择 S2
→ FastAPI /api/review/stream
→ ConversationBuffer 追加 user message
→ LLMClient.stream_chat(messages, config_ref)
→ OpenAI-compatible stream=True
→ LLMStreamEvent
→ encode_sse
→ 前端 / curl 增量接收
→ message_done 后追加 assistant history
```

这个数据流里有一个关键点：SSE app 不直接依赖 OpenAI SDK 的 chunk。它只消费 `llm_core` 的 `LLMStreamEvent`。这样后续换 provider、加 RAG event 或接 Agent runtime 时，前端协议可以继续沿用。

---

## 最小实现

本节代码要验证两件事：

1. 模型 chunk 能被翻译成稳定应用事件。
2. FastAPI 能把这些事件作为 SSE 输出给前端。

正文只保留两个关键片段，完整代码阅读顺序见 [llm_core README](../../source/packages/llm_core/README.md) 和 [SSE app README](../../source/apps/02_llm_streaming_api/README.md)。

### 1. 统一事件对象

[`streaming.py`](../../source/packages/llm_core/streaming.py)：

```python
@dataclass(frozen=True)
class LLMStreamEvent:
    type: StreamEventType
    run_id: str
    sequence: int
    delta: Optional[str] = None
    content: Optional[str] = None
    message: Optional[str] = None
    code: Optional[str] = None
```

这段代码的重点不是字段多，而是职责清楚：

- `type` 告诉前端如何处理事件。
- `run_id` 区分一次模型运行。
- `sequence` 帮助排查乱序和丢事件。
- `delta` 是增量 token。
- `content` 是最终聚合消息。
- `code/message` 是错误事件的机器码和人类可读信息。

如果只传裸字符串，前端要靠猜；有了事件对象，UI 状态机可以按类型更新。

### 2. FastAPI SSE 输出

[`source/apps/02_llm_streaming_api/main.py`](../../source/apps/02_llm_streaming_api/main.py)：

```python
def event_stream() -> Iterator[str]:
    final_content = ""
    for event in client.stream_chat(messages, config_ref, temperature=temperature):
        if event.type == "message_done" and event.content:
            final_content = event.content
        yield encode_sse(event)
    if final_content:
        history.add_assistant(final_content)

return StreamingResponse(
    event_stream(),
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
)
```

这里有两个关键取舍。

第一，FastAPI app 只负责把事件编码成 SSE，不直接处理 SDK chunk。供应商差异留在 `llm_core.providers`，HTTP 协议留在 app 层。

第二，history 的追加发生在流结束后，并且只追加 `message_done.content`。前端可以显示 token，但后端不会把半成品 token 存成一条 assistant message。

### 3. SSE 文本形态

SSE 每条事件是文本协议，不是普通 JSON 数组。本项目的 `encode_sse` 输出形态类似：

```text
id: demo-S2-a1b2c3d4:2
event: token
data: {"type":"token","run_id":"demo-S2-a1b2c3d4","sequence":2,"delta":"风险"}
```

前端可以根据 `event` 或 `data.type` 分发。课程阶段保留两者，是为了让浏览器 `EventSource`、`fetch` 流读取和命令行 `curl -N` 都容易观察。

如果用 `curl -N` 观察，你会一直看到 `id:`、`event:`、`data:`，这正是 SSE 协议原文，不是最终交互体验。浏览器页面会把同样的 `token.delta` 渲染成打字机效果；开发者工具的 Network 面板则能看到原始事件流。

---

## 主流框架实现

| 方式 | 适合场景 | 与本节关系 |
| --- | --- | --- |
| FastAPI `StreamingResponse` + SSE | 单向生成、状态推送、浏览器和移动端易接 | 本节采用 |
| `fetch` + `ReadableStream` | 前端希望用 POST、带复杂 body 或自定义解析 | 可消费同样 SSE 文本或 NDJSON |
| WebSocket | 双向实时协作、语音、多用户协同 | 本节不需要，后续可选 |
| LangChain streaming callbacks | 框架内部模型、链路、工具回调 | 可映射到 `LLMStreamEvent` |
| LangGraph event stream | 节点级、工具级、状态机运行事件 | 后续 Agent / Workflow 再展开 |

真正要迁移的不是某个框架 API，而是事件分层：模型增量、业务事件、传输协议、前端状态各自有边界。

---

## 失败分析与能力边界

### 1. 前端能看到 token，但最终消息没有保存

- **表现**：页面实时出现了文字，刷新后历史里没有这条 assistant 回复。
- **原因**：只处理 `token`，没有等待 `message_done`；或者生成中途 `error`。
- **怎么验证**：看 SSE 是否出现 `event: message_done`，检查 `data.content` 是否存在。只有 `message_done.content` 应进入 history。

### 2. `curl` 一次性吐出整段内容

- **表现**：接口最终能返回，但不是逐 token 刷新。
- **原因**：模型供应商、代理、网关或终端缓冲了流；也可能当前模型配置不支持 streaming。
- **怎么验证**：先看 `models.yaml` 的 `capabilities.streaming`；再用 `curl -N`；如果本地 uvicorn 正常但部署后不正常，怀疑反向代理缓冲。

### 3. 两次请求的内容混在一起

- **表现**：页面同时发起两个评审，token 交错显示到同一块 UI。
- **原因**：前端没有按 `run_id` 隔离状态，或后端没有给每次 run 标识。
- **怎么验证**：检查每条 SSE 的 `run_id` 和 `sequence`。同一 UI 容器只消费同一 `run_id`。

### 4. 下一轮对话被上一轮中间过程污染

- **表现**：用户问“继续”，模型引用了半截输出、错误信息或工具日志。
- **原因**：把 token delta、error、检索日志、工具结果直接塞进 conversation history。
- **怎么验证**：打印 `ConversationBuffer.to_messages()`，确认里面只有 system、user、assistant 最终消息。

### 5. 用户取消请求后后端仍在生成

- **表现**：前端关闭页面或取消请求，后端仍然消耗 token。
- **原因**：取消和断连检测需要额外处理，不能靠最小 SSE 自动完成。
- **当节最小判断**：知道这是可靠性问题，不把它当成本节已经解决；取消、超时、重试与降级放到 06。

### 常见误区

| 误区 | 纠正 |
| --- | --- |
| 「stream=True 就等于前端实时体验」 | SDK stream 只是 token 增量，前端还需要事件协议 |
| 「SSE 只能传纯文本」 | SSE 是文本协议，`data` 可以放 JSON 字符串 |
| 「token 到了就可以保存历史」 | 只有 `message_done.content` 是稳定 assistant 消息 |
| 「Conversation 就是所有上下文」 | history、检索上下文、工具结果、workflow state 必须分层 |
| 「本节有 SSE 就等于生产可用」 | 生产还需要取消、重连、鉴权、限流、持久化和观测 |

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| 上下文预算、历史裁剪、摘要压缩 | 05 | 知道 history 不能无限增长，当前只用 `max_messages` |
| 超时、取消、重试、降级 | 06 | 能通过 `error` 事件显式暴露失败 |
| 调用记录落盘与回归对比 | 07 | 当前只观察单次 run 的事件 |
| RAG 检索进度事件 | 03_rag | 本节只做 LLM message event |
| Tool / Agent / Workflow 节点事件 | 04_agent | 本节事件协议预留扩展，不实现真实 runtime |
| 前端完整工作台 | 06_ai_native | 本节只提供可被前端消费的 SSE 接口 |

---

## 本节实战

### 目标

为需求评审助手增加一个 FastAPI SSE 入口：用户选择 PRD 样例后，后端通过 `LLMClient.stream_chat` 逐步输出事件，前端或命令行可以实时观察生成过程。

### 涉及文件

关键路径：

- [`source/packages/llm_core/streaming.py`](../../source/packages/llm_core/streaming.py)：流式事件与 SSE 编码。
- [`source/packages/llm_core/conversation.py`](../../source/packages/llm_core/conversation.py)：最小 Conversation Buffer。
- [`source/packages/llm_core/client.py`](../../source/packages/llm_core/client.py)：`LLMClient.stream_chat`。
- [`source/packages/llm_core/providers/openai_compat.py`](../../source/packages/llm_core/providers/openai_compat.py)：OpenAI-compatible streaming 实现。
- [`source/apps/02_llm_streaming_api/main.py`](../../source/apps/02_llm_streaming_api/main.py)：FastAPI SSE app。
- [`source/apps/02_llm_streaming_api/index.html`](../../source/apps/02_llm_streaming_api/index.html)：浏览器打字机观察页面。

完整运行说明与输出字段见 [SSE app README](../../source/apps/02_llm_streaming_api/README.md)。

### 实现步骤

1. `ConversationBuffer` 根据 `session_id` 准备 system + user messages。
2. `LLMClient.stream_chat(messages, config_ref)` 读取 `models.yaml`，检查 chat 配置并调用 provider。
3. `OpenAICompatProvider.stream_chat` 使用 `stream=True` 接收模型 chunk。
4. 每个 chunk 转成 `LLMStreamEvent(type="token", delta=...)`。
5. FastAPI 使用 `encode_sse(event)` 输出 `text/event-stream`。
6. 收到 `message_done.content` 后，把最终 assistant 消息追加到 history。

### 运行方式

仓库根目录：

```bash
pip install -r requirements.txt
pip install -e .
cp .env.example .env
uvicorn main:app --app-dir source/apps/02_llm_streaming_api --reload --port 8004
```

然后打开浏览器（推荐，页面与 API 同源）：

```text
http://127.0.0.1:8004/
```

若用 Live Server 打开 `source/apps/02_llm_streaming_api/index.html`，页面通常在 `127.0.0.1:5500`，API 仍在 `8004`，属于跨域。本节 demo 已在 FastAPI 侧为常见 Live Server 端口配置 CORS，前端在非 `8004` 端口时会自动请求 `http://127.0.0.1:8004/api/review/stream`。无论哪种方式，都必须先启动 uvicorn。

点击 `Start`，页面会展示打字机效果。建议同时打开浏览器开发者工具，在 Network 面板查看 `/api/review/stream?...` 请求，观察响应头 `content-type: text/event-stream` 和持续到达的 `event/data`。Live Server 场景下，该请求的目标主机应是 `8004`，而不是 Live Server 端口。

如果想看 SSE 协议原文，另开一个终端：

```bash
curl -N "http://127.0.0.1:8004/api/review/stream?sample_id=S2&session_id=demo"
```

### 预期结果

应看到一组 SSE 事件：

- `message_start`：本次模型运行开始。
- `token`：增量文本，前端可以实时拼接展示。
- `message_done`：最终 assistant 内容，可进入 history。
- `done`：本次事件流结束。

浏览器页面看到的是打字机效果；终端看到的是原始 SSE 协议。两者来自同一个接口，只是观察层不同。

如果出现 `error`，先看 `code`：可能是 `auth`、`rate_limit`、`timeout` 或 `provider_error`。如果没有配置 `OPENAI_API_KEY`，接口会直接返回 500，提示补齐根目录 `.env`。

---

## 完成标准

- 能解释 token stream、event stream、SSE 三者的区别。
- 能说明为什么 `LLMStreamEvent` 需要 `run_id` 和 `sequence`。
- 能解释为什么 token delta 不进入 conversation history。
- 能运行 FastAPI app，在浏览器看到打字机效果，并用 Network 或 `curl -N` 观察 SSE 原文。
- 能说出本节没有解决哪些生产问题，例如取消、重试、断线恢复、RAG/Agent 事件。

### 运行与观察

```bash
uvicorn main:app --app-dir source/apps/02_llm_streaming_api --reload --port 8004
```

观察点：

- 浏览器 `http://127.0.0.1:8004/` 是否能点击 Start 并看到打字机效果。
- Network 中 `/api/review/stream?...` 是否是 `text/event-stream`。
- 是否先出现 `message_start`，再连续出现多个 `token`。
- `token.delta` 是否能拼成最终内容。
- 是否出现 `message_done.content`。
- 是否以 `done` 结束。

### 自检题

1. 为什么不能把 OpenAI SDK 的 chunk 原样暴露给前端？
2. `token.delta` 和 `message_done.content` 分别应该用于什么 UI 状态？
3. SSE、WebSocket 和普通 HTTP JSON 在本节场景下各有什么取舍？
4. 为什么 `ConversationBuffer` 不保存中间 token？
5. 如果 `curl -N` 不是逐 token 输出，你会按什么顺序排查？
6. 后续接入 RAG 或 Agent 时，哪些事件应该新增，哪些不应该混进 chat history？

---

## 本节沉淀

- `llm_core` 新增 `streaming`、`conversation` 与 `LLMClient.stream_chat`，并保留与 01–03 同一套 `config_ref` 调用方式。
- 需求评审助手获得一个可运行的 FastAPI SSE 入口，前端可以基于事件协议展示模型运行态。
- 下一节 [05_context_engineering.md](05_context_engineering.md) 将继续处理 history、需求材料、证据和中间结果如何进入上下文预算。

---

## 相关专题

- 上一篇：[03_structured_outputs.md](03_structured_outputs.md)
- 下一篇：[05_context_engineering.md](05_context_engineering.md)
- 课程大纲：[outline.md](outline.md)
