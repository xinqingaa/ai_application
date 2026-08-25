# 需求评审助手标准学习路径

这份文档是课程阅读顺序和课程序号的唯一真源。

目录名称、文件排列、知识地图分组和代码模块出现的先后，都不能替代这里规定的顺序。课程设计由项目目标反推知识；学习者按照认知前置正向学习：

```text
项目愿景与阶段契约
→ 概念
→ 机制与真实实验
→ 阶段项目检查点
→ 失败、修改与验收
```

课程只分为两个阶段，编号从第一阶段连续到第二阶段，不在阶段内部重置，也不建立另一套产品版本号：

```text
第一阶段：第 1–25 节
→ 第二阶段：第 26–65 节
```

## 怎样使用这条路径

- 按本页编号阅读，不按 `concepts/`、`mechanisms/` 或代码目录遍历。
- 每篇正文只说明知识前置和本文交付；读完后回到本页继续。
- 第二阶段从第 26 节继续，不重新从 1 开始。
- package 中已经存在某项能力，不代表当前步骤已经学习，也不代表产品已经启用。
- 每个阶段开始时可以先读取对应项目篇的业务场景、输入输出、Definition of Ready 和非目标；完成必要概念、机制和实验后，再回到同一项目篇完成检查点和阶段验收。
- 尚未有正文的步骤保留在正确位置，但不创建空文档、空 demo 或无效链接。

状态说明：

| 状态 | 含义 |
| --- | --- |
| 可学习 | 正文和必要实验已经存在，可以按路径进入 |
| 待编写 | 位置和目标已确定，正文与真实代码按学习需要落地 |
| 等待前置 | 正文已经存在，但必须先完成前面的知识或产品能力 |

## 必备基础检查

必备基础不是可选支撑，也不占用课程序号。已经具备时直接通过检查；不足时回查 `source/python_base/`、对应概念篇或产品 README，再进入主线。

开始第 1 节前，至少确认：

- 能在根目录使用 `uv run` 运行 Python。
- 能阅读函数、类、类型、异常和基础异步代码。
- 理解 HTTP 请求、响应、状态码、Header 与 JSON。
- 理解 Schema、序列化、环境变量和 `.env` 配置。
- 能区分普通响应、流式响应和应用事件。

开始第 11 节前，还要确认：

- 理解 PostgreSQL Server、Database、Schema、Table 和基础 SQL。
- 理解连接串、Role、migration 和索引解决什么问题。
- 能按第 11 节操作文档完成真实数据库准备。

这些能力在[知识地图](knowledge-map.md)中标记为“必备基础”，不是扩展内容。

## 怎样理解学习进展

学习进展同时发生在三个层次：

| 层次 | 学习者要完成什么 |
| --- | --- |
| 概念建立 | 能用自己的话解释对象、输入输出、相近概念和适用边界 |
| 机制掌握 | 能画出数据流，运行或解释实验，预测配置变化，并根据现象定位失败层 |
| 项目掌握 | 能把机制组合进产品，处理真实失败和需求变化，并用测试或评估完成阶段验收 |

质量证据随复杂度逐步进入，不单独阻塞 Agent 主线：

```text
固定 RAG：最小 Golden Set 与检索对照
→ 单 Agent：Tool、轨迹、停止和记忆评估
→ Multi-Agent：分工收益、成本、延迟和证据一致性对比
→ 第二阶段后部：Trace、Regression、Human Eval 与 Feedback 统一收束
```

## 第一阶段：RAG 应用基础

第一阶段要回答：

> 真实资料怎样成为可检索证据，固定 RAG 怎样形成可诊断、可引用、可拒答并能通过 API 和 Web 工作台交付的需求评审应用？

第一阶段不使用 Agent 动态决定下一步。它先把 Retriever、Context、Generator、Citation 和产品契约做稳定，使第二阶段可以把 Retriever 直接作为受治理 Tool 使用。

### 先取得第一阶段业务契约

