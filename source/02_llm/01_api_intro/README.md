# 01. LLM API 调用入门 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/02_llm/01_api_intro.md) 一步步动手操作

---

## 核心原则

```text
读文档 -> 看对应代码 -> 运行验证 -> 修改参数观察现象 -> 总结为什么会这样
```

- 在 `source/02_llm/01_api_intro/` 目录下操作
- 这一章的目标不是“会复制 SDK 示例”，而是弄清一次 LLM 调用到底发生了什么
- 每个脚本都尽量独立可运行
- 没有 API Key 时，也可以先用 mock 模式把调用流程走通
- 如果你已经有国内 OpenAI-compatible 平台配置，这一章就可以直接真实练习

---

## 项目结构

```text
01_api_intro/
├── README.md              ← 你正在读的这个文件
├── .env.example           ← 环境变量模板
├── llm_utils.py           ← 第一章公共工具：配置、调用、token、导出
├── 01_first_call.py       ← 第 1 步：第一条请求（文档第 2 章）
├── 02_messages_chat.py    ← 第 2 步：消息格式与多轮对话（文档第 3 章）
├── 03_token_params.py     ← 第 3 步：Token / 上下文 / 参数 / 成本（文档第 4-5 章）
├── 04_chat_cli.py         ← 第 4 步：最小可用聊天 CLI（文档第 6 章）
└── exports/               ← 运行时自动生成：会话导出文件
```

---

## 前置准备

### 1. 安装依赖

推荐先进入虚拟环境，再安装：

```bash
pip install openai python-dotenv tiktoken
```

依赖说明：

- `openai`：用于调用 OpenAI-compatible 平台
- `python-dotenv`：从 `.env` 自动加载环境变量
- `tiktoken`：做更准确的 Token 估算

### 2. 配置环境变量

把 `.env.example` 复制为 `.env`，按你当前可用的平台填写。

本章推荐优先用以下平台完成真实实验：

1. 百炼 / 通义千问
2. DeepSeek
3. GLM

只要平台支持 OpenAI-compatible 协议，就能直接复用本章代码。

### 3. 运行方式

```bash
cd source/02_llm/01_api_intro

python 01_first_call.py
python 02_messages_chat.py
python 03_token_params.py
python 04_chat_cli.py
```

---

## 第 1 步：第一条请求（文档第 2 章）

**对应文件**：`01_first_call.py`  
**对应文档**：第 2 章「环境准备与第一条请求」

### 操作流程

1. 先读文档第 2 章，重点理解：
   - 一次最小调用需要什么
   - 请求体由哪些部分组成
   - 响应对象里最重要的字段是什么

2. 打开 `01_first_call.py`，按顺序看这几个函数：
   - `print_config_summary()`：看当前实际运行配置
   - `print_request_anatomy()`：看请求体结构
   - `print_response_anatomy()`：理解响应对象字段
   - `run_call_demo()`：真实或 mock 调用
   - `print_common_failures()`：常见错误排查

3. 运行：

```bash
python 01_first_call.py
```

### 重点观察

- `provider / base_url / model` 是否和你的预期一致
- `request_preview` 是否真的包含 `messages / temperature / max_tokens`
- `response_preview` 里哪些字段最值得你关心
- 如果当前没有 API Key，mock 模式的输出是否能帮助你理解完整链路

### 建议主动修改

- 修改 `prompt`
- 修改 `temperature`
- 改成你真实使用的平台和模型
- 故意把 model 写错一次，体验错误排查顺序

---

## 第 2 步：消息格式与多轮对话（文档第 3 章）

**对应文件**：`02_messages_chat.py`  
**对应文档**：第 3 章「消息格式与多轮对话」

### 操作流程

1. 先读文档第 3 章，理解：
   - `system / user / assistant`
   - 为什么模型不会自己记住历史
   - 为什么会话状态本质上是应用层管理

2. 运行：

```bash
python 02_messages_chat.py
```

