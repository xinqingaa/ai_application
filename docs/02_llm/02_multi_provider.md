# 02. 多平台模型接入与统一抽象

> 本节目标：理解为什么 OpenAI SDK 能成为统一入口，掌握国内 OpenAI-compatible 平台的接入方式，看懂 OpenAI / Claude / Gemini 的关键接口差异，并把这些差异收敛到配置层和统一客户端层

---

## 1. 概述

### 学习目标

- 理解为什么课程里优先讲 OpenAI 风格接口
- 理解 OpenAI、Claude、Gemini 在请求组织和 SDK 设计上的关键差异
- 掌握百炼 / 通义、DeepSeek、GLM 等国内 OpenAI-compatible 平台的接入方式
- 学会把平台差异收敛到配置层，而不是散落在业务逻辑里
- 能写出一个支持 `messages` 级输入的最小统一客户端

### 预计学习时间

- OpenAI SDK 统一入口：1 小时
- 平台差异拆解：1-1.5 小时
- OpenAI-compatible 平台实践：1 小时
- 统一客户端封装：1-2 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| 切换模型供应商 | `api_key`、`base_url`、`model` 配置管理 |
| 降低实验成本 | OpenAI-compatible 平台复用同一套调用方式 |
| 业务解耦 | 统一客户端、配置层、能力矩阵 |
| 模型路由与降级 | provider 切换、备用模型、扩展位 |
| 后续结构化输出与流式输出 | 都依赖稳定的统一抽象 |

> **这一章解决的核心问题不是“哪个平台最好”，而是“如何让你的代码不被某个平台死绑”。**

### 这一章的学习边界

这一章重点解决：

1. 为什么 OpenAI 风格接口适合做统一入口
2. 平台差异具体落在什么层
3. OpenAI-compatible 平台的工程意义
4. 配置层和统一客户端应该长什么样

这一章不展开：

- 完整多平台 SDK 适配器体系
- 复杂模型路由策略
- 自动降级和熔断体系
- 流式统一层
- 结构化输出统一层

这些会在后续章节继续叠加。

### 本章与第一章的衔接

第一章解决的是：

- 一次调用怎么发出去
- `messages` 怎么组织
- Token 和参数怎么理解

第二章解决的是：

- 如果平台变了，代码怎么不重写
- 如果模型供应商变了，业务代码如何保持稳定
- 哪些差异该在配置层解决
- 哪些差异必须保留在 adapter 或 provider 层

所以第二章本质上是：

> 从“会调用一个模型”过渡到“会设计一层不被模型平台绑死的调用抽象”。

---

## 2. 为什么 OpenAI SDK 可以作为统一入口 📌

### 2.1 课程为什么先讲 OpenAI 风格

课程里优先使用 OpenAI SDK，并不是因为你必须接入 OpenAI 官方平台，而是因为它在当前生态里有三个现实优势：

1. 资料最丰富
2. 示例最多
3. 很多平台选择兼容它的接口风格

这意味着你学的是一种**主流接口范式**，而不是某一家厂商的特殊写法。

### 2.2 OpenAI 风格接口的最小形态

一个最典型的调用长这样：

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://your-compatible-endpoint",
)

