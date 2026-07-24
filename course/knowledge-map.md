# AI 应用集中知识清单

这份文档是课程知识清单的唯一真源。

它回答：

- V0–V6 每个版本需要哪些知识。
- LLM、RAG、Agent、Workflow、Eval、AI Native 和工程基础分别需要学到什么程度。
- 每项知识的前置、项目位置、文档、代码和当前状态。

它不替代 [课程入口](README.md) 和项目篇。项目篇决定强学习顺序；本清单负责完整性和可检索性。

## 使用方式

### 看项目学习路线

从“按项目版本查看”进入，找到当前版本的主线知识 ID，再到对应能力域表查看前置、文档和代码。

### 看完整知识路线

从“按能力域查看”进入，检查某个能力域是否覆盖完整，以及哪些内容属于主线、支撑或未来认知。

### 状态含义

| 状态 | 含义 |
| --- | --- |
| 已落地 | 正文和主要代码已存在，仍可能按新文档职责修订 |
| 待重切 | 已有内容，但需迁移为概念篇或机制篇 |
| 待编写 | 已确定进入课程，正文尚未落地 |
| 项目落地 | 需要在对应 V0–V6 项目篇和产品中实现 |
| 未来认知 | 保留知识位置，不进入当前项目验收 |

## 按项目版本查看

### V0：固定 RAG 基线

主线知识：

- LLM：`K-LLM-01`、`K-LLM-02`、`K-LLM-03`、`K-LLM-04`、`K-LLM-05`、`K-LLM-07`、`K-LLM-08`
- RAG：`K-RAG-01`、`K-RAG-02`、`K-RAG-03`、`K-RAG-04`、`K-RAG-05`、`K-RAG-06`、`K-RAG-07`、`K-RAG-08`、`K-RAG-10`、`K-RAG-11`
- Eval：`K-EVAL-01`、`K-EVAL-02`、`K-EVAL-07`
- AI Native：`K-UX-01`、`K-UX-02`、`K-UX-03`、`K-UX-09`
- 工程：`K-ENG-01`、`K-ENG-02`、`K-ENG-03`

支撑知识：

- `K-LLM-06`、`K-LLM-09`、`K-LLM-11`
- `K-RAG-09`
- `K-ENG-04`

### V1：可信结构化评审

在 V0 基础上增加：

- `K-LLM-04`、`K-RAG-11`、`K-RAG-12`
- `K-EVAL-03`
- `K-UX-04`

### V2：质量闭环

在 V1 基础上增加：

- `K-RAG-13`、`K-RAG-15`
- `K-EVAL-01`–`K-EVAL-04`、`K-EVAL-07`–`K-EVAL-11`
- `K-UX-08`

### V3：单 Agent RAG

在 V2 基础上增加：

- `K-RAG-09`、`K-RAG-14`
- `K-AGENT-01`–`K-AGENT-07`
- `K-AGENT-10`、`K-AGENT-12`
- `K-EVAL-05`
- `K-UX-02`、`K-UX-03`

### V4：可控 Workflow

在 V3 基础上增加：

- `K-WF-01`–`K-WF-07`
- `K-AGENT-08`、`K-AGENT-12`
- `K-EVAL-06`、`K-EVAL-12`
- `K-UX-06`
- `K-ENG-05`

### V5：多 Agent 评审

在 V4 基础上增加：

- `K-MA-01`–`K-MA-07`
- `K-AGENT-09`
- `K-EVAL-05`、`K-EVAL-06`
- `K-UX-05`

### V6：产品化

在 V5 基础上增加：

- `K-UX-07`–`K-UX-11`
- `K-ENG-04`–`K-ENG-08`
- `K-EVAL-07`–`K-EVAL-12`

未来认知不作为 V0–V6 完成门槛：

- `K-RAG-16`
- `K-AGENT-11`、`K-AGENT-13`、`K-AGENT-14`
- `K-ENG-09`

## 按能力域查看

### LLM 与模型交互

