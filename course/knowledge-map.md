# AI 应用知识地图

这份文档是课程的完整知识书架。

它回答：

- AI 应用开发需要理解哪些概念和机制。
- 每项知识解决什么范围的问题。
- 理解它之前真正需要知道什么。
- 它最早在哪个项目版本进入。
- 对应正文和代码在哪里。

它不安排当前阅读顺序，也不承担项目任务。现在应该读什么，以 [课程入口](README.md) 的正向学习路线为准；什么时候把能力组合成产品，以对应项目篇为准。

## 怎样使用

### 想开始学习

不要从这张表逐行阅读。回到 [课程入口](README.md)，按当前路线从概念、机制和小实验开始。

### 想查完整知识体系

选择一个能力域，沿该域的关系主线查看知识之间怎样连接，再按需要进入正文。

### 想检查项目为什么缺一项能力

先从项目失败现象判断属于模型、检索、上下文、工具、状态、评估还是交互，再来这里定位对应机制和代码入口。

## 状态和定位

| 标记 | 含义 |
| --- | --- |
| 主线 | 会直接进入某个项目版本的核心闭环 |
| 支撑 | 按真实问题进入，不作为开始下一阶段的统一门禁 |
| 未来认知 | 保留视野，当前项目不实现 |
| 已落地 | 已有正文和主要代码 |
| 待编写 | 已确认知识位置，正文随真实学习和代码一起落地 |
| 待重切 | 已有实现或实验，但正文职责仍需按新规范整理 |

知识项不与文档一一对应。一篇概念篇或机制篇可以讲清多个紧密相关的知识，一项知识也可以被概念、机制和项目从不同角度使用。

## LLM 与模型交互

关系主线：

模型在应用中的位置
→ Prompt、Context 与 Schema 契约
→ Provider / Prompt / Structured Output / Context
→ Reliability / Harness / Cost / Streaming

前半建立模型调用和业务契约，后半按可靠性、评估、成本和产品交互需要进入。

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LLM 应用问题空间与能力边界 | 概念 | 主线 | V0 | 无 | [阅读正文](concepts/llm-in-ai-applications.md) | `source/demos/02_llm_basics/` | 已落地 |
| 一次模型调用的生命周期 | 概念+机制 | 主线 | V0 | LLM 应用问题空间与能力边界 | [阅读正文](mechanisms/llm/model-api-and-provider.md) | `llm_core/client` | 已落地 |
| Provider、模型配置与供应商差异 | 机制 | 主线 | V0 | 一次模型调用的生命周期 | [阅读正文](mechanisms/llm/model-api-and-provider.md) | `llm_core/providers`、`config` | 已落地 |
| Prompt、Schema、Context 的模型契约 | 概念 | 主线 | V0 | LLM 应用问题空间与能力边界 | [阅读正文](concepts/model-input-output-contracts.md) | `llm_core/prompts`、`schemas`、`context` | 已落地 |
| 面向应用的 Prompt Engineering | 机制 | 主线 | V0 | Prompt、Schema、Context 的模型契约 | [阅读正文](mechanisms/llm/prompt-engineering.md) | `llm_core/prompts` | 已落地 |
| Streaming 与 Conversation | 机制 | 支撑 | V0 | 一次模型调用的生命周期 | [阅读正文](mechanisms/llm/streaming-and-conversation.md) | `llm_core/streaming`、`conversation` | 已落地 |
| Structured Output 与本地校验 | 机制 | 主线 | V0 | Prompt、Schema、Context 的模型契约 | [阅读正文](mechanisms/llm/structured-output.md) | `llm_core/structured`、`schemas` | 已落地 |
| Context Engineering 与预算 | 机制 | 主线 | V0 | Prompt、Schema、Context 的模型契约 | [阅读正文](mechanisms/llm/context-engineering.md) | `llm_core/context` | 已落地 |
| 错误分类、重试、降级与可靠调用 | 机制 | 支撑 | V0 | 一次模型调用的生命周期 | [阅读正文](mechanisms/llm/reliability-and-errors.md) | `llm_core/errors`、`reliability` | 已落地 |
| 调用 Harness、回归与版本比较 | 机制 | 主线 | V0 | 面向应用的 Prompt Engineering、Structured Output 与本地校验、错误分类、重试、降级与可靠调用 | [阅读正文](mechanisms/llm/calling-harness-and-regression.md) | `llm_core/harness` | 已落地 |
| Token、成本、延迟与缓存 | 机制 | 支撑 | V0 | 一次模型调用的生命周期 | [阅读正文](mechanisms/llm/cost-latency-and-caching.md) | `llm_core/costing`、`cache` | 已落地 |
| Function Calling API 形态 | 机制 | 主线 | V3 | Structured Output 与本地校验 | 归入 Agent Tool 机制 | 后续 `agent_core` | 待编写 |

