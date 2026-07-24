# AI 应用课程

这里是课程的唯一阅读入口。

课程只围绕一个项目展开：把“需求评审助手”从可信 RAG 逐步演进为单 Agent、可控 Workflow 和多 Agent 评审系统。项目决定课程为什么学、选择哪些知识；学习者仍然按照“概念 → 机制与实验 → 项目综合实践”的方向正向学习。

长期目标与版本定义见 [strategy.md](../docs/strategy.md)，学习和工程规则见 [learning-guide.md](../docs/learning-guide.md)。

## 先知道我们要做什么

需求评审助手接收 PRD、业务规则、接口文档、客户端规则和历史评审资料，输出结构化风险、依据和需要补充的信息。

它不会一开始就做成复杂平台，而是逐步建立：

```text
真实模型理解需求
→ 外部资料可以被检索
→ 检索证据进入模型上下文
→ 输出能够被程序校验
→ 证据不足时拒答或追问
→ 用固定样例评估和回归
→ 单 Agent 动态补检索
→ Workflow 管理状态和人工介入
→ 多 Agent 分工、汇总与冲突处理
→ 可运行、可观察、可部署的产品
```

这段项目预览只用于保持方向。完整项目规格不是第一篇教材。

## 当前从哪里开始

当前正向路线从模型与 AI 应用的基本关系开始。

### 第一段：建立模型应用心智

1. [LLM 在 AI 应用中的位置与边界](concepts/llm-in-ai-applications.md)
   理解普通程序、模型、RAG、Agent 和 Workflow 分别解决什么问题。
2. [Prompt、Context 与 Schema 的模型契约](concepts/model-input-output-contracts.md)
   理解应用怎样约束模型的任务、证据和输出。
3. [模型 API、Provider 与统一调用入口](mechanisms/llm/model-api-and-provider.md)
   跑通真实模型调用，理解请求、响应、供应商和统一调用层。

### 第二段：让模型结果进入程序

1. [面向应用的 Prompt Engineering](mechanisms/llm/prompt-engineering.md)
   把随手写的提示词变成可版本化、可比较的任务协议。
2. [Structured Output 与本地校验](mechanisms/llm/structured-output.md)
   把概率文本变成应用可以接受或拒绝的业务对象。
3. [错误分类、重试、降级与可靠调用](mechanisms/llm/reliability-and-errors.md)
   理解鉴权、限流、超时、解析失败和降级为什么不能统一处理。

完成这一段后，应当能用真实模型稳定生成并校验一份结构化需求风险结果，但它使用的证据仍然是静态材料。

### 第三段：让应用获得外部知识

这一段不按“先学完 LLM、再开始 RAG”的方式切割，而是围绕证据进入模型的链路学习：

1. RAG 与外部知识的边界。
2. 文档加载、清洗与来源保留。
3. Chunking 与 Metadata。
4. Embedding、Vector Store 与相似度。
5. 关键词、向量、混合检索与 Retriever 契约。
6. [Context Engineering 与预算](mechanisms/llm/context-engineering.md)。
7. 可信生成、来源候选和证据不足。

对应 RAG 正文只在内容和真实代码一起落地时创建，不预建空文档。完整知识位置可在 [知识地图](knowledge-map.md) 中查看。

### 第四段：建立可比较的质量基线

1. [Calling Harness 与回归](mechanisms/llm/calling-harness-and-regression.md)。
2. Golden Set 与最小检索评估。
3. 直接 LLM、关键词 RAG、向量或混合 RAG 使用同一批样例对比。
4. [Token、成本、延迟与缓存](mechanisms/llm/cost-latency-and-caching.md)作为运行支撑按需进入。

### 第五段：完成 V0 综合项目

完成前面的核心概念、机制和小实验后，再进入：

- [V0：固定 RAG 需求评审基线](project/stage-1-single-agent-rag/v0-fixed-rag.md)

项目篇不再从头教授概念。它负责把已经理解和验证过的能力组合到 `rag_core` 与 `review_assistant/`，完成设计选择、失败复现、需求变更和版本验收。

### 产品交互按项目需要进入

[Streaming 与 Conversation](mechanisms/llm/streaming-and-conversation.md)用于理解模型事件如何被前端消费。它不是理解 RAG 的前置；当 V0 开始提供产品运行状态、SSE 或浏览器入口时再阅读。

## 为什么这不是倒着学

课程设计和学习顺序是两个方向：

```text
设计课程：项目目标 → 反推需要哪些知识
学习课程：项目愿景 → 概念 → 机制与实验 → 项目综合实践
```

项目始终提供方向，但完整项目篇位于一次学习循环的后半段。

## 两个阶段和七个版本

| 阶段 | 版本 | 核心结果 |
| --- | --- | --- |
| 阶段一 | V0 固定 RAG 基线 | 真实资料、检索、上下文和结构化评审输出 |
| 阶段一 | V1 可信结构化评审 | Sources、Citation 校验、Refusal 和补充问题 |
| 阶段一 | V2 质量闭环 | Golden Set、RAG Eval、bad case、feedback 和回归 |
| 阶段一 | V3 单 Agent RAG | Query Rewrite、Source Routing、补检索和追问 |
| 阶段二 | V4 可控 Workflow | 状态、分支、人工审核、中断、恢复和重试 |
| 阶段二 | V5 多 Agent 评审 | 多角色协作、汇总、证据合并和冲突处理 |
| 阶段二 | V6 产品化 | AI Native 工作台、质量面板、部署和作品化 |

每个版本都遵循同一循环：

```text
新问题
→ 补充概念和机制
→ 小实验
→ 项目升级
→ 失败与评估
→ 版本验收
```

## 三类文档的职责

### 概念篇

回答“是什么、为什么需要、与相近概念有什么区别、边界在哪里”。概念篇建立判断，不负责完整运行手册。

### 机制篇

回答“数据怎样变化、为什么有效、如何实现和实验、失败时先查哪里”。机制篇引用真实 package 和 demo，但不替代其 README。

### 项目篇

位于一轮核心概念和机制之后，负责业务契约、集成任务、设计选择、失败题、需求变更和版本验收。

## 课程、代码与产品

```text
course/README.md       当前正向学习路线
course/knowledge-map.md 完整知识书架
course/concepts/       概念篇
course/mechanisms/     机制篇与实验解释
course/project/        阶段性综合实践与验收
source/packages/       通用能力唯一实现
source/demos/          机制实验与失败复现
source/apps/           学习期组合实验
review_assistant/      可运行产品真源
```

## 真实调用

LLM、RAG、Agent 和 Eval 主路径调用真实模型或真实外部服务。缺少 key、限流、超时和能力不支持时应清晰失败，不静默返回 Mock 结果。

`python_base/` 是已经完成的 Python 基础练习，按需要回查，不作为进入主线前必须重新通关的课程。
