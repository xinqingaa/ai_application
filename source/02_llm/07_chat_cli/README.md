# 07. 综合项目 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/02_llm/07_chat_cli.md) 一步步完成第七章综合项目

---

## 核心原则

```text
先理解为什么课程最后要做综合项目 -> 再跑统一服务层 -> 再跑 CLI -> 再跑 API -> 最后通过导出、统计和命令模式把前六章能力真正串起来
```

- 在 `source/02_llm/07_chat_cli/` 目录下操作
- 这一章的重点不是“再写一个聊天 demo”，而是把前六章的能力收束成一个真实可运行的项目骨架
- 没有 API Key 时，CLI 和 API 依然可以在 mock 模式下完整练习，包括多轮会话、流式输出、JSON 模式、统计和导出
- 有真实模型时，依然优先建议百炼 / 通义、DeepSeek、GLM；教学理解继续参考 OpenAI / Claude / Gemini
- 第七章默认你已经完成前六章，因为它会直接复用消息管理、provider 切换、Prompt 文件、结构化输出、流式输出和可靠性控制这些能力

---

## 项目结构

```text
07_chat_cli/
├── README.md                    ← 你正在读的这个文件
├── .env.example                 ← 第七章环境变量模板
├── schemas.py                   ← 数据结构：消息、会话、统计、风控、结果对象
├── llm_service.py               ← 统一服务层：聊天、流式、成本、缓存、配额、导出
├── chat_cli.py                  ← 命令行项目入口
├── chat_api.py                  ← FastAPI 版本接口
├── prompts/
│   └── meeting_summary.txt      ← /prompt 命令练习样例
└── exports/                     ← 运行时导出的会话记录
```

---

## 前置准备

### 1. 安装依赖

推荐先进入虚拟环境，再安装：

```bash
pip install openai python-dotenv fastapi uvicorn
```

如果你想获得更准确的 token 估算，可以额外安装：

```bash
pip install tiktoken
```

### 2. 配置环境变量

把 `.env.example` 复制为 `.env`，按你当前可用的平台填写。

第七章建议优先完成两类实验：

1. 先用 mock 模式把命令流、状态管理、导出和 API 形态跑通
2. 再用真实 provider 对比不同平台下的普通输出、流式输出和成本统计

### 3. 运行方式

```bash
cd source/02_llm/07_chat_cli

python llm_service.py
python chat_cli.py --demo
python chat_cli.py
uvicorn chat_api:app --reload --port 8000
```

---

## 第 1 步：先跑统一服务层（文档第 2-4 章）

**对应文件**：`llm_service.py`  
**对应文档**：第 2 章「为什么课程最后要做综合项目」+ 第 3-4 章「项目分层与运行时状态」

### 这一步要解决什么

在真实项目里，CLI 和 API 不应该各写一套聊天逻辑。

你需要先有一个统一服务层，把这些东西收束进去：

- provider 读取
- 多轮消息管理
- JSON 模式
- 流式输出
- usage / cost 统计
- 缓存
- 配额
- 导出

### 操作流程

1. 先读文档第 2-4 章。
2. 打开 `llm_service.py`，重点看：
   - `ProjectLLMService`
   - `chat()`
   - `stream_chat()`
   - `export_session()`
3. 运行：

```bash
python llm_service.py
```

### 重点观察

- `TurnResult` 为什么要返回这么多字段，而不是只返回一段字符串
- mock 模式下是否仍然返回 `usage / cost / request_preview`
- 服务层是怎样同时兼顾会话、缓存、配额和导出的

### 建议主动修改

- 改 `daily_limit_tokens`
- 改 `cache_ttl_seconds`
- 改默认 provider
- 观察返回结构里 `json_mode / stream_mode / from_cache` 的作用

---

## 第 2 步：跑命令行项目（文档第 5-7 章）

**对应文件**：`chat_cli.py`  
**对应文档**：第 5 章「多轮对话 CLI 的命令设计」+ 第 6 章「从功能脚本走向项目入口」

### 这一步要解决什么

第七章的核心项目是一个真正可运行的多轮对话 CLI。

这个 CLI 不是简单输入一句、输出一句，它需要支持：

- 多轮会话
- provider 切换
- model 切换
- JSON 模式
- 流式输出
- 统计查看
- 会话导出
- 从文件加载 Prompt

### 操作流程

#### 方式 A：先跑内置 demo

```bash
python chat_cli.py --demo
```

#### 方式 B：进入交互模式

```bash
python chat_cli.py
```

### 重点观察

- `/json on` 后普通输出会发生什么变化
- `/stream on` 后为什么输出会逐段打印
- `/stats` 里哪些字段能帮助你理解项目运行状态
- `/export` 导出的 JSON 能否用来回放或排查问题

