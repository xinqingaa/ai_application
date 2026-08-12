# 需求评审助手标准学习路径

这份文档是课程阅读顺序的唯一真源。

目录名称、文件排列、知识地图分组和代码模块出现的先后，都不能替代这里规定的顺序。课程设计由项目目标反推知识；学习者按照认知前置正向学习：

```text
项目愿景
→ 概念
→ 机制与真实实验
→ 项目综合实践
→ 失败、修改与验收
```

## 怎样使用这条路径

- 按当前版本的主线顺序阅读，不按 `concepts/`、`mechanisms/` 的目录顺序遍历。
- 每篇正文只说明知识前置和本文交付；读完后回到本页继续。
- “按需支撑”不是版本门禁，遇到对应产品或运行问题时再进入。
- 尚未有正文的步骤保留在正确位置，但不创建空文档或无效链接。
- package 中已经存在某项能力，不代表当前步骤已经学习，也不代表产品已经启用。
- 每个版本开始时可以先读取对应项目篇的业务场景、输入输出、Definition of Ready 和非目标，用它建立后续实验契约；完成概念与机制后，再回到同一项目篇进行综合实现和验收。这是对同一真源的两次使用，不建立第二条项目路线。
- V0-V3 每个版本都同时推进模型或知识能力、产品 API、AI Native 前端和质量证据；前端不等到 V6 才开始。

状态说明：

| 状态 | 含义 |
| --- | --- |
| 可学习 | 正文和必要实验已经存在，可以按路径进入 |
| 待编写 | 位置和目标已确定，正文与真实代码一起落地 |
| 等待前置 | 正文已经存在，但必须先完成前面的知识 |
| 按需支撑 | 不阻塞主线，在真实问题出现时进入 |

## V0：固定 RAG 可运行基线

V0 要回答：

> 模型怎样理解需求，外部资料怎样成为可检索证据，应用怎样通过 API 和最小工作台交付可观察、可比较的评审结果？

### 先取得 V0 业务契约

开始第一段前，先阅读 [V0 项目篇](project/stage-1-single-agent-rag/v0-fixed-rag.md) 的“业务场景”“V0 Definition of Ready”“输入与输出契约”和“V0 明确不做”。此时只确认待评审对象、参考知识、固定资料、问题集、输出和非目标，不提前进入实现任务、检索参数或验收结论。

这份业务契约是后续文档实验、Golden Set 和四路对照的共同前提。完成第 1–23 步后，再回到同一项目篇完成综合实现和版本验收。

### 第一段：模型在应用中负责什么

1. **[LLM 在 AI 应用中的位置与边界](concepts/llm-in-ai-applications.md)** · 可学习
   建立普通程序、LLM、RAG、Agent 和 Workflow 的职责边界。
2. **[模型输入输出契约：Prompt、Schema 与 Context](concepts/model-input-output-contracts.md)** · 可学习
   理解任务、证据和结果为什么必须由应用建立契约。
3. **[Model API、调用生命周期与 Provider 抽象](mechanisms/model-api-and-provider.md)** · 可学习
   运行真实模型，理解统一调用入口、供应商差异和错误边界。

### 第二段：让模型结果进入程序

4. **[面向应用的 Prompt Engineering](mechanisms/prompt-engineering.md)** · 可学习
   把临时提示词变成可命名、可版本化、可比较的任务协议。
5. **[Structured Output 与应用侧校验](mechanisms/structured-output.md)** · 可学习
   用 Schema、解析和业务校验决定结果能否进入程序。
6. **[Reliability、错误分类与可见降级](mechanisms/reliability-and-errors.md)** · 可学习
   区分可重试、不可重试、结构化失败和显式降级。

完成这一段后，应能使用真实模型生成结构化风险结果，并解释失败发生在哪一层。此时证据仍来自固定输入，不要把 Context Builder 当成 Retriever。

### 第三段：让外部资料成为可检索证据

