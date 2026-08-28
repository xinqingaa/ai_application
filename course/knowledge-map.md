# 需求评审助手知识地图

本文维护课程的完整知识范围、认知前置、核心边界、学习入口和产品关系。它不安排阅读顺序，也不维护课程序号；唯一阅读顺序见[标准学习路径](learning-path.md)。

## 怎样使用知识地图

- **必备基础**：主线默认依赖；不足时先补，不占课程序号。
- **主线**：课程必须掌握，但不自动表示产品默认开放全部能力。
- **扩展**：理解边界，只有真实问题与收益证据成立时深入或接入。
- **未来认知**：知道它解决什么，当前不写占位正文和实现。

产品关系使用“产品必接、条件接入、受控实验、扩展或不实现”。最终产品要求仍以根 [SPEC.md](../SPEC.md) 为真源；本列只说明知识怎样落到当前需求评审助手。

## LLM 应用基础

本域回答模型怎样进入普通应用，并把概率性生成收敛为可调用、可校验、可诊断和可比较的边界。它不讨论训练模型或搭建通用模型平台。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| LLM 应用边界 | 主线 | 第一阶段 | 区分确定性程序、模型生成、RAG、Agent 与 Workflow，判断哪些责任不能交给模型 | 无 | [概念](concepts/llm-in-ai-applications.md) | 产品必接；指导整体选型 |
| Prompt、Schema 与 Context 契约 | 主线 | 第一阶段 | 把任务、证据和输出形状分开，避免把 Prompt 当作应用全部契约 | LLM 边界 | [概念](concepts/model-input-output-contracts.md) | 产品必接；`llm_core` 与产品 Schema |
| 调用生命周期与 Provider | 主线 | 第一阶段 | 统一配置、请求、响应、使用量和供应商错误，业务不绑定具体 SDK | HTTP、JSON、配置 | [机制](mechanisms/model-api-and-provider.md) · [实验](labs/model-api-and-provider.md) | 产品必接；`llm_core` |
| Prompt Engineering | 主线 | 第一阶段 | 将 Prompt 变成版本化任务协议，能固定输入并比较单一变化 | 调用边界 | [机制](mechanisms/prompt-engineering.md) · [实验](labs/prompt-engineering.md) | 产品必接；`llm_core/prompts` |
| Structured Output 与应用校验 | 主线 | 第一阶段 | 区分模型格式约束、解析、Schema 与业务校验，失败不能静默修成成功 | Prompt、JSON Schema | [机制](mechanisms/structured-output.md) · [实验](labs/structured-output.md) | 产品必接；`llm_core/structured` 与产品 Schema |
| Reliability 与错误分类 | 主线 | 第一阶段 | 按错误性质决定重试、失败或显式降级，不让可靠性外壳掩盖真实错误 | Provider、Structured Output | [机制](mechanisms/reliability-and-errors.md) · [实验](labs/reliability-and-errors.md) | 产品必接；`llm_core` |
| Calling Harness、Case 与 Record | 主线 | 第一阶段 | 用稳定 Case、运行配置和记录重复比较调用，不把一次输出当回归 | 模型调用、Prompt、Schema | [机制](mechanisms/calling-harness-and-regression.md) | 产品必接；`llm_core` 与产品 eval |
| Token、成本、延迟与缓存 | 主线 | 第一阶段 | 记录资源代价和缓存身份，区分真实节省与缓存污染实验 | Calling Harness | [机制](mechanisms/cost-latency-and-caching.md) | 产品必接；运行记录 |

## 固定 RAG 与可信证据