## RAG 与知识系统

关系主线：

外部知识为什么需要 RAG
→ 文档与 Chunk
→ Embedding 与索引
→ Retrieval 与诊断
→ Context Construction
→ 可信生成与评估

RAG 与 LLM 通过 Context 和 Structured Output 相接，不是两门彼此隔离的课程。

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RAG 问题空间与完整链路 | 概念 | 主线 | V0 | LLM 应用问题空间与能力边界 | `concepts/rag-and-external-knowledge.md` | 后续 `rag_core` | 待编写 |
| 固定 RAG、搜索、数据库与 Agent 的边界 | 概念 | 主线 | V0 | RAG 问题空间与完整链路 | `concepts/rag-and-external-knowledge.md` | 后续 `rag_core` | 待编写 |
| Document Loading、Cleaning 与结构保留 | 机制 | 主线 | V0 | RAG 问题空间与完整链路 | `mechanisms/rag/document-loading-and-cleaning.md` | 后续 `rag_core/ingestion` | 待编写 |
| Chunking、父子块与 Metadata | 机制 | 主线 | V0 | Document Loading、Cleaning 与结构保留 | `mechanisms/rag/chunking-and-metadata.md` | 后续 `rag_core/chunking` | 待编写 |
| Embedding 的表示与相似度 | 概念+机制 | 主线 | V0 | RAG 问题空间与完整链路 | `mechanisms/rag/embedding-and-similarity.md` | 后续 `rag_core/embedding` | 待编写 |
| Vector Store、索引与 pgvector | 机制 | 主线 | V0 | Embedding 的表示与相似度 | `mechanisms/rag/vector-store-and-pgvector.md` | 后续 `rag_core/vector_store` | 待编写 |
| 关键词、向量、混合检索与 Top-k | 机制 | 主线 | V0 | Chunking、父子块与 Metadata、Embedding 的表示与相似度 | `mechanisms/rag/retrieval-strategies.md` | 后续 `rag_core/retrieval` | 待编写 |
| Retriever 契约、过滤、阈值与结果诊断 | 机制 | 主线 | V0 | 关键词、向量、混合检索与 Top-k | `mechanisms/rag/retriever-contract.md` | 后续 `rag_core/retrieval` | 待编写 |
| Query Rewrite 与 Source Routing | 机制 | 主线 | V3 | Retriever 契约、过滤、阈值与结果诊断 | `mechanisms/rag/query-rewrite-and-routing.md` | 后续 `rag_core/query` | 待编写 |
| Context Construction 与 Compression | 机制 | 主线 | V0 | Retriever 契约、过滤、阈值与结果诊断、Context Engineering 与预算 | `mechanisms/rag/context-construction.md` | `llm_core/context` + 后续 `rag_core` | 待编写 |
| 可信生成、Sources、Citation 与 Refusal | 概念+机制 | 主线 | V0/V1 | Context Construction 与 Compression、Structured Output 与本地校验 | `mechanisms/rag/trusted-generation.md` | 后续 `rag_core/generation` | 待编写 |
| Citation 校验与证据充分性 | 机制 | 主线 | V1 | 可信生成、Sources、Citation 与 Refusal | `mechanisms/rag/citation-and-evidence-validation.md` | 后续 `rag_core/evidence` | 待编写 |
| RAG Evaluation | 机制+项目 | 主线 | V2 | 关键词、向量、混合检索与 Top-k、可信生成、Sources、Citation 与 Refusal | `mechanisms/eval/rag-evaluation.md` | 后续 `eval_core` | 待编写 |
| Retriever as Tool 与 Single Agent RAG | 机制 | 主线 | V3 | Query Rewrite 与 Source Routing、Tool Runtime 与结构化错误 | `mechanisms/agent/single-agent-rag.md` | 后续 `agent_core` | 待编写 |
| RAG Failure Analysis 与 Bad Case 回流 | 机制 | 主线 | V2 | RAG Evaluation | `mechanisms/rag/failure-analysis.md` | 后续 `eval_core` | 待编写 |
| RAPTOR、GraphRAG、复杂解析等高级知识生产 | 概念 | 未来认知 | 未来 | Chunking、父子块与 Metadata、关键词、向量、混合检索与 Top-k | 待按需创建 | 无当前实现 | 未来认知 |
| 文档版本、更新、删除一致性与权限过滤 | 机制 | 支撑 | V1/V2 | Document Loading、Cleaning 与结构保留、Chunking、父子块与 Metadata | `mechanisms/rag/knowledge-governance.md` | 后续 `rag_core/governance` | 待编写 |
| RAG Memory、写入、检索与遗忘 | 概念+机制 | 支撑 | V3 | Retriever 契约、过滤、阈值与结果诊断 | `mechanisms/agent/memory-and-context.md` | 后续 `agent_core/memory` | 待编写 |

