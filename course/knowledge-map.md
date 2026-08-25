# AI 应用知识地图

这份文档是课程的完整知识书架。

它回答：

- AI 应用开发需要理解哪些概念和机制。
- 每项知识解决什么范围的问题。
- 理解它之前真正需要知道什么。
- 它属于第一阶段、第二阶段、跨阶段还是未来认知。
- 对应正文和代码在哪里。

它不安排阅读顺序，也不维护课程序号。现在应该读什么，以[标准学习路径](learning-path.md)为准；什么时候把能力组合成产品，以对应阶段项目篇为准。

## 怎样使用

### 想开始学习

不要从这张表逐行阅读。回到[标准学习路径](learning-path.md)，按第 1–65 节连续编号，从概念、机制和小实验进入。

### 想查完整知识体系

选择一个能力域，沿该域的关系主线查看知识之间怎样连接，再按需要进入正文。

### 想检查项目为什么缺一项能力

先从项目失败现象判断属于模型、知识生产、检索、上下文、工具、状态、协作、评估还是交互，再来这里定位对应机制和代码入口。

## 正文状态、学习定位与产品关系

| 标记 | 含义 |
| --- | --- |
| 主线 | 标准学习路径必须理解、实验或作出设计判断；不等于能力必然进入产品默认链路 |
| 必备基础 | 进入对应主线前必须具备；已有经验者可以通过检查，不必重新通关 |
| 扩展 | 不阻塞阶段验收，在真实问题出现或希望深化时进入 |
| 未来认知 | 保留视野，当前项目不实现 |
| 已落地 | 正文与该文档类型所需的必要实验已经存在；产品是否接入另看代码入口和项目篇 |
| 待编写 | 知识位置已确认，正文与真实代码按学习需要逐步落地 |
| 等待前置 | 正文或项目契约已存在，但必须先完成前面的知识或产品能力 |

表格中的“正文状态”只回答当前能否按正文学习，不表示产品已经启用。代码入口独立说明实现位置：`后续` 表示尚未实现，真实路径表示已有实现，`无项目实现` 表示当前只做认知，`条件准入` 表示必须先实验但未必进入产品。

知识项不与文档一一对应。一篇概念篇或机制篇可以讲清多个紧密相关的知识，一项知识也可以被概念、机制和项目从不同角度使用。

## 两个阶段的能力主链

### 第一阶段：RAG 应用基础

```text
模型边界与输入输出契约
→ 文档解析、Chunk 与 Metadata
→ Embedding、Lexical、Dense 与 RRF
→ Retriever Contract 与 Context
→ Structured Output、Citation、Refusal
→ Review API 与证据界面
→ Calling Harness、Golden Set 与固定对照
```

第一阶段交付可运行、可诊断、具有最小可信证据的固定 RAG 产品。Reranker、GraphRAG、OCR/VLM 和完整质量平台属于扩展，不阻塞进入第二阶段。

### 第二阶段：Agent、Tools 与 Multi-Agent 系统

```text
执行结构判断
→ Agent Harness
→ Tool Schema、Runtime、权限与停止
→ Agentic RAG
→ State、Conversation、Memory
→ SSE、Streaming 与运行界面
→ MCP、通用工具与 Agent Skills
→ Planning 与 Deep Research
→ Multi-Agent、Delegation 与 A2A
→ 必要 Workflow、恢复与人工介入
→ Trace、Evaluation 与 Feedback
```

Multi-Agent 是第二阶段核心；Workflow 只补齐显式状态、恢复、人工介入和副作用控制，不单独成为大阶段。质量证据在每个复杂度层级进入，完整质量工程在第二阶段后部收束。

## 阶段项目

| 项目 | 类型 | 定位 | 进入阶段 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 固定 RAG 需求评审助手 | 项目 | 主线 | 第一阶段 | 第一阶段第 1–24 节 | [第一阶段项目篇](project/stage-1-rag-application/rag-review-assistant.md) | `review_assistant/` | 等待前置 |
| Agent 协作需求评审系统 | 项目 | 主线 | 第二阶段 | 第一阶段项目、第二阶段 Agent / Tool / Multi-Agent 主线 | 第二阶段项目篇在进入实现前创建 | 后续 `review_assistant/` | 待编写 |

## LLM 与模型交互

关系主线：