本域沿“资料 → Chunk → 检索 → Context → 生成 → Citation”追踪来源和控制。高级索引只有在固定基线暴露真实问题时才进入产品。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| RAG、搜索、数据库与 Agentic RAG 边界 | 主线 | 第一阶段 | 区分内部可引用知识、外部搜索、存储和动态检索决策，建立完整 RAG 总图 | LLM 契约 | [概念](concepts/rag-and-external-knowledge.md) | 产品必接；架构边界 |
| 内容识别、解析路由与来源保留 | 主线 | 第一阶段 | 根据真实内容选择解析路线，保留结构、版本、定位和明确失败 | 文件、字符串 | [机制](mechanisms/document-loading-and-cleaning.md) · [实验](labs/document-loading-and-cleaning.md) | 产品必接；`rag_core/ingestion` |
| Chunking、父子块与 Metadata | 主线 | 第一阶段 | 把文档结构转换为可检索单位，同时保持身份、来源和业务过滤信息 | 统一文档表示 | [机制](mechanisms/chunking-and-metadata.md) · [实验](labs/chunking-and-metadata.md) | 产品必接；`rag_core/chunking` |
| Embedding 与相似度 | 主线 | 第一阶段 | 在固定向量空间比较语义接近程度，明确度量方向和空间身份 | Chunk、真实 Provider | [机制](mechanisms/embedding-and-similarity.md) · [实验](labs/embedding-and-similarity.md) | 产品必接；`rag_core/embedding` |
| Lexical Retrieval 与 PostgreSQL FTS | 主线 | 第一阶段 | 用词项和倒排索引召回精确字段、接口名与版本，区分候选匹配和业务理解 | PostgreSQL、Chunk | [机制](mechanisms/lexical-retrieval.md) · [实验](labs/lexical-retrieval.md) | 产品必接；`rag_core/retrieval` 与 PostgreSQL |
| pgvector、Dense Retrieval 与 ANN | 主线 | 第一阶段 | 在数据库中保存同一空间的向量，建立 exact 基线后再理解 ANN 的收益与边界 | Embedding、PostgreSQL | [机制](mechanisms/vector-store-and-pgvector.md) · [实验](labs/vector-store-and-pgvector.md) | 产品必接；`rag_core/retrieval` 与 pgvector |
| 多路召回与 RRF | 主线 | 第一阶段 | 将不可直接相加的多路排名按统一候选身份融合，并保留路线贡献 | Lexical、Dense | [机制](mechanisms/multi-retrieval-and-rrf.md) · [实验](labs/multi-retrieval-and-rrf.md) | 产品必接；`rag_core/retrieval` |
| Top-k、阈值、Filter 与诊断 | 主线 | 第一阶段 | 固定过滤、每路候选、阈值、融合和截断顺序，解释候选在哪层消失 | 多路召回 | [机制](mechanisms/retriever-contract.md) · [实验](labs/retriever-contract.md) | 产品必接；Retriever Contract |
| Context 装配、预算与 Compression | 主线 | 第一阶段 | 从候选池选择模型本轮可见材料，保留来源并控制去重、分区和预算 | Retriever Contract | [机制](mechanisms/context-engineering.md) · [实验](labs/context-engineering.md) | 产品必接；`llm_core/context` 与 RAG 适配 |
| 可信生成与 Citation Candidate | 主线 | 第一阶段 | 限制模型只能声明本轮候选来源，并区分模型声明与应用验证 | Context、Structured Output | [机制](mechanisms/trusted-generation.md) · [实验](labs/trusted-generation.md) | 产品必接；`rag_core/generation` |
| Citation 支持性 | 主线 | 第一阶段 | 判断被引用内容是否真正支持对应结论，合法 ID 不能代替语义支持 | 可信生成 | 待编写机制与实验 | 产品必接；后续 `rag_core/evidence` |
| 证据充分性、Refusal 与补充问题 | 主线 | 第一阶段 | 在证据不足时拒绝强结论，并把缺口转成具体可回答问题 | Citation 支持性 | 待编写机制与实验 | 产品必接；后续 `rag_core/evidence` |
| Reranker 与准入证据 | 扩展 | 第一阶段 | 在固定召回基线后学习重排，以及什么收益证据才足以进入产品 | RRF、Golden Set | `mechanisms/reranking.md` | 条件接入；不作为固定基线默认能力 |
| 文档更新、删除与 Citation 失效 | 扩展 | 第一阶段 | 处理知识版本变化后索引、缓存和历史 Citation 的失效与重建 | 来源身份、Citation | `mechanisms/knowledge-governance.md` | 条件接入；知识治理 |
| OCR / VLM 与复杂文档 | 扩展 | 第一阶段 | 处理扫描、图片和复杂版面，明确识字、结构恢复和来源定位的不同证据 | 文档解析 | `mechanisms/ocr-vlm-normalization.md` | 条件接入；对照实验 |
| RAPTOR、GraphRAG、Neo4j 与多跳检索 | 扩展 | 第一阶段 | 理解层次摘要、图关系、图数据库和多跳检索分别解决什么；Neo4j 是可选图存储与查询基础设施，不等于已经获得高质量知识图谱，也不能绕过固定基线准入 | Chunk、RRF | `concepts/advanced-rag-indexes.md` | 当前不实现；出现可验证的关系检索需求后再做 Neo4j GraphRAG 对照 |

## Agent 框架、Harness 与 Tool Runtime