## Agent 与 Tool

关系主线：

判断是否需要 Agent
→ Function Calling 与 Tool Schema
→ Tool Runtime 与治理
→ Agent Loop、停止和安全
→ 记忆、Agentic RAG 与子 Agent

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chain、Workflow、Agent 与 Multi-Agent 边界 | 概念 | 主线 | V3 | 固定 RAG、搜索、数据库与 Agent 的边界 | `concepts/agent-and-workflow-boundaries.md` | 后续 `agent_core` | 待编写 |
| Function Calling 与 Tool Schema | 机制 | 主线 | V3 | Function Calling API 形态 | `mechanisms/agent/tool-schema.md` | 后续 `agent_core/tools` | 待编写 |
| Tool Runtime 与结构化错误 | 机制 | 主线 | V3 | Function Calling 与 Tool Schema | `mechanisms/agent/tool-runtime.md` | 后续 `agent_core/tools` | 待编写 |
| 工具权限、确认、幂等与审计 | 机制 | 主线 | V3/V4 | Tool Runtime 与结构化错误 | `mechanisms/agent/tool-governance.md` | 后续 `agent_core/tools` | 待编写 |
| Agent Loop 与停止条件 | 机制 | 主线 | V3 | Tool Runtime 与结构化错误 | `mechanisms/agent/agent-loop.md` | 后续 `agent_core/runtime` | 待编写 |
| Planning、Task Decomposition 与 Reflection | 机制 | 支撑 | V3 | Agent Loop 与停止条件 | `mechanisms/agent/planning-and-reflection.md` | 后续 `agent_core/runtime` | 待编写 |
| LangChain Agent Patterns | 机制 | 主线 | V3 | Agent Loop 与停止条件 | 并入对应 Agent 机制篇 | 后续 `agent_core` | 待编写 |
| Agentic RAG 深化 | 机制 | 支撑 | V4 | Retriever as Tool 与 Single Agent RAG、Workflow State、Node 与 Edge | `mechanisms/agent/agentic-rag.md` | 后续 `agent_core` | 待编写 |
| Workflow as Tool 与子 Agent | 机制 | 主线 | V5 | Human-in-the-loop、Multi-Agent 拆分判断 | `mechanisms/agent/workflow-as-tool.md` | 后续 `agent_core` | 待编写 |
| Agent Memory 与 Context | 机制 | 主线 | V3 | RAG Memory、写入、检索与遗忘、Agent Loop 与停止条件 | `mechanisms/agent/memory-and-context.md` | 后续 `agent_core/memory` | 待编写 |
| MCP、A2A 与 Agent Skills | 概念 | 未来认知 | 未来 | Tool Runtime 与结构化错误 | 待按需创建 | 无当前实现 | 未来认知 |
| Guardrails、Safety 与人工接管 | 机制 | 主线 | V3/V4 | 工具权限、确认、幂等与审计、Agent Loop 与停止条件 | `mechanisms/agent/guardrails-and-safety.md` | 后续 `agent_core/safety` | 待编写 |
| Deep Research | 概念 | 未来认知 | 未来 | Workflow State、Node 与 Edge、Planning、Task Decomposition 与 Reflection | 待按需创建 | 无当前实现 | 未来认知 |
| 多模态 Agent、Browser、Code、File、Search 工具 | 概念 | 未来认知 | 未来 | Tool Runtime 与结构化错误 | 待按需创建 | 无当前实现 | 未来认知 |