response = client.chat.completions.create(
    model="your-model-name",
    messages=[
        {"role": "system", "content": "你是一个有帮助的 AI 助手"},
        {"role": "user", "content": "你好"}
    ],
    temperature=0.3,
    max_tokens=256,
)
```

它背后包含的抽象其实很清晰：

| 对象 | 含义 |
|------|------|
| `client` | 连接哪个平台 |
| `base_url` | 请求发往哪个端点 |
| `model` | 调用哪个模型 |
| `messages` | 当前全部上下文 |
| `response` | 结构化响应对象 |

### 2.3 为什么这套形态对多平台特别有价值

因为只要平台支持 OpenAI-compatible 协议，很多时候你只需要改：

1. `api_key`
2. `base_url`
3. `model`

业务主逻辑通常可以不变。

这对学习阶段尤其重要，因为你当前需要：

- 低成本练习
- 高频切换平台
- 快速建立调用手感

如果每个平台都完全换一套调用方式，学习成本会明显上升。

### 2.4 OpenAI 风格接口到底统一了什么

它统一的不只是 SDK 名字，而是以下这些关键结构：

1. 聊天输入以 `messages` 为核心
2. 请求里通常有 `model`
3. 参数通常围绕 `temperature / max_tokens / stop`
4. 响应通常有 `choices` 和 `usage`
5. 流式响应也遵循相似的“逐段事件”思路

这就是为什么它适合作为“课程主线入口”。

### 2.5 OpenAI 风格并不等于“所有平台完全一样”

这是一个很关键的边界。

OpenAI 风格统一的是**大方向**，但不同平台仍然可能在这些地方出现差异：

1. system prompt 放置方式
2. 请求字段命名
3. 流式事件结构
4. 原生结构化输出能力
5. 多模态输入组织方式

也就是说：

> 它足够适合做统一入口，但还不足以让你完全忽略平台差异。

这也是第二章必须存在的原因。

### 2.6 为什么对你当前阶段尤其合适

你的当前策略很明确：

- 教学理解上：OpenAI / Claude / Gemini
- 实际接入上：百炼 / 通义、DeepSeek、GLM

这种做法本身就是在利用 OpenAI-compatible 的优势：

> 用主流接口风格建立理解，用低成本平台完成大量练习。

所以第二章不是和你的实践策略冲突，恰恰是在为它做工程上的理论支撑。

---

## 3. 平台差异具体落在哪里 📌

### 3.1 为什么不能只说“这些平台差不多”

如果只停留在“它们都能聊天、都能流式、都能多模态”这种层面，后面做统一抽象时很容易犯错。

真正工程里，你要知道差异**具体落在哪一层**。

至少要区分：

1. 配置层差异
2. 请求体差异
3. 响应体差异
4. 能力矩阵差异
5. SDK 形态差异

### 3.2 第一类差异：配置层

最基础的差异包括：

| 项目 | OpenAI-compatible 平台常见差异 |
|------|---------------------------|
| `api_key` | 不同平台对应不同环境变量 |
| `base_url` | 端点不同 |
| `model` | 模型名不同 |
| 是否就绪 | 某些平台当前环境是否已配置 |

这些差异应该优先收敛到配置层，而不是写到业务里。

### 3.3 第二类差异：system prompt 的组织方式

这是很典型的接口差异。

OpenAI 风格里，system 常常直接作为第一条消息：

```json
{
  "messages": [
    {"role": "system", "content": "你是一个有帮助的 AI 助手"},
    {"role": "user", "content": "你好"}
  ]
}
```

Claude 风格里，system 常常被单独传：

```json
{
  "system": "你是一个有帮助的 AI 助手",
  "messages": [
    {"role": "user", "content": "你好"}
  ]
}
```

这就意味着：

> 你不能把“system 一定是 messages[0]”当成跨平台永远成立的规则。

### 3.4 第三类差异：消息内容对象的组织方式

在 OpenAI 风格里，文本消息通常很直接：

```json
{"role": "user", "content": "你好"}
```

在 Gemini 风格里，内容经常会组织成 `parts`：

```json
{
  "role": "user",
  "parts": [{"text": "你好"}]
}
```

这种差异在你开始接触多模态时会变得更明显。

### 3.5 第四类差异：响应体结构

OpenAI 风格响应里，最常见的是：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "..."
      }
    }
  ],
  "usage": {...}
}
```

而不同平台可能会在这些地方变化：

1. 回复内容的层级路径
2. usage 是否齐全
3. finish_reason 的命名
4. 流式事件字段

所以统一客户端不能只考虑“怎么发”，还要考虑“怎么统一收”。

### 3.6 第五类差异：能力矩阵

不同平台不只是“字段不同”，还可能能力就不同。

例如你需要关心：

| 能力 | 是否所有平台都一样 |
|------|----------------|
| OpenAI-compatible | 否 |
| system 单独传递 | 否 |
| 流式输出 | 常见，但实现细节不完全相同 |
| 原生结构化输出 | 否 |
| Vision | 常见，但消息结构不同 |

这意味着统一抽象不能假设“所有能力 everywhere available”。

### 3.7 平台差异不该落到业务层

一个常见的坏味道是业务代码里出现很多分支：