3. 重点看代码中的几部分：
   - `Conversation`：最小历史管理器
   - `print_single_vs_multi_turn()`：单轮和多轮消息结构
   - `demo_system_prompt_comparison()`：两个不同 system prompt 如何改变回答风格
   - `demo_conversation_manager()`：如何裁剪历史并导出会话

### 重点观察

- 单轮和多轮的 token 估算差异
- `system prompt` 改变后，模型风格为什么会变化
- 历史裁剪前后，消息列表和 token 估算怎么变
- 导出的 JSON 会话文件长什么样

### 建议主动修改

- 改两个对比用的 system prompt
- 给 Conversation 多加两轮消息
- 把 `keep_last_messages` 改大或改小

---

## 第 3 步：Token、上下文、参数和成本（文档第 4-5 章）

**对应文件**：`03_token_params.py`  
**对应文档**：第 4 章「Token、上下文窗口与成本」+ 第 5 章「常用参数」

### 操作流程

1. 运行：

```bash
python 03_token_params.py
```

2. 这个脚本会按顺序展示：
   - 文本 token 对比
   - 消息历史的 token 预算
   - 两种裁剪方法
   - 成本估算公式
   - 参数预设
   - 如何设计参数实验

3. 如果安装了 `tiktoken`，Token 估算会更准确；没有安装时会退回启发式估算。

### 重点观察

- 中文、英文、中英混合文本的 token 差异
- 同一段历史，按“最近消息裁剪”和“按预算裁剪”有什么不同
- 成本估算公式如何从 usage 推导出来
- 为什么参数实验要一次只改一个变量

### 建议主动修改

- 替换文本样例
- 修改 `max_input_tokens`
- 按你实际平台价格填写 `.env` 中的单价
- 自己设计一组参数预设

---

## 第 4 步：最小可用聊天 CLI（文档第 6 章）

**对应文件**：`04_chat_cli.py`
**对应文档**：第 6 章「从最小调用走向最小工具」

### 构建顺序

如果你现在读 `04_chat_cli.py` 会觉得"代码不少，不知道从哪下手"，先记住一句话：

> `04_chat_cli.py` 本质上就是：`while True` 循环 + 会话历史 `messages` + 一次模型调用 + 若干控制命令

也就是说，它不是一个神秘的大程序，而是把前面三节学过的东西串起来：

1. 用 `llm_utils.py` 发一次请求
2. 用 `ConversationState` 保留历史
3. 用 `handle_command()` 处理 `/help`、`/trim`、`/export` 这些控制命令
4. 用 `SessionStats` 累计 usage

### 先看骨架，不要先看细节

建议按下面的顺序读代码：

```text
第 1 遍：只看 main()
  找 while True
  找 state.add_user()
  找 call_openai_compatible_chat()
  找 state.add_assistant()

第 2 遍：只看 ConversationState
  看 system_prompt 怎么进入 messages
  看 user / assistant 怎么写回历史
  看 trim() 为什么只裁剪历史

第 3 遍：只看 handle_command()
  看命令为什么不发给模型
  看 /system /model /trim /mock /log 分别改了什么状态

第 4 遍：再看 stats 和 export
  理解 usage 为什么要累计
  理解为什么要把会话导出为 JSON
```

### 启动流程图

先把程序启动时发生的事看清楚：

```text
启动脚本
-> load_env_if_possible()      读取 .env
-> load_provider_config()      生成 config
-> ConversationState(...)      创建会话历史，先放 system prompt
-> SessionStats()              创建统计对象
-> force_mock                  决定默认是否用 mock
-> show_log=False              默认不打印额外日志
-> 进入 while True             开始聊天循环
```

### 一轮对话的主流程

真正的聊天主线只有这一条：

```text
用户输入
-> 判断是不是 / 开头的命令
-> 如果是命令：handle_command() 本地处理
-> 如果不是命令：
   state.add_user(raw)
   -> 用当前 messages 发请求
   -> 得到 result
   -> 如果 show_log=True，打印简要日志
   -> state.add_assistant(result.content)
   -> stats.add_usage(result.usage)
   -> 打印 AI 回复
```