## Workflow

关系主线：

State / Node / Edge
→ 状态契约与合并
→ 条件、循环和并行
→ Checkpoint / Interrupt / Resume
→ Human-in-the-loop
→ 重试、副作用与幂等

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Workflow State、Node 与 Edge | 机制 | 主线 | V4 | Chain、Workflow、Agent 与 Multi-Agent 边界 | `mechanisms/workflow/state-node-edge.md` | 后续 `agent_core/workflow` | 待编写 |
| Node 输入输出契约与状态合并 | 机制 | 主线 | V4 | Workflow State、Node 与 Edge | `mechanisms/workflow/state-contracts.md` | 后续 `agent_core/workflow` | 待编写 |
| 条件、循环与并行 | 机制 | 主线 | V4 | Workflow State、Node 与 Edge | `mechanisms/workflow/branch-loop-parallel.md` | 后续 `agent_core/workflow` | 待编写 |
| Checkpoint、Interrupt 与 Resume | 机制 | 主线 | V4 | Node 输入输出契约与状态合并 | `mechanisms/workflow/checkpoint-and-resume.md` | 后续 `agent_core/workflow` | 待编写 |
| Human-in-the-loop | 机制 | 主线 | V4 | Checkpoint、Interrupt 与 Resume | `mechanisms/workflow/human-in-the-loop.md` | 后续 `agent_core/workflow` | 待编写 |
| 节点重试、副作用与幂等 | 机制 | 主线 | V4 | Node 输入输出契约与状态合并、工具权限、确认、幂等与审计 | `mechanisms/workflow/retry-and-idempotency.md` | 后续 `agent_core/workflow` | 待编写 |
| LangGraph 框架映射与运行调试 | 机制 | 主线 | V4 | Workflow State、Node 与 Edge、Node 输入输出契约与状态合并、条件、循环与并行、Checkpoint、Interrupt 与 Resume、Human-in-the-loop、节点重试、副作用与幂等 | 并入 Workflow 机制篇 | 后续 `agent_core/workflow` | 待编写 |

## Multi-Agent

关系主线：