```python
if provider == "openai":
    ...
elif provider == "claude":
    ...
elif provider == "gemini":
    ...
elif provider == "deepseek":
    ...
```

问题是：

1. 业务和平台耦合
2. 新增 provider 时要改很多地方
3. 日志、重试、流式、结构化输出都会越来越难统一

正确方向应该是：

> 业务代码尽量不关心 provider 细节，provider 差异收敛到底层。

### 3.8 这一章里要建立的抽象边界意识

至少要把这些层区分出来：

| 层 | 职责 |
|------|------|
| 配置层 | provider 信息、默认 model、base_url、环境变量 |
| 能力矩阵 | 该 provider 支持什么能力 |
| 请求构建层 | 按 provider 组织 payload |
| 调用层 | 真正发请求，处理 timeout / retry |
| 统一响应层 | 解析不同平台响应并返回统一结构 |
| 业务层 | 调用 `client.chat()`，不关心底层平台细节 |

如果这几个层次不分清楚，第二章就等于白学。

---

## 4. OpenAI / Claude / Gemini 的具体接口差异 📌

### 4.1 为什么这一节要具体到 payload 级别

如果只说“Claude 的 system 不一样，Gemini 的多模态不一样”，这种认知是不够用的。

工程里必须把差异具体到：

- 请求字段
- 内容组织
- system 放哪里
- 响应怎么取

### 4.2 OpenAI 风格请求预览

```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "你是一个严谨的技术助教，回答要分点。"},
    {"role": "user", "content": "请解释多平台统一抽象为什么重要。"}
  ],
  "temperature": 0.2,
  "max_tokens": 240,
  "stop": ["END"]
}
```

特点：

1. `messages` 是核心
2. `system` 通常 inline 在消息列表中
3. 参数和消息都集中在同一个请求对象里

### 4.3 Claude 风格请求预览

```json
{
  "model": "claude-sonnet-4-0",
  "system": "你是一个严谨的技术助教，回答要分点。",
  "messages": [
    {"role": "user", "content": "请解释多平台统一抽象为什么重要。"}
  ],
  "temperature": 0.2,
  "max_tokens": 240,
  "stop_sequences": ["END"]
}
```

特点：

1. `system` 往往独立字段
2. `stop_sequences` 的命名和 OpenAI 风格不同
3. 这类差异会直接影响你如何构建 request adapter

### 4.4 Gemini 风格请求预览

```json
{
  "model": "gemini-2.5-pro",
  "systemInstruction": {
    "parts": [{"text": "你是一个严谨的技术助教，回答要分点。"}]
  },
  "contents": [
    {
      "role": "user",
      "parts": [{"text": "请解释多平台统一抽象为什么重要。"}]
    }
  ],
  "generationConfig": {
    "temperature": 0.2,
    "maxOutputTokens": 240
  }
}
```

特点：

1. 内容组织为 `parts`
2. `systemInstruction` 结构与前两者不同
3. `generationConfig` 也是单独对象

### 4.5 三者最关键的差异总结

| 项目 | OpenAI | Claude | Gemini |
|------|--------|--------|--------|
| system 放置 | inline message | 单独字段 | `systemInstruction` |
| 用户消息结构 | `content` 字符串/对象 | `content` | `parts` |
| 参数位置 | 顶层 | 顶层 | `generationConfig` |
| OpenAI-compatible | 否，但为参考标准 | 否 | 否 |

### 4.6 哪些差异应该被抽象，哪些不该

应该被抽象的：

1. `chat(messages, temperature, max_tokens)` 这种通用能力
2. provider 配置
3. 统一响应对象
4. debug / retry / timeout

不应该强行抽象过度的：

1. 每个平台专有高级能力
2. 每个平台完全不同的工具调用结构
3. 每个平台完全不同的多模态高级输入形态

这就是所谓的：

> 统一公共子集，保留差异能力扩展位。

### 4.7 为什么这对后续课程重要

后面你会进入：

- 结构化输出
- 流式输出
- RAG
- Agent

如果第二章没有把平台差异和抽象边界讲清楚，后面所有功能都会变成：

> 每加一个能力，就为每个平台单独写一遍

那工程复杂度会迅速失控。