你可以把多轮对话理解成一句话：

> 每轮都把当前完整历史重新发给模型，而不是指望模型自动记住你上一轮说过什么。

### main() 主循环逐段拆解

如果你现在最困惑的是 `main()`，建议只盯着 `while True` 这一段。它可以拆成 8 步：

1. `raw = input("\n> ").strip()`
   作用：读取一行终端输入。
   这里拿到的只是原始字符串，还没有决定它是“命令”还是“聊天内容”。

2. `if not raw: continue`
   作用：空输入直接跳过，避免无意义进入后续流程。

3. `if raw.startswith("/")`
   作用：先把 `/help`、`/trim`、`/mock`、`/log` 这类命令分流出去。
   关键认知：
   只要是 `/` 开头，就应该先由 CLI 本地处理，而不是发给模型。

4. `handle_command(...)`
   作用：命令命中后，直接修改本地状态或打印提示。
   例如：
   - `/system` 修改 `state.system_prompt`
   - `/model` 修改 `config.model`
   - `/mock` 修改 `force_mock`
   - `/log` 修改 `show_log`

5. `state.add_user(raw)`
   作用：如果这不是命令，而是一条正常聊天消息，就先把用户输入写入历史。
   这是多轮对话成立的第一步。

6. `messages = list(state.messages)`
   作用：生成本轮调用的上下文快照。
   为什么要这样做：
   因为模型本轮真正能看到的，就是此刻这份完整 `messages` 列表。

7. `call_openai_compatible_chat(...)` 或 `mock_chat_response(...)`
   作用：真正拿模型结果。
   分支逻辑是：
   - 正常模式：优先走真实请求
   - 失败或未配置 key：走 mock

8. `state.add_assistant(...)` + `stats.add_usage(...)` + 打印输出
   作用：
   - 把 assistant 回复写回历史
   - 把 usage 累计到统计对象
   - 打印 `AI:`、`usage`、`history_estimated_tokens`

你可以把主循环压缩成这一条：

```text
读输入
-> 先分流命令
-> 如果不是命令，就写入 user 历史
-> 用当前完整历史发请求
-> 拿到结果后写回 assistant 历史
-> 更新统计并打印输出
```

### 为什么你之前输入 /log 会发给模型

如果命令分流写得不严，就会出现一种很常见的 bug：

```text
用户输入 /log
-> 没有命中具体命令分支
-> 程序继续往下走
-> state.add_user("/log")
-> /log 被当成普通聊天文本发给模型
```

所以命令分流有一个很重要的原则：

> 只要输入是 `/` 开头，就不应该默认落到模型调用链里。

正确行为应该是：

- 命中命令：本地处理
- 命令写法不完整：本地提示用法
- 未知命令：本地提示“输入 /help 查看帮助”

### 从 0 构建 ChatCLI 的正确顺序

不要一上来就想着"我要写一个完整聊天工具"，那样很容易乱。正确顺序是：

```text
阶段 1：先能发一条请求
  用户输入 -> messages -> call -> print(content)

阶段 2：再加 while True
  让它可以连续输入，但这时还没有历史

阶段 3：再加 ConversationState
  把 user / assistant 历史都写回 messages

阶段 4：再加 handle_command
  让 /help /trim /model /system 这些命令不走模型调用

阶段 5：最后加 stats / export / show_log
  让它从“能聊天”升级到“能观察、能统计、能复盘”
```

### 先分清两类参数

读 CLI 时，最容易混淆的是"哪些参数发给模型，哪些参数只是 CLI 自己用"。

| 参数类型 | 例子 | 作用 |
|---------|------|------|
| 模型请求参数 | `temperature`、`max_tokens` | 真正发给模型，影响生成结果 |
| 应用运行参数 | `keep_last_messages`、`force_mock`、`show_log` | 只影响 CLI 自己的行为，不直接发给模型 |

其中 `show_log` 是这一章新增的一个**应用侧调试参数**：

- `False`：保持当前简洁输出
- `True`：额外打印本轮简要日志