```text
模型在应用中的位置
→ Prompt、Context 与 Schema 契约
→ Provider、Structured Output 与 Reliability
→ Calling Harness、Cost 与 Cache
```

| 知识 | 类型 | 定位 | 进入阶段 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LLM 应用问题空间与能力边界 | 概念 | 主线 | 第一阶段 | 无 | [阅读正文](concepts/llm-in-ai-applications.md) | `llm_invoke_lab/first_chat.py` | 已落地 |
| Prompt、Schema、Context 的模型契约 | 概念 | 主线 | 第一阶段 | LLM 应用问题空间与能力边界 | [阅读正文](concepts/model-input-output-contracts.md) | `llm_core/prompts`、`schemas`、`context` | 已落地 |
| 一次模型调用的生命周期 | 机制 | 主线 | 第一阶段 | 模型输入输出契约 | [阅读正文](mechanisms/model-api-and-provider.md) | `llm_core/client`、`llm_invoke_lab` | 已落地 |
| Provider、模型配置与供应商差异 | 机制 | 主线 | 第一阶段 | 一次模型调用的生命周期 | [阅读正文](mechanisms/model-api-and-provider.md) | `llm_core/providers`、`config` | 已落地 |
| 面向应用的 Prompt Engineering | 机制 | 主线 | 第一阶段 | 模型输入输出契约 | [阅读正文](mechanisms/prompt-engineering.md) | `llm_core/prompts` | 已落地 |
| Structured Output 与本地校验 | 机制 | 主线 | 第一阶段 | Prompt Engineering | [阅读正文](mechanisms/structured-output.md) | `llm_core/structured`、`schemas` | 已落地 |
| 错误分类、重试、降级与可靠调用 | 机制 | 主线 | 第一阶段 | 一次模型调用的生命周期、Structured Output | [阅读正文](mechanisms/reliability-and-errors.md) | `llm_core/errors`、`reliability` | 已落地 |
| Context Engineering 与预算 | 机制 | 主线 | 第一阶段 | 模型输入输出契约、Retriever Contract | [阅读正文](mechanisms/context-engineering.md) | `llm_core/context`、`rag_core/context` | 已落地 |
| 调用 Harness、回归与版本比较 | 机制 | 主线 | 第一阶段 | 固定 RAG 生成链、可靠调用 | [阅读正文](mechanisms/calling-harness-and-regression.md) | `llm_core/harness`、`llm_regression_lab` | 已落地 |
| Token、成本与延迟记录 | 机制 | 主线 | 第一阶段 | Calling Harness | [阅读正文](mechanisms/cost-latency-and-caching.md) | `llm_core/costing`、`llm_regression_lab` | 已落地 |
| Exact-match Cache 与失效边界 | 机制 | 扩展 | 第一阶段 | Token、成本与延迟记录 | [阅读正文](mechanisms/cost-latency-and-caching.md) | `llm_core/cache` | 已落地 |

## RAG 与知识系统

关系主线：

```text
内容识别与解析路由
→ 结构还原、清洗与来源保留
→ Chunk 与 Metadata
→ Embedding、Lexical、Dense 与 RRF
→ 过滤、阈值与诊断
→ Context
→ 可信生成、Citation 与 Refusal
→ Retriever as Tool
```