本域从成熟框架中的第一个真实 Agent 出发，建立动态决策所需的应用控制面。框架负责运行原语，模型提出行动，应用 Runtime 负责校验、权限、执行、状态、停止和错误；本地封装和外部连接都不能绕过这层边界。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| 固定程序、Workflow、Agent、Multi-Agent 边界 | 主线 | 第二阶段 | 根据步骤是否固定、是否需恢复和是否有独立责任选择最简单结构 | 固定 RAG | `concepts/agent-and-workflow-boundaries.md` | 产品必接的设计判断 |
| Provider API、Agent 框架、状态运行时、本地 package 与产品组装分层 | 主线 | 第二阶段 | 区分模型能力、框架原语、通用治理契约和领域行为，避免把一次 SDK 调用误认为完整产品，也避免重复造框架 | 固定 RAG、可靠调用 | 待编写概念与机制 | 产品必接的架构判断 |
| LangChain Agent、Tool 与 Middleware | 主线 | 第二阶段 | 先用框架提供的最小 Tool 形状快速形成真实 Loop，再从公开运行模型理解消息、工具调用、中间件和停止；完整 Tool 契约在运行后补齐 | 框架分层、Structured Output | 待编写机制与实验 | 产品必接；高层 Agent 与 Tool 组合默认框架 |
| 最小原生 Loop 对照 | 主线 | 第二阶段 | 用最少代码观察“模型决定—应用校验与执行—结果回填—停止”，只证明控制责任，不发展成第二套教学框架 | LangChain 首个 Agent | 配套受控实验 | 受控实验；不进入产品主路径 |
| Agent Harness 与控制面 | 主线 | 第二阶段 | 统一模型、上下文、工具、状态、权限、预算、停止、事件和观测；框架提供执行原语，本地应用保留策略与治理 | LangChain 首个 Agent、可靠调用 | `mechanisms/agent-harness.md` | 产品必接；由框架与后续 `agent_core/runtime` 共同承担 |
| Function Calling 与 Tool Schema | 主线 | 第二阶段 | 将模型的工具名和参数草案约束为可校验候选，不等同于执行授权 | Structured Output | `mechanisms/tool-schema.md` | 产品必接；后续 `agent_core/tools` |
| Tool 执行生命周期、超时、取消与结构化错误 | 主线 | 第二阶段 | 统一参数校验、开始执行、超时或取消、结果转换和错误回填，所有 Tool 共享同一执行边界 | Tool Schema | `mechanisms/tool-runtime.md` | 产品必接；后续 `agent_core/tools` |
| Tool 权限、确认与审计 | 主线 | 第二阶段 | 对读取、写入和外部行动应用最小权限与确认规则，并记录每次授权决定及其依据 | Tool Runtime | `mechanisms/tool-governance.md` | 产品必接；产品权限策略 |
| Tool 重放安全与幂等 | 主线 | 第二阶段 | 用执行记录和幂等键防止重试、恢复和重复请求再次产生副作用；无法消除影响时显式进入补偿边界 | Tool Runtime、Run State、Workflow State | `mechanisms/retry-and-idempotency.md` | 产品必接；写入与外部行动 |
| Prompt Injection 与应用控制边界 | 主线 | 第二阶段 | 把网页、文件和 Tool Result 视为不可信内容，禁止其改变系统规则和权限 | Tool 治理 | `mechanisms/guardrails-and-safety.md` | 产品必接；后续 `agent_core/safety` |
| Agent Loop、预算与停止 | 主线 | 第二阶段 | 在观察、决策、行动和结果间循环，并通过预算、无进展和停止原因终止；框架自带 Loop 不等于应用可以省略预算与停止契约 | LangChain Agent、Harness、Tool Runtime | `mechanisms/agent-loop.md` | 产品必接；框架执行、`agent_core/runtime` 约束 |
| Retriever as Tool | 主线 | 第二阶段 | 把固定 Retriever 契约接入 Tool Runtime，保留来源、空结果和路线失败 | Retriever Contract、Tool Runtime | `mechanisms/retriever-as-tool.md` | 产品必接；RAG 唯一实现复用 |
| Query Rewrite | 主线 | 第二阶段 | 改写检索表达但保留原问题、技术标识和可追踪关系，避免无信息循环 | Retriever Tool | `mechanisms/query-rewrite.md` | 产品必接；后续 `agent_core/query` |
| 检索路由、补检索与追问 | 主线 | 第二阶段 | 根据证据缺口在已有 Retriever、查询表达和用户补充间决定继续检索、换路、追问或停止；外部 Tool 接入后扩展来源集合而不改变决策语义 | Retriever Tool、Query Rewrite、证据充分性 | `mechanisms/source-routing.md` | 产品必接；产品路由策略 |
| `agent_core` 稳定契约与框架适配 | 主线 | 第二阶段 | 让产品领域组装依赖稳定的请求结果、Tool、Run State、停止、事件和 Trace 契约，当前由下层适配 LangChain，后续 LangGraph 进入同一边界；只在跨入口复用、统一治理或隔离框架变化产生真实价值后提取 | 首个框架 Agent、Tool Runtime、最小 Run State | 待编写机制与项目检查点 | 产品必接；通用边界进入 `source/packages/agent_core/`，评审 Prompt、领域 Schema、策略与角色进入 `source/apps/review_assistant/agent/` |
| 替代 Agent 框架与迁移边界 | 扩展 | 第二阶段 | 以 OpenAI Agents SDK、LlamaIndex Agent / Workflow 等做受控对照，检查本地契约是否过度绑定主框架；不并行建设第二套产品主线 | 首个 Agent 闭环、`agent_core` 边界 | 边界认知或对照实验 | 条件接入；由真实迁移或数据编排需求触发 |