它的目标不是改变模型回答，而是帮助你观察：

- 本轮到底发了什么 `request_preview`
- 模型为什么停下，`finish_reason` 是什么
- 平台返回了什么 `response_preview`
- 有没有 `usage`

### 操作流程

1. 运行：

```bash
python 04_chat_cli.py
```

2. 先输入一个普通问题，确认能得到回复。

3. 然后依次尝试以下命令：

```text
/help
/params
/history
/stats
/trim 6
/system 你是一个严谨的技术助教，回答控制在 100 字内。
/log on
/export
/quit
```

### 重点观察

- CLI 里真正的状态是什么
- 历史消息如何增长
- `/trim` 后输入 token 估算如何变化
- `/stats` 如何累计 usage 和成本
- `show_log` 打开后，`request_preview / finish_reason / response_preview` 会如何出现
- `/export` 导出的会话 JSON 长什么样

### 调试建议：使用 /log 切换 show_log

初学阶段，你很容易只盯着 `AI: ...` 这一行，但真正有教学价值的其实还有：

- 请求到底带了哪些 `messages`
- 本轮 `finish_reason` 是 `stop` 还是 `length`
- 平台有没有返回 `usage`

CLI 提供了 `/log` 命令来切换 `show_log`：

```text
> /log on
已开启 show_log 简要日志。

> 什么是 token？
AI: Token 是模型处理文本的最小单位...
[log] show_log=True，本轮简要日志如下：
{
  "provider": "bailian",
  "model": "qwen-plus",
  "mocked": false,
  "finish_reason": "stop",
  "usage": {...},
  "request_preview": {...},
  "response_preview": {...}
}

> /log off
已关闭 show_log 简要日志。
```

- `/log on`：开启后，`show_log=True`，每轮对话会额外打印简要日志
- `/log off`：关闭后回到简洁输出
- 默认关闭，不影响正常使用体验

建议在以下场景开启 `/log`：
- 想观察 `finish_reason` 是 `stop` 还是 `length`（判断输出是否被截断）
- 想确认发给模型的消息列表是否正确
- 想对比 mock 模式和真实模式的响应结构差异

### 建议主动修改

- 给 CLI 增加一个 `/context` 命令，打印当前估算 token
- 改 system prompt，再做几轮对话
- 开启 `/log on` 后观察一次真实调用，再关闭对比终端输出差异
- 在真实模式和 mock 模式之间切换，比较体验差异

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 |
|---------|---------|---------|
| 第 2 章 | 第一条请求、请求体、响应体、错误排查 | `01_first_call.py` |
| 第 3 章 | `messages` 结构、多轮对话、system prompt、历史管理 | `02_messages_chat.py` |
| 第 4-5 章 | Token、上下文预算、成本公式、参数建议 | `03_token_params.py` |
| 第 6 章 | 最小聊天工具、命令、统计、导出 | `04_chat_cli.py` |
| 整章通用 | provider 配置、模型调用、token 估算、导出 | `llm_utils.py` |

---

## 建议的学习顺序

1. 先跑 `01_first_call.py`
2. 再看 `02_messages_chat.py`
3. 再理解 `03_token_params.py`
4. 最后重点玩 `04_chat_cli.py`

这个顺序对应的学习目标是：

1. 先知道怎么发请求
2. 再知道多轮对话怎么维持
3. 再知道为什么会越来越贵
4. 最后把这些概念串成一个最小工具

---

## 常见问题

### 1. 没有 API Key，能不能学？

可以。这一章所有脚本都支持 mock 路径。你可以先把请求结构、消息历史、Token 估算、CLI 流程学明白，再补真实平台配置。

### 2. 为什么第一章就做 CLI？

因为 CLI 是最小可用产品雏形。只要你能做出一个会保留历史、能统计 usage、能导出会话的 CLI，后面做 API 服务和前端就顺很多。

### 3. 为什么这里没有直接上流式输出？

因为第一章的目标是先把同步调用、消息结构、Token 和参数打牢。流式输出会在后面章节单独讲，否则第一章心智负担会太重。