| ID | 知识 | 类型 | 首次版本 | 前置 | 文档 | 代码 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-LLM-01 | LLM 应用问题空间与能力边界 | 概念 | V0 | 无 | `concepts/llm-in-ai-applications.md` | `source/demos/02_llm_basics/` | 已落地 |
| K-LLM-02 | 一次模型调用的生命周期 | 概念+机制 | V0 | K-LLM-01 | `mechanisms/llm/model-api-and-provider.md` | `llm_core/client` | 已落地 |
| K-LLM-03 | Provider、模型配置与供应商差异 | 机制 | V0 | K-LLM-02 | `mechanisms/llm/model-api-and-provider.md` | `llm_core/providers`、`config` | 已落地 |
| K-LLM-04 | Prompt、Schema、Context 的模型契约 | 概念 | V0 | K-LLM-01 | `concepts/model-input-output-contracts.md` | `llm_core/prompts`、`schemas`、`context` | 已落地 |
| K-LLM-05 | 面向应用的 Prompt Engineering | 机制 | V0 | K-LLM-04 | `mechanisms/llm/prompt-engineering.md` | `llm_core/prompts` | 已落地 |
| K-LLM-06 | Streaming 与 Conversation | 机制 | V0 支撑 | K-LLM-02 | `mechanisms/llm/streaming-and-conversation.md` | `llm_core/streaming`、`conversation` | 已落地 |
| K-LLM-07 | Structured Output 与本地校验 | 机制 | V0 | K-LLM-04 | `mechanisms/llm/structured-output.md` | `llm_core/structured`、`schemas` | 已落地 |
| K-LLM-08 | Context Engineering 与预算 | 机制 | V0 | K-LLM-04 | `mechanisms/llm/context-engineering.md` | `llm_core/context` | 已落地 |
| K-LLM-09 | 错误分类、重试、降级与可靠调用 | 机制 | V0 支撑 | K-LLM-02 | `mechanisms/llm/reliability-and-errors.md` | `llm_core/errors`、`reliability` | 已落地 |
| K-LLM-10 | 调用 Harness、回归与版本比较 | 机制 | V2 | K-LLM-05、07、09 | `mechanisms/llm/calling-harness-and-regression.md` | `llm_core/harness` | 已落地 |
| K-LLM-11 | Token、成本、延迟与缓存 | 机制 | V0 支撑 | K-LLM-02 | `mechanisms/llm/cost-latency-and-caching.md` | `llm_core/costing`、`cache` | 已落地 |
| K-LLM-12 | Function Calling API 形态 | 机制 | V3 | K-LLM-07 | 归入 Agent Tool 机制 | 后续 `agent_core` | 待编写 |

### RAG 与知识系统