### 建议主动修改

- 用 `/provider deepseek` 或 `/provider glm` 切平台
- 用 `/model xxx` 手动指定模型
- 用 `/system ...` 改成更严格或更宽松的助手角色
- 反复发送几轮消息，观察 `turn_count` 和 `estimated_tokens_current_history`

---

## 第 3 步：练习从文件加载 Prompt（文档第 6-7 章）

**对应文件**：`chat_cli.py` + `prompts/meeting_summary.txt`  
**对应文档**：第 7 章「Prompt 文件、命令系统与项目可扩展性」

### 这一步要解决什么

前几章已经讲过 Prompt 不该永远写死在代码里。到了综合项目里，你应该能直接：

- 从文件加载 Prompt
- 把它作为本轮任务输入
- 在 JSON 模式和普通模式之间切换观察结果差异

### 操作流程

进入 CLI 后执行：

```text
/prompt prompts/meeting_summary.txt
```

或者先开 JSON 模式再发：

```text
/json on
/prompt prompts/meeting_summary.txt
```

### 重点观察

- `/prompt` 命令是“只读取文件”还是“读取并立即发送”
- 为什么文件 Prompt 会比长字符串更适合维护
- 在 JSON 模式下，输出是否更像程序接口

### 建议主动修改

- 自己在 `prompts/` 下新增一个总结、抽取或分类模板
- 故意写一版很模糊的 Prompt，对比输出变化
- 给 Prompt 加更严格的字段约束，观察 JSON 结果是否更稳定

---

## 第 4 步：跑 FastAPI 版本（文档第 8 章）

**对应文件**：`chat_api.py`  
**对应文档**：第 8 章「同一套服务层如何同时支撑 CLI 和 API」

### 这一步要解决什么

第七章不是做两个项目，而是证明：

> 同一套服务层，既可以支撑 CLI，也可以支撑 API。

### 操作流程

1. 启动服务：

```bash
uvicorn chat_api:app --reload --port 8000
```

2. 浏览器打开：

```text
http://localhost:8000/docs
```

3. 重点测试：
   - `GET /health`
   - `POST /chat`
   - `POST /chat/stream`
   - `GET /sessions/{session_id}`

### 重点观察

- `/chat` 和 CLI 是否共用同样的返回结构思路
- `/chat/stream` 的 SSE 事件是不是围绕统一服务层生成
- API 层是否只做了“请求映射”，而不是把业务逻辑再写一遍

### 建议主动修改

- 先在 `/chat` 里测试普通返回
- 再在 `/chat/stream` 里测试流式返回
- 在同一个 `session_id` 下连发两轮消息，观察历史变化

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 |
|---------|---------|---------|
| 第 2-4 章 | 综合项目设计、分层、状态管理 | `schemas.py`, `llm_service.py` |
| 第 5-7 章 | CLI 命令、Prompt 文件、项目入口 | `chat_cli.py`, `prompts/meeting_summary.txt` |
| 第 8 章 | API 复用、SSE 接口、统一服务层 | `chat_api.py`, `llm_service.py` |
| 第 9 章 | 统计、导出、回顾前六章能力 | `llm_service.py`, `exports/` |

---

## 建议的学习顺序

1. 先跑 `llm_service.py`
2. 再跑 `chat_cli.py --demo`
3. 然后进入 `chat_cli.py` 交互模式
4. 练习 `/prompt`、`/stats`、`/export`
5. 最后启动 `chat_api.py`

这个顺序对应的能力递进是：

1. 先看服务层是否成立
2. 再看 CLI 是否把服务层用起来
3. 再练命令式状态管理
4. 再看导出和可观测性
5. 最后理解同一内核怎样复用到 API

---

## 推荐的一轮完整练习

你可以按下面这一轮走一遍：

```text
1. python chat_cli.py
2. 输入一条普通问题
3. /json on
4. 再问一条需要结构化结果的问题
5. /stream on
6. 再问一条长一点的问题
7. /stats
8. /prompt prompts/meeting_summary.txt
9. /export
10. /quit
```

如果这一轮走通，你基本就已经把前六章的大部分核心能力串起来了。

---

## 你完成本章后应该达到什么程度

如果这一章学完后你已经能做到下面这些事，就说明综合项目落地是成功的：

- 能说明为什么 CLI、API、服务层要分开
- 能写一个支持多轮会话和命令状态的最小聊天项目
- 能在项目里接入 JSON 模式、流式输出、统计和导出
- 能把 provider 切换、Prompt 文件、成本统计和安全检查放进统一服务层
- 能看懂一个 AI 应用从“脚本集合”走向“项目骨架”的关键转折点
