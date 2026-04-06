# 01. LLM API 调用入门

> 本节目标：跑通第一条 LLM 请求，真正理解聊天消息结构、多轮对话、Token、上下文窗口、成本和常用参数，并把这些知识落到一个最小可用聊天 CLI 上

---

## 1. 概述

### 学习目标

- 完成一次最小可用的 LLM API 调用
- 理解 `messages` 消息结构和 `system / user / assistant` 三种角色
- 理解多轮对话为什么本质上是“应用侧管理历史消息”
- 理解 Token、上下文窗口和成本之间的关系
- 掌握 `temperature`、`max_tokens`、`top_p`、`stop` 等常用参数
- 能写出一个带历史、统计、裁剪、导出的最小可用聊天 CLI

### 预计学习时间

- 环境准备与第一条请求：45 分钟
- 消息格式与多轮对话：1 小时
- Token / 上下文 / 成本：1 小时
- 参数实验：45 分钟
- CLI 实战：1-2 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| 第一次接入模型 | `api_key`、`base_url`、`model`、最小请求体 |
| 聊天产品 | `messages` 结构、多轮历史管理 |
| 成本控制 | Token 估算、上下文裁剪、usage 解读 |
| 输出稳定性 | `temperature`、`top_p`、`max_tokens` |
| 聊天后端雏形 | 一个带历史和统计的 CLI |

> **这一章不是讲模型底层原理，而是先把模型接起来，并且真正看懂“一次调用到底发生了什么”。**

### 这一章的学习边界

这一章重点解决的是：

1. 如何发出一次请求
2. 如何组织 `messages`
3. 如何理解响应对象
4. 如何估算 Token 和成本
5. 如何把这些能力封装成最小工具

这一章不展开：

- Transformer / Attention / 训练流程
- RAG
- Agent
- LangChain 主线
- 多平台复杂适配器体系

这些内容会在后续章节继续展开。

### 平台学习策略

课程中的平台理解会以 `OpenAI / Claude / Gemini` 作为主流参考，因为它们代表了当前最常见的接口风格和产品能力。

但在实际练习中，你完全可以优先使用：

- 百炼 / 通义千问
- DeepSeek
- GLM

原因很简单：

1. 成本更友好
2. 网络访问更方便
3. 很多平台支持 OpenAI-compatible 协议
4. 可以直接复用 `OpenAI SDK`

所以你当前阶段要建立的是一种能力：

> 用主流接口思路理解 LLM API，再用低成本平台完成高频练习。

---

## 2. 环境准备与第一条请求 📌

### 2.1 为什么第一章必须先跑通一次真实请求

很多人在学 LLM 时，会先看 Prompt Engineering、RAG、Agent、Workflow、LangChain，但如果到那个时候还没有真正发出过一条请求，就会有一个很大的问题：

> 概念理解越来越多，但对运行时对象完全没有感觉。

应用开发里最重要的第一步不是抽象，而是先建立最小闭环：

```text
用户输入
-> 构造 messages
-> 发起 HTTP 请求
-> 模型推理
-> 返回响应对象
-> 代码提取 message.content
-> 打印结果
```

只有这个闭环跑通了，后面的多轮对话、结构化输出、流式响应、统一客户端封装，才有扎实基础。

### 2.2 一次最小调用到底需要什么

最小可用的聊天调用通常只需要 4 个核心元素：

1. `api_key`
2. `base_url`
3. `model`
4. `messages`

示例：

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="your-compatible-base-url",
)

response = client.chat.completions.create(
    model="your-model-name",
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
)