| ID | 知识 | 类型 | 首次版本 | 前置 | 文档 | 代码 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-RAG-01 | RAG 问题空间与完整链路 | 概念 | V0 | K-LLM-01 | `concepts/rag-and-external-knowledge.md` | 后续 `rag_core` | 待编写 |
| K-RAG-02 | 固定 RAG、搜索、数据库与 Agent 的边界 | 概念 | V0 | K-RAG-01 | `concepts/rag-and-external-knowledge.md` | 后续 `rag_core` | 待编写 |
| K-RAG-03 | Document Loading、Cleaning 与结构保留 | 机制 | V0 | K-RAG-01 | `mechanisms/rag/document-loading-and-cleaning.md` | 后续 `rag_core/ingestion` | 待编写 |
| K-RAG-04 | Chunking、父子块与 Metadata | 机制 | V0 | K-RAG-03 | `mechanisms/rag/chunking-and-metadata.md` | 后续 `rag_core/chunking` | 待编写 |
| K-RAG-05 | Embedding 的表示与相似度 | 概念+机制 | V0 | K-RAG-01 | `mechanisms/rag/embedding-and-similarity.md` | 后续 `rag_core/embedding` | 待编写 |
| K-RAG-06 | Vector Store、索引与 pgvector | 机制 | V0 | K-RAG-05 | `mechanisms/rag/vector-store-and-pgvector.md` | 后续 `rag_core/vector_store` | 待编写 |
| K-RAG-07 | 关键词、向量、混合检索与 Top-k | 机制 | V0 | K-RAG-04、05 | `mechanisms/rag/retrieval-strategies.md` | 后续 `rag_core/retrieval` | 待编写 |
| K-RAG-08 | Retriever 契约、过滤、阈值与结果诊断 | 机制 | V0 | K-RAG-07 | `mechanisms/rag/retriever-contract.md` | 后续 `rag_core/retrieval` | 待编写 |
| K-RAG-09 | Query Rewrite 与 Source Routing | 机制 | V3 | K-RAG-08 | `mechanisms/rag/query-rewrite-and-routing.md` | 后续 `rag_core/query` | 待编写 |
| K-RAG-10 | Context Construction 与 Compression | 机制 | V0 | K-RAG-08、K-LLM-08 | `mechanisms/rag/context-construction.md` | `llm_core/context` + 后续 `rag_core` | 待编写 |
| K-RAG-11 | 可信生成、Sources、Citation 与 Refusal | 概念+机制 | V0/V1 | K-RAG-10、K-LLM-07 | `mechanisms/rag/trusted-generation.md` | 后续 `rag_core/generation` | 待编写 |
| K-RAG-12 | Citation 校验与证据充分性 | 机制 | V1 | K-RAG-11 | `mechanisms/rag/citation-and-evidence-validation.md` | 后续 `rag_core/evidence` | 待编写 |
| K-RAG-13 | RAG Evaluation | 机制+项目 | V2 | K-RAG-07、11 | `mechanisms/eval/rag-evaluation.md` | 后续 `eval_core` | 待编写 |
| K-RAG-14 | Retriever as Tool 与 Single Agent RAG | 机制 | V3 | K-RAG-09、K-AGENT-03 | `mechanisms/agent/single-agent-rag.md` | 后续 `agent_core` | 待编写 |
| K-RAG-15 | RAG Failure Analysis 与 Bad Case 回流 | 机制 | V2 | K-RAG-13 | `mechanisms/rag/failure-analysis.md` | 后续 `eval_core` | 待编写 |
| K-RAG-16 | RAPTOR、GraphRAG、复杂解析等高级知识生产 | 概念 | 未来 | K-RAG-04、07 | 待按需创建 | 无当前实现 | 未来认知 |
| K-RAG-17 | 文档版本、更新、删除一致性与权限过滤 | 机制 | V1/V2 支撑 | K-RAG-03、04 | `mechanisms/rag/knowledge-governance.md` | 后续 `rag_core/governance` | 待编写 |
| K-RAG-18 | RAG Memory、写入、检索与遗忘 | 概念+机制 | V3 支撑 | K-RAG-08 | `mechanisms/agent/memory-and-context.md` | 后续 `agent_core/memory` | 待编写 |

### Agent 与 Tool