| 知识 | 类型 | 定位 | 进入阶段 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RAG 问题空间与完整链路 | 概念 | 主线 | 第一阶段 | LLM 应用问题空间与能力边界 | [阅读正文](concepts/rag-and-external-knowledge.md) | `rag_core` | 已落地 |
| 固定 RAG、搜索、数据库与 Agentic RAG 的边界 | 概念 | 主线 | 第一阶段 | RAG 问题空间与完整链路 | [阅读正文](concepts/rag-and-external-knowledge.md) | 选型边界 | 已落地 |
| 内容识别、格式检测与解析路由 | 机制 | 主线 | 第一阶段 | RAG 问题空间与完整链路 | [阅读正文](mechanisms/document-loading-and-cleaning.md) | `rag_core/ingestion`、`rag_ingestion_lab` | 已落地 |
| 最小结构还原、清洗与来源保留 | 机制 | 主线 | 第一阶段 | 内容识别与解析路由 | [阅读正文](mechanisms/document-loading-and-cleaning.md) | `rag_core/ingestion` | 已落地 |
| Chunking、父子块与 Metadata | 机制 | 主线 | 第一阶段 | 结构还原、清洗与来源保留 | [阅读正文](mechanisms/chunking-and-metadata.md) | `rag_core/chunking`、`inspect_chunking.py` | 已落地 |
| Embedding 表示与向量相似度 | 机制 | 主线 | 第一阶段 | RAG 问题空间、Chunking | [阅读正文](mechanisms/embedding-and-similarity.md) | `rag_core/embedding`、`inspect_embedding.py` | 已落地 |
| Lexical Retrieval、BM25 边界与 PostgreSQL FTS | 机制 | 主线 | 第一阶段 | Chunking、PostgreSQL 必备基础 | [阅读正文](mechanisms/lexical-retrieval.md) | `rag_core/lexical`、`postgres_fts.py` | 已落地 |
| pgvector、Dense Retrieval 与向量索引 | 机制 | 主线 | 第一阶段 | Embedding 表示与向量相似度、PostgreSQL 必备基础 | [阅读正文](mechanisms/vector-store-and-pgvector.md) | `rag_core/vector_store`、`postgres_dense.py` | 已落地 |
| 多路召回与 RRF 融合 | 机制 | 主线 | 第一阶段 | Lexical Retrieval、Dense Retrieval | [阅读正文](mechanisms/multi-retrieval-and-rrf.md) | `rag_core/retrieval/fusion.py`、`inspect_rrf_retrieval.py` | 已落地 |
| Top-k、阈值、Metadata Filter 与 Retrieval 诊断 | 机制 | 主线 | 第一阶段 | 多路召回与 RRF | [阅读正文](mechanisms/retriever-contract.md) | `rag_core/retrieval/hybrid.py` | 已落地 |
| Context Construction 与 Compression | 机制 | 主线 | 第一阶段 | Retriever Contract、Context Engineering | [阅读正文](mechanisms/context-engineering.md) | `llm_core/context`、`rag_core/context` | 已落地 |
| 可信生成、Sources 与 Citation Candidate | 机制 | 主线 | 第一阶段 | Context Construction、Structured Output | [阅读正文](mechanisms/trusted-generation.md) | `rag_core/generation` | 已落地 |
| Citation 支持性、证据充分性、Refusal 与补充问题 | 机制 | 主线 | 第一阶段 | 可信生成与 Citation Candidate | `mechanisms/citation-and-evidence-validation.md` | 后续 `rag_core/evidence` | 待编写 |
| Retriever as Tool 与 Agentic RAG | 机制 | 主线 | 第二阶段 | Retriever Contract、Tool Runtime | `mechanisms/single-agent-rag.md` | 后续 `agent_core` | 待编写 |
| Query Rewrite 与 Source Routing | 机制 | 主线 | 第二阶段 | Retriever Contract、Agent Loop | `mechanisms/query-rewrite-and-routing.md` | 后续 `agent_core/query` | 待编写 |
| Reranker 与产品准入证据 | 机制 | 扩展 | 第一阶段 | RRF、最小 RAG Evaluation | `mechanisms/reranking.md` | 条件准入：通过收益门槛后进入 `rag_core/retrieval` | 待编写 |
| 文档版本、更新、删除一致性与 Citation 失效 | 机制 | 扩展 | 第一阶段 | 来源保留、Chunk、Citation | `mechanisms/knowledge-governance.md` | 后续 `rag_core/governance` | 待编写 |
| 复杂文档、OCR/VLM 与多模态归一化 | 机制 | 扩展 | 第一阶段 | 内容识别与结构还原 | `mechanisms/ocr-vlm-normalization.md` | 后续 ingestion 对照实验 | 待编写 |
| RAPTOR、GraphRAG 与普通 RAG 的边界 | 概念 | 扩展 | 第一阶段 | Chunking、RRF | `concepts/advanced-rag-indexes.md` | 无项目实现 | 待编写 |
| Neo4j 多跳检索与 RAG 融合 | 机制 | 扩展 | 第一阶段 | GraphRAG 边界 | `mechanisms/graph-retrieval.md` | 后续对照实验 | 待编写 |
| 多用户知识权限与可见范围 | 概念 | 未来认知 | 未来认知 | 知识治理、Metadata Filter | 无当前正文 | 无当前实现 | 未来认知 |

## Agent Harness、Tool 与研究能力

关系主线：

