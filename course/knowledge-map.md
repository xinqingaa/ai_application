# AI 应用知识地图

本文是课程能力范围、前置关系和学习入口的知识书架，不安排阅读顺序，也不维护课程序号。现在读什么只看[标准学习路径](learning-path.md)。

定位：**主线**必须理解、实验或作出设计判断；**必备基础**可以通过检查；**扩展**不阻塞阶段验收；**未来认知**只保留视野。主线学习不自动等于产品默认接入，产品要求以根 [SPEC](../SPEC.md) 为准。

## 阶段主链

```text
第一阶段
模型契约 → 知识生产 → 检索 → Context → 可信生成 → API/UI → 最小比较

第二阶段
Agent Harness → Tool Runtime → Agentic RAG → MCP/Tools/Skills
→ 状态与事件 → Deep Research → Multi-Agent/A2A
→ 必要 Workflow → Trace/Eval/Feedback
```

## LLM 与模型交互

| 知识 | 定位 | 阶段 | 前置 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- | --- |
| LLM 应用边界 | 主线 | 第一阶段 | 无 | [概念](concepts/llm-in-ai-applications.md) | `llm_invoke_lab` |
| Prompt、Schema 与 Context 契约 | 主线 | 第一阶段 | LLM 边界 | [概念](concepts/model-input-output-contracts.md) | `llm_core` |
| 调用生命周期与 Provider | 主线 | 第一阶段 | 模型契约 | [机制](mechanisms/model-api-and-provider.md) · [实验](labs/model-api-and-provider.md) | `llm_core/client`、`providers` |
| Prompt Engineering | 主线 | 第一阶段 | 模型契约 | [机制](mechanisms/prompt-engineering.md) · [实验](labs/prompt-engineering.md) | `llm_core/prompts` |
| Structured Output 与应用校验 | 主线 | 第一阶段 | Schema | [机制](mechanisms/structured-output.md) · [实验](labs/structured-output.md) | `llm_core/structured`、`schemas` |
| Reliability 与错误分类 | 主线 | 第一阶段 | 调用生命周期 | [机制](mechanisms/reliability-and-errors.md) · [实验](labs/reliability-and-errors.md) | `llm_core/reliability` |
| Calling Harness、Case 与 Record | 主线 | 第一阶段 | 可靠调用 | [机制](mechanisms/calling-harness-and-regression.md) | `llm_core/harness` |
| Token、成本、延迟与缓存 | 主线 | 第一阶段 | Calling Harness | [机制](mechanisms/cost-latency-and-caching.md) | `llm_core/costing`、`cache` |

## RAG 与知识生产

| 知识 | 定位 | 阶段 | 前置 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- | --- |
| RAG、搜索、数据库与 Agentic RAG 边界 | 主线 | 第一阶段 | LLM 边界 | [概念](concepts/rag-and-external-knowledge.md) | 选型边界 |
| 内容识别、解析路由与来源保留 | 主线 | 第一阶段 | RAG 边界 | [机制](mechanisms/document-loading-and-cleaning.md) · [实验](labs/document-loading-and-cleaning.md) | `rag_core/ingestion` |
| Chunking、父子块与 Metadata | 主线 | 第一阶段 | 文档解析 | [机制](mechanisms/chunking-and-metadata.md) · [实验](labs/chunking-and-metadata.md) | `rag_core/chunking` |
| Embedding 与相似度 | 主线 | 第一阶段 | Chunk | [机制](mechanisms/embedding-and-similarity.md) · [实验](labs/embedding-and-similarity.md) | `rag_core/embedding` |
| Lexical Retrieval 与 PostgreSQL FTS | 主线 | 第一阶段 | Chunk、PostgreSQL | [机制](mechanisms/lexical-retrieval.md) · [实验](labs/lexical-retrieval.md) | `rag_core/lexical`、`retrieval/postgres_fts.py` |
| pgvector、Dense Retrieval 与 ANN | 主线 | 第一阶段 | Embedding、PostgreSQL | [机制](mechanisms/vector-store-and-pgvector.md) · [实验](labs/vector-store-and-pgvector.md) | `rag_core/vector_store`、`retrieval/postgres_dense.py` |
| 多路召回与 RRF | 主线 | 第一阶段 | Lexical、Dense | [机制](mechanisms/multi-retrieval-and-rrf.md) · [实验](labs/multi-retrieval-and-rrf.md) | `rag_core/retrieval/fusion.py` |
| Top-k、阈值、Filter 与诊断 | 主线 | 第一阶段 | RRF | [机制](mechanisms/retriever-contract.md) · [实验](labs/retriever-contract.md) | `rag_core/retrieval/hybrid.py` |
| Context 装配、预算与 Compression | 主线 | 第一阶段 | Retriever Contract | [机制](mechanisms/context-engineering.md) · [实验](labs/context-engineering.md) | `rag_core/context`、`llm_core/context` |
| 可信生成与 Citation Candidate | 主线 | 第一阶段 | Context、Structured Output | [机制](mechanisms/trusted-generation.md) · [实验](labs/trusted-generation.md) | `rag_core/generation` |
| Citation 支持性 | 主线 | 第一阶段 | 可信生成 | `mechanisms/citation-support.md` | 后续 `rag_core/evidence` |
| 证据充分性、Refusal 与补充问题 | 主线 | 第一阶段 | Citation 支持性 | `mechanisms/evidence-sufficiency.md` | 后续 `rag_core/evidence` |
| Reranker 与准入证据 | 扩展 | 第一阶段 | RRF、Golden Set | `mechanisms/reranking.md` | 条件接入 `rag_core/retrieval` |
| 文档更新、删除与 Citation 失效 | 扩展 | 第一阶段 | 来源、Chunk、Citation | `mechanisms/knowledge-governance.md` | 后续 `rag_core/governance` |
| OCR/VLM 与复杂文档 | 扩展 | 第一阶段 | 文档解析 | `mechanisms/ocr-vlm-normalization.md` | 对照实验 |
| RAPTOR、GraphRAG 与多跳检索 | 扩展 | 第一阶段 | Chunk、RRF | `concepts/advanced-rag-indexes.md` | 无默认产品实现 |