| ID | 知识 | 类型 | 首次版本 | 前置 | 文档 | 代码 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-AGENT-01 | Chain、Workflow、Agent 与 Multi-Agent 边界 | 概念 | V3 | K-RAG-02 | `concepts/agent-and-workflow-boundaries.md` | 后续 `agent_core` | 待编写 |
| K-AGENT-02 | Function Calling 与 Tool Schema | 机制 | V3 | K-LLM-12 | `mechanisms/agent/tool-schema.md` | 后续 `agent_core/tools` | 待编写 |
| K-AGENT-03 | Tool Runtime 与结构化错误 | 机制 | V3 | K-AGENT-02 | `mechanisms/agent/tool-runtime.md` | 后续 `agent_core/tools` | 待编写 |
| K-AGENT-04 | 工具权限、确认、幂等与审计 | 机制 | V3/V4 | K-AGENT-03 | `mechanisms/agent/tool-governance.md` | 后续 `agent_core/tools` | 待编写 |
| K-AGENT-05 | Agent Loop 与停止条件 | 机制 | V3 | K-AGENT-03 | `mechanisms/agent/agent-loop.md` | 后续 `agent_core/runtime` | 待编写 |
| K-AGENT-06 | Planning、Task Decomposition 与 Reflection | 机制 | V3 支撑 | K-AGENT-05 | `mechanisms/agent/planning-and-reflection.md` | 后续 `agent_core/runtime` | 待编写 |
| K-AGENT-07 | LangChain Agent Patterns | 机制 | V3 | K-AGENT-05 | 并入对应 Agent 机制篇 | 后续 `agent_core` | 待编写 |
| K-AGENT-08 | Agentic RAG 深化 | 机制 | V4 支撑 | K-RAG-14、K-WF-01 | `mechanisms/agent/agentic-rag.md` | 后续 `agent_core` | 待编写 |
| K-AGENT-09 | Workflow as Tool 与子 Agent | 机制 | V5 | K-WF-05、K-MA-01 | `mechanisms/agent/workflow-as-tool.md` | 后续 `agent_core` | 待编写 |
| K-AGENT-10 | Agent Memory 与 Context | 机制 | V3 | K-RAG-18、K-AGENT-05 | `mechanisms/agent/memory-and-context.md` | 后续 `agent_core/memory` | 待编写 |
| K-AGENT-11 | MCP、A2A 与 Agent Skills | 概念 | 未来 | K-AGENT-03 | 待按需创建 | 无当前实现 | 未来认知 |
| K-AGENT-12 | Guardrails、Safety 与人工接管 | 机制 | V3/V4 | K-AGENT-04、05 | `mechanisms/agent/guardrails-and-safety.md` | 后续 `agent_core/safety` | 待编写 |
| K-AGENT-13 | Deep Research | 概念 | 未来 | K-WF-01、K-AGENT-06 | 待按需创建 | 无当前实现 | 未来认知 |
| K-AGENT-14 | 多模态 Agent、Browser、Code、File、Search 工具 | 概念 | 未来 | K-AGENT-03 | 待按需创建 | 无当前实现 | 未来认知 |

### Workflow

| ID | 知识 | 类型 | 首次版本 | 前置 | 文档 | 代码 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-WF-01 | Workflow State、Node 与 Edge | 机制 | V4 | K-AGENT-01 | `mechanisms/workflow/state-node-edge.md` | 后续 `agent_core/workflow` | 待编写 |
| K-WF-02 | Node 输入输出契约与状态合并 | 机制 | V4 | K-WF-01 | `mechanisms/workflow/state-contracts.md` | 后续 `agent_core/workflow` | 待编写 |
| K-WF-03 | 条件、循环与并行 | 机制 | V4 | K-WF-01 | `mechanisms/workflow/branch-loop-parallel.md` | 后续 `agent_core/workflow` | 待编写 |
| K-WF-04 | Checkpoint、Interrupt 与 Resume | 机制 | V4 | K-WF-02 | `mechanisms/workflow/checkpoint-and-resume.md` | 后续 `agent_core/workflow` | 待编写 |
| K-WF-05 | Human-in-the-loop | 机制 | V4 | K-WF-04 | `mechanisms/workflow/human-in-the-loop.md` | 后续 `agent_core/workflow` | 待编写 |
| K-WF-06 | 节点重试、副作用与幂等 | 机制 | V4 | K-WF-02、K-AGENT-04 | `mechanisms/workflow/retry-and-idempotency.md` | 后续 `agent_core/workflow` | 待编写 |
| K-WF-07 | LangGraph 框架映射与运行调试 | 机制 | V4 | K-WF-01–06 | 并入 Workflow 机制篇 | 后续 `agent_core/workflow` | 待编写 |

### Multi-Agent

| ID | 知识 | 类型 | 首次版本 | 前置 | 文档 | 代码 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-MA-01 | Multi-Agent 拆分判断 | 概念 | V5 | K-AGENT-01、K-WF-01 | `concepts/multi-agent-collaboration.md` | 后续 `agent_core/multi_agent` | 待编写 |
| K-MA-02 | 角色责任、上下文、工具和输出契约 | 机制 | V5 | K-MA-01 | `mechanisms/agent/multi-agent-contracts.md` | 后续 `agent_core/multi_agent` | 待编写 |
| K-MA-03 | Supervisor / Worker 与任务分配 | 机制 | V5 | K-MA-02 | `mechanisms/agent/supervisor-worker.md` | 后续 `agent_core/multi_agent` | 待编写 |
| K-MA-04 | 共享状态、私有上下文与证据 | 机制 | V5 | K-MA-02、K-WF-02 | `mechanisms/agent/multi-agent-state.md` | 后续 `agent_core/multi_agent` | 待编写 |
| K-MA-05 | 并行执行、依赖和失败隔离 | 机制 | V5 | K-MA-03、K-WF-03 | `mechanisms/agent/multi-agent-execution.md` | 后续 `agent_core/multi_agent` | 待编写 |
| K-MA-06 | 结果汇总、证据合并与冲突裁决 | 机制 | V5 | K-MA-04 | `mechanisms/agent/result-merge-and-conflict.md` | 后续 `agent_core/multi_agent` | 待编写 |
| K-MA-07 | 单 Agent 与多 Agent 基线比较 | 机制+项目 | V5 | K-MA-01–06 | 对应 V5 项目篇 | 后续 `eval_core` | 待编写 |