## MCP 与外部工具

本域把外部需求、公共资料和本地工作区接入统一 Runtime。它围绕“售后接口 v2 与多端契约一致性评审”提供真实职责，而不是孤立工具演示。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| MCP 解决的问题与协议责任边界 | 主线 | 第二阶段 | 标准化外部能力的描述和交换，区分 MCP、Function Calling 与内部 Runtime；协议与 SDK 版本属于真实接入实验，不改变这一责任划分 | Tool Runtime | `concepts/mcp-and-tool-connectivity.md` | 产品必接；真实只读 MCP |
| MCP Host、Client、Server 职责 | 主线 | 第二阶段 | 明确谁承载应用、谁发起协议请求、谁提供能力；接入可用不代表能力可信或已经获得执行权限 | MCP 边界 | 同上 | 产品必接；MCP 适配层 |
| MCP 能力发现、能力模型与内部映射 | 主线 | 第二阶段 | 通过官方 SDK 或成熟适配器发现 Tool、Resource、Prompt 等能力，再映射为内部 Schema、权限、来源和结构化结果；不自行重写协议栈 | MCP 角色、Tool Runtime | `mechanisms/mcp-capability-mapping.md` | 产品必接；`agent_core/mcp` 适配与治理 |
| MCP 请求生命周期、传输、错误与取消 | 主线 | 第二阶段 | 按明确规范修订跟踪发现、请求、结果和取消，区分无状态协议请求、业务显式状态和旧版会话机制 | MCP 能力模型 | `mechanisms/mcp-lifecycle.md` 与配套实验 | 产品必接；官方 SDK / 框架适配器接入，`agent_core/mcp` 统一错误与治理 |
| MCP 信任、权限与 Runtime 边界 | 主线 | 第二阶段 | 外部能力不能自行获得本地权限，版本或 Schema 不兼容必须显式失败，所有调用仍受内部治理与审计 | MCP 请求生命周期、Tool 治理 | 并入 MCP 机制与实验 | 产品必接；产品权限策略 |
| Search Tool | 主线 | 第二阶段 | 生成查询并发现候选来源，搜索摘要只用于导航，不直接成为 Citation | Tool Runtime、Citation | `mechanisms/search-tool.md` | 产品必接；外部研究 |
| Browser Tool | 主线 | 第二阶段 | 打开、导航和抽取候选页面，保留 URL、标题、时间和内容定位并防注入 | Search、Tool 治理 | `mechanisms/browser-tool.md` | 产品必接；外部研究 |
| File Read 与来源身份 | 主线 | 第二阶段 | 在批准工作区选择性读取 PRD、OpenAPI、客户端模型和配置，防路径逃逸并保留哈希与定位 | Tool Runtime、来源模型 | `mechanisms/file-read-tool.md` | 产品必接；受控评审工作区 |
| File Write、暂存与确认 | 主线 | 第二阶段 | 只向运行级暂存区原子写入评审产物，处理覆盖、确认、重试和幂等 | File Read、Tool 副作用 | `mechanisms/file-write-tool.md` | 产品必接；原始输入默认只读 |
| Code Tool 准入与任务契约 | 主线 | 第二阶段 | 判断专用 Validator 是否足够，只有项目已有脚本或测试需要执行时才使用通用 Code | Tool Runtime、File Read | `concepts/code-tool-admission.md` | 产品必接于契约验证场景；不开放任意 Shell |
| Code Tool 沙箱与结构化执行 | 主线 | 第二阶段 | 隔离输入输出，限制命令、环境、网络和资源，并返回退出码、日志、超时和产物 | Code 准入、Tool 治理 | `mechanisms/code-tool-runtime.md` | 产品必接；受控执行实验与产品策略 |
| 多模态 Agent Tool | 扩展 | 第二阶段 | 让 Agent 观察图片或复杂视觉材料，同时保留来源、权限和模型能力边界 | Browser、File Tool | 按需概念篇 | 条件接入；当前不实现 |

## Agent Skills

