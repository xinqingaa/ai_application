# 01. RAG 基础概念 - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md) 学完第一章，并在不依赖后续章节的前提下跑通最小 RAG 闭环。

---

## 核心原则

```text
先看为什么需要 RAG -> 再跑最小检索问答闭环 -> 最后判断什么时候该用什么方案
```

- 在 `source/04_rag/01_rag_basics/` 目录下操作
- 本章不做项目骨架，不做多模块预埋，不接真实 Embedding / 向量库 / LLM
- 本章代码只保留三个目标：问题意识、最小链路、方案边界
- 不需要 API Key
- 旧的 `labs/phase_1_scaffold/` 只作为迁移期备份，不再是当前学习入口

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
  放本章所有最小对象、内存知识库、关键词检索、回答生成和方案判断逻辑
- `01_why_rag.py`
  对比“不接 RAG”和“接入 RAG”面对同一个问题时的差异
- `02_rag_pipeline.py`
  逐步打印 `问题 -> 检索 -> 上下文 -> 回答 + 来源`
- `03_solution_decision.py`
  把“什么时候该用 RAG”变成可执行的判断示例

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
- RAG 的最小价值不是“更聪明”，而是“先找到依据，再回答”
- 不是所有问题都该上 RAG

---

## 第 1 步：先看为什么需要 RAG

**对应文件**：`01_why_rag.py`

这个脚本会打印两类问题：

1. 课程私有知识问题
2. 通用常识问题

重点观察：

- 为什么私有知识问题在不接 RAG 时只能拒答或模糊回答
- 为什么接入最小检索后，可以返回依据和来源
- 为什么通用常识并不天然需要 RAG

---

## 第 2 步：看最小 RAG 数据流

**对应文件**：`02_rag_pipeline.py`

这一章只保留一条最小在线链路：

```text
问题 -> 检索 -> 上下文 -> 回答 + 来源
```

重点观察：

- `retrieve()`
- `build_context()`
- `answer_with_rag()`

运行后重点看：

- 哪些关键词触发了召回
- 为什么检索结果先变成上下文，再进入回答阶段
- 最终输出为什么不是单纯字符串，而是 `answer + sources`

---

## 第 3 步：看什么时候该用什么方案

**对应文件**：`03_solution_decision.py`

这一章不只讲“RAG 是什么”，还要讲“什么时候不用它”。

重点观察：

- 长上下文适合什么情况
- 直接查现有系统适合什么情况
- 固定 `2-step RAG` 为什么是默认主线
- 为什么 `Agentic RAG` 不该在第一章出现

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_rag_basics.py`

测试只锁定本章最重要的四件事：

1. 私有知识问题能检索到正确来源
2. 带 RAG 的回答会返回来源
3. 不带 RAG 时不会假装知道私有知识
4. 方案判断顺序符合课程主线

---

## 建议学习顺序

1. 先读 [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
2. 再跑 `python 01_why_rag.py`
3. 再跑 `python 02_rag_pipeline.py`
4. 最后跑 `python 03_solution_decision.py`

---

## 学完这一章后你应该能回答

- RAG 到底在解决什么问题
- 为什么不是所有问题都该上 RAG
- 最小 `2-step RAG` 在线链路长什么样
- 为什么第一章先做独立闭环，而不是先搭完整项目工程

---

## 当前真实进度和下一章

- 当前真实进度：第一章已经改成独立学习单元
- 完成标准：能跑通最小闭环，能解释输入输出和来源，能做基本方案判断
- 下一章：进入 [source/04_rag/02_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/README.md)，只处理文档加载、切分、metadata 和 chunk 输出