### Evaluation 与 Observability

| ID | 知识 | 类型 | 首次版本 | 前置 | 文档 | 代码 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-EVAL-01 | Evaluation Dataset 与 Golden Set | 机制 | V0/V2 | 项目业务契约 | `mechanisms/eval/dataset-and-golden-set.md` | 后续 `eval_core` | 待编写 |
| K-EVAL-02 | Retrieval 与 Generation Eval | 机制 | V0/V2 | K-RAG-07、11 | `mechanisms/eval/rag-evaluation.md` | 后续 `eval_core/rag` | 待编写 |
| K-EVAL-03 | Citation 与 Refusal Eval | 机制 | V1/V2 | K-RAG-11、12 | `mechanisms/eval/citation-and-refusal.md` | 后续 `eval_core/rag` | 待编写 |
| K-EVAL-04 | Bad Case Management | 机制 | V2 | K-EVAL-01–03 | `mechanisms/eval/bad-case-management.md` | 后续 `eval_core` | 待编写 |
| K-EVAL-05 | Agent Trajectory 与 Tool Eval | 机制 | V3/V5 | K-AGENT-03、05 | `mechanisms/eval/agent-and-tool-evaluation.md` | 后续 `eval_core/agent` | 待编写 |
| K-EVAL-06 | Workflow Eval 与 Human Review | 机制 | V4/V5 | K-WF-01、05 | `mechanisms/eval/workflow-evaluation.md` | 后续 `eval_core/workflow` | 待编写 |
| K-EVAL-07 | Trace、Span 与 Run 关联 | 机制 | V0 | K-LLM-02 | `mechanisms/eval/trace-and-observability.md` | `llm_core/harness` + 后续 `eval_core` | 待编写 |
| K-EVAL-08 | Versioning、Regression 与 Experiment | 机制 | V2 | K-EVAL-01、07 | `mechanisms/eval/versioning-and-regression.md` | 后续 `eval_core` | 待编写 |
| K-EVAL-09 | Cost、Latency 与运行指标 | 机制 | V2/V6 | K-LLM-11 | `mechanisms/eval/cost-latency-metrics.md` | `llm_core/costing` + 后续 `eval_core` | 待编写 |
| K-EVAL-10 | LLM-as-Judge 与 Human Eval | 机制 | V2 | K-EVAL-01 | `mechanisms/eval/llm-as-judge.md` | 后续 `eval_core` | 待编写 |
| K-EVAL-11 | Feedback Loop | 机制+项目 | V2 | K-EVAL-04 | `mechanisms/eval/feedback-loop.md` | 后续 `eval_core` | 待编写 |
| K-EVAL-12 | Engineering Contract Tests | 机制 | V0/V4 | 项目 Schema | `mechanisms/eval/engineering-contract-tests.md` | package / product tests | 待编写 |

### AI Native 体验

