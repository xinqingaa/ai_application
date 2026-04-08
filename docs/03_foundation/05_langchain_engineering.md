# 05. LangChain 工程化基础

> 本节目标：在已经理解 LangChain 核心抽象的基础上，把这些抽象真正落成 `foundation_lab` 的工程结构，明确目录、配置、分层、日志、测试和接口边界，让 `03` 阶段从“写示例”进入“写最小项目骨架”

---

## 1. 概述

### 学习目标

- 理解为什么 `foundation_lab` 不能写成一个大脚本
- 理解原生 SDK 与 LangChain 为什么要在项目里同时保留
- 理解 `config / llm / prompts / chains / retrievers / tools / services` 的分层职责
- 理解为什么 `service` 层必须存在
- 知道 `03` 阶段的日志、测试、接口应该做到什么程度

### 预计学习时间

- 工程目标与分层思路：0.5-1 小时
- 目录结构和模块职责：1 小时
- 原生 SDK / LangChain 双轨设计：0.5 小时
- 最小日志、测试、API 设计：0.5-1 小时

### 本节在整体路径中的重要性

| 工程问题 | 本章解决方式 |
|---------|-------------|
| 代码写散 | 用清晰分层控制职责 |
| Prompt 到处拷贝 | 放入独立 prompts 层 |
| 业务判断堆在接口里 | 引入 service 层 |
| 想学框架却没有项目骨架 | 用 `foundation_lab` 建立最小工程结构 |
| 到 04/05 重新推翻重写 | 先在 03 把结构做对 |

> **这一章解决的核心问题不是“项目有多复杂”，而是“项目结构是否正确，是否能支撑后续扩展”。**

### 本章的学习边界

这一章重点解决：

1. `foundation_lab` 应该如何分层
2. 为什么要同时保留原生 SDK 和 LangChain
3. 为什么 `service` 层比直接从 API 调 chain 更合理
4. 03 阶段的最小日志、测试和接口如何设计

这一章不展开：

- 数据库接入
- Docker 部署
- 权限系统
- 异步任务队列
- 生产级可观测性平台

这些都不是 `03` 阶段应承担的复杂度。

### 本章与前后章节的衔接

上一章 [04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md) 解决的是：

- 核心抽象是什么
- 最小链怎么写

这一章要继续把这些抽象落成：

- 一个真正可维护的最小项目结构

再往后：

- [06_foundation_lab_design.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/06_foundation_lab_design.md) 会给出完整项目设计
- [07_foundation_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/07_foundation_lab_tasks.md) 会给出明确实施顺序

---

## 2. 为什么 03 阶段必须讲工程化 📌

如果 `03` 只讲原理和抽象，不讲工程化，后面通常会出现三个问题：

1. 到了 `04` 才开始想目录怎么拆
2. 到了 `05` 才开始想配置、日志、接口怎么组织
3. 虽然懂概念，但代码仍然写成一团脚本

所以 `03` 阶段讲工程化，不是为了做完整平台，而是为了让你在复杂度还低的时候，把结构做对。

一句话说，就是：

- `03` 阶段要解决“项目骨架”
- `04/05` 阶段再解决“能力深度”

---

## 3. 原生 SDK 和 LangChain 为什么要同时保留 📌

### 3.1 原生 SDK 的价值

原生 SDK 的优点很直接：

- 透明
- 接近底层调用本质
- 更容易定位 provider 级问题

对于学习来说，它会帮助你知道：

- 如果不用框架，自己到底需要写哪些胶水代码

### 3.2 LangChain 的价值

LangChain 的优点也很直接：

- 组件化
- 组合能力强
- 更容易迁移到 RAG / Agent

它会帮助你从“会调用一次模型”过渡到：

- 会组织一条稳定的数据流

### 3.3 为什么 foundation_lab 两者都要保留

在 `foundation_lab` 中，两者并存不是重复，而是刻意设计。

你应该同时保留：

- `client_native.py`
- `client_langchain.py`

这样你才能真正看清：

- 哪些能力是模型 API 本身提供的
- 哪些是 LangChain 帮你组织出来的

这一步对后续做 RAG、Agent 非常有价值。

---

## 4. foundation_lab 的建议分层 📌

建议的最小结构是：

```plain
app/
  config.py
  main.py
  schemas.py
  llm/
  prompts/
  chains/
  retrievers/
  tools/
  services/
  observability/
scripts/
tests/
```

下面要解决的是：每一层到底负责什么。

### 4.1 config

负责：

