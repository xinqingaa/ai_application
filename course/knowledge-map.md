# AI 应用知识地图

这份文档是课程的完整知识书架。

它回答：

- AI 应用开发需要理解哪些概念和机制。
- 每项知识解决什么范围的问题。
- 理解它之前真正需要知道什么。
- 它最早在哪个项目版本进入。
- 对应正文和代码在哪里。

它不安排阅读顺序，也不承担项目任务。现在应该读什么，以 [标准学习路径](learning-path.md) 为准；什么时候把能力组合成产品，以对应项目篇为准。

## 怎样使用

### 想开始学习

不要从这张表逐行阅读。回到 [标准学习路径](learning-path.md)，按认知前置从概念、机制和小实验开始。

### 想查完整知识体系

选择一个能力域，沿该域的关系主线查看知识之间怎样连接，再按需要进入正文。

### 想检查项目为什么缺一项能力

先从项目失败现象判断属于模型、检索、上下文、工具、状态、评估还是交互，再来这里定位对应机制和代码入口。

## 正文状态、学习定位与产品关系

| 标记 | 含义 |
| --- | --- |
| 主线 | 当前版本必须理解、实验或作出设计判断；不等于能力必然进入产品默认链路 |
| 支撑 | 按真实问题进入，不作为开始下一阶段的统一门禁 |
| 未来认知 | 保留视野，当前项目不实现 |
| 已落地 | 正文与该文档类型所需的必要实验已经存在；产品是否接入另看代码入口和项目篇 |
| 待编写 | 已确认知识位置，正文按真实学习和代码需要逐步落地 |
| 待重切 | 已有实现或实验，但正文职责仍需按新规范整理 |

表格中的“正文状态”只回答当前能否按正文学习，不表示产品已经启用。代码入口独立说明实现位置：`后续` 表示尚未实现，真实路径表示已有实现，`无项目实现` 表示当前只做认知，`条件准入` 表示必须先实验但未必进入产品。产品必需能力和版本验收仍以对应项目篇为真源。

知识项不与文档一一对应。一篇概念篇或机制篇可以讲清多个紧密相关的知识，一项知识也可以被概念、机制和项目从不同角度使用。表格中的“类型”只记录该知识当前主要由哪类文档承载；跨类型使用不写成“概念+机制”或“机制+项目”。

## LLM 与模型交互

关系主线：

模型在应用中的位置
→ Prompt、Context 与 Schema 契约
→ Provider / Prompt / Structured Output / Context
→ Reliability / Harness / Cost / Streaming

前半建立模型调用和业务契约，后半按可靠性、评估、成本和产品交互需要进入。

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LLM 应用问题空间与能力边界 | 概念 | 主线 | V0 | 无 | [阅读正文](concepts/llm-in-ai-applications.md) | `source/demos/llm_invoke_lab/first_chat.py` | 已落地 |
| 一次模型调用的生命周期 | 机制 | 主线 | V0 | LLM 应用问题空间与能力边界 | [阅读正文](mechanisms/model-api-and-provider.md) | `llm_core/client`、`llm_invoke_lab` | 已落地 |
| Provider、模型配置与供应商差异 | 机制 | 主线 | V0 | 一次模型调用的生命周期 | [阅读正文](mechanisms/model-api-and-provider.md) | `llm_core/providers`、`config`、`llm_invoke_lab` | 已落地 |
| Prompt、Schema、Context 的模型契约 | 概念 | 主线 | V0 | LLM 应用问题空间与能力边界 | [阅读正文](concepts/model-input-output-contracts.md) | `llm_core/prompts`、`schemas`、`context` | 已落地 |
| 面向应用的 Prompt Engineering | 机制 | 主线 | V0 | Prompt、Schema、Context 的模型契约 | [阅读正文](mechanisms/prompt-engineering.md) | `llm_core/prompts`、`llm_invoke_lab` | 已落地 |
| Streaming 与 Conversation | 机制 | 支撑 | V0 | 一次模型调用的生命周期 | [阅读正文](mechanisms/streaming-and-conversation.md) | `llm_core/streaming`、`conversation`、`apps/llm_streaming_api` | 已落地 |
| Structured Output 与本地校验 | 机制 | 主线 | V0 | Prompt、Schema、Context 的模型契约 | [阅读正文](mechanisms/structured-output.md) | `llm_core/structured`、`schemas`、`llm_invoke_lab` | 已落地 |
| Context Engineering 与预算 | 机制 | 主线 | V0 | Prompt、Schema、Context 的模型契约、Top-k、阈值、Metadata Filter 与 Retrieval 诊断 | [阅读正文](mechanisms/context-engineering.md) | `llm_core/context`、`rag_core/context`、`rag_retrieval_lab/inspect_rag_context.py` | 已落地 |
| 错误分类、重试、降级与可靠调用 | 机制 | 主线 | V0 | 一次模型调用的生命周期 | [阅读正文](mechanisms/reliability-and-errors.md) | `llm_core/errors`、`reliability`、`llm_reliability_lab` | 已落地 |
| 调用 Harness、回归与版本比较 | 机制 | 主线 | V0 | 面向应用的 Prompt Engineering、Structured Output 与本地校验、错误分类、重试、降级与可靠调用、固定 RAG 生成链 | [阅读正文](mechanisms/calling-harness-and-regression.md) | `llm_core/harness`、`llm_regression_lab` | 已落地 |
| Token、成本与延迟记录 | 机制 | 主线 | V0 | 调用 Harness、回归与版本比较 | [阅读正文](mechanisms/cost-latency-and-caching.md) | `llm_core/costing`、`llm_regression_lab` | 已落地 |
| Exact-match Cache 与失效边界 | 机制 | 支撑 | V0 | Token、成本与延迟记录 | [阅读正文](mechanisms/cost-latency-and-caching.md) | `llm_core/cache`、`llm_regression_lab` | 已落地 |