本段从知识生产开始，依次完成文档解析与结构还原、切片与索引、检索、上下文装配和可信生成；V3 再在这些固定能力之上增加 Agent 动态编排。

7. **[RAG 与外部知识的边界](concepts/rag-and-external-knowledge.md)** · 可学习
   区分模型已有知识、搜索、数据库查询、固定 RAG 和 Agentic RAG。
8. **[文档内容识别、解析路由、结构还原与来源保留](mechanisms/document-loading-and-cleaning.md)** · 可学习
   以 PDF 为复杂样例理解原生文本、扫描件和图文混排的处理路线；代码实现 TXT、Markdown、DOCX 与文本型 PDF 的最小结构还原，交付带来源位置的 `KnowledgeDocument`，但不产生 Chunk。
9. **[Chunking、父子块与 Metadata](mechanisms/chunking-and-metadata.md)** · 可学习
   接收第 8 步产生的 `DocumentElement`，建立用于检索的语义切片、父子块和 Metadata，理解切分怎样影响召回、引用和后续更新。
10. **[Embedding 表示与向量相似度](mechanisms/embedding-and-similarity.md)** · 可学习
    承接第 9 步的可回查 Chunk，使用真实 Embedding 服务理解距离、归一化和 Embedding 空间一致性边界。
11. **[Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索](mechanisms/lexical-retrieval.md)** · 可学习
    理解词项检索和 BM25 原理；产品使用 PostgreSQL FTS，不把其排序函数误称为 BM25。数据库基础不够时，先按需阅读 [PostgreSQL 零基础](concepts/postgresql-for-ai-applications.md) 再返回本步。
12. **[pgvector、Dense Retrieval 与向量索引](mechanisms/vector-store-and-pgvector.md)** · 可学习
    建立向量检索，并观察索引、过滤和相似度分数。
13. **多路召回与 RRF 融合** · 待编写
    分别保留 lexical 和 dense 排名，再用 RRF 形成可解释的融合候选。
14. **Top-k、阈值、Metadata Filter 与 Retrieval 诊断** · 待编写
    记录每路排名、融合排名、过滤条件、阈值淘汰和无结果原因。
15. **[Context Engineering：输入装配、预算与证据边界](mechanisms/context-engineering.md)** · 等待前置
    Retriever 先产生候选证据，Context Builder 再决定本轮模型真正看到什么；Context 注入不属于文档解析或 Chunking。
16. **可信生成、Sources、Citation Candidate 与证据不足** · 待编写
    约束模型依据候选证据生成；V0 只建立 Citation Candidate，不宣称完成 Citation 校验。

完成第 7–16 步，且能亲自运行实验、解释数据流、定位一次真实边界并完成修改题，可以称为已经完成**固定 RAG 核心机制入门**：你知道资料怎样变成 Chunk，lexical / dense / RRF 怎样形成候选，候选怎样进入 Context，以及模型怎样基于候选生成。这里只阅读正文或跑通命令，还不能称为掌握；完成第 20、22、23 步的对照与评估，并回到 V0 项目完成真实产品、bad case、变更和验收后，才达到本仓库的 **V0 固定 RAG 项目掌握**。Citation 支持性校验、证据充分性、Refusal 和知识更新在 V1，系统评估、Reranker 准入与 bad case 闭环在 V2，因此第 16 步不表示“RAG 已全部学完”。

### 第四段：把能力交付成最小产品

17. **AI Native 应用界面与不确定性表达** · 待编写
    理解前端为什么必须表达结果、证据、状态和真实失败，而不只是显示聊天文本。
18. **FastAPI、Review API 与错误契约** · 待编写
    把固定 RAG Pipeline 暴露为产品 API，并让业务错误和工程错误可以区分。
19. **最小请求状态与结构化 Web 评审界面** · 待编写
    建立 `idle`、`submitting`、`success`、`error` 状态，展示风险结果、候选来源、最终上下文和诊断。