---

## 5. 国内 OpenAI-compatible 平台的工程价值 📌

### 5.1 为什么它们特别适合当前阶段

对于你当前的目标，这类平台有明显优势：

1. 成本更可控
2. 网络更稳定
3. 接入门槛低
4. 大部分基础调用可直接复用 OpenAI SDK

这意味着你可以把大量时间花在：

- 消息结构
- Prompt
- 结构化输出
- 流式
- 工程封装

而不是浪费在“每个平台 SDK 完全重学一遍”。

### 5.2 这一类平台常见的接入参数

通常你只需要准备：

1. API Key
2. Base URL
3. Model 名称

例如：

```python
client = OpenAI(
    api_key=os.getenv("BAILIAN_API_KEY"),
    base_url=os.getenv("BAILIAN_BASE_URL"),
)
```

### 5.3 一个更现实的理解

OpenAI-compatible 并不等于 100% 完全一致。

你要有两个预期：

1. 基础聊天调用通常很容易复用
2. 高级能力并不一定完全一致

例如某些平台可能在这些地方出现差异：

- 参数支持范围
- 结构化输出能力
- 工具调用字段
- streaming 事件细节

所以第二章的正确认知不是：

> 兼容 = 永远不用管差异

而是：

> 兼容 = 你可以把大量重复工作省掉，但仍然要保留差异处理边界。

### 5.4 为什么配置层是关键

如果你把 provider 差异主要压缩成：

```python
{
    "api_key": "...",
    "base_url": "...",
    "model": "..."
}
```

那业务代码就容易保持稳定。

这跟前端里做环境配置、服务端点映射，本质上是一个思路。

### 5.5 这一章里配置层至少该描述什么

至少应该有：

1. provider 名称
2. display name
3. provider 类型
4. 环境变量映射
5. 默认 base_url
6. 默认 model
7. 能力矩阵
8. 备注说明

如果缺了这些信息，后面统一客户端很容易变成“到处猜平台行为”。

### 5.6 provider registry 的价值

把平台信息集中注册有几个明显好处：

1. 新增 provider 更容易
2. 做能力矩阵更容易
3. 做可用性检查更容易
4. 调试和打印更容易

这也是为什么第二章的代码里，不应该只是一堆零散 `if provider == ...`。

### 5.7 配置层不应该做什么

配置层不应该负责：

1. 拼业务 Prompt
2. 页面逻辑
3. 各种业务条件判断
4. 每个页面里各写一遍 provider 判断

配置层只描述 provider，不承担业务职责。

---

## 6. 从配置层走向统一客户端 📌

### 6.1 为什么不能只停留在“能切配置”

如果你只做到“能换 `api_key / base_url / model`”，很快会遇到这些问题：

1. 响应解析散落在各处
2. 错误处理散落在各处
3. debug 信息散落在各处
4. 后续结构化输出和流式输出没有统一挂载点

所以第二章的目标不是“会改配置”，而是：

> 开始建立一个最小但正确的统一客户端。

### 6.2 一个最小统一客户端应该提供什么

至少应该提供这些能力：

1. 根据 provider 加载配置
2. 接收统一的请求对象
3. 统一返回响应对象
4. 支持切换 provider
5. 支持 debug、timeout、retry
6. 为非兼容平台保留扩展位

### 6.3 为什么第二章的统一接口必须以 `messages` 为中心

这是第二章最容易写错的地方。

很多人会偷懒写成：

```python
client.chat(prompt: str)
```

看起来方便，但问题很大：

1. 丢失多轮对话能力
2. 丢失 system prompt 的独立组织能力
3. 后续结构化输出、流式输出、工具调用都容易返工

所以第二章的统一客户端至少应该接受：

```python
ChatRequest(
    messages=[...],
    temperature=0.3,
    max_tokens=300,
)
```

### 6.4 统一请求对象的价值

统一请求对象至少可以承载：

1. `messages`
2. `temperature`
3. `max_tokens`
4. `stop`
5. `metadata`

这会让你后面扩展结构化输出、实验记录、A/B 对比更容易。

### 6.5 统一响应对象的价值

统一响应对象至少应该包含：