开始第 1 节前，先阅读[第一阶段项目篇](project/stage-1-rag-application/rag-review-assistant.md)的“业务场景”“Definition of Ready”“输入与输出契约”和“明确不做”。此时只确认固定业务材料、问题集、输出、对照和非目标，不提前进入实现任务或验收结论。

完成第 1–24 节后，再回到同一项目篇完成第 25 节的综合实现和阶段验收。

### 模型进入应用

1. **[LLM 在 AI 应用中的位置与边界](concepts/llm-in-ai-applications.md)** · 可学习
   建立普通程序、LLM、RAG、Agent 和 Workflow 的职责边界。
2. **[模型输入输出契约：Prompt、Schema 与 Context](concepts/model-input-output-contracts.md)** · 可学习
   理解任务、证据和结果为什么必须由应用建立契约。
3. **[Model API、调用生命周期与 Provider 抽象](mechanisms/model-api-and-provider.md)** · 可学习
   运行真实模型，理解统一调用入口、供应商差异和错误边界。
4. **[面向应用的 Prompt Engineering](mechanisms/prompt-engineering.md)** · 可学习
   把临时提示词变成可命名、可版本化、可比较的任务协议。
5. **[Structured Output 与应用侧校验](mechanisms/structured-output.md)** · 可学习
   用生成约束、解析、Schema 和业务校验决定结果能否进入程序。
6. **[Reliability、错误分类与可见降级](mechanisms/reliability-and-errors.md)** · 可学习
   区分可重试、不可重试、结构化失败和显式降级。

完成这一段后，应能使用真实模型生成结构化风险结果，并解释失败发生在哪一层。此时证据仍来自固定输入，不要把 Context Builder 当成 Retriever。

### 建立固定 RAG 核心链

7. **[RAG 与外部知识的边界](concepts/rag-and-external-knowledge.md)** · 可学习
   画出固定 RAG 从文件到生成的总图，区分模型已有知识、搜索、数据库查询、固定 RAG 和 Agentic RAG。
8. **[文档内容识别、解析路由、结构还原与来源保留](mechanisms/document-loading-and-cleaning.md)** · 可学习
   将 TXT、Markdown、DOCX 与文本型 PDF 变成带来源位置的知识文档，但不产生 Chunk。
9. **[Chunking、父子块与 Metadata](mechanisms/chunking-and-metadata.md)** · 可学习
   建立用于检索的语义切片、父子块和 Metadata，理解切分对召回、引用和更新的影响。
10. **[Embedding 表示与向量相似度](mechanisms/embedding-and-similarity.md)** · 可学习
    使用真实 Embedding 服务理解向量、距离、归一化和空间一致性边界。
11. **[Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索](mechanisms/lexical-retrieval.md)** · 可学习
    在真实 PostgreSQL 中按词找候选；数据库准备和第一次查询见[第 11 节操作文档](../source/demos/rag_retrieval_lab/docs/11-lexical-retrieval.md)。
12. **[pgvector、Dense Retrieval 与向量索引](mechanisms/vector-store-and-pgvector.md)** · 可学习
    使用同一批 Chunk 和问题建立向量检索，观察索引、过滤和相似度分数。
13. **[多路召回与 RRF 融合](mechanisms/multi-retrieval-and-rrf.md)** · 可学习
    分别保留 lexical 和 dense 排名，再用 RRF 形成可解释的融合候选。
14. **[Top-k、阈值、Metadata Filter 与 Retrieval 诊断](mechanisms/retriever-contract.md)** · 可学习
    记录每路排名、过滤条件、阈值淘汰、融合排名和无结果原因。
15. **[Context Engineering：输入装配、预算与证据边界](mechanisms/context-engineering.md)** · 可学习
    Retriever 先产生候选，Context Builder 再决定本轮模型真正看到什么。
16. **[可信生成、Sources、Citation Candidate 与证据不足](mechanisms/trusted-generation.md)** · 可学习
    约束模型依据候选证据生成，并检查模型声明的来源是否属于本轮候选。

### 完成最小可信 RAG

