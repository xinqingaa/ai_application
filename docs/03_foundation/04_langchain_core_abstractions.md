# 04. LangChain 核心抽象

> 本节目标：从这一章开始，`03_foundation` 正式进入代码和工程实践。你将不再只是理解概念，而是开始用 LangChain 的核心抽象组织 `foundation_lab` 的最小代码骨架，为后续 `04_rag` 和 `05_agent` 建立统一执行模型

---

## 1. 概述

### 学习目标

- 理解为什么 `03` 阶段要开始引入 LangChain
- 掌握 `Model / Prompt / OutputParser / Runnable / Retriever / Tool` 这几个核心抽象
- 能用这些抽象解释 `foundation_lab` 的最小结构
- 能写出最小 `prompt -> llm -> parser` 链
- 能初步区分“检索能力”和“工具能力”

### 预计学习时间

- 为什么要学 LangChain：0.5 小时
- 核心抽象理解：1.5 小时
- 最小 LCEL 代码：1 小时
- `foundation_lab` 中的映射关系：0.5-1 小时

### 本节在整体路径中的重要性

| 场景 | 对应抽象 |
|------|---------|
| 模型调用组件化 | `Model` |
| Prompt 独立管理 | `PromptTemplate` |
| 输出可消费 | `OutputParser` |
| 数据流显式化 | `Runnable / LCEL` |
| 知识入口 | `Retriever` |
| 动作能力 | `Tool` |

> **这一章解决的核心问题不是“会不会用 LangChain”，而是“能不能从一堆脚本思维，转成组件化的 AI 应用工程思维”。**

### 本章的学习边界

这一章重点解决：

1. 为什么要在 `03` 阶段开始写 LangChain 代码
2. 哪些抽象最值得先学
3. 这些抽象在 `foundation_lab` 中如何落位
4. 什么地方该写最小代码，什么地方还不必展开

这一章不展开：

- 真正的向量数据库接入
- 真实 RAG Chain
- 真正的 Agent Executor
- LangGraph 状态流

这些分别属于 `04_rag` 和 `05_agent`。

### 本章与前后章节的衔接

前三章解决的是：

- 模型是什么
- 上下文为什么重要
- 方案该怎么选

从这一章开始，真正进入：

- 如何把这些理解组织成代码

下一章 [05_langchain_engineering.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/05_langchain_engineering.md) 会继续把这些抽象落成 `foundation_lab` 的工程结构。

所以这一章本质上是：

> 从“理解 AI 应用为什么这样设计”，过渡到“开始把它写成最小工程骨架”。

---

## 2. 为什么要在 03 阶段学 LangChain 📌

### 2.1 不是因为 LangChain 必须用

先把这个边界说清楚：

- LangChain 不是必须用的

很多能力你都可以用原生 SDK 自己组织出来。

但 `03` 阶段引入 LangChain 的价值在于：

- 它能更清楚地暴露 AI 应用里的核心对象
- 它能让你提前建立 RAG 和 Agent 的统一数据流心智

### 2.2 它最适合解决什么问题

LangChain 最适合帮助你解决：

- 模型调用如何组件化
- Prompt 如何组件化
- 输出解析如何组件化
- 检索和工具如何进入统一执行流

这正好对应 `foundation_lab` 的目标：

- 不是做复杂产品
- 而是把抽象和结构做对

### 2.3 为什么现在开始写代码是合理的

从这一章开始正式写代码，是因为：

- 前三章解决的是认知和判断
- 如果这里还不动手，后面的 `04/05` 会缺少抽象基础

所以这里的代码目标不是“大”，而是“最小但正确”。

---

## 3. 六个最核心的抽象 📌

## 3.1 Model

`Model` 解决的是：

- 如何统一调用模型

在工程里你最应该关心的是：

- 模型怎么初始化
- 参数怎么配置
- 如何支持普通调用和流式调用

在 `foundation_lab` 中，这一层会保留两套实现：

- 原生 SDK
- LangChain 封装

目的不是重复，而是对照。

### 3.2 Prompt

`Prompt` 解决的是：

- 如何稳定组织输入

在工程里它意味着：

- Prompt 不应该散落在函数内部
- Prompt 应该是独立组件
- Prompt 应该支持变量注入

### 3.3 OutputParser

`OutputParser` 解决的是：

- 模型输出如何进入下游程序

你后面会越来越频繁遇到这个问题：