1. `provider`
2. `model`
3. `content`
4. `usage`
5. `finish_reason`
6. `request_preview`
7. `raw_response_preview`
8. `mocked`
9. `elapsed_ms`
10. `error`

这样做的最大价值是：

- 上层业务不用关心底层平台差异
- debug 更容易
- 日志更容易
- 结构化输出和流式可以继续复用这个壳

### 6.6 `request_preview` 为什么重要

统一客户端不仅要“会调用”，还要“能解释自己在调用什么”。

所以 `request_preview` 很有价值：

1. 调试时可以直接看到最终 payload
2. 切 provider 时可以观察形态差异
3. 可以帮助你定位到底是 Prompt 问题还是 provider adapter 问题

### 6.7 retry、timeout、debug 应该放在哪里

这些能力不应该放在业务页面层，而应该优先放在统一客户端层。

原因很简单：

1. 它们是横切能力
2. 几乎所有调用都需要
3. 散落在上层会很难维护

所以第二章就应该开始建立这个意识。

### 6.8 非 OpenAI-compatible 平台该怎么办

第二章不要求你现在把 Claude / Gemini 真正接完。

更合理的做法是：

1. 在 provider registry 中登记它们
2. 让配置层和能力矩阵知道它们存在
3. 给它们做 request preview
4. 在统一客户端里先保留 placeholder / 扩展位

这样你既不会把这章做成半成品，也不会为了“全接完”而失控。

### 6.9 第二章的统一客户端边界

这一章的统一客户端应该做到：

- provider 配置统一
- request shape 统一
- response shape 统一
- debug / retry / timeout 统一
- 非兼容平台保留扩展位

不需要做到：

- 真正支持所有官方 SDK
- 抽象所有高级能力
- 完整策略路由

这一步的目标是方向正确，不是一步到位。

### 6.10 本章对应代码

本章对应：

- `source/02_llm/02_multi_provider/provider_utils.py`
- `source/02_llm/02_multi_provider/01_openai_compatible.py`
- `source/02_llm/02_multi_provider/02_provider_config.py`
- `source/02_llm/02_multi_provider/03_unified_client.py`

建议你重点观察：

1. provider registry 是怎么组织的
2. request preview 是怎么按平台变化的
3. 为什么统一客户端接受 `ChatRequest` 而不是 `prompt: str`
4. 为什么统一客户端要带 `describe()`、`debug`、`retry`

---

## 7. 本章代码与文件说明

本章代码目录：`source/02_llm/02_multi_provider/`

| 文件 | 作用 |
|------|------|
| `provider_utils.py` | provider 注册表、能力矩阵、请求预览、统一客户端 |
| `01_openai_compatible.py` | 演示同一套 OpenAI SDK 切换不同平台 |
| `02_provider_config.py` | 演示配置层和请求预览比较 |
| `03_unified_client.py` | 演示统一客户端的 messages 级接口 |
| `.env.example` | 多平台环境变量模板 |

建议顺序：

1. 先看 `01_openai_compatible.py`
2. 再看 `02_provider_config.py`
3. 最后重点看 `03_unified_client.py`

---

## 8. 本章小结

这一章真正要建立的是工程抽象意识：

1. OpenAI SDK 适合做统一入口，但不是全世界都完全一样
2. Claude / Gemini 的差异必须具体到 payload 和能力矩阵层面理解
3. OpenAI-compatible 平台非常适合低成本练习
4. provider 差异应该优先收敛到配置层、请求构建层和统一客户端层
5. 第二章的统一抽象不能把聊天能力降级成一个裸字符串接口

如果这一章打牢，后面的结构化输出、流式响应、错误处理和成本控制都会更容易接到同一条主线上。

---

## 9. 练习建议

1. 在 `provider_utils.py` 中新增一个 provider，补齐它的能力矩阵和默认配置。
2. 修改 `02_provider_config.py` 里的比较 request，给它加上更复杂的 `messages`，观察不同平台 preview 如何变化。
3. 在 `03_unified_client.py` 中新增一个 `dry_run()` 方法，只返回 request preview，不发请求。
4. 尝试让统一客户端支持自定义 `stop` 参数。
5. 思考：如果后面要统一结构化输出，这一章的哪些设计可以直接复用？