先证明单 Agent 不足
→ 划分角色、上下文、工具和输出契约
→ 分配与并行执行
→ 共享状态和失败隔离
→ 汇总、证据合并与冲突裁决
→ 与单 Agent 基线比较

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Multi-Agent 拆分判断 | 概念 | 主线 | V5 | Chain、Workflow、Agent 与 Multi-Agent 边界、Workflow State、Node 与 Edge | `concepts/multi-agent-collaboration.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 角色责任、上下文、工具和输出契约 | 机制 | 主线 | V5 | Multi-Agent 拆分判断 | `mechanisms/agent/multi-agent-contracts.md` | 后续 `agent_core/multi_agent` | 待编写 |
| Supervisor / Worker 与任务分配 | 机制 | 主线 | V5 | 角色责任、上下文、工具和输出契约 | `mechanisms/agent/supervisor-worker.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 共享状态、私有上下文与证据 | 机制 | 主线 | V5 | 角色责任、上下文、工具和输出契约、Node 输入输出契约与状态合并 | `mechanisms/agent/multi-agent-state.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 并行执行、依赖和失败隔离 | 机制 | 主线 | V5 | Supervisor / Worker 与任务分配、条件、循环与并行 | `mechanisms/agent/multi-agent-execution.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 结果汇总、证据合并与冲突裁决 | 机制 | 主线 | V5 | 共享状态、私有上下文与证据 | `mechanisms/agent/result-merge-and-conflict.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 单 Agent 与多 Agent 基线比较 | 机制+项目 | 主线 | V5 | Multi-Agent 拆分判断、角色责任、上下文、工具和输出契约、Supervisor / Worker 与任务分配、共享状态、私有上下文与证据、并行执行、依赖和失败隔离、结果汇总、证据合并与冲突裁决 | 对应 V5 项目篇 | 后续 `eval_core` | 待编写 |

## Evaluation 与 Observability

关系主线：

固定样例与 Golden Set
→ 检索、生成、Citation 和 Refusal 评估
→ Agent / Workflow 轨迹评估
→ Trace、版本和回归
→ Bad Case 与 Feedback Loop

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Evaluation Dataset 与 Golden Set | 机制 | 主线 | V0/V2 | 项目业务契约 | `mechanisms/eval/dataset-and-golden-set.md` | 后续 `eval_core` | 待编写 |
| Retrieval 与 Generation Eval | 机制 | 主线 | V0/V2 | 关键词、向量、混合检索与 Top-k、可信生成、Sources、Citation 与 Refusal | `mechanisms/eval/rag-evaluation.md` | 后续 `eval_core/rag` | 待编写 |
| Citation 与 Refusal Eval | 机制 | 主线 | V1/V2 | 可信生成、Sources、Citation 与 Refusal、Citation 校验与证据充分性 | `mechanisms/eval/citation-and-refusal.md` | 后续 `eval_core/rag` | 待编写 |
| Bad Case Management | 机制 | 主线 | V2 | Evaluation Dataset 与 Golden Set、Retrieval 与 Generation Eval、Citation 与 Refusal Eval | `mechanisms/eval/bad-case-management.md` | 后续 `eval_core` | 待编写 |
| Agent Trajectory 与 Tool Eval | 机制 | 主线 | V3/V5 | Tool Runtime 与结构化错误、Agent Loop 与停止条件 | `mechanisms/eval/agent-and-tool-evaluation.md` | 后续 `eval_core/agent` | 待编写 |
| Workflow Eval 与 Human Review | 机制 | 主线 | V4/V5 | Workflow State、Node 与 Edge、Human-in-the-loop | `mechanisms/eval/workflow-evaluation.md` | 后续 `eval_core/workflow` | 待编写 |
| Trace、Span 与 Run 关联 | 机制 | 主线 | V0 | 一次模型调用的生命周期 | `mechanisms/eval/trace-and-observability.md` | `llm_core/harness` + 后续 `eval_core` | 待编写 |
| Versioning、Regression 与 Experiment | 机制 | 主线 | V2 | Evaluation Dataset 与 Golden Set、Trace、Span 与 Run 关联 | `mechanisms/eval/versioning-and-regression.md` | 后续 `eval_core` | 待编写 |
| Cost、Latency 与运行指标 | 机制 | 主线 | V2/V6 | Token、成本、延迟与缓存 | `mechanisms/eval/cost-latency-metrics.md` | `llm_core/costing` + 后续 `eval_core` | 待编写 |
| LLM-as-Judge 与 Human Eval | 机制 | 主线 | V2 | Evaluation Dataset 与 Golden Set | `mechanisms/eval/llm-as-judge.md` | 后续 `eval_core` | 待编写 |
| Feedback Loop | 机制+项目 | 主线 | V2 | Bad Case Management | `mechanisms/eval/feedback-loop.md` | 后续 `eval_core` | 待编写 |
| Engineering Contract Tests | 机制 | 主线 | V0/V4 | 项目 Schema | `mechanisms/eval/engineering-contract-tests.md` | package / product tests | 待编写 |

## AI Native 体验

关系主线：

模型事件和响应状态
→ Schema 驱动的结果展示
→ RAG / Workflow / Multi-Agent 运行过程
→ 标注、反馈和工程错误体验
→ 完整工作台

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AI Native 问题空间 | 概念 | 主线 | V0 | LLM 应用问题空间与能力边界 | `concepts/ai-native-interface.md` | 产品 workbench | 待编写 |
| Streaming State Synchronization | 机制 | 主线 | V0/V3 | Streaming 与 Conversation | `mechanisms/ai-native/streaming-state.md` | 产品 workbench | 待编写 |
| AI Response State Machine | 机制 | 主线 | V0/V3 | Streaming State Synchronization | `mechanisms/ai-native/response-state-machine.md` | 产品 workbench | 待编写 |
| Schema Driven UI 与结构化评审报告 | 机制 | 主线 | V1 | Structured Output 与本地校验 | `mechanisms/ai-native/schema-driven-review.md` | 产品 workbench | 待编写 |
| Multi-Agent UI / UX | 机制 | 主线 | V5 | 角色责任、上下文、工具和输出契约、Supervisor / Worker 与任务分配、共享状态、私有上下文与证据、并行执行、依赖和失败隔离、结果汇总、证据合并与冲突裁决 | `mechanisms/ai-native/multi-agent-ux.md` | 产品 workbench | 待编写 |
| Workflow Runtime UI | 机制 | 主线 | V4 | Workflow State、Node 与 Edge、Node 输入输出契约与状态合并、条件、循环与并行、Checkpoint、Interrupt 与 Resume、Human-in-the-loop | `mechanisms/ai-native/workflow-runtime-ui.md` | 产品 workbench | 待编写 |
| RAG Knowledge Workbench | 机制+项目 | 主线 | V6 | Document Loading、Cleaning 与结构保留、文档版本、更新、删除一致性与权限过滤 | 对应 V6 项目篇 | 产品 workbench | 待编写 |
| Eval、Labeling 与 Feedback UI | 机制+项目 | 主线 | V2/V6 | Bad Case Management、Feedback Loop | `mechanisms/ai-native/eval-and-feedback-ui.md` | 产品 workbench | 待编写 |
| FastAPI Service Layer 与 API Design | 机制 | 主线 | V0 | Python / HTTP | `mechanisms/engineering/fastapi-and-api.md` | 产品 app | 待编写 |
| 工程观测与错误体验 | 机制 | 主线 | V0/V6 | Trace、Span 与 Run 关联 | `mechanisms/ai-native/error-and-observability-ux.md` | 产品 app / workbench | 待编写 |
| Project AI Native Architecture | 项目 | 主线 | V6 | 全部主线 | 对应 V6 项目篇 | `review_assistant/` | 待编写 |

## 工程基础

工程能力按项目需要进入，用于承载真实 API、数据、任务、观测和部署，不扩展成独立后端大课。

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Python、HTTP、JSON 与配置 | 基础 | 支撑 | V0 | `python_base` | 按需回查 `python_base/` | 根项目 | 已落地 |
| FastAPI 与 API 契约 | 机制 | 主线 | V0 | Python、HTTP、JSON 与配置 | `mechanisms/engineering/fastapi-and-api.md` | 产品 app | 待编写 |
| SSE 与事件协议 | 机制 | 主线 | V0 | Streaming 与 Conversation、FastAPI 与 API 契约 | `mechanisms/engineering/sse-event-protocol.md` | 现有 streaming app | 已落地/待重切 |
| PostgreSQL / pgvector 数据模型 | 机制 | 支撑 | V0/V6 | SQL 基础、Vector Store、索引与 pgvector | `mechanisms/engineering/postgres-and-pgvector.md` | 产品 infra | 待编写 |
| Redis、后台任务与入库状态 | 机制 | 主线 | V4 | Document Loading、Cleaning 与结构保留、Checkpoint、Interrupt 与 Resume | `mechanisms/engineering/background-jobs.md` | 产品 infra | 待编写 |
| Docker Compose 本地部署 | 机制+项目 | 主线 | V6 | 产品入口 | `mechanisms/engineering/docker-compose.md` | 产品 infra | 待编写 |
| 日志、Metrics 与工程观测 | 机制 | 主线 | V0/V6 | Trace、Span 与 Run 关联 | `mechanisms/engineering/logging-and-metrics.md` | 产品 app / infra | 待编写 |
| 文件、对象存储与数据生命周期 | 机制 | 主线 | V0/V6 | Document Loading、Cleaning 与结构保留 | `mechanisms/engineering/file-storage.md` | 产品 infra | 待编写 |
| Kubernetes、灰度、多租户与权限中台 | 概念 | 未来认知 | 未来 | Docker Compose 本地部署、日志、Metrics 与工程观测 | 无当前正文 | 无当前实现 | 未来认知 |

## 维护边界

- 新增知识前先判断能否合并到现有知识。
- 知识名称必须让学习者直接理解，不使用内部编号或编号范围。
- 当前正向阅读顺序只维护在 course/README.md。
- 项目业务任务、设计选择和验收只维护在 course/project/。
- 框架映射优先并入对应机制篇，不独立形成第四类文档。
- 未来认知不创建占位正文、空 package、空 demo 或空 app。