```text
执行结构判断
→ Agent Harness
→ Tool Schema 与 Runtime
→ 权限、停止与 Guardrails
→ Agentic RAG
→ State、Conversation 与 Memory
→ MCP、通用工具与 Agent Skills
→ Planning 与 Deep Research
```

| 知识 | 类型 | 定位 | 进入阶段 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chain、固定 RAG、Workflow、Agent 与 Multi-Agent 边界 | 概念 | 主线 | 第二阶段 | 第一阶段固定 RAG | `concepts/agent-and-workflow-boundaries.md` | 选型边界 | 待编写 |
| Agent Harness 与应用控制面 | 机制 | 主线 | 第二阶段 | 执行结构判断、可靠调用 | `mechanisms/agent-harness.md` | 后续 `agent_core/runtime` | 待编写 |
| Function Calling 与 Tool Schema | 机制 | 主线 | 第二阶段 | Structured Output | `mechanisms/tool-schema.md` | 后续 `agent_core/tools` | 待编写 |
| Tool Runtime 与结构化错误 | 机制 | 主线 | 第二阶段 | Tool Schema | `mechanisms/tool-runtime.md` | 后续 `agent_core/tools` | 待编写 |
| 工具权限、高风险确认、超时、幂等与审计 | 机制 | 主线 | 第二阶段 | Tool Runtime | `mechanisms/tool-governance.md` | 后续 `agent_core/tools` | 待编写 |
| Agent Loop、预算、最大步数与停止原因 | 机制 | 主线 | 第二阶段 | Tool Runtime | `mechanisms/agent-loop.md` | 后续 `agent_core/runtime` | 待编写 |
| Guardrails、Safety 与应用控制边界 | 机制 | 主线 | 第二阶段 | 工具治理、Agent Loop | `mechanisms/guardrails-and-safety.md` | 后续 `agent_core/safety` | 待编写 |
| Run State、Conversation、Memory 与业务知识边界 | 概念 | 主线 | 第二阶段 | Agent Harness | `concepts/memory-and-knowledge-boundaries.md` | 后续 `agent_core/memory` | 待编写 |
| 短期记忆：窗口、摘要与预算 | 机制 | 主线 | 第二阶段 | 状态与记忆边界、Context Engineering | `mechanisms/short-term-memory.md` | 后续 `agent_core/memory` | 待编写 |
| 长期记忆：用户确认偏好、作用域、检索与治理 | 机制 | 主线 | 第二阶段 | 短期记忆、Embedding | `mechanisms/long-term-memory.md` | 条件接入 `agent_core/memory` | 待编写 |
| MCP 与 Tool / Resource 连接边界 | 机制 | 主线 | 第二阶段 | Tool Runtime、工具治理 | `mechanisms/mcp-integration.md` | 后续 MCP 对照实验与 `agent_core/tools` | 待编写 |
| Browser 与 Search Tool | 机制 | 主线 | 第二阶段 | Tool Runtime、来源与 Citation | `mechanisms/browser-and-search-tools.md` | 后续 Agent Tool 实验 | 待编写 |
| Code 与 File Tool | 机制 | 主线 | 第二阶段 | Tool Runtime、工具治理 | `mechanisms/code-and-file-tools.md` | 后续受控执行实验 | 待编写 |
| Agent Skills 与可复用领域能力 | 机制 | 主线 | 第二阶段 | Tool Runtime、MCP 边界 | `mechanisms/agent-skills.md` | `skills/` + 后续 Agent 实验 | 待编写 |
| Planning、Task Decomposition 与 Reflection | 机制 | 主线 | 第二阶段 | Agent Loop、Tool Runtime | `mechanisms/planning-and-reflection.md` | 后续 `agent_core/runtime` | 待编写 |
| Deep Research | 机制 | 主线 | 第二阶段 | Planning、Browser / Search Tool、Citation | `mechanisms/deep-research.md` | 后续研究实验与 `agent_core/research` | 待编写 |
| Mem0 与自建 Memory Runtime 对照 | 机制 | 扩展 | 第二阶段 | 长期记忆 | 并入长期记忆机制篇 | 对照实验，不作为产品默认依赖 | 待编写 |
| LangChain / LangGraph Agent 模式映射 | 机制 | 扩展 | 第二阶段 | Agent Harness、Agent Loop | 并入对应机制篇 | 按实现映射到 `agent_core` | 待编写 |
| 多模态 Agent Tool | 概念 | 扩展 | 第二阶段 | Tool Runtime、Browser / File Tool | 待按需创建 | 无默认产品实现 | 待编写 |