本域在 Agent Loop、Context Budget 和 Tool 治理成立后，引入可发现、按需加载的任务说明与资源。Skill 与 MCP 没有认知依赖，也不会因包含脚本而获得额外权限。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| Skill 与 Prompt、Tool、MCP 的边界 | 主线 | 第二阶段 | Skill 封装任务说明、资源和流程知识，不等于 Prompt、可执行 Tool 或外部协议 | Agent Loop、Context Budget、Tool 治理 | `concepts/agent-skills.md` | 产品必接；领域 Skill Registry |
| Skill 格式、元数据与资源组织 | 主线 | 第二阶段 | 用最小元数据声明用途和适用任务，区分说明、参考资料、脚本、资产以及客户端特有扩展 | Skill 边界 | `mechanisms/agent-skill-format.md` | 产品必接；接口契约或客户端兼容 Skill |
| Skill 发现、激活与渐进加载 | 主线 | 第二阶段 | 先发现最小描述，任务匹配后才加载说明和必要资源，避免无关 Skill 占用 Context | Skill 格式、Context Budget | `mechanisms/agent-skill-loading.md` | 产品必接；后续 `agent_core/skills` |
| Skill 脚本执行、版本与安全 | 主线 | 第二阶段 | 脚本仍通过受治理执行边界，记录 Skill 与资源版本，处理兼容性、权限、确认和失败 | Skill 加载、Tool 治理 | 并入 Skill 机制与实验 | 产品必接；领域 Skill Runtime |

根 `skills/` 是 Codex 维护仓库使用的 Skill 示例，不是产品 Agent Skills 的运行目录。

## State、Conversation、Memory 与事件

本域把 Agent 中间过程转成应用可持久化、传输和展示的事实，并防止会话、记忆和业务知识互相冒充。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| 最小 Run State、停止原因与运行身份 | 主线 | 第二阶段 | 在首个 Agent 闭环中先记录当前步骤、预算、工具调用、停止原因和运行身份，为恢复、事件和 Trace 建立共同事实 | Agent Loop | 待编写机制与实验 | 产品必接；`agent_core/state` 的最小契约 |
| Run State、Conversation、Memory 与业务知识边界 | 主线 | 第二阶段 | 区分当前执行事实、消息、压缩记忆、偏好和可引用资料，不能把框架消息历史当成全部状态 | 最小 Run State、Context Engineering | `concepts/memory-and-knowledge-boundaries.md` | 产品必接；`agent_core/state` 与产品策略 |
| 短期记忆、摘要与预算 | 主线 | 第二阶段 | 控制长会话进入模型的内容，摘要必须可回查且不能冒充原始证据 | Context Engineering | `mechanisms/short-term-memory.md` | 产品必接；后续 `agent_core/memory` |
| 长期偏好记忆、确认与治理 | 主线 | 第二阶段 | 只保存用户明确确认的跨会话偏好，记录来源、作用域和版本，支持查看、更新、删除和关闭；不能冒充业务证据 | 短期记忆、记忆边界 | `mechanisms/long-term-memory.md` | 产品必接；后续 `agent_core/memory` 与产品偏好策略 |
| Token Stream 与 Event Stream | 主线 | 第二阶段 | 区分文本增量和 Tool、证据、状态、错误等结构化运行事实 | Agent Loop | `mechanisms/token-and-event-stream.md` | 产品必接；基础事件 |
| Agent Event 类型、身份与版本 | 主线 | 第二阶段 | 用运行身份、序号、类型和版本让生产者与消费者解释同一事件 | Event Stream | `mechanisms/agent-event-protocol.md` | 产品必接；事件 Schema |
| 顺序、取消、重复与迟到结果 | 主线 | 第二阶段 | 先定义生产和消费事件时的顺序、去重、取消与迟到结果语义，避免 UI 与 Run State 分叉；该一致性不依赖某种传输 | Event 协议、Tool Runtime、Run State | `mechanisms/event-consistency.md` | 产品必接；运行时与工作台 |
| SSE 传输与重连 | 主线 | 第二阶段 | 通过 SSE 传输既定事件，处理心跳、游标、断线和恢复，不把连接状态当业务状态 | Event 一致性、FastAPI | `mechanisms/sse-transport.md` | 产品必接；Review API |
| Agent Response State 与运行界面 | 主线 | 第二阶段 | 将事件还原为运行、等待、部分完成、取消、失败和完成等用户状态 | Event 一致性、Agent Loop | `mechanisms/agent-runtime-ui.md` | 产品必接；Web 工作台 |

## Deep Research