17. **Citation 支持性、证据充分性、Refusal 与补充问题** · 待编写
    区分候选来源、模型声明、引用存在、证据支持和证据充分；证据不足时拒答或提出可回答的补充问题。

本节负责可信 RAG 输出边界，不扩展完整 Citation 运营平台。

### 把 RAG 交付成应用

18. **AI Native 应用界面与不确定性表达** · 待编写
    理解前端为什么必须表达结果、证据、状态和真实失败，而不只是显示聊天文本。
19. **FastAPI、Review API 与错误契约** · 待编写
    把固定 RAG Pipeline 暴露为产品 API，并区分业务错误、模型错误、检索错误和工程依赖错误。
20. **请求状态、结构化评审与证据交互** · 待编写
    建立请求状态机，展示结构化风险、Citation、Refusal、补充问题、最终上下文和诊断。

第一阶段只建设一个最小 Web 工作台，普通请求响应即可。Streaming、SSE 和 Agent 运行轨迹在第二阶段进入主线。

### 建立最小比较能力

21. **[LLM Calling Harness 与最小回归](mechanisms/calling-harness-and-regression.md)** · 等待前置
    固定 Case、Run Config 和 Record，记录直接 LLM 与固定 RAG 的运行事实；它是实验装置，不是完整评估平台。
22. **[Token、成本、延迟与缓存边界](mechanisms/cost-latency-and-caching.md)** · 等待前置
    记录 usage、估算成本、阶段耗时和总延迟，判断缓存何时会掩盖质量或返回过期结果。
23. **Evaluation Dataset 与最小 Golden Set** · 待编写
    固定问题、期望来源、风险覆盖、证据不足行为和实验前约定。
24. **直接 LLM、Lexical、Dense 与 RRF RAG 对比** · 待编写
    四条路径使用同一组样例，判断多路召回是否恢复单路弱项，并并列记录质量、成本、延迟和失败。

### 第一阶段综合项目

25. **[第一阶段：固定 RAG 需求评审助手](project/stage-1-rag-application/rag-review-assistant.md)** · 等待前置
    组合 `llm_core`、`rag_core` 和 `review_assistant/`，完成真实运行、最小可信证据、Review API、Web 工作台、bad case、需求修改、固定对照和阶段验收。

### 第一阶段能力收束

完成第一阶段后，应能够独立解释并修改：

- 文件到知识文档、Chunk、索引和候选的知识生产链。
- lexical、dense、RRF、过滤、阈值和诊断。
- Retriever、Context Builder 和 Generator 的责任边界。
- Structured Output、Citation、证据充分性、Refusal 和补充问题。
- Review API、请求状态和证据界面。
- 最小 Golden Set、固定对照、成本和延迟记录。

第一阶段交付的是稳定固定 RAG，不是完整质量平台。Reranker、知识更新治理、OCR/VLM、GraphRAG 和完整评估平台保留在知识地图扩展区，不阻塞进入第二阶段。

## 第二阶段：Agent、Tools 与 Multi-Agent 系统

第二阶段要回答：

> 当查询、知识源、工具和协作步骤不能完全预先固定时，怎样让 Agent 动态行动，同时由应用控制权限、状态、停止、证据、恢复和评估？

第二阶段不重做第一阶段的知识生产、检索和可信生成。Agent 负责选择下一步；Retriever、RRF、Citation 校验和产品契约继续由应用代码执行。

第二阶段项目篇在真正进入实现前创建，不预建空文档。它将维护同一个阶段契约，并在第 42、57 和 65 节提供三次返回检查点。

### 从固定 RAG 进入单 Agent

26. **Chain、固定 RAG、Workflow、Agent 与 Multi-Agent 的边界** · 待编写
    用固定 RAG 的真实边界判断哪些步骤需要模型动态决策，哪些仍应保持确定性程序。
27. **Agent Harness：模型、上下文、工具、状态与控制面** · 待编写
    建立承载模型、上下文、Tool、权限、循环、停止、事件和观测的应用宿主；区分 Agent Harness 与 LLM Calling Harness。