## Multi-Agent 与 A2A

关系主线：

```text
先证明单 Agent 不足
→ 划分责任、上下文、工具和输出契约
→ Delegation 与并行执行
→ 共享状态和失败隔离
→ 证据合并与冲突裁决
→ A2A 互操作
→ 与单 Agent 基线比较
```

| 知识 | 类型 | 定位 | 进入阶段 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Multi-Agent 拆分判断 | 概念 | 主线 | 第二阶段 | 单 Agent 基线、执行结构判断 | `concepts/multi-agent-collaboration.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 角色责任、上下文、工具与输出契约 | 机制 | 主线 | 第二阶段 | Multi-Agent 拆分判断 | `mechanisms/multi-agent-contracts.md` | 后续 `agent_core/multi_agent` | 待编写 |
| Supervisor、Worker、Delegation 与任务分配 | 机制 | 主线 | 第二阶段 | Multi-Agent 契约 | `mechanisms/supervisor-worker.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 共享状态、私有上下文与证据 | 机制 | 主线 | 第二阶段 | Multi-Agent 契约、Run State | `mechanisms/multi-agent-state.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 并行执行、任务依赖与失败隔离 | 机制 | 主线 | 第二阶段 | Delegation、共享状态 | `mechanisms/multi-agent-execution.md` | 后续 `agent_core/multi_agent` | 待编写 |
| 结果汇总、证据合并与冲突裁决 | 机制 | 主线 | 第二阶段 | 共享状态与证据 | `mechanisms/result-merge-and-conflict.md` | 后续 `agent_core/multi_agent` | 待编写 |
| A2A 任务、状态、结果与错误交换 | 机制 | 主线 | 第二阶段 | Multi-Agent 契约、Delegation | `mechanisms/a2a-collaboration.md` | 后续 A2A 对照实验 | 待编写 |
| Multi-Agent 运行观测与协作界面 | 机制 | 主线 | 第二阶段 | 并行执行、汇总与冲突 | `mechanisms/multi-agent-ux.md` | 产品 workbench | 待编写 |
| 单 Agent 与 Multi-Agent 基线比较 | 项目 | 主线 | 第二阶段 | 完整 Multi-Agent 主线 | 第二阶段项目篇 | 后续 `eval_core` | 待编写 |

## 必要 Workflow 控制

Workflow 不单独成为项目阶段。它在 Agent 与 Multi-Agent 之后补齐显式状态、恢复、人工介入和副作用控制。

```text
State / Node / Edge
→ 条件、循环与并行
→ Checkpoint / Interrupt / Resume
→ Human-in-the-loop
→ 重试、副作用与幂等
→ Workflow as Tool / 子 Agent
```

| 知识 | 类型 | 定位 | 进入阶段 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Workflow State、Node、Edge 与状态契约 | 机制 | 主线 | 第二阶段 | Agent Harness、Run State | `mechanisms/state-node-edge.md` | 后续 `agent_core/workflow` | 待编写 |
| 条件、循环与并行 | 机制 | 主线 | 第二阶段 | Workflow State | `mechanisms/branch-loop-parallel.md` | 后续 `agent_core/workflow` | 待编写 |
| Checkpoint、Interrupt 与 Resume | 机制 | 主线 | 第二阶段 | Workflow State | `mechanisms/checkpoint-and-resume.md` | 后续 `agent_core/workflow` | 待编写 |
| Human-in-the-loop | 机制 | 主线 | 第二阶段 | Checkpoint 与 Resume | `mechanisms/human-in-the-loop.md` | 后续 `agent_core/workflow` | 待编写 |
| 节点重试、副作用与幂等 | 机制 | 主线 | 第二阶段 | 状态契约、工具治理 | `mechanisms/retry-and-idempotency.md` | 后续 `agent_core/workflow` | 待编写 |
| Workflow as Tool、子 Agent 与可恢复编排 | 机制 | 主线 | 第二阶段 | Agent Loop、Multi-Agent、Workflow State | `mechanisms/workflow-as-tool.md` | 后续 `agent_core/workflow` | 待编写 |
| 通用低代码 Workflow 画布 | 概念 | 未来认知 | 未来认知 | 完整 Workflow Runtime | 无当前正文 | 无当前实现 | 未来认知 |

## Evaluation 与 Observability

质量工程不独占阶段。最小证据在对应机制旁进入，完整 Trace、Regression、Human Eval 和 Feedback 在第二阶段后部统一收束。

```text
最小 Golden Set 与固定对照
→ Agent Tool / Trajectory / Stop Evaluation
→ Deep Research 来源与停止评估
→ Multi-Agent 分工与协作收益比较
→ Trace、Versioning、Regression、Bad Case 与 Feedback
```

| 知识 | 类型 | 定位 | 进入阶段 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Evaluation Dataset 与最小 Golden Set | 机制 | 主线 | 第一阶段 | 阶段项目契约 | `mechanisms/dataset-and-golden-set.md` | 后续 `eval_core` | 待编写 |
| 固定 RAG 四路对照 | 项目 | 主线 | 第一阶段 | Golden Set、固定 RAG 生成链 | 第一阶段项目篇 | 后续 `eval_core/rag` | 待编写 |
| Retrieval 与 Generation Eval 深化 | 机制 | 扩展 | 第一阶段 | 最小 Golden Set、Retriever、Generator | `mechanisms/rag-evaluation.md` | 后续 `eval_core/rag` | 待编写 |
| Citation 与 Refusal Eval 深化 | 机制 | 扩展 | 第一阶段 | Citation、Refusal | `mechanisms/citation-and-refusal.md` | 后续 `eval_core/rag` | 待编写 |
| Agent Trajectory、Tool 与 Memory Eval | 机制 | 主线 | 第二阶段 | Tool Runtime、Memory、Agent Loop | `mechanisms/agent-and-tool-evaluation.md` | 后续 `eval_core/agent` | 待编写 |
| Deep Research 来源、覆盖与停止评估 | 机制 | 主线 | 第二阶段 | Deep Research | 并入 Deep Research 与统一评估机制篇 | 后续 `eval_core/research` | 待编写 |
| Multi-Agent 分工、协作与冲突评估 | 机制 | 主线 | 第二阶段 | Multi-Agent 完整主线 | 并入统一评估机制篇 | 后续 `eval_core/multi_agent` | 待编写 |
| Workflow 路径与 Human Review | 机制 | 主线 | 第二阶段 | Workflow、Human-in-the-loop | 并入统一评估机制篇 | 后续 `eval_core/workflow` | 待编写 |
| Trace、Span 与 Run 关联 | 机制 | 主线 | 第二阶段 | Calling Harness、Agent Harness | `mechanisms/trace-and-observability.md` | `llm_core/harness` + 后续 `eval_core` | 待编写 |
| Versioning、Regression 与 Experiment | 机制 | 主线 | 第二阶段 | Trace、Golden Set | `mechanisms/versioning-and-regression.md` | 后续 `eval_core` | 待编写 |
| LLM-as-Judge 与 Human Eval | 机制 | 主线 | 第二阶段 | Evaluation Dataset | `mechanisms/llm-as-judge.md` | 后续 `eval_core` | 待编写 |
| Bad Case Management 与 Feedback Loop | 机制 | 主线 | 第二阶段 | 统一评估、Trace | `mechanisms/bad-case-management.md`、`mechanisms/feedback-loop.md` | 后续 `eval_core` | 待编写 |
| 完整评估平台与质量工作台 | 项目 | 扩展 | 第二阶段 | 统一质量工程 | 按真实需要进入项目篇 | 产品 workbench | 待编写 |

## AI Native 体验

关系主线：

```text
固定 RAG 请求状态与证据
→ Agent 结构化事件与运行状态
→ Tool、Memory 与轨迹
→ Multi-Agent 分工、冲突与人工介入
```

当前主项目只维护一个 Web 工作台，不并行建设 Flutter App。

| 知识 | 类型 | 定位 | 进入阶段 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AI Native 问题空间与不确定性表达 | 概念 | 主线 | 第一阶段 | LLM 应用边界 | `concepts/ai-native-interface.md` | 产品 workbench | 待编写 |
| 最小请求状态与结构化评审界面 | 机制 | 主线 | 第一阶段 | Structured Output、Review API | `mechanisms/review-request-state.md` | 产品 workbench | 待编写 |
| Sources、Citation、Refusal 与补充信息交互 | 机制 | 主线 | 第一阶段 | Citation、Refusal | `mechanisms/evidence-and-refusal-ui.md` | 产品 workbench | 待编写 |
| SSE 结构化事件协议 | 机制 | 主线 | 第二阶段 | Agent Loop、FastAPI | `mechanisms/sse-event-protocol.md` | `llm_core/streaming`、产品 app | 待编写 |
| Streaming State Synchronization | 机制 | 主线 | 第二阶段 | SSE 事件协议 | `mechanisms/streaming-state.md` | 产品 workbench | 待编写 |
| AI Response State Machine 与 Agent Runtime UI | 机制 | 主线 | 第二阶段 | Streaming、Agent Loop | `mechanisms/response-state-machine.md`、`mechanisms/agent-runtime-ui.md` | 产品 workbench | 待编写 |
| Multi-Agent 运行观测与协作界面 | 机制 | 主线 | 第二阶段 | Multi-Agent 执行与冲突 | `mechanisms/multi-agent-ux.md` | 产品 workbench | 待编写 |
| Workflow 恢复与人工介入界面 | 机制 | 主线 | 第二阶段 | Checkpoint、Human-in-the-loop | `mechanisms/workflow-runtime-ui.md` | 产品 workbench | 待编写 |
| Eval、Labeling 与 Feedback UI | 机制 | 扩展 | 第二阶段 | Bad Case 与 Feedback | `mechanisms/eval-and-feedback-ui.md` | 产品 workbench | 待编写 |
| Flutter AI Native 客户端 | 概念 | 扩展 | 第二阶段 | Web 产品主链 | 待按需创建 | 无当前产品实现 | 待编写 |

## 工程基础

工程能力不是“可有可无的支撑课”。必备基础已经具备时可以直接通过检查；不足时必须补齐，避免把基础设施问题误判成模型、检索或 Agent 问题。

| 知识 | 类型 | 定位 | 进入阶段 | 理解前提 | 文档入口 | 代码入口 | 正文状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Python、HTTP、JSON、异步与配置 | 基础 | 必备基础 | 跨阶段 | `source/python_base` | 按必备检查回查 `source/python_base/` | 根项目 | 已落地 |
| PostgreSQL 关系模型、SQL 与本地运行 | 概念 | 必备基础 | 第一阶段 | Python、HTTP、JSON 与配置 | [阅读正文](concepts/postgresql-for-ai-applications.md) | 产品 infra、第 11 节操作文档 | 已落地 |
| FastAPI、Review API 与错误契约 | 机制 | 主线 | 第一阶段 | HTTP、JSON、Structured Output | `mechanisms/fastapi-and-api.md` | 产品 app | 待编写 |
| SSE 与流式 HTTP | 机制 | 主线 | 第二阶段 | HTTP、Agent Loop | Streaming 相关机制篇 | 产品 app / workbench | 待编写 |
| 日志、Metrics 与工程观测 | 机制 | 主线 | 第二阶段 | Trace、结构化事件 | `mechanisms/logging-and-metrics.md` | `app_log` + 产品 app | 待编写 |
| Redis、后台任务与入库状态 | 机制 | 扩展 | 第一阶段 | 知识生产、状态与恢复 | `mechanisms/background-jobs.md` | 产品 infra | 待编写 |
| Docker Compose 本地部署 | 机制 | 扩展 | 第二阶段 | 产品入口 | `mechanisms/docker-compose.md` | 产品 infra | 待编写 |
| 文件、对象存储与数据生命周期 | 机制 | 扩展 | 第一阶段 | 知识生产、知识治理 | `mechanisms/file-storage.md` | 产品 infra | 待编写 |
| Kubernetes、灰度、多租户与权限中台 | 概念 | 未来认知 | 未来认知 | 部署、观测、权限 | 无当前正文 | 无当前实现 | 未来认知 |

## 维护边界

- 新增知识前先判断能否合并到现有知识。
- 知识名称必须让学习者直接理解，不使用内部编号或编号范围。
- 标准阅读顺序和第 1–65 节编号只维护在 `course/learning-path.md`。
- 知识地图只维护能力范围、前置、阶段、定位、正文和代码入口。
- 项目业务任务、设计选择和验收只维护在 `course/project/`。
- 框架映射优先并入对应机制篇，不独立形成第四类文档。
- 未来认知不创建占位正文、空 package、空 demo 或空 app。