本域只处理普通 RAG 或一次网页回查不足的问题。研究过程必须有任务契约、可追踪证据和停止条件，不能把长时间搜索等同于深入研究。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| Research 启动条件与任务契约 | 主线 | 第二阶段 | 判断何时进入 Research，并冻结问题、输出、来源范围、预算和非目标 | Agent Loop、Search | `concepts/deep-research-boundaries.md` | 产品必接；外部兼容性评审 |
| Research Planning 与任务拆解 | 主线 | 第二阶段 | 将复杂问题拆成有依赖、预期证据和完成条件的子问题 | Research 契约 | `mechanisms/research-planning.md` | 产品必接；后续 `agent_core/research` |
| 迭代搜索、进度检查与重新规划 | 主线 | 第二阶段 | 根据新术语、覆盖缺口和无效方向调整查询与计划，避免无进展循环 | Planning、Search | `mechanisms/research-search-loop.md` | 产品必接；后续 `agent_core/research` |
| Evidence Ledger 与来源身份 | 主线 | 第二阶段 | 用稳定来源、定位、声明、时间和子问题关系积累可去重证据 | Browser、Citation | `mechanisms/evidence-ledger.md` | 产品必接；研究运行记录 |
| 来源质量、权威性、独立性与重复 | 主线 | 第二阶段 | 判断多个来源是否权威、及时和独立，不能用链接数量代替证据强度 | Evidence Ledger | `mechanisms/source-quality.md` | 产品必接；研究评估 |
| 交叉验证、冲突与不确定性 | 主线 | 第二阶段 | 比较不同版本和条件下的来源，保留不可自动裁决的冲突与缺口 | 来源质量 | `mechanisms/research-conflict.md` | 产品必接；研究与人工确认 |
| 带来源综合与 Citation | 主线 | 第二阶段 | 从证据账本生成结论，区分直接支持、合理推断和未解决问题 | 冲突处理 | `mechanisms/research-synthesis.md` | 产品必接；研究输出 |
| 覆盖、预算与停止条件 | 主线 | 第二阶段 | 根据子问题覆盖、新增证据、冲突和资源上限决定完成或停止 | 完整研究链 | `mechanisms/research-stopping.md` | 产品必接；Research Runtime |
| Deep Research 评估 | 主线 | 第二阶段 | 比较来源覆盖、冲突处理、Citation、停止、成本和延迟，不用篇幅评价研究质量 | 完整研究链 | 配套实验与项目篇 | 产品必接；产品 eval，通用后再进 `eval_core` |

## Multi-Agent

本域在单 Agent 基线之后学习责任拆分与协作状态。没有独立责任或可验证收益时，不进入 Multi-Agent；框架协作原语不能替代角色和结果契约。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| Multi-Agent 拆分判断 | 主线 | 第二阶段 | 判断任务是否存在独立责任、上下文、工具或并行收益，而非机械拆 Prompt | 单 Agent 基线 | `concepts/multi-agent-collaboration.md` | 产品必接的准入判断 |
| 角色、上下文、工具与输出契约 | 主线 | 第二阶段 | 为每个 Agent 定义责任与非责任、可见上下文、权限和交付 | 拆分判断 | `mechanisms/multi-agent-contracts.md` | 产品必接；后续 `agent_core/multi_agent` |
| Supervisor、Worker 与 Delegation | 主线 | 第二阶段 | 处理委派、拒绝、重派和回收，Supervisor 不替代领域责任 | Agent 契约 | `mechanisms/supervisor-worker.md` | 产品必接；后续 `agent_core/multi_agent` |
| 共享状态、私有上下文与证据 | 主线 | 第二阶段 | 在共享任务和批准证据的同时隔离私有上下文与权限 | Run State、Agent 契约 | `mechanisms/multi-agent-state.md` | 产品必接；协作状态 |
| 并行、依赖、取消与失败隔离 | 主线 | 第二阶段 | 调度独立和依赖任务，传播取消并防止局部失败被误判为无风险 | Delegation | `mechanisms/multi-agent-execution.md` | 产品必接；协作运行时 |
| 结果合并、证据归属与冲突裁决 | 主线 | 第二阶段 | 去重结果、保留责任人与证据，区分自动合并和必须暴露的分歧 | 共享状态 | `mechanisms/result-merge-and-conflict.md` | 产品必接；汇总策略 |
| Multi-Agent 运行观测与界面 | 主线 | 第二阶段 | 展示角色、进度、局部失败、证据和冲突，不暴露无意义内部对话 | 并行与冲突 | `mechanisms/multi-agent-ux.md` | 产品必接；产品工作台 |
| Multi-Agent 协作收益评估 | 主线 | 第二阶段 | 与单 Agent 比较质量、成本、延迟、证据一致性和失败定位 | 完整协作链 | 项目检查点 | 产品必接；没有收益时保留单 Agent |
| CrewAI、AutoGen 等角色化框架 | 未来认知 | 未来 | 理解角色化多 Agent 框架解决的编排问题；先完成单 Agent 基线、LangGraph 恢复和协作收益评估，不提前引入 | Multi-Agent 完整链路 | 无当前正文 | 当前不实现 |

## A2A 互操作

