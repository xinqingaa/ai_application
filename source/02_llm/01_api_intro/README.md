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
/export
/quit
```

### 重点观察

- CLI 里真正的状态是什么
- 历史消息如何增长
- `/trim` 后输入 token 估算如何变化
- `/stats` 如何累计 usage 和成本
- `/export` 导出的会话 JSON 长什么样

### 建议主动修改

- 给 CLI 增加一个 `/context` 命令，打印当前估算 token
- 改 system prompt，再做几轮对话
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
