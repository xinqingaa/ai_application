# AI 应用课程

这里是学习者进入课程的首页。

课程只围绕一个项目展开：把“需求评审助手”从固定 RAG 应用逐步演进为以 Agentic RAG 为知识基础的多 Agent 协作系统。

## 从这里开始

第一次进入课程，直接打开：

> **[需求评审助手标准学习路径](learning-path.md)**

这条路径是阅读顺序和第 1–65 节编号的唯一真源。不要按照 `concepts/`、`mechanisms/`、文件名或代码目录自行推断先后。`concepts/` 与 `mechanisms/` 均为平铺正文，不按能力域分子目录。

如果只是查某项知识属于哪里、依赖什么、是否已有正文，使用：

> [AI 应用知识地图](knowledge-map.md)

知识地图不维护第二套课表，也不要求按能力域逐行通关。

## 最终要做出什么

需求评审助手接收 PRD、业务规则、接口文档、客户端规则和历史评审资料，输出结构化风险、依据、需要补充的信息和可观察的执行过程。

它沿同一个业务闭环逐步增加能力：

```text
真实模型理解需求
→ TXT、Markdown、DOCX 和文本型 PDF 成为可检索资料
→ PostgreSQL 全文检索与 pgvector 多路召回并由 RRF 融合
→ Top-k、阈值、过滤和每路排名可以被诊断
→ 检索证据进入模型上下文
→ Structured Output、Citation、Refusal 和补充问题进入应用契约
→ Review API 与 Web 工作台展示结果、证据、状态和真实失败
→ Agent Harness 承载上下文、工具、权限、循环和停止
→ 单 Agent 动态改写、选源、检索、追问和停止
→ MCP、Agent Skills 与 Browser / Search / Code / File Tool
→ Deep Research 完成多步搜索、验证和带来源综合
→ Multi-Agent 分工、并行、汇总与冲突处理
→ A2A 与必要 Workflow 管理互操作、恢复和人工介入
→ Trace、评估、bad case 和反馈完成质量收束
→ 可运行、可观察、可部署的产品
```

课程设计从这个目标反推知识，但学习者不是倒着读项目：

```text
设计课程：阶段目标 → 反推真正需要的知识
学习课程：项目愿景 → 阶段业务契约 → 概念 → 机制与实验 → 回到同一项目篇完成检查点和验收
```

## 两个阶段

| 阶段 | 连续编号 | 目标 |
| --- | --- | --- |
| 第一阶段：RAG 应用基础 | 第 1–25 节 | 固定 RAG、最小可信证据、Review API、Web 工作台和固定对照 |
| 第二阶段：Agent、Tools 与 Multi-Agent | 第 26–65 节 | Agent Harness、Tools、MCP、Agent Skills、Deep Research、Multi-Agent、A2A、必要 Workflow 和质量收束 |

第二阶段从第 26 节继续，不重新从 1 开始。课程不建立阶段内产品版本号。

能力优先级是：

```text
RAG 应用基础
→ Agent Harness 与 Tools
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ 完整质量工程
```

质量不是最后才出现：第一阶段有最小 Golden Set 和固定对照，单 Agent 有 Tool 与轨迹评估，Multi-Agent 有单 Agent 基线比较；完整 Trace、Regression、Human Eval 和 Feedback 在第二阶段后部统一收束。

## 必备基础

Python、HTTP、JSON、异步、配置和 PostgreSQL 属于必备基础：

- 已经具备时，通过学习路径中的检查直接进入主线。
- 不足时，回查 `source/python_base/`、PostgreSQL 概念篇和对应操作文档。
- 不要求为了形式重新通关已经掌握的基础课。

Streaming、Conversation 和事件协议属于第二阶段 Agent 产品主线。

## 文档和代码分别负责什么

| 入口 | 学习时用来做什么 |
| --- | --- |
| `course/learning-path.md` | 确定现在读什么、下一步进入哪里 |
| `course/knowledge-map.md` | 查看完整知识范围、前置、阶段、定位和落地位置 |
| `course/concepts/` | 建立定义、区别、判断和能力边界 |
| `course/mechanisms/` | 理解数据流、机制、实验和失败定位 |
| `course/project/` | 读取阶段契约，完成集成检查点、综合实践和验收 |
| `source/packages/` | 阅读可复用能力的唯一真实实现 |
| `source/demos/` | 运行机制对照和失败复现 |
| `source/apps/` | 观察学习期 API、SSE 等组合实验 |
| `review_assistant/` | 运行和演进最终产品 |

概念篇、机制篇和项目篇是职责分类，不是三个要分别读完的目录。标准学习路径会根据认知前置在它们之间穿插。

## 怎样使用项目篇

每个阶段使用同一份项目篇：

```text
阶段开始先读业务场景、输入输出、Definition of Ready 和非目标
→ 按学习路径完成概念、机制与真实实验
→ 在路径规定的检查点回到同一项目篇组合能力
→ 观察真实 bad case 或正常策略边界
→ 修改一个需求
→ 用测试或评估完成阶段验收
```

第二阶段可以在单 Agent、Multi-Agent 和最终交付处多次返回同一项目篇，但这些检查点不是新版本。

## 真实调用

LLM、RAG、Agent 和 Eval 的学习主路径调用真实模型或真实外部服务。缺少 key、限流、超时和能力不支持时应清晰失败，不静默返回 Mock 结果。

fake、mock 或 simulation 只用于单元测试、离线排查、稳定复现失败路径或明确标注的对照实验，不能证明真实模型或项目质量。
