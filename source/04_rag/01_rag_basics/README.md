# 01. RAG 基础概念 - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md) 学完第一章，并在不依赖后续章节的前提下跑通最小 RAG 闭环。

---

## 核心原则

```text
先判断问题该走哪条路 -> 再看最小检索问答闭环 -> 最后判断什么时候该用什么方案
```

- 在 `source/04_rag/01_rag_basics/` 目录下操作
- 本章不做项目骨架，不做多模块预埋，不接真实 Embedding / 向量库 / LLM
- 本章代码只保留三个目标：问题意识、最小链路、方案边界
- 不需要 API Key
- 本章目录就是当前学习入口

---

## 项目结构

```text
01_rag_basics/
├── README.md
├── rag_basics.py
├── 01_why_rag.py
├── 02_rag_pipeline.py
├── 03_solution_decision.py
└── tests/
    └── test_rag_basics.py
```

- `rag_basics.py`
  放本章所有最小对象、问题路由、内存知识库、关键词检索、回答生成和方案判断逻辑
- `01_why_rag.py`
  对比“只做单次模型调用”和“先判断再选方案”面对同一个问题时的差异
- `02_rag_pipeline.py`
  逐步打印 `先路由 -> 再决定是否进入 RAG -> 检索 -> 上下文 -> 回答 + 来源`
- `03_solution_decision.py`
  把“什么时候该用长上下文 / 现有系统 / Hosted File Search / 固定 RAG / Hybrid RAG / Agentic RAG”变成可执行的判断示例

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/01_rag_basics
```

### 2. 当前命令

```bash
python 01_why_rag.py
python 02_rag_pipeline.py
python 03_solution_decision.py
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python 01_why_rag.py
```

你最先要建立的直觉是：

- 模型不懂你的私有资料时，单次调用并不能自动知道答案
- 不是所有问题都应该先进入 RAG
- 如果问题更像结构化查询，应该优先查现有系统
- RAG 的最小价值不是“更聪明”，而是“先找到依据，再回答”

---

## 第 1 步：先看为什么需要 RAG

**对应文件**：`01_why_rag.py`

这个脚本会打印三类问题：

1. 课程私有知识问题
2. 通用常识问题
3. 结构化系统查询

重点观察：

- 为什么私有知识问题应该先检索再回答
- 为什么通用常识并不天然需要 RAG
- 为什么结构化查询更适合直接查现有系统，而不是先塞进 RAG

---

## 第 2 步：看最小 RAG 数据流

**对应文件**：`02_rag_pipeline.py`

这一章真正要看的链路是：

```text
先路由 -> 如果需要再进入：问题 -> 检索 -> 上下文 -> 回答 + 来源
```

重点观察：

- `route_question()`
- `retrieve()`
- `build_context()`
- `answer_question()`

运行后重点看：

- 为什么有些问题根本不会进入 RAG
- 哪些关键词触发了召回
- 为什么检索结果先变成上下文，再进入回答阶段
- 最终输出为什么不是单纯字符串，而是 `answer + sources`
- 为什么 `Python 系统课可以退钱吗？` 这种问题路由正确，但 toy 检索仍然会漏召回

---

## 第 3 步：看什么时候该用什么方案

**对应文件**：`03_solution_decision.py`

这一章不只讲“RAG 是什么”，还要讲“什么时候不用它”。

重点观察：

- 长上下文适合什么情况
- 直接查现有系统适合什么情况
- Hosted File Search 适合什么阶段
- 固定 `2-step RAG` 为什么是默认主线
- Hybrid RAG 什么时候值得加
- 为什么 `Agentic RAG` 不该在第一章出现

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_rag_basics.py`

测试里会保留一个 mini golden set，只锁定本章最重要的几件事：

1. 通用常识问题不会误走 RAG
2. 结构化查询会直接查现有系统
3. 私有知识问题能检索到正确来源
4. 课程类问题即使路由正确，也可能因为关键词检索太弱而漏召回
5. 方案判断顺序符合课程主线

---

## 建议学习顺序

1. 先读 [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
2. 再跑 `python 01_why_rag.py`
3. 再跑 `python 02_rag_pipeline.py`
4. 最后跑 `python 03_solution_decision.py`

---

## 第一章最小回归集

第一章不做完整评估系统，但应该保留一个最小回归集，避免你改完示例后不知道有没有偏离教学主线。

一个足够小的回归集可以长这样：

```python
mini_golden_set = [
    {
        "question": "法国首都是什么？",
        "expected_route": "直接回答",
        "expected_sources": [],
    },
    {
        "question": "订单 1024 的状态是什么？",
        "expected_route": "直接查现有系统",
        "expected_sources": ["orders_table"],
    },
    {
        "question": "Python 系统课可以退费吗？",
        "expected_route": "固定 2-step RAG",
        "expected_sources": ["refund_policy.md"],
    },
]
```

这不是完整评估体系，但已经足够回答三个问题：

- 教学主线有没有跑偏
- 来源有没有丢
- 路由逻辑有没有把所有问题都错误塞进 RAG

---

## 失败案例也要刻意观察

运行下面这条命令：

```bash
python 02_rag_pipeline.py "Python 系统课可以退钱吗？"
```

你会看到：

- 路由判断会认为这题应该走 `固定 2-step RAG`
- 但关键词检索不会命中 `退款 / 退费`
- 最终返回“当前知识库里没有命中相关资料”

这个反例非常重要，因为它正好说明：

> 第一章先建立“该不该走 RAG”的直觉；后续章节才去解决“走了 RAG 但为什么没召回好”的工程问题。

---

## 学完这一章后你应该能回答

- RAG 到底在解决什么问题
- 为什么不是所有问题都该上 RAG
- 为什么应该先判断问题类型，再决定是否进入 RAG
- 最小 `2-step RAG` 在线链路长什么样
- 为什么第一章就应该保留最小回归样本
- 为什么第一章先做独立闭环，而不是先搭完整项目工程

---

## 当前真实进度和下一章

- 当前真实进度：第一章已经改成独立学习单元
- 完成标准：能跑通最小闭环，能解释路由、输入输出和来源，能做基本方案判断
- 下一章：进入 [source/04_rag/02_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/README.md)，只处理文档加载、切分、metadata 和 chunk 输出