## RAG 与知识系统

端到端四层能力主线：

```text
知识生产
1. 内容识别与解析路由
→ 文件容器 
→ 内容形态
→ 文本抽取 / OCR / 视觉理解
2. 结构还原、清洗与统一表示
→ 原始片段 
→ 标题、段落、表格、阅读顺序和来源位置

固定 RAG
3. Chunk 与 Metadata
→ Lexical / Dense Index
→ Retrieve、RRF 与诊断
→ Context
→ Generate 与评估

动态控制
4.Tool Contract + Tool Runtime
→ Agent 选择 Query / Source / Retrieve / Ask / Stop
```

RAG 与 LLM 通过 Context 和 Structured Output 相接，不是两门彼此隔离的课程。

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RAG 问题空间与完整链路 | 概念 | 主线 | V0 | LLM 应用问题空间与能力边界 | [阅读正文](concepts/rag-and-external-knowledge.md) | 后续 `rag_core` | 已落地 |
| 固定 RAG、搜索、数据库与 Agent 的边界 | 概念 | 主线 | V0 | RAG 问题空间与完整链路 | [阅读正文](concepts/rag-and-external-knowledge.md) | 后续 `rag_core` | 已落地 |
| 内容识别、格式检测与解析路由 | 机制 | 主线 | V0 | RAG 问题空间与完整链路 | [阅读正文](mechanisms/document-loading-and-cleaning.md) | `rag_core/ingestion`、`rag_ingestion_lab` | 已落地 |
| 最小结构还原、清洗与来源保留 | 机制 | 主线 | V0 | 内容识别、格式检测与解析路由 | [阅读正文](mechanisms/document-loading-and-cleaning.md) | `rag_core/ingestion`、`rag_ingestion_lab` | 已落地 |
| 复杂文档与多模态知识生产边界 | 概念 | 支撑 | V1 | 内容识别、格式检测与解析路由、最小结构还原、清洗与来源保留 | `concepts/multimodal-knowledge-production.md` | 无项目实现 | 待编写 |
| 扫描 PDF、图片 OCR/VLM 与 Markdown 归一化 | 机制 | 支撑 | V1 | 复杂文档与多模态知识生产边界 | `mechanisms/ocr-vlm-normalization.md` | 后续按需扩展 ingestion demo | 待编写 |
| 图片理解与音频 ASR 归一化 | 机制 | 支撑 | V3 | 复杂文档与多模态知识生产边界 | `mechanisms/image-audio-normalization.md` | 后续多模态对照 demo | 待编写 |
| 视频理解与流式语音产品 | 概念 | 未来认知 | 未来 | 图片理解与音频 ASR 归一化 | 待按需创建 | 无当前实现 | 未来认知 |
| Chunking、父子块与 Metadata | 机制 | 主线 | V0 | 最小结构还原、清洗与来源保留 | [阅读正文](mechanisms/chunking-and-metadata.md) | `rag_core/chunking`、`rag_ingestion_lab/inspect_chunking.py` | 已落地 |
| Embedding 表示与向量相似度 | 机制 | 主线 | V0 | RAG 问题空间与完整链路、Chunking、父子块与 Metadata | [阅读正文](mechanisms/embedding-and-similarity.md) | `llm_core/client/service.py`、`rag_core/embedding`、`rag_retrieval_lab/inspect_embedding.py` | 已落地 |
| Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索 | 机制 | 主线 | V0 | Chunking、父子块与 Metadata | [阅读正文](mechanisms/lexical-retrieval.md) | `rag_core/lexical`、`rag_core/retrieval`、`rag_retrieval_lab/inspect_lexical_retrieval.py` | 已落地 |
| pgvector、Dense Retrieval 与向量索引 | 机制 | 主线 | V0 | Embedding 表示与向量相似度 | [阅读正文](mechanisms/vector-store-and-pgvector.md) | `rag_core/vector_store`、`rag_core/retrieval/postgres_dense.py`、`rag_retrieval_lab/inspect_dense_retrieval.py` | 已落地 |
| 多路召回与 RRF 融合 | 机制 | 主线 | V0 | Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索、pgvector、Dense Retrieval 与向量索引 | [阅读正文](mechanisms/multi-retrieval-and-rrf.md) | `rag_core/retrieval/fusion.py`、`rag_retrieval_lab/inspect_rrf_retrieval.py` | 已落地 |
| Top-k、阈值、Metadata Filter 与 Retrieval 诊断 | 机制 | 主线 | V0 | 多路召回与 RRF 融合 | [阅读正文](mechanisms/retriever-contract.md) | `rag_core/retrieval/hybrid.py`、`rag_retrieval_lab/inspect_retrieval_contract.py` | 已落地 |
| Reranker、重排诊断与产品准入证据 | 机制 | 主线 | V2 | 多路召回与 RRF 融合、Retrieval 与 Generation Eval | `mechanisms/reranking.md` | 条件准入：通过收益门槛后进入 `rag_core/retrieval` | 待编写 |
| Query Rewrite 与 Source Routing | 机制 | 主线 | V3 | Top-k、阈值、Metadata Filter 与 Retrieval 诊断 | `mechanisms/query-rewrite-and-routing.md` | 后续 `rag_core/query` | 待编写 |
| Context Construction 与 Compression | 机制 | 主线 | V0 | Top-k、阈值、Metadata Filter 与 Retrieval 诊断、Context Engineering 与预算 | [阅读正文](mechanisms/context-engineering.md) | `llm_core/context`、`rag_core/context`、`rag_retrieval_lab/inspect_rag_context.py` | 已落地 |
| 可信生成、Sources 与 Citation Candidate | 机制 | 主线 | V0 | Context Construction 与 Compression、Structured Output 与本地校验 | [阅读正文](mechanisms/trusted-generation.md) | `rag_core/generation`、`review.risk_review@5.0.0`、`rag_retrieval_lab/inspect_trusted_generation.py` | 已落地 |
| Citation 校验、证据充分性、Refusal 与补充问题 | 机制 | 主线 | V1 | 可信生成、Sources 与 Citation Candidate | `mechanisms/citation-and-evidence-validation.md` | 后续 `rag_core/evidence` | 待编写 |
| Retriever as Tool 与 Single Agent RAG | 机制 | 主线 | V3 | Query Rewrite 与 Source Routing、Tool Runtime 与结构化错误 | `mechanisms/single-agent-rag.md` | 后续 `agent_core` | 待编写 |
| RAG Failure Analysis 与 Bad Case 回流 | 机制 | 主线 | V2 | Retrieval 与 Generation Eval、Citation 与 Refusal Eval | `mechanisms/failure-analysis.md` | 后续 `eval_core` | 待编写 |
| RAPTOR、GraphRAG、知识图谱与普通 RAG 的边界 | 概念 | 支撑 | V2 | Chunking、父子块与 Metadata、多路召回与 RRF 融合 | `concepts/advanced-rag-indexes.md` | 无项目实现 | 待编写 |
| Neo4j 多跳检索与 RAG 融合 | 机制 | 支撑 | V2 | RAPTOR、GraphRAG、知识图谱与普通 RAG 的边界 | `mechanisms/graph-retrieval.md` | 后续 GraphRAG 对照 demo | 待编写 |
| 文档版本、更新、删除一致性与 Citation 失效 | 机制 | 主线 | V1 | 最小结构还原、清洗与来源保留、Chunking、父子块与 Metadata | `mechanisms/knowledge-governance.md` | 后续 `rag_core/governance` | 待编写 |
| 多用户知识权限与可见范围 | 概念 | 未来认知 | 未来 | 文档版本、更新、删除一致性与 Citation 失效、Metadata Filter | 待按需创建 | 无当前实现 | 未来认知 |