print(response.choices[0].message.content)
```

这里要建立两个非常重要的直觉：

1. **你不是在“打开一个聊天窗口”**，而是在发一次结构化请求
2. **模型响应不是原始字符串**，而是一个结构化响应对象

### 2.3 为什么课程里优先讲 OpenAI SDK

不是因为你必须使用 OpenAI 官方平台，而是因为：

1. 它的接口风格已经成为事实上的参考样式
2. 资料最丰富，示例最多
3. 很多国内平台支持 OpenAI-compatible 协议

所以你学的不是“OpenAI 一家厂商的私有写法”，而是：

> 一种在行业里被广泛复用的聊天接口组织方式

这也是为什么你现在可以用国内平台练习，但依然要理解 OpenAI 风格的请求结构。

### 2.4 环境变量管理

不要把 API Key 硬编码在代码里。

最基础的写法：

```python
import os

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
```

如果你熟悉前端项目，可以把它理解成：

- `.env` 管配置
- 代码里通过环境变量读取运行时参数

这件事的重要性不只在安全，还在于：

1. 你可以轻松切换 provider
2. 你可以轻松切换 model
3. 你可以让代码和环境解耦

### 2.5 第一条请求的心智模型

先把这 5 个对象看清楚：

| 对象 | 作用 |
|------|------|
| `client` | 模型服务客户端 |
| `model` | 本次请求使用的具体模型 |
| `messages` | 当前请求要带给模型的上下文 |
| `response` | 模型返回的结构化结果 |
| `usage` | 这次调用消耗的 Token 统计 |

初学阶段最重要的不是马上做抽象，而是对这些对象形成手感。

### 2.6 请求体长什么样

如果把一次聊天调用想象成 JSON 请求体，大致会长这样：

```json
{
  "model": "qwen-plus",
  "messages": [
    {
      "role": "system",
      "content": "你是一个有帮助的 AI 助手，回答要简洁。"
    },
    {
      "role": "user",
      "content": "你好，请介绍一下你自己。"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 256
}
```

真正重要的是你能解释每一项：

- `model`：调用哪个模型
- `messages`：这次请求的全部上下文
- `temperature`：输出发散程度
- `max_tokens`：输出长度上限

### 2.7 响应对象长什么样

一个典型的响应对象可以抽象成这样：

```json
{
  "id": "chatcmpl-abc123",
  "model": "demo-model",
  "choices": [
    {
      "index": 0,
      "finish_reason": "stop",
      "message": {
        "role": "assistant",
        "content": "这是一个示例回复。"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 35,
    "completion_tokens": 42,
    "total_tokens": 77
  }
}
```

作为应用开发者，你通常最关心这几部分：

1. `choices[0].message.content`
2. `choices[0].finish_reason`
3. `model`
4. `usage`

### 2.8 `finish_reason` 有什么用

很多人只盯着 `content`，却忽略了 `finish_reason`。

它很重要，因为它能帮助你判断：

- 为什么输出停止了
- 是正常结束还是被截断
- 是不是应该重试或者增大 `max_tokens`

常见值包括：

| 值 | 含义 |
|------|------|
| `stop` | 正常结束 |
| `length` | 达到输出上限被截断 |
| 其他平台特定值 | 工具调用、内容限制等场景 |

如果你发现回答总是半截，很可能不是模型“变笨了”，而是：

> 你的 `max_tokens` 太小，`finish_reason` 已经在提示你了。

### 2.9 `usage` 有什么用

`usage` 是本章必须养成习惯去看的字段。

它通常包括：

- `prompt_tokens`
- `completion_tokens`
- `total_tokens`

这些值至少解决三个问题：

1. 这次调用大概花了多少钱
2. 为什么某一轮对话变慢了
3. 为什么某一轮对话突然贵了很多

如果你后面做真实产品，`usage` 会直接进入：

- 日志
- 成本统计
- 用户配额
- 限流和告警

### 2.10 OpenAI-compatible 平台的本质

对你当前阶段来说，最重要的不是记住每个平台的网址，而是理解：

> 很多平台虽然不是 OpenAI 官方，但会兼容 OpenAI 风格的聊天接口。

这意味着你可以继续写：

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-key",
    base_url="your-compatible-endpoint",
)
```

然后通过切换：

1. `api_key`
2. `base_url`
3. `model`

来复用同一套代码。

### 2.11 第一条请求的完整最小示例

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("BAILIAN_API_KEY"),
    base_url=os.getenv("BAILIAN_BASE_URL"),
)

response = client.chat.completions.create(
    model=os.getenv("BAILIAN_MODEL", "qwen-plus"),
    messages=[
        {"role": "system", "content": "你是一个有帮助的 AI 助手，回答要简洁。"},
        {"role": "user", "content": "你好，请介绍一下自己。"},
    ],
    temperature=0.3,
    max_tokens=256,
)

print(response.choices[0].message.content)
print(response.usage)
```

### 2.12 真实调用失败时先看什么

第一章最容易遇到的不是代码语法问题，而是运行时配置问题。

建议排查顺序：

1. `provider` 是否是你以为的那个平台
2. `base_url` 是否正确
3. `model` 是否存在
4. API Key 是否有效
5. 请求参数是否兼容
6. 网络 / 限流 / 服务端错误

这一步非常工程化，不要把失败都归因于“模型有问题”。

### 2.13 第一条请求的常见错误

| 错误类型 | 常见原因 |
|------|------|
| 鉴权失败 | API Key 无效、过期、写错环境变量 |
| 请求地址错误 | `base_url` 写错或不兼容 |
| 模型不存在 | `model` 写错 |
| 参数不支持 | 某平台不支持某个字段 |
| 网络错误 | 超时、连接失败、DNS 问题 |
| 限流错误 | 请求频率过高 |

### 2.14 本节对应代码

本节对应：

- `source/02_llm/01_api_intro/01_first_call.py`
- `source/02_llm/01_api_intro/llm_utils.py`

建议你运行时重点观察：

1. `request_preview`
2. `response_preview`
3. `usage`
4. 失败时的报错信息

---

## 3. 消息格式与多轮对话 📌

### 3.1 为什么聊天模型的核心输入是 `messages`

在聊天模型里，输入通常不是一个单一字符串，而是一组按顺序排列的消息：

```python
messages = [
    {"role": "system", "content": "你是一个有帮助的 AI 助手"},
    {"role": "user", "content": "你好"},
]
```

这和传统函数调用很不一样。

因为这里传的不是“一个问题”，而是：

> 当前对话状态的一个快照

### 3.2 三种角色：`system / user / assistant`

最常见的三个角色如下：

| 角色 | 作用 |
|------|------|
| `system` | 定义长期稳定的角色和行为约束 |
| `user` | 当前轮用户输入 |
| `assistant` | 过去轮次模型输出 |

应用开发里，真正重要的不是背角色名，而是知道它们为什么要分开。

### 3.3 `system` 适合放什么

`system` 适合放“长期稳定不太变”的规则，例如：

1. 角色身份
2. 回答风格
3. 输出边界
4. 长期生效的行为原则

例如：

```python
{
    "role": "system",
    "content": "你是一个 AI 开发助教，回答要简洁，优先使用应用开发视角。"
}
```

这里放的是“长期规则”，而不是本轮具体问题。

### 3.4 `user` 适合放什么

`user` 适合放：

1. 本轮任务
2. 本轮输入数据
3. 本轮材料
4. 当前具体约束

例如：

```python
{
    "role": "user",
    "content": "请用 100 字解释为什么多轮对话要管理历史消息。"
}
```

### 3.5 `assistant` 为什么也要放进历史

因为如果你做多轮对话，模型不仅要看到用户说了什么，还要看到自己上一轮说了什么。

否则很容易出现：

- 语义断裂
- 重复回答
- 忘记前文立场

所以 `assistant` 历史消息不是可有可无，而是多轮对话的重要组成部分。

### 3.6 为什么模型不会“自己记住你”

API 调用不是一个自动持久化记忆系统。

每次调用时，模型只知道你传进去的东西。

这意味着：

- 你不传历史，它就不知道上一轮说了什么
- 你传多少，它就只看到多少
- 历史消息越多，成本越高

所以多轮对话的本质不是“模型有记忆”，而是：

```text
应用侧负责保存历史
应用侧负责重新把历史传给模型
```

如果你有前端经验，可以把这件事类比成：

- 多轮会话本质上是状态管理
- `messages` 就是一种对话状态快照

### 3.7 单轮和多轮对话的区别

单轮：

```python
messages = [
    {"role": "user", "content": "什么是 Python？"}
]
```

多轮：

```python
messages = [
    {"role": "system", "content": "你是一个编程助教，回答要简洁。"},
    {"role": "user", "content": "什么是 Python？"},
    {"role": "assistant", "content": "Python 是一种通用编程语言。"},
    {"role": "user", "content": "它适合做 AI 应用开发吗？"},
]
```

区别不只是“多了几条消息”，而是：

> 多轮对话开始引入上下文管理问题。

### 3.8 一个常见误区：把所有东西都塞进一条 user 文本

初学者常见写法：

```python
messages = [
    {
        "role": "user",
        "content": "你是一个 AI 助手，请用简洁风格回答。我上一轮问了 Python，这一轮我想继续问它适不适合做 AI 应用开发。"
    }
]
```

这不是不能跑，但有几个问题：

1. 角色和任务混在一起
2. 历史和当前轮混在一起
3. 后续不好维护
4. 很难做裁剪和复用

这就是为什么要把 `system / user / assistant` 分开。

### 3.9 `system prompt` 的定位

`system prompt` 不是魔法，而是高优先级运行时规则。

它常见的用途包括：

1. 指定角色
2. 指定风格
3. 指定结构化要求
4. 限制回答边界

示例：

```python
{
    "role": "system",
    "content": "你是一名 Python 助教。回答要简洁，优先给出开发视角解释。"
}
```

### 3.10 一个好 `system prompt` 的特点

通常具备这些特点：

1. 长期有效
2. 规则稳定
3. 不掺杂本轮临时输入
4. 不写得过长

坏的写法往往是：

- 把具体数据塞进 `system`
- 把一次性任务塞进 `system`
- 把过多细节和示例全部堆进去

### 3.11 `system prompt` 真的会改变输出吗

会，而且通常影响很明显。

例如这两个版本：

版本 A：

```text
你是一个技术助教。回答要简洁，控制在 80 字以内。
```

版本 B：

```text
你是一个友好的技术伙伴。回答可以口语化，并在最后给一个学习建议。
```

即使用户问题一样，输出风格也很可能明显不同。

这也是为什么 Prompt 工程不能只看“用户说了什么”，还要看“系统层是怎么约束的”。

### 3.12 多轮对话里的三个现实问题

只要你开始保留历史消息，就一定会遇到：

1. 历史越来越长
2. Token 越来越高
3. 上下文越来越贵

所以多轮对话从来不只是“列表 append 一下”，而是很快会进入工程问题。

### 3.13 最小历史管理器应该做什么

哪怕只是第一章，一个最小会话管理器也应该至少具备：

1. 初始化 system prompt
2. 添加 user 消息
3. 添加 assistant 消息
4. 输出当前快照
5. 在必要时做裁剪

### 3.14 一个最小 `Conversation` 结构

```python
from dataclasses import dataclass, field

@dataclass
class Conversation:
    system_prompt: str
    messages: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self):
        self.messages.append({"role": "system", "content": self.system_prompt})

    def add_user(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text: str):
        self.messages.append({"role": "assistant", "content": text})
```

这已经非常接近后面真实聊天产品里的基础会话状态结构。

### 3.15 为什么第一章就要做导出会话

因为一旦你能把会话导出为 JSON，你就能做很多事：

1. 调试
2. 回放
3. 数据分析
4. 问题复现
5. 后续评测

这会让你更早建立“LLM 应用也需要工程可观测性”的意识。

### 3.16 本节对应代码

本节对应：

- `source/02_llm/01_api_intro/02_messages_chat.py`
- `source/02_llm/01_api_intro/llm_utils.py`

建议你重点观察：

1. 单轮和多轮消息结构差异
2. system prompt 改变对输出的影响
3. 历史裁剪前后的 token 变化
4. 导出的会话 JSON 内容

---

## 4. Token、上下文窗口与成本 📌

### 4.1 Token 不是字符，也不是单词

Token 是模型处理文本时的最小单位，但它既不完全等于字符，也不完全等于单词。

例如：

- 英文通常按词片切分
- 中文往往一个字可能对应一个或多个 token
- 中英混合文本的 token 分布会更复杂

这意味着你不能简单地把“字数”直接等价成“模型成本”。

### 4.2 为什么应用开发者必须关心 Token

因为 Token 直接影响：

| 影响项 | 说明 |
|------|------|
| 成本 | 大多数模型按输入 / 输出 token 计费 |
| 延迟 | 输入越长，推理通常越慢 |
| 稳定性 | 噪声上下文越多，回答越容易偏 |
| 产品体验 | 多轮聊天会随着历史增长变慢变贵 |

如果你做的是传统 Web 接口，可能只关心 JSON 大小；但做 LLM 应用时，Token 是更核心的计量单位。

### 4.3 `prompt_tokens` 和 `completion_tokens`

你至少要分清这两个概念：

| 字段 | 含义 |
|------|------|
| `prompt_tokens` | 输入给模型的 token 数 |
| `completion_tokens` | 模型输出的 token 数 |
| `total_tokens` | 二者之和 |

这能帮你判断：

- 是历史过长导致贵
- 还是模型输出过长导致贵

### 4.4 为什么中文和英文的 Token 成本感知不同

一个非常常见的直觉误区是：

> 看起来字数差不多，成本应该差不多。

实际上不同语言、不同编码器下，Token 数量可能差很多。

所以第一章里就要做两件事：

1. 观察中英文 token 差异
2. 养成估算 token 的习惯

### 4.5 `tiktoken` 的作用

`tiktoken` 可以帮助你更准确地估算文本 token 数。

示例：

```python
import tiktoken

encoding = tiktoken.get_encoding("cl100k_base")
tokens = encoding.encode("人工智能正在改变世界。")
print(len(tokens))
```

在没有 `tiktoken` 时，也可以用启发式估算，但你要知道：

> 启发式估算只是教学辅助，不是精确计费依据。

### 4.6 不同编码器为什么会不同

你会看到类似：

- `cl100k_base`
- `o200k_base`

它们代表不同的编码器方案。

第一章你不需要深究 tokenizer 原理，但要知道：

1. 不同模型可能对应不同编码器
2. 同一段文本在不同编码器下 token 数可能不同
3. 真正精确估算时，要尽量匹配目标模型使用的编码器

### 4.7 上下文窗口是什么

上下文窗口可以简单理解为：

> 一次请求里，模型能处理的输入 + 输出总量上限

也就是说：

```text
输入 token + 输出 token <= 上下文窗口
```

这个公式非常重要，因为它决定了：

- 你能塞多少历史消息
- 你还能给模型留多少输出空间

### 4.8 只看输入长度是不够的

如果你只看输入，而忽略输出上限，就会犯一个常见错误：

> 输入已经接近上限，结果还把 `max_tokens` 设得很大。

这样很容易导致：

- 请求失败
- 输出被截断
- 行为不稳定

所以更正确的想法是：

```text
总预算 = 模型上下文窗口
输出预留 = max_tokens
输入可用预算 = 总预算 - 输出预留
```

### 4.9 一个简单上下文预算例子

假设某模型上下文预算是一个固定值，你先预留 1000 tokens 给输出。

那么：

```text
输入可用预算 = 总预算 - 1000
```

如果你的历史消息已经超了，就要开始裁剪。

第一章你不需要死记所有模型窗口大小，但必须建立这个预算意识。

### 4.10 为什么多轮对话会越来越贵

因为每一轮请求，通常都会重新把历史消息发给模型。

例如：

第 1 轮：

- system
- user(1)

第 2 轮：

- system
- user(1)
- assistant(1)
- user(2)

第 3 轮：

- system
- user(1)
- assistant(1)
- user(2)
- assistant(2)
- user(3)

也就是说，**后面的每一轮通常都包含前面的很多内容**。

这就是为什么聊天产品不做历史管理，很快就会：

- 越来越慢
- 越来越贵
- 越来越容易超上下文

### 4.11 最基础的裁剪策略：保留最近消息

第一章先掌握最常见的一种方法就够了：

> 保留 system prompt + 最近若干条非 system 消息

示例：

```python
def trim_messages(messages: list[dict[str, str]], keep_last_messages: int = 6):
    system_messages = [item for item in messages if item["role"] == "system"]
    others = [item for item in messages if item["role"] != "system"]
    return system_messages + others[-keep_last_messages:]
```

这不是最聪明的方法，但在第一阶段非常实用。

### 4.12 另一种裁剪思路：按 Token 预算裁剪

有时候只按“消息条数”裁剪不够，因为有些消息很短，有些消息很长。

这时更合理的方法是：

> 以输入 token 预算为准，从最近消息开始回收

这样做的好处是：

1. 更贴近真实成本控制
2. 更贴近上下文窗口约束
3. 不会因为某条消息特别长而失真

### 4.13 成本估算公式

第一章不写死任何平台当前真实价格，而是先掌握公式：

```text
输入成本 = prompt_tokens / 1_000_000 * 输入单价
输出成本 = completion_tokens / 1_000_000 * 输出单价
总成本 = 输入成本 + 输出成本
```

只要你知道平台控制台上的单价，就能自己代入。

### 4.14 一个成本估算例子

假设某次调用：

- `prompt_tokens = 1200`
- `completion_tokens = 400`

如果某平台价格是：

- 输入：`$0.8 / 1M tokens`
- 输出：`$2.0 / 1M tokens`

那么：

```text
输入成本 = 1200 / 1_000_000 * 0.8
输出成本 = 400 / 1_000_000 * 2.0
总成本 = 两者相加
```

学会这个公式之后，你就不再只是“感觉贵”，而是能真正算账。

### 4.15 成本控制的第一章目标

这一章你至少要做到：

1. 会看 usage
2. 会估算 token
3. 会做最基础的历史裁剪
4. 会做简单成本估算

这已经足够支撑后面更复杂的章节。

### 4.16 本节对应代码

本节对应：

- `source/02_llm/01_api_intro/03_token_params.py`
- `source/02_llm/01_api_intro/llm_utils.py`

建议重点观察：

1. 文本 token 对比
2. 两种历史裁剪方式
3. usage 到成本的换算

---

## 5. 常用参数：如何控制输出 📌

### 5.1 参数不是越多越好，先抓最重要的两个

初学阶段最重要的两个参数是：

1. `temperature`
2. `max_tokens`

其他参数先做到：

- 知道存在
- 了解大概作用

### 5.2 `temperature` 是什么

`temperature` 控制输出的发散程度。

可以粗略理解为：

- 越低：越稳定、越保守
- 越高：越发散、越有变化

### 5.3 不同场景下的 `temperature` 建议

| 场景 | 建议 |
|------|------|
| 代码生成 | `0` 到 `0.2` |
| 结构化提取 | `0` |
| 通用问答 | `0.3` 到 `0.6` |
| 创意写作 | `0.8` 到 `1.0` |

重点不是记死数字，而是理解它背后的目标：

- 稳定任务 -> 降低发散
- 创意任务 -> 允许变化

### 5.4 一个常见误区：`temperature=0` 就绝对稳定

不是。

它通常会更稳定，但并不意味着：

- 每次都 100% 一模一样
- 所有平台行为完全一致
- 所有任务都最适合 0

正确理解应该是：

> `temperature` 是在调输出分布，不是在打开一个“确定性开关”。

### 5.5 `max_tokens` 是什么

`max_tokens` 控制输出长度上限。

它的作用包括：

1. 限制输出过长
2. 控制成本
3. 控制延迟
4. 避免一次生成太多无关内容

### 5.6 `max_tokens` 太小会怎样

可能会导致：

- 回答被截断
- `finish_reason` 变成 `length`
- 输出看起来像“半句话”

所以当你发现回答总是不完整时，不要只怪模型，先看：

1. `max_tokens`
2. `finish_reason`

### 5.7 `top_p` 是什么

`top_p` 控制采样时保留多少概率质量的候选词。

初学阶段只需要知道：

- 它和 `temperature` 都会影响发散程度
- 通常先调一个，不要一开始同时乱调两个

### 5.8 `stop` 是什么

`stop` 用于指定遇到某些标记时就停止生成。

它常用于：

1. 列表输出
2. 固定格式输出
3. 避免多余尾巴内容

例如：

```python
stop=["END"]
```

### 5.9 `presence_penalty` 和 `frequency_penalty`

这两个参数初学阶段不用深调，但要知道：

- `presence_penalty`：降低话题重复
- `frequency_penalty`：降低措辞重复

如果后面遇到模型老是复读，这两个参数可能会有帮助。

### 5.10 参数实验应该怎么做

一个很重要的工程习惯是：

> 一次只改一个变量

错误做法：

- 同时改 prompt
- 同时改 temperature
- 同时改 top_p
- 同时改 max_tokens

这样即使结果变了，你也不知道是谁导致的。

### 5.11 参数实验的最小方法

固定同一个 prompt，例如：

```text
请写一句关于春天和编程的短句。
```

然后只改：

1. `temperature = 0`
2. `temperature = 0.5`
3. `temperature = 1.0`

再观察：

- 输出是否更稳定
- 输出是否更发散
- 输出长度是否变化

### 5.12 一个常见参数预设思路

你完全可以在项目里做一个参数预设表：

```python
PRESETS = {
    "code": {"temperature": 0.1, "max_tokens": 800},
    "extract": {"temperature": 0.0, "max_tokens": 300},
    "chat": {"temperature": 0.4, "max_tokens": 500},
    "creative": {"temperature": 0.9, "max_tokens": 1000},
}
```

这样你后续做产品时，就不需要每次临时瞎调。

### 5.13 本节对应代码

参数部分主要对应：

- `source/02_llm/01_api_intro/03_token_params.py`

建议你重点观察：

1. 预设参数表
2. 参数实验设计
3. 参数和任务类型的对应关系

---

## 6. 从最小调用走向最小工具 📌

### 6.1 为什么第一章就做 CLI

很多课程把聊天工具放到很后面，但第一章就做一个最小 CLI 有几个明显好处：

1. 它能把前面所有知识串起来
2. 它让你从“看示例”切换到“使用一个小产品”
3. 它是后面 API 服务和前端聊天页面的最小原型

### 6.2 第一章的 CLI 不追求什么

这一章的 CLI 不追求：

- 数据库存储
- 流式输出
- 多用户会话系统
- 工具调用
- RAG

它只追求：

1. 能聊天
2. 能保留历史
3. 能查看参数
4. 能看统计
5. 能裁剪历史
6. 能导出会话

### 6.3 第一章的 CLI 应该有哪些命令

建议至少包括：

| 命令 | 作用 |
|------|------|
| `/help` | 查看帮助 |
| `/history` | 查看历史 |
| `/clear` | 清空历史 |
| `/model <name>` | 切换模型 |
| `/system <text>` | 修改 system prompt |
| `/params` | 查看当前运行参数 |
| `/trim <n>` | 裁剪历史 |
| `/stats` | 查看累计 token 和成本 |
| `/export` | 导出会话 |
| `/mock on/off` | 切换 mock 模式 |
| `/quit` | 退出 |

### 6.4 CLI 的状态是什么

它至少要维护三类状态：

1. 当前 provider / model / 参数
2. 当前会话历史
3. 当前累计统计

也就是说，一个最小聊天 CLI 本质上已经是一个微型应用，而不只是几行 `input()`。

### 6.5 为什么 CLI 里也要做统计

因为真实 AI 应用里，统计几乎总是必需的。

至少要能看到：

- 当前轮数
- 累计输入 tokens
- 累计输出 tokens
- 估算成本

这会让你更早习惯：

> LLM 调用不是黑盒文本生成，而是要被工程化管理的资源消耗过程。

### 6.6 为什么 CLI 里要支持导出

导出会话能帮助你：

1. 回放问题
2. 复现 bug
3. 做数据分析
4. 为后续评测准备样本

这一步在第一章就做，后面你会很受益。

### 6.7 第一章 CLI 的真实意义

如果你能把这一章的 CLI 理解透，后面很多东西都会顺：

- `/history` 对应多轮上下文管理
- `/trim` 对应成本控制
- `/stats` 对应 usage 统计
- `/system` 对应 Prompt 调整
- `/export` 对应日志与可观测性

它本质上是后续 AI 聊天产品的最小切片。

### 6.8 本节对应代码

本节对应：

- `source/02_llm/01_api_intro/04_chat_cli.py`
- `source/02_llm/01_api_intro/llm_utils.py`

建议你重点操作：

1. `/params`
2. `/history`
3. `/trim`
4. `/stats`
5. `/export`

---

## 7. 本章代码与文件说明

本章代码目录：`source/02_llm/01_api_intro/`

| 文件 | 作用 |
|------|------|
| `llm_utils.py` | 公共工具：环境变量、provider 配置、调用、token、导出 |
| `01_first_call.py` | 请求 / 响应对象拆解和第一条调用 |
| `02_messages_chat.py` | 角色、消息结构、system prompt、多轮历史 |
| `03_token_params.py` | Token 估算、上下文预算、成本公式、参数建议 |
| `04_chat_cli.py` | 最小可用聊天 CLI |
| `.env.example` | 环境变量模板 |

建议顺序：

1. 先跑 `01_first_call.py`
2. 再跑 `02_messages_chat.py`
3. 再跑 `03_token_params.py`
4. 最后用 `04_chat_cli.py` 把概念串起来

---

## 8. 本章小结

这一章你真正要建立的不是“会复制一段 SDK 示例”，而是以下 8 个核心认知：

1. 一次 LLM 调用是一个结构化请求，不是随便问一句话
2. 请求体最核心的是 `model + messages + 参数`
3. 响应对象里最重要的是 `content / finish_reason / usage`
4. 多轮对话本质上是应用侧管理历史消息
5. Token 决定成本、延迟和上下文容量
6. 历史不裁剪，多轮聊天一定会越来越贵
7. 参数调优的目标是控制输出风险，而不是追求神秘技巧
8. 一个最小聊天 CLI 已经包含了很多真实 AI 应用的雏形

如果这一章学扎实，后面的结构化输出、流式输出和服务封装都会更顺。

---

## 9. 练习建议

1. 把 `01_first_call.py` 中的 provider 改成你当前实际可用的平台，完成一次真实请求。
2. 在 `02_messages_chat.py` 中写两种完全不同的 `system prompt`，比较输出风格差异。
3. 在 `03_token_params.py` 中替换文本样例，比较中文、英文和中英混合的 token 差异。
4. 在 `03_token_params.py` 中，把你真实平台价格填进 `.env`，自己算一次成本。
5. 给 `04_chat_cli.py` 增加一个 `/context` 命令，打印当前会话估算 token。
6. 在 CLI 中连续对话 5-8 轮，然后用 `/trim` 和 `/stats` 观察裁剪前后的变化。
7. 用 `/export` 导出一次会话，打开 JSON 文件，观察它和后续结构化日志之间的联系。