本域在本地 Agent 责任契约稳定后学习跨进程或跨系统互操作。A2A 是独立协议与 SDK 生态，不等于本地 Delegation、框架 Handoff 或 MCP 能力连接。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| A2A 角色与协议边界 | 主线 | 第二阶段 | 区分跨 Agent 任务协议、本地委派、MCP 能力连接和普通函数调用 | Multi-Agent 契约 | `concepts/a2a-boundaries.md` | 产品必接于互操作实验 |
| Agent Card 与能力发现 | 主线 | 第二阶段 | 描述远程 Agent 的身份、能力、端点和安全要求，并区分能力 Skill 描述与 Agent Skills 文件格式 | A2A 边界 | 并入 A2A 概念篇 | 产品必接于远程 Agent 发现 |
| A2A Message、Task、Part 与 Artifact | 主线 | 第二阶段 | 区分交互消息、可跟踪工作、内容片段和任务产物，避免把对话文本当成任务状态或最终交付 | Agent Card | `mechanisms/a2a-data-model.md` | 产品必接于互操作契约 |
| A2A Task 生命周期与更新 | 主线 | 第二阶段 | 交换提交、执行、等待输入或鉴权、完成、失败、拒绝、取消和流式更新等可互操作事实 | A2A 数据模型 | `mechanisms/a2a-lifecycle.md` | 产品必接于互操作实验 |
| A2A 协议绑定、安全、版本与互操作 | 主线 | 第二阶段 | 保持抽象语义独立于具体传输，固定规范与 SDK 版本验证鉴权、错误和两个实现的解释一致性 | A2A 生命周期 | 配套机制、实验与项目检查点 | 产品必接于真实互操作实验 |

## 必要 Workflow

本域只为显式状态、持久化、恢复、人工确认和副作用提供确定性骨架。主线使用 LangGraph 的公开状态运行模型，不自行实现图执行器；它不扩展为独立项目阶段或低代码平台。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| State、Node 与状态转换 | 主线 | 第二阶段 | 通过 LangGraph 将必须稳定执行的步骤表达为合法状态转换，区分确定性节点和模型决策；产品定义 State 语义，框架负责执行 | Agent State、LangChain Agent | `mechanisms/workflow-state.md` | 产品必接于需要恢复的路径；`agent_core/langgraph` 适配 |
| Checkpoint、持久化与 Resume | 主线 | 第二阶段 | 使用框架持久化能力保存可恢复状态，并处理代码、配置或输入变化后的恢复边界，不重复实现 Checkpointer | Workflow State | `mechanisms/checkpoint-and-resume.md` | 产品必接于长任务 |
| Interrupt 与 Human-in-the-loop | 主线 | 第二阶段 | 使用正式 Interrupt 将等待确认、批准、拒绝、修改和超时表达为可恢复状态 | Checkpoint | `mechanisms/human-in-the-loop.md` | 产品必接于写入和高风险行动 |
| 重放安全：重试、执行记录与幂等 | 主线 | 第二阶段 | 恢复和重放先依靠执行记录与幂等键避免重复外部行动；无法以幂等消除影响时，再显式定义补偿责任 | Tool Runtime、Run State、Workflow State | `mechanisms/retry-and-idempotency.md` | 产品必接；写入与外部行动 |
| 可恢复 Workflow 组合 | 主线 | 第二阶段 | 只把确实需要显式状态和恢复的 Research 或协作片段放入 Workflow | 完整 Workflow 原语 | 项目检查点 | 产品必接的最小组合，不建设画布 |
| Workflow as Tool 与子 Agent 编排 | 扩展 | 第二阶段 | 理解把固定流程暴露为 Tool 或嵌入 Agent 的组合边界，避免循环所有权不清 | Workflow、Agent | `mechanisms/workflow-as-tool.md` | 条件接入 |
| 通用低代码画布 | 未来认知 | 未来 | 理解可视化编排和平台治理解决的问题，当前项目不承担平台建设 | 完整 Workflow Runtime | 无当前正文 | 当前不实现 |

## Evaluation、Observability 与 AI Native 产品

