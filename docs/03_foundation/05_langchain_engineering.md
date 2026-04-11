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

### 当前状态与第一入口

当前这一章仍然属于“代码前置设计”，不是现成项目说明。

所以当前第一入口是：

- 本文档本身

它当前负责固定未来工程骨架，而不是解释一个已经存在的完整代码目录。

未来正式编码时，这一章对应的第一批核心文件应是：

- `source/03_foundation/foundation_lab/app/config.py`
- `source/03_foundation/foundation_lab/app/llm/client_native.py`
- `source/03_foundation/foundation_lab/app/llm/client_langchain.py`
- `source/03_foundation/foundation_lab/app/services/qa_service.py`
- `source/03_foundation/foundation_lab/app/main.py`

未来项目真正可运行后，第一运行入口应转移到：

- `source/03_foundation/foundation_lab/README.md`

### 建议学习顺序

建议按这个顺序读：

1. 先读 `2-3`，理解为什么 `03` 阶段必须先把结构做对
2. 再读 `4-5`，固定目录分层和 `service` 的必要性
3. 最后读 `6-8`，确认日志、测试、API 应做到什么程度，以及未来第一批文件清单

卡住时回看：

1. `3. 原生 SDK 和 LangChain 为什么要同时保留`
2. `4. foundation_lab 的建议分层`
3. `5. 为什么 service 层必须存在`

### 计划代码映射

| 文档部分 | 对应代码/文档 | 角色 | 说明 |
|----------|---------------|------|------|
| `2. 为什么 03 阶段必须讲工程化` | 本文档 | 第一阅读入口 | 固定工程化目标，避免脚本化失控 |
| `3. 原生 SDK 和 LangChain` | 未来 `client_native.py`、`client_langchain.py` | 对照实现 | 保持透明与组件化双轨理解 |
| `4. foundation_lab 的建议分层` | 未来 `app/config.py`、`app/llm/`、`app/prompts/`、`app/chains/`、`app/retrievers/`、`app/tools/`、`app/services/`、`app/observability/` | 计划目录骨架 | 固定最小项目职责 |
| `5. service 层必须存在` | 未来 `qa_service.py` | 计划主编排入口 | 防止接口层堆业务判断 |
| `6. 日志、测试和 API` | 未来 `logger.py`、`tests/`、`main.py`、项目 README | 计划收口路径 | 说明最小工程化要做到什么程度 |

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

## 8. 实施动作

当前这章的实施动作，是先把未来工程骨架固定成可以直接落地的清单：

1. 明确哪些文件属于配置、模型、Prompt、链路、检索、工具、服务和观测
2. 明确 `service` 作为统一编排层必须独立存在
3. 明确日志、测试、API 的最低完成线
4. 明确项目 README 未来需要承担哪些说明职责

当前阶段的输入是：

1. [04_langchain_core_abstractions.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/04_langchain_core_abstractions.md)
2. 本文档中的分层与职责说明

当前阶段的输出是：

1. 一份不再摇摆的目录和文件职责清单
2. 一套最小工程化边界
3. 一份未来项目 README 的责任清单

卡住时优先回看：

1. `4. foundation_lab 的建议分层`
2. `5. 为什么 service 层必须存在`
3. `6. 03 阶段的日志、测试和 API 到什么程度`

---

## 9. 本章学完你应该做到什么

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

## 10. 完成标准

### 理解层

- 能解释为什么 `foundation_lab` 不能写成一个大脚本
- 能解释为什么原生 SDK 和 LangChain 要同时保留
- 能解释为什么 `service` 层必须存在

### 操作层

- 能按建议顺序读完整章重点
- 能列出未来第一批要创建的核心文件
- 卡住时知道该回看哪几个关键小节

### 代码准备层

- 能说明未来项目最小分层如何组织
- 能说明日志、测试、API、README 的最低完成线
- 能说明当前章节是在固定工程骨架，不是在假装项目已经写完

### 映射层

- 能说清本章与未来 `config.py`、`client_native.py`、`client_langchain.py`、`qa_service.py`、`main.py` 的关系
- 能说清本章与 `06-07` 的承接关系

---

## 11. 本章小结

这一章你真正应该带走的是：

1. `03` 的工程化目标是建立最小但正确的骨架
2. 原生 SDK 负责透明，LangChain 负责组件化，两者都值得保留
3. `config / llm / prompts / chains / retrievers / tools / services` 是合理的最小分层
4. `service` 层是后续从示例走向项目的关键
5. 从这一章开始，`foundation_lab` 已经不只是一个想法，而是可以正式开始搭建的项目