- 模型输出不是“给人看就行”，而是要给系统继续消费

所以 parser 的价值不是装饰，而是：

- 让模型输出变成程序可消费结果

### 3.4 Runnable / LCEL

这是 LangChain 最值得在 `03` 阶段学的部分。

因为它会把 AI 应用里的执行流程显式表达成：

```plain
input -> prompt -> llm -> parser
```

它的意义在于：

- 不再把模型调用当成黑盒函数
- 而是把数据流拆成可观察、可替换、可扩展的组件链

### 3.5 Retriever

`Retriever` 解决的是：

- 给定 query，返回相关文档

你现在先不要把它和向量数据库绑死。

更成熟的理解应该是：

- 向量数据库只是 retriever 的一种底层实现
- `Retriever` 本身表达的是“知识入口能力”

在 `foundation_lab` 里，你会先做：

- `mock_retriever`

### 3.6 Tool

`Tool` 解决的是：

- 给模型一个“可调用的动作能力”

它可以是：

- API
- 函数
- 数据库操作
- 文件系统能力

这一层是后续 `Agent` 的核心入口，但在 `03` 阶段你只需要先理解：

- 它和 `Retriever` 不是一回事

---

## 4. 在 foundation_lab 里这些抽象怎么落位 📌

### 4.1 最小链路

`foundation_lab` 里第一条真正要跑通的链是：

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个严谨的技术助理"),
    ("human", "请简要解释：{topic}")
])

chain = prompt | llm | StrOutputParser()

result = chain.invoke({"topic": "什么是 Retriever"})
print(result)
```

这段代码的重要性不在于它有多复杂，而在于它把三个核心抽象显式串起来了：

- Prompt
- Model
- Parser

### 4.2 第二步该补什么

最小链跑通后，再补两条边：

1. `mock_retriever`
2. `mock_tool`

然后让 `service` 层统一组织：

- 普通问答
- 检索增强问答
- 工具辅助问答

### 4.3 为什么这里先不做真正 Agent

因为 `03` 的任务是理解抽象，不是提前把 `05` 做掉。

如果这里过早进入：

- 自动工具选择
- 多步推理循环
- 状态流转

那你会在错误阶段引入过高复杂度。

---

## 5. 原生 SDK 和 LangChain 的对照关系 📌

这一章非常重要的一点，是你要开始同时保留两套理解：

### 原生 SDK 的价值

- 透明
- 接近本质
- 更容易定位底层问题

### LangChain 的价值

- 组件化
- 更容易扩展到 RAG 和 Agent
- 更容易建立统一工程结构

所以在 `foundation_lab` 中，你应该同时保留：

- `client_native.py`
- `client_langchain.py`

并通过对照脚本去回答：

- LangChain 到底替你抽象了什么

这是 `03` 阶段最值得获得的学习收益之一。

---

## 6. 这一章你要真正写哪些代码 📌

从这一章开始，真正进入代码实践。

最小要求是：

1. 初始化一个 LangChain `ChatModel`
2. 写一个最小 `ChatPromptTemplate`
3. 写一个 `StrOutputParser`
4. 用 LCEL 把它们串起来
5. 跑通一次 `invoke`
6. 尝试一次 `stream`

如果只读不写，这一章基本等于没学到位。

但这里也要控制边界，不要现在去做：

- 向量库接入
- 真正文档处理
- 真正 Agent
- 多工具编排

这些都属于后续阶段。

---

## 7. 本章学完你应该做到什么

你不需要做到：

- 会背 LangChain 所有 API
- 会写复杂 Agent
- 会做完整 RAG

你应该做到：

- 能解释 LangChain 为什么值得在 `03` 学
- 能说清 `Model / Prompt / Parser / Runnable / Retriever / Tool` 的边界
- 能用最小代码跑通 `prompt -> llm -> parser`
- 知道 `foundation_lab` 的编码起点从这里正式开始

---

## 8. 本章小结

这一章你真正应该带走的是：

1. 从这一章开始，`03_foundation` 正式进入代码阶段
2. LangChain 的价值在于帮助你建立统一工程抽象，而不是背 API
3. `Model / Prompt / Parser / Runnable / Retriever / Tool` 是最值得先掌握的核心对象
4. `foundation_lab` 的最小编码起点是 `prompt -> llm -> parser`
5. `Retriever` 和 `Tool` 现在只需要先理解边界，不要过早做复杂实现