## Agent 与 Tool

关系主线：

判断是否需要 Agent
→ State、Conversation、Memory 与业务知识
→ Function Calling 与 Tool Runtime
→ Retriever / Memory as Tool
→ Agent Loop、停止和安全

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chain、Workflow、Agent 与 Multi-Agent 边界 | 概念 | 主线 | V3 | 固定 RAG、搜索、数据库与 Agent 的边界 | `concepts/agent-and-workflow-boundaries.md` | 后续 `agent_core` | 待编写 |
| Run State、Conversation、Memory 与业务知识的边界 | 概念 | 主线 | V3 | Chain、Workflow、Agent 与 Multi-Agent 边界 | `concepts/memory-and-knowledge-boundaries.md` | 后续 `agent_core/memory` | 待编写 |
| 短期记忆：滑动窗口、摘要与预算 | 机制 | 主线 | V3 | Run State、Conversation、Memory 与业务知识的边界、Context Engineering 与预算 | `mechanisms/short-term-memory.md` | 后续 `agent_core/memory` | 待编写 |
| 长期记忆：用户确认偏好、作用域、检索与治理 | 机制 | 主线 | V3 | 短期记忆：滑动窗口、摘要与预算、Embedding 表示与向量相似度 | `mechanisms/long-term-memory.md` | V3 最小产品接入：后续 `agent_core/memory` | 待编写 |
| Mem0 与自建 Memory Runtime 对照 | 机制 | 支撑 | V3 | 长期记忆：用户确认偏好、作用域、检索与治理 | 并入长期记忆机制篇 | 对照实验，不作为产品依赖 | 待编写 |
| Function Calling 与 Tool Schema | 机制 | 主线 | V3 | Structured Output 与本地校验 | `mechanisms/tool-schema.md` | 后续 `agent_core/tools` | 待编写 |
| Tool Runtime 与结构化错误 | 机制 | 主线 | V3 | Function Calling 与 Tool Schema | `mechanisms/tool-runtime.md` | 后续 `agent_core/tools` | 待编写 |
| 工具权限、确认、幂等与审计 | 机制 | 主线 | V3 | Tool Runtime 与结构化错误 | `mechanisms/tool-governance.md` | 后续 `agent_core/tools` | 待编写 |
| Agent Loop 与停止条件 | 机制 | 主线 | V3 | Tool Runtime 与结构化错误 | `mechanisms/agent-loop.md` | 后续 `agent_core/runtime` | 待编写 |
| Planning、Task Decomposition 与 Reflection | 机制 | 支撑 | V3 | Agent Loop 与停止条件 | `mechanisms/planning-and-reflection.md` | 后续 `agent_core/runtime` | 待编写 |
| LangChain Agent Patterns | 机制 | 主线 | V3 | Agent Loop 与停止条件 | 并入对应 Agent 机制篇 | 后续 `agent_core` | 待编写 |
| Agentic RAG 深化 | 机制 | 支撑 | V4 | Retriever as Tool 与 Single Agent RAG、Workflow State、Node 与 Edge | `mechanisms/agentic-rag.md` | 后续 `agent_core` | 待编写 |
| Workflow as Tool 与子 Agent | 机制 | 主线 | V5 | Human-in-the-loop、Multi-Agent 拆分判断 | `mechanisms/workflow-as-tool.md` | 后续 `agent_core` | 待编写 |
| MCP、A2A 与 Agent Skills | 概念 | 未来认知 | 未来 | Tool Runtime 与结构化错误 | 待按需创建 | 无当前实现 | 未来认知 |
| Guardrails、Safety 与应用控制边界 | 机制 | 主线 | V3 | 工具权限、确认、幂等与审计、Agent Loop 与停止条件 | `mechanisms/guardrails-and-safety.md` | 后续 `agent_core/safety` | 待编写 |
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

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Workflow State、Node 与 Edge | 机制 | 主线 | V4 | Chain、Workflow、Agent 与 Multi-Agent 边界 | `mechanisms/state-node-edge.md` | 后续 `agent_core/workflow` | 待编写 |
| Node 输入输出契约与状态合并 | 机制 | 主线 | V4 | Workflow State、Node 与 Edge | `mechanisms/state-contracts.md` | 后续 `agent_core/workflow` | 待编写 |
| 条件、循环与并行 | 机制 | 主线 | V4 | Workflow State、Node 与 Edge | `mechanisms/branch-loop-parallel.md` | 后续 `agent_core/workflow` | 待编写 |
| Checkpoint、Interrupt 与 Resume | 机制 | 主线 | V4 | Node 输入输出契约与状态合并 | `mechanisms/checkpoint-and-resume.md` | 后续 `agent_core/workflow` | 待编写 |
| Human-in-the-loop | 机制 | 主线 | V4 | Checkpoint、Interrupt 与 Resume | `mechanisms/human-in-the-loop.md` | 后续 `agent_core/workflow` | 待编写 |
| 节点重试、副作用与幂等 | 机制 | 主线 | V4 | Node 输入输出契约与状态合并、工具权限、确认、幂等与审计 | `mechanisms/retry-and-idempotency.md` | 后续 `agent_core/workflow` | 待编写 |
| LangGraph 框架映射与运行调试 | 机制 | 主线 | V4 | Workflow State、Node 与 Edge、Node 输入输出契约与状态合并、条件、循环与并行、Checkpoint、Interrupt 与 Resume、Human-in-the-loop、节点重试、副作用与幂等 | 并入 Workflow 机制篇 | 后续 `agent_core/workflow` | 待编写 |