| ID | 知识 | 类型 | 首次版本 | 前置 | 文档 | 代码 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-UX-01 | AI Native 问题空间 | 概念 | V0 | K-LLM-01 | `concepts/ai-native-interface.md` | 产品 workbench | 待编写 |
| K-UX-02 | Streaming State Synchronization | 机制 | V0/V3 | K-LLM-06 | `mechanisms/ai-native/streaming-state.md` | 产品 workbench | 待编写 |
| K-UX-03 | AI Response State Machine | 机制 | V0/V3 | K-UX-02 | `mechanisms/ai-native/response-state-machine.md` | 产品 workbench | 待编写 |
| K-UX-04 | Schema Driven UI 与结构化评审报告 | 机制 | V1 | K-LLM-07 | `mechanisms/ai-native/schema-driven-review.md` | 产品 workbench | 待编写 |
| K-UX-05 | Multi-Agent UI / UX | 机制 | V5 | K-MA-02–06 | `mechanisms/ai-native/multi-agent-ux.md` | 产品 workbench | 待编写 |
| K-UX-06 | Workflow Runtime UI | 机制 | V4 | K-WF-01–05 | `mechanisms/ai-native/workflow-runtime-ui.md` | 产品 workbench | 待编写 |
| K-UX-07 | RAG Knowledge Workbench | 机制+项目 | V6 | K-RAG-03、17 | 对应 V6 项目篇 | 产品 workbench | 待编写 |
| K-UX-08 | Eval、Labeling 与 Feedback UI | 机制+项目 | V2/V6 | K-EVAL-04、11 | `mechanisms/ai-native/eval-and-feedback-ui.md` | 产品 workbench | 待编写 |
| K-UX-09 | FastAPI Service Layer 与 API Design | 机制 | V0 | Python / HTTP | `mechanisms/engineering/fastapi-and-api.md` | 产品 app | 待编写 |
| K-UX-10 | 工程观测与错误体验 | 机制 | V0/V6 | K-EVAL-07 | `mechanisms/ai-native/error-and-observability-ux.md` | 产品 app / workbench | 待编写 |
| K-UX-11 | Project AI Native Architecture | 项目 | V6 | 全部主线 | 对应 V6 项目篇 | `review_assistant/` | 待编写 |

### 工程基础

| ID | 知识 | 类型 | 首次版本 | 前置 | 文档 | 代码 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K-ENG-01 | Python、HTTP、JSON 与配置 | 支撑 | V0 | `python_base` | 按需机制篇 | 根项目 | 已落地 |
| K-ENG-02 | FastAPI 与 API 契约 | 机制 | V0 | K-ENG-01 | `mechanisms/engineering/fastapi-and-api.md` | 产品 app | 待编写 |
| K-ENG-03 | SSE 与事件协议 | 机制 | V0 | K-LLM-06、K-ENG-02 | `mechanisms/engineering/sse-event-protocol.md` | 现有 streaming app | 已落地/待重切 |
| K-ENG-04 | PostgreSQL / pgvector 数据模型 | 机制 | V0 支撑/V6 | SQL 基础、K-RAG-06 | `mechanisms/engineering/postgres-and-pgvector.md` | 产品 infra | 待编写 |
| K-ENG-05 | Redis、后台任务与入库状态 | 机制 | V4 | K-RAG-03、K-WF-04 | `mechanisms/engineering/background-jobs.md` | 产品 infra | 待编写 |
| K-ENG-06 | Docker Compose 本地部署 | 机制+项目 | V6 | 产品入口 | `mechanisms/engineering/docker-compose.md` | 产品 infra | 待编写 |
| K-ENG-07 | 日志、Metrics 与工程观测 | 机制 | V0/V6 | K-EVAL-07 | `mechanisms/engineering/logging-and-metrics.md` | 产品 app / infra | 待编写 |
| K-ENG-08 | 文件、对象存储与数据生命周期 | 机制 | V0/V6 | K-RAG-03 | `mechanisms/engineering/file-storage.md` | 产品 infra | 待编写 |
| K-ENG-09 | Kubernetes、灰度、多租户与权限中台 | 概念 | 未来 | K-ENG-06、07 | 无当前正文 | 无当前实现 | 未来认知 |

## 知识项维护规则

- 新增知识前先判断能否合并到现有知识项。
- 项目版本需要的知识必须出现在“按项目版本查看”中。
- 文档落地后更新文档路径和状态。
- 代码落地后更新唯一 package 或产品入口。
- 框架映射优先并入机制篇，不独立形成第四类文档。
- 未来认知不创建占位正文或代码。
- 删除旧 outline 前，逐项确认有效内容已进入本清单或对应正文。