V0 只建设 Web 前端，使用普通请求响应即可。Streaming、SSE、Flutter App 和复杂运行轨迹不作为 V0 主线门禁。

### 第五段：建立可比较基线

20. **[LLM Calling Harness 与最小回归](mechanisms/calling-harness-and-regression.md)** · 等待前置
    固定 Case、Run Config 和 Record，记录直接 LLM 与固定 RAG 的运行事实。
21. **[Token、成本、延迟与缓存边界](mechanisms/cost-latency-and-caching.md)** · 可学习
    V0 必须掌握 usage、成本估算、阶段耗时、总延迟和实验预算；Exact-match Cache、cache key 与失效实验仍按真实需要进入，不作为 V0 验收门禁。
22. **Golden Set 与最小检索、生成评估** · 待编写
    固定问题、期望来源、风险覆盖和证据不足行为。
23. **直接 LLM、Lexical RAG、Dense RAG 与 RRF RAG 对比** · 待编写
    四条路径使用同一组样例，判断多路召回是否提高检索和评审质量。

### 第六段：进入 V0 项目

24. **[V0：固定 RAG 需求评审基线](project/stage-1-single-agent-rag/v0-fixed-rag.md)** · 等待前置
    组合 `llm_core`、后续 `rag_core` 和 `review_assistant/`，完成真实运行、最小工作台、失败复现、需求修改和版本验收。

### V0 按需支撑

- **[Streaming、事件协议与 Conversation](mechanisms/streaming-and-conversation.md)** · 按需支撑
  当前用于理解交互机制和学习期实验；V3 再把结构化事件正式接入 Agent 产品链。
- **Python、HTTP、JSON 与配置** · 按需支撑
  遇到基础问题时回查 `course/python_base/`，不要求重新通关。
- **[PostgreSQL 零基础：读懂并使用项目数据库](concepts/postgresql-for-ai-applications.md)** · 按需支撑
  第 11 步的 Server、Schema、SQL、事务、索引或 migration 基础不足时先补齐；它不新增主线路径步骤。

## V1：可信结构化评审

V1 要回答：

> 应用怎样证明风险结论来自有效证据，并在证据不足时拒答或向用户追问？

### 第一段：从来源候选进入可信引用

1. **Sources、Citation 与 Citation Candidate 的边界** · 待编写
   区分检索候选、模型声明的引用和应用校验后的引用。
2. **Citation 校验与证据定位** · 待编写
   校验引用是否存在、是否支持结论，以及如何定位原文。
3. **证据充分性、Refusal 与补充问题** · 待编写
   在材料不足时拒绝无依据结论，并生成可回答的补充问题。
4. **知识版本、更新与来源一致性** · 待编写
   保证引用能够关联当前有效资料，明确更新和删除边界。

### 第二段：让可信状态进入产品契约

5. **可信评审 Schema 与业务校验** · 待编写
   让风险、证据、拒答和补充问题成为明确数据契约。
6. **Citation、Refusal 与工程契约测试** · 待编写
   使用确定性测试验证证据关系和失败边界。
7. **Schema Driven UI 与结构化评审报告** · 待编写
   根据业务 Schema 展示风险、严重程度、建议和可信状态。
8. **来源定位、证据查看与补充信息交互** · 待编写
   支持从风险进入引用原文，区分有依据、证据不足和需要补充。

### 第三段：进入 V1 项目

9. **V1：可信结构化需求评审** · 待编写
   在 V0 产品上增加 Citation 校验、Refusal、补充问题和可信证据界面，并完成失败、变更和验收。

### V1 按需支撑

- **复杂文档与多模态知识生产边界** · 待编写
  概念篇比较文本型 PDF、扫描件、图片、音频和视频进入知识系统时的信息损失、成本和适用边界。
- **扫描 PDF、图片 OCR/VLM 与 Markdown 归一化实验** · 待编写
  机制篇用少量固定样例观察 OCR、版面、图片描述和来源定位；不进入 V1 产品验收。