28. **Function Calling 与 Tool Schema** · 待编写
    将模型提出的行动约束为可解析、可校验的工具调用草案。
29. **Tool Runtime 与结构化错误** · 待编写
    由应用校验并执行工具，将真实结果或失败转换为稳定契约。
30. **工具权限、高风险确认、超时、幂等与审计** · 待编写
    分离模型提议和应用执行，治理副作用、重复调用、权限和人工确认。
31. **Agent Loop、预算、最大步数与停止原因** · 待编写
    显式表达继续、完成、追问、等待确认、达到上限、工具失败和安全阻止。
32. **Query Rewrite 与 Source Routing** · 待编写
    根据任务改写检索查询并选择允许的知识源，同时保留原问题和路由理由。
33. **Retriever as Tool 与 Agentic RAG** · 待编写
    将第一阶段 Retriever 暴露为受治理 Tool，保留查询、过滤、候选、诊断和失败原因。
34. **Guardrails、Safety 与应用控制边界** · 待编写
    限制工具、预算、敏感数据和不可接受输出，确保 Prompt 不能绕过控制面。

### State、Conversation 与 Memory

35. **Run State、Conversation、Memory 与业务知识的边界** · 待编写
    区分当前运行步骤、会话消息、记忆和可引用业务事实的作用域与生命周期。
36. **短期记忆：窗口、摘要、压缩与上下文预算** · 待编写
    处理窗口淘汰、摘要触发、原始消息范围、摘要版本和失真诊断。
37. **长期记忆：用户确认偏好、作用域、检索与治理** · 待编写
    只保存用户明确确认且跨会话仍有效的偏好或约束，支持来源、更新、删除和关闭；学习主线不等于强制产品接入。

### Streaming 与 Agent 产品状态

38. **SSE 结构化事件协议** · 待编写
    使用 Token Stream、Event Stream、SSE 和稳定事件字段，承载 Tool Call、检索、等待、停止与错误。
39. **Streaming State Synchronization：顺序、取消、重连与重复事件** · 待编写
    处理事件顺序、断线重连、取消传播、重复消费和最终提交。
40. **AI Response State Machine 与 Agent Runtime UI** · 待编写
    建立运行中、调用工具、等待补充、等待确认、完成、失败和终止状态，并展示证据变化和停止原因。
41. **Agent Trajectory、Tool 与 Memory Evaluation** · 待编写
    评估工具选择、参数、步骤、停止、记忆污染、质量、成本和延迟。
42. **单 Agent RAG 集成检查点** · 待编写
    回到第二阶段项目篇，完成 Query Rewrite、Source Routing、Retriever Tool、补检索、追问、停止、SSE 和运行界面。

### MCP、通用工具与 Agent Skills

43. **MCP：Agent 与工具、资源和外部上下文的连接边界** · 待编写
    理解协议连接解决什么、Tool Runtime 仍需负责什么，并接入一个可观察的真实工具或资源。
44. **Browser 与 Search Tool：搜索、来源判断和引用** · 待编写
    处理查询、结果筛选、来源可信度、重复来源和引用回查。
45. **Code 与 File Tool：执行、文件处理、沙箱与副作用** · 待编写
    区分读取、生成、执行和写入能力，明确沙箱、权限、超时和不可逆操作。
46. **Agent Skills：说明、资源、脚本与可复用执行能力** · 待编写
    区分 Skill、Prompt、Tool、MCP 和普通文档，理解领域能力怎样被按需加载和执行。
47. **Planning、Task Decomposition 与 Reflection** · 待编写
    在复杂任务需要时分解步骤、检查进展和修正计划，同时限制无收益的自我循环。
48. **Deep Research：搜索、验证、迭代与带来源综合** · 待编写
    组合 Planning、Search、Browser、来源判断和停止条件，完成可追踪的多步研究任务。

### Multi-Agent 与 A2A

49. **Multi-Agent 拆分判断** · 待编写
    先证明单 Agent 不足，再判断是否存在独立责任、上下文、工具或可验证并行收益。