## Agent Harness 与 Tool Runtime

| 知识 | 定位 | 阶段 | 前置 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- | --- |
| 固定程序、Workflow、Agent、Multi-Agent 边界 | 主线 | 第二阶段 | 固定 RAG | `concepts/agent-and-workflow-boundaries.md` | 选型边界 |
| Agent Harness 与控制面 | 主线 | 第二阶段 | 可靠调用 | `mechanisms/agent-harness.md` | 后续 `agent_core/runtime` |
| Function Calling 与 Tool Schema | 主线 | 第二阶段 | Structured Output | `mechanisms/tool-schema.md` | 后续 `agent_core/tools` |
| Tool 执行生命周期、结果与结构化错误 | 主线 | 第二阶段 | Tool Schema | `mechanisms/tool-runtime.md` | 后续 `agent_core/tools` |
| Retriever as Tool | 主线 | 第二阶段 | Retriever Contract、Tool Runtime | `mechanisms/retriever-as-tool.md` | 后续 `agent_core/tools` |
| Query Rewrite | 主线 | 第二阶段 | Retriever Tool | `mechanisms/query-rewrite.md` | 后续 `agent_core/query` |
| Source Routing 与补检索 | 主线 | 第二阶段 | Query Rewrite | `mechanisms/source-routing.md` | 后续 `agent_core/query` |
| Agent Loop、预算与停止 | 主线 | 第二阶段 | Tool Runtime | `mechanisms/agent-loop.md` | 后续 `agent_core/runtime` |
| 只读 Tool 权限、超时、取消与审计 | 主线 | 第二阶段 | Tool Runtime | `mechanisms/tool-governance.md` | 后续 `agent_core/tools` |
| Prompt Injection 与应用控制边界 | 主线 | 第二阶段 | Tool 治理 | `mechanisms/guardrails-and-safety.md` | 后续 `agent_core/safety` |

## MCP、通用工具与 Agent Skills

| 知识 | 定位 | 阶段 | 前置 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- | --- |
| MCP 解决的问题与协议边界 | 主线 | 第二阶段 | Tool Runtime | `concepts/mcp-and-tool-connectivity.md` | MCP 适配层 |
| MCP Host、Client、Server 职责 | 主线 | 第二阶段 | MCP 边界 | 同上 | MCP 适配层 |
| Tool、Resource 与内部能力映射 | 主线 | 第二阶段 | MCP 角色 | `mechanisms/mcp-lifecycle.md` | 后续 `agent_core/mcp` |
| 初始化、能力发现、调用、结果、错误与取消 | 主线 | 第二阶段 | MCP 角色 | `mechanisms/mcp-lifecycle.md` + 配套实验 | 后续 `agent_core/mcp` |
| MCP 信任、权限与 Tool Runtime 边界 | 主线 | 第二阶段 | Tool 治理 | 并入 MCP 机制与实验 | 产品权限策略 |
| Browser 与 Search Tool | 主线 | 第二阶段 | Tool Runtime、Citation | `mechanisms/browser-and-search-tools.md` | Agent Tool 实验 |
| File Tool 读取、写入与来源 | 主线 | 第二阶段 | Tool Runtime | `mechanisms/file-tool.md` | 受控文件工具 |
| Code Tool、沙箱与副作用 | 主线 | 第二阶段 | Tool 治理 | `mechanisms/code-tool.md` | 受控执行实验 |
| Skill 与 Prompt、Tool、MCP 的边界 | 主线 | 第二阶段 | Tool Runtime、MCP | `concepts/agent-skills.md` | 产品 Skill Registry |
| Skill 说明、资源、脚本与按需加载 | 主线 | 第二阶段 | Skill 边界 | `mechanisms/agent-skill-loading.md` | 后续 `agent_core/skills` |
| Skill 作用域、Context Budget、版本与安全 | 主线 | 第二阶段 | Skill 加载 | 并入 Skill 机制与实验 | 后续 `agent_core/skills` |
| 多模态 Agent Tool | 扩展 | 第二阶段 | Browser、File Tool | 按需概念篇 | 无默认产品实现 |