## V2：质量闭环

V2 要回答：

> 怎样用固定数据、运行记录、人工反馈和回归结果证明一次改动真正改善了评审质量？

### 第一段：建立评估对象和指标

1. **Evaluation Dataset 与 Golden Set 深化** · 待编写
   从 V0 最小样例扩展为可版本化的评估数据集。
2. **Retrieval Evaluation** · 待编写
   评估来源命中、排序和无关候选，而不是只看最终回答。
3. **Generation、Citation 与 Refusal Evaluation** · 待编写
   分开评估风险覆盖、无依据结论、引用正确性和拒答合理性。
4. **LLM-as-Judge 与 Human Eval** · 待编写
   明确自动评审与人工判断分别能证明什么。
5. **Reranker、重排诊断与产品准入证据** · 待编写
   用真实 Reranker 对比 RRF 基线；只有预先定义的质量收益大于延迟、成本和维护复杂度时才进入产品默认链路。

### 第二段：把一次结果变成可回归事实

6. **Trace、Span、Run 与版本关联** · 待编写
   关联模型、Prompt、Retriever、Schema、输入、结果和错误。
7. **Versioning、Regression 与 Experiment** · 待编写
   控制变量比较版本，避免用单次好结果证明质量提升。
8. **Bad Case Management 与失败归因** · 待编写
   判断问题应修改数据、Retriever、Context、Prompt、Schema 还是模型。
9. **Feedback Loop** · 待编写
   将人工反馈转为可复现样例、标签和回归任务。
10. **质量、成本与延迟联合判断** · 待编写
   防止把更便宜、更快或可解析误当成更正确。

### 第三段：建立质量工作台

11. **Eval、Labeling 与 Feedback UI** · 待编写
    展示运行记录、版本比较、指标和 bad case，并支持人工标注与反馈。
12. **V2：需求评审质量闭环** · 待编写
    在产品中接入评估、回归、bad case 和最小质量面板，完成失败、变更和验收。

V2 是质量工作台的起点。V6 负责完善和作品化，不从零开始建设质量界面。

### V2 按需支撑

- **RAPTOR、GraphRAG、知识图谱与普通 RAG 的边界** · 待编写
  概念篇用于判断长文档总结、实体关系和多跳问题何时值得使用高级索引。
- **Neo4j 多跳检索与 RAG 融合实验** · 待编写
  机制篇仅使用小型固定图和可验证问题观察实体、关系、路径与文本证据融合；没有稳定多跳 bad case 时不进入项目。

## V3：单 Agent RAG

V3 要回答：

> 当固定 RAG 无法预先决定查询、知识源和补检索步骤时，怎样让单 Agent 动态行动，同时保持应用控制、可观察和可评估？

V3 增加的是运行时控制层，不重做 V0 已建立的知识生产、索引和检索机制。Agent 决定何时改写查询、选择知识源、调用 Retriever、补检索、追问或停止；Retriever、RRF 和满足准入条件的 Reranker 继续负责候选过滤、排序和诊断。

### 第一段：判断为什么需要 Agent

1. **Chain、固定 RAG、Workflow、Agent 与 Multi-Agent 边界** · 待编写
   用固定 RAG 的真实失败证明哪些步骤需要模型动态决策。

### 第二段：建立可治理的短期记忆与用户确认型长期记忆

2. **Run State、Conversation、Memory 与业务知识的边界** · 待编写
   区分当前运行状态、会话历史、跨会话用户确认偏好和可引用业务资料，明确业务事实不能由 Memory 替代。
3. **短期记忆：滑动窗口、摘要与预算** · 待编写
   明确窗口淘汰、摘要触发、原始消息范围、摘要版本和失真诊断。