## Multi-Agent

关系主线：

先证明单 Agent 不足
→ 划分角色、上下文、工具和输出契约
→ 分配与并行执行
→ 共享状态和失败隔离
→ 汇总、证据合并与冲突裁决
→ 与单 Agent 基线比较

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Multi-Agent 拆分判断 | 概念 | 主线 | V5 | Chain、Workflow、Agent 与 Multi-Agent 边界、Workflow State、Node 与 Edge | `concepts/multi-agent-collaboration.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 角色责任、上下文、工具和输出契约 | 机制 | 主线 | V5 | Multi-Agent 拆分判断 | `mechanisms/multi-agent-contracts.md` | 后续 `agent_core/multi_agent` | 待编写 |
| Supervisor / Worker 与任务分配 | 机制 | 主线 | V5 | 角色责任、上下文、工具和输出契约 | `mechanisms/supervisor-worker.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 共享状态、私有上下文与证据 | 机制 | 主线 | V5 | 角色责任、上下文、工具和输出契约、Node 输入输出契约与状态合并 | `mechanisms/multi-agent-state.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 并行执行、依赖和失败隔离 | 机制 | 主线 | V5 | Supervisor / Worker 与任务分配、条件、循环与并行 | `mechanisms/multi-agent-execution.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 结果汇总、证据合并与冲突裁决 | 机制 | 主线 | V5 | 共享状态、私有上下文与证据 | `mechanisms/result-merge-and-conflict.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 单 Agent 与多 Agent 基线比较 | 项目 | 主线 | V5 | Multi-Agent 拆分判断、角色责任、上下文、工具和输出契约、Supervisor / Worker 与任务分配、共享状态、私有上下文与证据、并行执行、依赖和失败隔离、结果汇总、证据合并与冲突裁决 | 对应 V5 项目篇 | 后续 `eval_core` | 待编写 |

## Evaluation 与 Observability

关系主线：

固定样例与 Golden Set
→ 检索、生成、Citation 和 Refusal 评估
→ Agent / Workflow 轨迹评估
→ Trace、版本和回归
→ Bad Case 与 Feedback Loop

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Evaluation Dataset 与最小 Golden Set | 机制 | 主线 | V0 | 项目业务契约 | `mechanisms/dataset-and-golden-set.md` | 后续 `eval_core` | 待编写 |
| Retrieval 与 Generation Eval | 机制 | 主线 | V2 | 多路召回与 RRF 融合、Top-k、阈值、Metadata Filter 与 Retrieval 诊断、可信生成、Sources 与 Citation Candidate | `mechanisms/rag-evaluation.md` | 后续 `eval_core/rag` | 待编写 |
| Citation 与 Refusal Eval | 机制 | 主线 | V2 | Citation 校验、证据充分性、Refusal 与补充问题 | `mechanisms/citation-and-refusal.md` | 后续 `eval_core/rag` | 待编写 |
| Bad Case Management | 机制 | 主线 | V2 | Evaluation Dataset 与最小 Golden Set、Retrieval 与 Generation Eval、Citation 与 Refusal Eval | `mechanisms/bad-case-management.md` | 后续 `eval_core` | 待编写 |
| Agent Trajectory、Tool 与 Memory Eval | 机制 | 主线 | V3 | Tool Runtime 与结构化错误、长期记忆：用户确认偏好、作用域、检索与治理、Agent Loop 与停止条件 | `mechanisms/agent-and-tool-evaluation.md` | 后续 `eval_core/agent` | 待编写 |
| Workflow Eval 与 Human Review | 机制 | 主线 | V4 | Workflow State、Node 与 Edge、Human-in-the-loop | `mechanisms/workflow-evaluation.md` | 后续 `eval_core/workflow` | 待编写 |
| Trace、Span 与 Run 关联 | 机制 | 主线 | V2 | 调用 Harness、回归与版本比较、Evaluation Dataset 与最小 Golden Set | `mechanisms/trace-and-observability.md` | `llm_core/harness` + 后续 `eval_core` | 待编写 |
| Versioning、Regression 与 Experiment | 机制 | 主线 | V2 | Evaluation Dataset 与最小 Golden Set、Trace、Span 与 Run 关联 | `mechanisms/versioning-and-regression.md` | 后续 `eval_core` | 待编写 |
| Cost、Latency 与运行指标 | 机制 | 主线 | V2 | Token、成本与延迟记录、Trace、Span 与 Run 关联 | `mechanisms/cost-latency-metrics.md` | `llm_core/costing` + 后续 `eval_core` | 待编写 |
| LLM-as-Judge 与 Human Eval | 机制 | 主线 | V2 | Evaluation Dataset 与最小 Golden Set | `mechanisms/llm-as-judge.md` | 后续 `eval_core` | 待编写 |
| Feedback Loop | 机制 | 主线 | V2 | Bad Case Management | `mechanisms/feedback-loop.md` | 后续 `eval_core` | 待编写 |
| Engineering Contract Tests | 机制 | 主线 | V1 | 项目 Schema、Citation 校验、证据充分性、Refusal 与补充问题 | `mechanisms/engineering-contract-tests.md` | package / product tests | 待编写 |

## AI Native 体验

关系主线：

最小 Web 请求状态与评审结果
→ 可信证据与结构化报告
→ 评估、标注和反馈
→ Agent / Workflow / Multi-Agent 运行过程
→ 工作台整合与交付

当前主项目的 `workbench` 统一指 Web 工作台；Flutter 不作为 V0–V6 产品入口或验收项。

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AI Native 问题空间 | 概念 | 主线 | V0 | LLM 应用问题空间与能力边界 | `concepts/ai-native-interface.md` | 产品 workbench | 待编写 |
| 最小请求状态与结构化 Web 评审界面 | 机制 | 主线 | V0 | AI Native 问题空间、Structured Output 与本地校验、FastAPI、Review API 与错误契约 | `mechanisms/review-request-state.md` | 产品 Web workbench | 待编写 |
| Schema Driven UI 与结构化评审报告 | 机制 | 主线 | V1 | Structured Output 与本地校验 | `mechanisms/schema-driven-review.md` | 产品 workbench | 待编写 |
| Sources、Citation、Refusal 与补充信息交互 | 机制 | 主线 | V1 | Citation 校验、证据充分性、Refusal 与补充问题、Schema Driven UI 与结构化评审报告 | `mechanisms/evidence-and-refusal-ui.md` | 产品 workbench | 待编写 |
| Eval、Labeling 与 Feedback UI | 机制 | 主线 | V2 | Bad Case Management、Feedback Loop | `mechanisms/eval-and-feedback-ui.md` | 产品 workbench | 待编写 |
| SSE 结构化事件协议 | 机制 | 主线 | V3 | Agent Loop 与停止条件、FastAPI、Review API 与错误契约 | `mechanisms/sse-event-protocol.md` | 产品 app / workbench | 待编写 |
| Streaming State Synchronization | 机制 | 主线 | V3 | SSE 结构化事件协议 | `mechanisms/streaming-state.md` | 产品 workbench | 待编写 |
| AI Response State Machine | 机制 | 主线 | V3 | Streaming State Synchronization、Agent Loop 与停止条件 | `mechanisms/response-state-machine.md` | 产品 workbench | 待编写 |
| Tool Call、Memory、证据变化与 Agent 轨迹 UI | 机制 | 主线 | V3 | AI Response State Machine、Agent Trajectory、Tool 与 Memory Eval | `mechanisms/agent-runtime-ui.md` | 产品 workbench | 待编写 |
| Workflow Runtime UI | 机制 | 主线 | V4 | Workflow State、Node 与 Edge、Node 输入输出契约与状态合并、条件、循环与并行、Checkpoint、Interrupt 与 Resume、Human-in-the-loop | `mechanisms/workflow-runtime-ui.md` | 产品 workbench | 待编写 |
| Multi-Agent UI / UX | 机制 | 主线 | V5 | 角色责任、上下文、工具和输出契约、Supervisor / Worker 与任务分配、共享状态、私有上下文与证据、并行执行、依赖和失败隔离、结果汇总、证据合并与冲突裁决 | `mechanisms/multi-agent-ux.md` | 产品 workbench | 待编写 |
| 知识与质量工作台完善 | 项目 | 主线 | V6 | 文档版本、更新、删除一致性与 Citation 失效、Eval、Labeling 与 Feedback UI | 对应 V6 项目篇 | 产品 workbench | 待编写 |
| 工作台整合、部署与作品化 | 项目 | 主线 | V6 | 全部主线 | 对应 V6 项目篇 | `review_assistant/` | 待编写 |

## 工程基础

工程能力按项目需要进入，用于承载真实 API、数据、任务、观测和部署，不扩展成独立后端大课。

| 知识 | 类型 | 定位 | 最早进入 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Python、HTTP、JSON 与配置 | 基础 | 支撑 | V0 | `python_base` | 按需回查 `python_base/` | 根项目 | 已落地 |
| FastAPI、Review API 与错误契约 | 机制 | 主线 | V0 | Python、HTTP、JSON 与配置、Structured Output 与本地校验 | `mechanisms/fastapi-and-api.md` | 产品 app | 待编写 |
| PostgreSQL 关系模型、SQL 与本地运行 | 概念 | 支撑 | V0 | Python、HTTP、JSON 与配置 | [阅读正文](concepts/postgresql-for-ai-applications.md) | `review_assistant/infra`、产品 README | 已落地 |
| Redis、后台任务与入库状态 | 机制 | 主线 | V4 | 内容识别、格式检测与解析路由、最小结构还原、清洗与来源保留、Checkpoint、Interrupt 与 Resume | `mechanisms/background-jobs.md` | 产品 infra | 待编写 |
| Docker Compose 本地部署 | 机制 | 主线 | V6 | 产品入口 | `mechanisms/docker-compose.md` | 产品 infra | 待编写 |
| 日志、Metrics 与工程观测 | 机制 | 主线 | V2 | Trace、Span 与 Run 关联 | `mechanisms/logging-and-metrics.md` | `app_log` + 后续产品 app / infra | 待编写 |
| 文件、对象存储与数据生命周期 | 机制 | 支撑 | V6 | 内容识别、格式检测与解析路由、最小结构还原、清洗与来源保留、文档版本、更新、删除一致性与 Citation 失效 | `mechanisms/file-storage.md` | 产品 infra | 待编写 |
| Kubernetes、灰度、多租户与权限中台 | 概念 | 未来认知 | 未来 | Docker Compose 本地部署、日志、Metrics 与工程观测 | 无当前正文 | 无当前实现 | 未来认知 |

## 维护边界

- 新增知识前先判断能否合并到现有知识。
- 知识名称必须让学习者直接理解，不使用内部编号或编号范围。
- 标准阅读顺序只维护在 `course/learning-path.md`。
- 项目业务任务、设计选择和验收只维护在 course/project/。
- 框架映射优先并入对应机制篇，不独立形成第四类文档。
- 未来认知不创建占位正文、空 package、空 demo 或空 app。