根 `skills/` 是 Codex 维护仓库使用的 Skill 示例，不是产品 Agent Skills 的运行目录。

## State、Conversation 与事件

| 知识 | 定位 | 阶段 | 前置 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- | --- |
| Run State、Conversation、Memory 与业务知识边界 | 主线 | 第二阶段 | Agent Harness | `concepts/memory-and-knowledge-boundaries.md` | 后续 `agent_core/state` |
| 短期记忆、摘要与预算 | 主线 | 第二阶段 | Context Engineering | `mechanisms/short-term-memory.md` | 后续 `agent_core/memory` |
| 长期偏好记忆与治理 | 扩展 | 第二阶段 | 记忆边界 | `mechanisms/long-term-memory.md` | 条件接入 |
| Token Stream 与 Event Stream | 主线 | 第二阶段 | Agent Loop | `mechanisms/token-and-event-stream.md` | `llm_core/streaming` |
| SSE 传输与事件协议 | 主线 | 第二阶段 | Event Stream、FastAPI | `mechanisms/sse-event-protocol.md` | 产品 API |
| 顺序、取消、重连与重复消费 | 主线 | 第二阶段 | SSE | `mechanisms/streaming-state.md` | 产品工作台 |
| Agent Response State 与运行界面 | 主线 | 第二阶段 | SSE、Agent Loop | `mechanisms/agent-runtime-ui.md` | 产品工作台 |

## Deep Research

| 知识 | 定位 | 阶段 | 前置 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- | --- |
| Planning、任务拆解与进度检查 | 主线 | 第二阶段 | Agent Loop | `mechanisms/planning.md` | 后续 `agent_core/research` |
| 迭代搜索与证据积累 | 主线 | 第二阶段 | Browser/Search | `mechanisms/research-loop.md` | 后续 `agent_core/research` |
| 来源判断、交叉验证与冲突证据 | 主线 | 第二阶段 | Citation | `mechanisms/research-evidence.md` | 后续 `agent_core/research` |
| 带来源综合与停止条件 | 主线 | 第二阶段 | 研究证据 | `mechanisms/research-synthesis.md` | 后续 `agent_core/research` |
| Research 来源、覆盖与停止评估 | 主线 | 第二阶段 | 完整研究链 | 配套实验与项目篇 | 后续 `eval_core/research` |

## Multi-Agent 与 A2A

| 知识 | 定位 | 阶段 | 前置 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- | --- |
| Multi-Agent 拆分判断 | 主线 | 第二阶段 | 单 Agent 基线 | `concepts/multi-agent-collaboration.md` | 选型边界 |
| 角色、上下文、工具与输出契约 | 主线 | 第二阶段 | 拆分判断 | `mechanisms/multi-agent-contracts.md` | 后续 `agent_core/multi_agent` |
| Supervisor、Worker 与 Delegation | 主线 | 第二阶段 | Agent 契约 | `mechanisms/supervisor-worker.md` | 同上 |
| 共享状态、私有上下文与证据 | 主线 | 第二阶段 | Run State | `mechanisms/multi-agent-state.md` | 同上 |
| 并行、依赖、取消与失败隔离 | 主线 | 第二阶段 | Delegation | `mechanisms/multi-agent-execution.md` | 同上 |
| 结果合并、证据归属与冲突裁决 | 主线 | 第二阶段 | 共享状态 | `mechanisms/result-merge-and-conflict.md` | 同上 |
| A2A 角色、任务与协议边界 | 主线 | 第二阶段 | Multi-Agent 契约 | `concepts/a2a-boundaries.md` | A2A 对照实验 |
| A2A 任务生命周期、结果、错误与取消 | 主线 | 第二阶段 | A2A 边界 | `mechanisms/a2a-lifecycle.md` | A2A 对照实验 |
| Multi-Agent 运行观测与界面 | 主线 | 第二阶段 | 并行与冲突 | `mechanisms/multi-agent-ux.md` | 产品工作台 |