50. **角色责任、上下文、工具与输出契约** · 待编写
    为每个 Agent 定义输入、私有上下文、允许工具、输出和明确非职责。
51. **Supervisor、Worker、Delegation 与任务分配** · 待编写
    明确谁拆任务、谁执行、谁重分配以及委派失败如何返回。
52. **共享状态、私有上下文与证据** · 待编写
    区分共享业务事实、局部推理、工具结果和最终可引用证据。
53. **并行执行、任务依赖与失败隔离** · 待编写
    表达可并行任务、依赖关系、局部失败、取消和部分结果。
54. **结果汇总、证据合并与冲突裁决** · 待编写
    保留分歧和证据归属，明确最终结果责任人和不可自动裁决的冲突。
55. **A2A：Agent 之间的任务、状态、结果与错误交换** · 待编写
    在本地责任和委派契约建立后，再理解跨 Agent 系统的互操作边界。
56. **Multi-Agent 运行观测与协作界面** · 待编写
    展示任务分配、Agent 状态、证据、等待、失败、冲突和最终裁决。
57. **单 Agent 与 Multi-Agent 基线比较** · 待编写
    回到第二阶段项目篇，在固定样例上比较质量、成本、延迟、证据一致性和失败定位难度。

### 必要的 Workflow 控制

58. **Workflow State、Node、Edge、条件、循环与并行** · 待编写
    将需要显式控制的流程建模为状态和节点，不把固定步骤交给模型猜测。
59. **Checkpoint、Interrupt、Resume 与 Human-in-the-loop** · 待编写
    明确中断前保存什么、恢复从哪里继续，以及人工决定如何进入状态。
60. **节点重试、副作用与幂等** · 待编写
    处理写操作、重复执行、补偿、重试、跳过和转人工。
61. **Workflow as Tool、子 Agent 与可恢复编排** · 待编写
    判断何时把确定性子流程封装为 Tool，何时使用子 Agent，何时需要 Workflow 管理恢复。

Workflow 不单独成为项目阶段，也不建设低代码画布。它只补齐 Agent 与 Multi-Agent 中确实需要的显式状态、恢复和人工控制。

### 质量收束与最终交付

62. **Trace、Span、Run、Versioning 与 Regression** · 待编写
    关联模型、Prompt、Retriever、Tool、Agent、Workflow、输入、状态、结果和错误。
63. **RAG、Agent、Deep Research 与 Multi-Agent Evaluation** · 待编写
    分层评估检索、证据、工具、轨迹、研究来源、协作分工和最终结果，并区分自动判断与人工判断。
64. **Bad Case Management、Human Eval 与 Feedback Loop** · 待编写
    将真实失败和人工反馈转成可复现样例、归因、修改任务和回归证据。
65. **第二阶段项目：Agent 协作需求评审系统** · 待编写
    完成 Agentic RAG、MCP、Agent Skills、Deep Research、Multi-Agent、A2A、必要 Workflow、运行界面、统一观测和阶段验收。

### 第二阶段能力收束

完成第二阶段后，应能够：

- 判断固定程序、单 Agent、Multi-Agent 和 Workflow 的适用边界。
- 设计 Agent Harness、Tool Schema、Tool Runtime、权限和停止条件。
- 将 Retriever、Browser、Search、Code 和 File 能力作为受治理 Tool 使用。
- 解释 MCP、Agent Skills 和 A2A 分别连接什么、不能替代什么。
- 设计 Conversation、短期记忆和长期偏好，同时防止记忆冒充业务证据。
- 构建可追踪来源、可停止、可评估的 Deep Research 任务。
- 为多个 Agent 划分责任、上下文、工具和输出契约，并处理并行、失败、汇总与冲突。
- 使用必要 Workflow 处理显式状态、恢复、人工介入和副作用。
- 通过事件、轨迹、Trace、Eval 和 UI 解释系统为什么行动、为什么停止、为什么失败。

完整但不规定阅读先后的能力范围见[知识地图](knowledge-map.md)。