- 模型名
- base URL
- API key 环境变量读取
- timeout
- retry
- 是否开启流式

原则：

- 不让这些配置散落在脚本里

### 4.2 llm

负责：

- 原生 SDK 调用
- LangChain 模型调用
- 提供最小统一接口

原则：

- 模型初始化逻辑不要混进业务层

### 4.3 prompts

负责：

- Prompt 模板本身
- Prompt 输入变量说明

原则：

- Prompt 不内联到业务函数里

### 4.4 chains

负责：

- 把 `prompt -> llm -> parser` 明确串起来

原则：

- 让数据流显式可见

### 4.5 retrievers

负责：

- 知识入口能力

在 `03` 阶段只做：

- `mock_retriever`

### 4.6 tools

负责：

- 动作能力

在 `03` 阶段只做：

- `mock_tool`

### 4.7 services

负责：

- 业务编排
- 路径选择
- 统一入口

这一层非常重要，因为它会决定你的项目是不是“有骨架”。

### 4.8 observability

负责：

- logger 初始化
- 记录请求入口、路径、耗时、错误

`03` 阶段到这里就够了。

---

## 5. 为什么 service 层必须存在 📌

很多初学者在这个阶段会这么写：

- API 直接调 chain
- API 里再判断要不要 retriever
- API 里再决定要不要工具

短期看很快，长期看会有几个问题：

1. 接口层职责越来越重
2. 检索和工具逻辑会散掉
3. 到 `04/05` 很难扩展成更复杂流程

所以在 `foundation_lab` 阶段就应该建立这个习惯：

- 接口层只负责入参与返回
- service 层负责业务组织

举个最小伪代码：

```python
def ask(question: str) -> str:
    if should_use_tool(question):
        return tool_answer(question)
    if should_use_retriever(question):
        return retrieval_answer(question)
    return normal_answer(question)
```

这还不是 Agent，但它已经在建立正确的编排入口。

---

## 6. 03 阶段的日志、测试和 API 到什么程度 📌

### 6.1 日志：先建立意识，不做重平台

你现在只需要做到：

- 有统一 logger
- 记录一次请求走了哪条路径
- 记录是否报错和大致耗时

不要现在做：

- 复杂 Trace 平台
- 全链路监控面板
- 多环境日志采集系统

### 6.2 测试：最小可控就够

建议只写几类轻量测试：

- Prompt 是否能正常格式化
- `mock_retriever` 是否能返回预期结果
- `mock_tool` 是否能得到预期结果

你现在的目标不是高覆盖率，而是建立：

- 组件可验证的习惯

### 6.3 API：只要最小可演示

`foundation_lab` 的 API 建议只提供：

- `POST /ask`
- `POST /ask/stream`

目的不是做完整服务，而是：

- 让最小骨架可运行、可演示、可后续迁移

---

## 7. foundation_lab 中你真正要写哪些代码 📌

从这篇开始，项目已经不是“示例集合”，而是“最小工程骨架”。

最小要求包括：

1. `config.py` 管配置
2. `client_native.py` 管原生调用
3. `client_langchain.py` 管 LangChain 调用
4. `qa_prompt.py` 管最小问答 Prompt
5. `qa_chain.py` 管 LCEL 链
6. `mock_retriever.py` 管知识入口样例
7. `mock_tools.py` 管动作能力样例
8. `qa_service.py` 管统一编排
9. `main.py` 暴露最小 API

也就是说，真正开始贴近 `foundation_lab` 的节点，可以这样理解：

- `04` 开始进入代码抽象
- `05` 开始进入项目骨架

这是我建议你现在的主节奏。

---

## 8. 本章学完你应该做到什么

你不需要做到：

- 写复杂项目
- 做完整部署
- 接入数据库和异步任务

你应该做到：

- 明白 `foundation_lab` 为什么不能写成一个脚本
- 明白为什么原生 SDK 和 LangChain 要同时保留
- 明白为什么 `service` 层必须存在
- 明白 `03` 阶段最小工程化做到什么程度就够
- 可以开始真正搭 `foundation_lab` 的目录和空骨架

---

## 9. 本章小结

这一章你真正应该带走的是：

1. `03` 的工程化目标是建立最小但正确的骨架
2. 原生 SDK 负责透明，LangChain 负责组件化，两者都值得保留
3. `config / llm / prompts / chains / retrievers / tools / services` 是合理的最小分层
4. `service` 层是后续从示例走向项目的关键
5. 从这一章开始，`foundation_lab` 已经不只是一个想法，而是可以正式开始搭建的项目