## 必要 Workflow

| 知识 | 定位 | 阶段 | 前置 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- | --- |
| State、Node 与状态转换 | 主线 | 第二阶段 | Agent State | `mechanisms/workflow-state.md` | 后续 `agent_core/workflow` |
| Checkpoint、Interrupt 与 Resume | 主线 | 第二阶段 | Workflow State | `mechanisms/checkpoint-and-resume.md` | 同上 |
| Human-in-the-loop | 主线 | 第二阶段 | Interrupt | `mechanisms/human-in-the-loop.md` | 同上 |
| 重试、副作用与幂等 | 主线 | 第二阶段 | Tool 治理 | `mechanisms/retry-and-idempotency.md` | 同上 |
| Workflow as Tool、子 Agent 与恢复 | 主线 | 第二阶段 | Agent、Workflow | `mechanisms/workflow-as-tool.md` | 同上 |
| 通用低代码画布 | 未来认知 | 未来 | 完整 Workflow Runtime | 无当前正文 | 无当前实现 |

## Evaluation、Observability 与 AI Native

| 知识 | 定位 | 阶段 | 前置 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- | --- |
| Review API、错误与请求状态 | 主线 | 第一阶段 | 固定 RAG | 待编写机制与实验 | 产品 app |
| 证据、Refusal 与补充信息界面 | 主线 | 第一阶段 | Citation、Refusal | 待编写机制与实验 | 产品工作台 |
| Evaluation Dataset 与 Golden Set | 主线 | 第一阶段 | 固定产品目标 | `mechanisms/dataset-and-golden-set.md` | 产品 eval |
| 固定 RAG 四路对照 | 主线 | 第一阶段 | Golden Set | 第一阶段项目篇 | 产品 eval |
| Agent Tool、轨迹、停止与记忆评估 | 主线 | 第二阶段 | Agent Loop | `mechanisms/agent-evaluation.md` | 后续 `eval_core/agent` |
| Deep Research 评估 | 主线 | 第二阶段 | Research | Research 检查点 | 后续 `eval_core/research` |
| Multi-Agent 协作收益评估 | 主线 | 第二阶段 | Multi-Agent | Multi-Agent 检查点 | 后续 `eval_core/multi_agent` |
| 结构化日志、Metrics 与事件关联 | 主线 | 第二阶段 | 结构化事件 | `mechanisms/logging-and-metrics.md` | `app_log`、产品 app |
| Trace、Span 与 Run | 主线 | 第二阶段 | Agent Harness | `mechanisms/trace-and-observability.md` | 后续 `eval_core` |
| Versioning、Experiment 与 Regression | 主线 | 第二阶段 | Trace、Golden Set | `mechanisms/versioning-and-regression.md` | 后续 `eval_core` |
| LLM-as-Judge 与 Human Eval | 主线 | 第二阶段 | Evaluation Dataset | `mechanisms/llm-as-judge.md` | 后续 `eval_core` |
| Bad Case 与 Feedback Loop | 主线 | 第二阶段 | Trace、Eval | `mechanisms/feedback-loop.md` | 产品 eval |
| 完整评估平台与质量工作台 | 扩展 | 第二阶段 | 完整质量工程 | 按真实需要进入项目篇 | 无默认实现 |

## 工程基础

| 知识 | 定位 | 阶段 | 学习入口 | 实现入口 |
| --- | --- | --- | --- | --- |
| Python、HTTP、JSON、异步与配置 | 必备基础 | 跨阶段 | `source/python_base/` | 根项目 |
| PostgreSQL、SQL 与本地运行 | 必备基础 | 第一阶段 | [概念](concepts/postgresql-for-ai-applications.md) · [实验](labs/lexical-retrieval.md) | 产品 infra |
| FastAPI 与 SSE | 主线 | 跨阶段 | 对应机制与实验篇 | 产品 app |
| Redis、后台任务与入库状态 | 扩展 | 第一阶段 | 按需机制篇 | 产品 infra |
| Docker Compose | 扩展 | 第二阶段 | 按需机制篇 | 产品 infra |
| Kubernetes、多租户与权限中台 | 未来认知 | 未来 | 无当前正文 | 无当前实现 |

## 维护边界

- 新知识先判断能否合并到现有问题。
- 知识地图不写课程序号、阅读状态或实时待办。
- 学习入口可以由多篇文档共同承担。
- 产品要求、项目学习任务和真实实现分别回到 SPEC、项目篇和 `source/`。
- 未来认知不创建占位正文、空 package、空 demo 或空 app。