质量证据贯穿每个检查点；本域在后部统一运行关联、版本、回归、自动与人工判断和反馈，不建设完整评估平台。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| Review API、错误与请求状态 | 主线 | 第一阶段 | 将固定 RAG 暴露为稳定 API，区分业务证据不足与系统执行失败 | 固定 RAG | 待编写机制与实验 | 产品必接；产品 app |
| 证据、Refusal 与补充信息界面 | 主线 | 第一阶段 | 让用户看到风险、证据、缺口、补充问题和真实状态 | Citation、Refusal | 待编写机制与实验 | 产品必接；Web 工作台 |
| Evaluation Dataset 与 Golden Set | 主线 | 第一阶段 | 固定问题、来源、风险覆盖和无答案行为，区分探索与验收 | 固定产品目标 | `mechanisms/dataset-and-golden-set.md` | 产品必接；产品 eval |
| 固定 RAG 四路对照 | 主线 | 第一阶段 | 在相同输入和生成条件下比较直接 LLM、Lexical、Dense 与 RRF | Golden Set | 第一阶段项目篇 | 产品必接；第一阶段基线 |
| Agent Tool、轨迹、停止与记忆评估 | 主线 | 第二阶段 | 检查 Tool 选择、参数、轨迹、停止、事件和摘要，不只评价最终文本 | Agent Loop、事件 | `mechanisms/agent-evaluation.md` | 产品必接；产品 eval |
| 结构化日志、Metrics 与事件关联 | 主线 | 第二阶段 | 关联输入、模型、检索、Tool、状态、成本和错误，区分业务输出与诊断 | 结构化事件 | `mechanisms/logging-and-metrics.md` | 产品必接；`app_log` 与产品 app |
| Trace、Span、Run 与本地运行记录 | 主线 | 第二阶段 | 表达父子调用、并行、耗时和错误传播，并将 LangSmith Trace 与本地 RunRecord、版本和业务结果关联；Trace 不替代质量判断 | Agent Harness、事件 | `mechanisms/trace-and-observability.md` | 本地记录产品必接、LangSmith 条件接入；通用契约稳定后再进 `eval_core` |
| Langfuse 与观测后端选择 | 扩展 | 第二阶段 | 比较 Langfuse 与 LangSmith 在部署、数据治理和跨框架集成上的边界，不让更换观测后端改变 RunRecord、事件和验收契约 | Trace 与验收契约 | 对照实验 | 条件接入；有自托管或跨框架需求时采用 |
| Versioning、Experiment 与 Regression | 主线 | 第二阶段 | 固定模型、Prompt、Schema、Retriever、Tool、Skill、Workflow 和数据版本 | Trace、Golden Set | `mechanisms/versioning-and-regression.md` | 产品必接；产品 eval |
| LLM-as-Judge 与 Human Eval | 主线 | 第二阶段 | 用人工校准的评分契约扩大评估，同时保留偏差、复核和不适用边界 | Evaluation Dataset | `mechanisms/llm-as-judge.md` | 条件采用；不能替代人工验收 |
| Bad Case 与 Feedback Loop | 主线 | 第二阶段 | 把线上失败和人工反馈转成可复现 Case、修复、回归和版本记录 | Trace、Regression | `mechanisms/feedback-loop.md` | 产品必接；产品 eval |
| 完整评估平台与质量工作台 | 扩展 | 第二阶段 | 理解跨团队数据、任务和权限治理，当前项目只保留最小产品闭环 | 完整质量工程 | 按真实需要进入项目篇 | 当前不实现 |

## 工程基础

这些能力是跨阶段运行真实 AI 应用的基础，不是保守的按需支持。已掌握时通过检查，不为基础语法机械增加课程序号。

| 知识 | 定位 | 阶段 | 核心问题与边界 | 前置 | 学习入口 | 产品关系与实现入口 |
| --- | --- | --- | --- | --- | --- | --- |
| Python、HTTP、JSON、异步与配置 | 必备基础 | 跨阶段 | 读写类型、异常、异步、网络请求、Schema、环境变量和配置，不展开通用语言课程 | 无 | `source/python_base/` | 产品必备；根项目 |
| PostgreSQL、SQL 与本地运行 | 必备基础 | 第一阶段 | 理解 Server、Database、Schema、Role、migration、SQL 与真实权限 | Python 基础 | [概念](concepts/postgresql-for-ai-applications.md) · [实验](labs/lexical-retrieval.md) | 产品必备；产品 infra |
| FastAPI 与 SSE | 主线 | 跨阶段 | 用稳定 HTTP API 和事件传输连接后端状态与 Web 工作台 | HTTP、异步 | 对应机制与实验篇 | 产品必接；产品 app |
| Redis、后台任务与入库状态 | 扩展 | 第一阶段 | 处理跨进程状态、长任务和队列，只有真实异步产品问题出现时接入 | Review API | 按需机制篇 | 条件接入；产品 infra |
| Docker Compose | 扩展 | 第二阶段 | 固定多服务本地环境，不能替代依赖契约、迁移和真实故障理解 | 产品服务 | 按需机制篇 | 条件接入；产品 infra |
| Kubernetes、多租户与权限中台 | 未来认知 | 未来 | 理解规模化部署与企业治理问题，当前课程不建设平台设施 | 完整产品运维 | 无当前正文 | 当前不实现 |

## 维护边界

- 新知识先判断能否合并到现有问题，再决定是否增加节点。
- 每个节点必须说明核心问题和边界；不能只留下标题、前置或文件路径。
- 知识地图不写课程序号、阅读状态或实时待办。
- 学习入口可以由多篇文档共同承担，知识项、正文和 demo 不强制一一对应。
- 产品要求、项目学习任务和真实实现分别回到 SPEC、项目篇和 `source/`。
- 未来认知不创建占位正文、空 package、空 demo、空 app 或空 fixture。