4. **长期记忆：用户确认偏好、作用域、检索与治理** · 待编写
   只保存用户明确确认且跨会话仍有效的偏好或约束，支持作用域、来源、更新、删除、关闭和注入预算；PRD、接口规则和历史评审仍进入可引用知识。

### 第三段：把模型行动变成可治理工具

5. **Function Calling 与 Tool Schema** · 待编写
   将模型提出的行动约束为可校验的工具调用草案。
6. **Tool Runtime 与结构化错误** · 待编写
   由应用执行工具、校验输入输出并暴露真实失败。
7. **工具权限、超时、幂等与审计** · 待编写
   明确模型决策和应用控制之间的边界。

### 第四段：把 Retriever 和 Memory 变成可治理工具

8. **Query Rewrite 与 Source Routing** · 待编写
   根据任务改写检索查询并选择允许的知识源。
9. **Retriever as Tool** · 待编写
   将已有 Retriever 暴露为可治理工具，保留查询、过滤条件、排序诊断、候选结果和失败原因；Agent 不自由替代 Retriever 排序。
10. **Memory Retrieval 与上下文注入** · 待编写
    分开检索长期记忆和业务证据，记录命中原因并防止记忆冒充 Citation。
11. **Agent Loop、最大步数与停止原因** · 待编写
   显式表达继续、完成、需要补充、达到上限、工具失败和安全阻止。
12. **补检索、质量判断与追问补全** · 待编写
   在证据不足时决定再次检索还是向用户提问。
13. **Guardrails 与应用控制边界** · 待编写
   限制工具、预算、风险操作和不可接受输出。
14. **Agent Trajectory、Tool 与 Memory Evaluation** · 待编写
    评估工具选择、参数、步骤、停止原因、记忆污染、质量、成本和延迟。

### 第五段：让 Agent 运行过程成为产品状态

15. **SSE 结构化事件协议** · 待编写
    将 Agent 状态、Tool Call、检索和错误转换为稳定应用事件。
16. **Streaming State Synchronization** · 待编写
    处理事件顺序、取消、重连、重复事件和最终提交。
17. **AI Response State Machine** · 待编写
    建立运行中、调用工具、等待补充、完成、失败和终止状态。
18. **Tool Call、Memory、证据变化与 Agent 轨迹 UI** · 待编写
    让用户看到当前步骤、记忆使用、证据变化、停止原因和真实失败。

### 第六段：进入 V3 项目

19. **V3：单 Agent RAG 需求评审** · 待编写
    在 V2 质量基线上增加短期记忆、面向用户确认偏好与约束的长期记忆、动态补检索、知识源选择、追问和 Agent 运行界面，并与关闭长期记忆和固定 RAG 的基线比较。

V3 不实现 Workflow Checkpoint、人工审批节点和恢复语义；这些进入 V4。

### V3 按需支撑

- **Mem0 与自建 Memory Runtime 对照** · 待编写
  机制篇比较记忆抽取、去重、更新、检索和治理边界；产品优先复用 PostgreSQL、pgvector 和已有运行时，不为框架本身增加依赖。
- **图片理解与音频 ASR 归一化实验** · 待编写
  用少量真实样例观察图片或音频怎样转换为可追踪文本；视频理解和语音产品交互只保留概念认知。

## V4-V6 暂定边界

阶段二暂不展开内部课表，只维护版本边界：

| 版本 | 暂定结果 |
| --- | --- |
| V4 可控 Workflow | State、分支、Checkpoint、Interrupt、Resume、Human-in-the-loop，以及对应运行时界面 |
| V5 多 Agent 评审 | 角色契约、共享状态、并行执行、失败隔离、汇总、冲突裁决，以及多 Agent 协作界面 |
| V6 产品化 | 整合并完善已有工作台和质量面板，补齐本地或个人私有服务器的单用户部署、演示和作品化；不把前端推迟到本版本才开始，不扩展多租户与企业合规平台 |

完整但不规定先后的知识范围见 [知识地图](knowledge-map.md)。
