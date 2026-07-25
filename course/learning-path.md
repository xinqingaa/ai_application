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

7. **RAG 与外部知识的边界** · 待编写
   区分模型已有知识、搜索、数据库查询、固定 RAG 和 Agentic RAG。
8. **文档加载、清洗与来源保留** · 待编写
   把固定业务资料转换为有来源身份的文档对象。
9. **Chunking、父子块与 Metadata** · 待编写
   理解切分怎样影响召回、引用和后续更新。
10. **Embedding、相似度与 Vector Store** · 待编写
    使用真实 Embedding 服务建立向量表示和可检索索引。
11. **关键词检索、向量检索与 Retriever 契约** · 待编写
    用同一查询比较关键词与向量检索，并保留候选结果和诊断。
12. **[Context Engineering：输入装配、预算与证据边界](mechanisms/context-engineering.md)** · 等待前置
    Retriever 先产生候选证据，Context Builder 再决定本轮模型真正看到什么。
13. **可信生成、Sources、Citation Candidate 与证据不足** · 待编写
    约束模型依据候选证据生成；V0 只建立 Citation Candidate，不宣称完成 Citation 校验。

### 第四段：把能力交付成最小产品

14. **AI Native 应用界面与不确定性表达** · 待编写
    理解前端为什么必须表达结果、证据、状态和真实失败，而不只是显示聊天文本。
15. **FastAPI、Review API 与错误契约** · 待编写
    把固定 RAG Pipeline 暴露为产品 API，并让业务错误和工程错误可以区分。
16. **最小请求状态与结构化评审界面** · 待编写
    建立 `idle`、`submitting`、`success`、`error` 状态，展示风险结果、候选来源、最终上下文和诊断。

V0 前端使用普通请求响应即可。Streaming、SSE 和复杂运行轨迹不作为 V0 主线门禁。

### 第五段：建立可比较基线

17. **[LLM Calling Harness 与最小回归](mechanisms/calling-harness-and-regression.md)** · 等待前置
    固定 Case、Run Config 和 Record，记录直接 LLM 与固定 RAG 的运行事实。
18. **Golden Set 与最小检索、生成评估** · 待编写
    固定问题、期望来源、风险覆盖和证据不足行为。
19. **直接 LLM、关键词 RAG、向量 RAG 对比** · 待编写
    三条路径使用同一组样例；Hybrid Retrieval 只作为增强项。

### 第六段：进入 V0 项目

20. **[V0：固定 RAG 需求评审基线](project/stage-1-single-agent-rag/v0-fixed-rag.md)** · 等待前置
    组合 `llm_core`、后续 `rag_core` 和 `review_assistant/`，完成真实运行、最小工作台、失败复现、需求修改和版本验收。

### V0 按需支撑

- **[Streaming、事件协议与 Conversation](mechanisms/streaming-and-conversation.md)** · 按需支撑
  当前用于理解交互机制和学习期实验；V3 再把结构化事件正式接入 Agent 产品链。
- **[Token、成本、延迟与缓存边界](mechanisms/cost-latency-and-caching.md)** · 按需支撑
  当 Harness 已有重复调用记录，需要比较预算、延迟或缓存失效时进入。
- **Python、HTTP、JSON 与配置** · 按需支撑
  遇到基础问题时回查 `course/python_base/`，不要求重新通关。

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

### 第二段：把一次结果变成可回归事实

5. **Trace、Span、Run 与版本关联** · 待编写
   关联模型、Prompt、Retriever、Schema、输入、结果和错误。
6. **Versioning、Regression 与 Experiment** · 待编写
   控制变量比较版本，避免用单次好结果证明质量提升。
7. **Bad Case Management 与失败归因** · 待编写
   判断问题应修改数据、Retriever、Context、Prompt、Schema 还是模型。
8. **Feedback Loop** · 待编写
   将人工反馈转为可复现样例、标签和回归任务。
9. **质量、成本与延迟联合判断** · 待编写
   防止把更便宜、更快或可解析误当成更正确。

### 第三段：建立质量工作台

10. **Eval、Labeling 与 Feedback UI** · 待编写
    展示运行记录、版本比较、指标和 bad case，并支持人工标注与反馈。
11. **V2：需求评审质量闭环** · 待编写
    在产品中接入评估、回归、bad case 和最小质量面板，完成失败、变更和验收。

V2 是质量工作台的起点。V6 负责完善和作品化，不从零开始建设质量界面。

## V3：单 Agent RAG

V3 要回答：

> 当固定 RAG 无法预先决定查询、知识源和补检索步骤时，怎样让单 Agent 动态行动，同时保持应用控制、可观察和可评估？

### 第一段：判断为什么需要 Agent

1. **Chain、固定 RAG、Workflow、Agent 与 Multi-Agent 边界** · 待编写
   用固定 RAG 的真实失败证明哪些步骤需要模型动态决策。
2. **Function Calling 与 Tool Schema** · 待编写
   将模型提出的行动约束为可校验的工具调用草案。
3. **Tool Runtime 与结构化错误** · 待编写
   由应用执行工具、校验输入输出并暴露真实失败。
4. **工具权限、超时、幂等与审计** · 待编写
   明确模型决策和应用控制之间的边界。

### 第二段：把 Retriever 变成可治理工具

5. **Query Rewrite 与 Source Routing** · 待编写
   根据任务改写检索查询并选择允许的知识源。
6. **Retriever as Tool** · 待编写
   保留查询、过滤条件、候选结果和失败原因。
7. **Agent Loop、最大步数与停止原因** · 待编写
   显式表达继续、完成、需要补充、达到上限、工具失败和安全阻止。
8. **补检索、质量判断与追问补全** · 待编写
   在证据不足时决定再次检索还是向用户提问。
9. **Guardrails 与应用控制边界** · 待编写
   限制工具、预算、风险操作和不可接受输出。
10. **Agent Trajectory 与 Tool Evaluation** · 待编写
    评估工具选择、参数、步骤、停止原因、质量、成本和延迟。

### 第三段：让 Agent 运行过程成为产品状态

11. **SSE 结构化事件协议** · 待编写
    将 Agent 状态、Tool Call、检索和错误转换为稳定应用事件。
12. **Streaming State Synchronization** · 待编写
    处理事件顺序、取消、重连、重复事件和最终提交。
13. **AI Response State Machine** · 待编写
    建立运行中、调用工具、等待补充、完成、失败和终止状态。
14. **Tool Call、证据变化与 Agent 轨迹 UI** · 待编写
    让用户看到当前步骤、证据变化、停止原因和真实失败。

### 第四段：进入 V3 项目

15. **V3：单 Agent RAG 需求评审** · 待编写
    在 V2 质量基线上增加动态补检索、知识源选择、追问和 Agent 运行界面，并与固定 RAG 基线比较。

V3 不实现 Workflow Checkpoint、人工审批节点和恢复语义；这些进入 V4。

## V4-V6 暂定边界

阶段二暂不展开内部课表，只维护版本边界：

| 版本 | 暂定结果 |
| --- | --- |
| V4 可控 Workflow | State、分支、Checkpoint、Interrupt、Resume、Human-in-the-loop，以及对应运行时界面 |
| V5 多 Agent 评审 | 角色契约、共享状态、并行执行、失败隔离、汇总、冲突裁决，以及多 Agent 协作界面 |
| V6 产品化 | 整合并完善已有工作台和质量面板，补齐本地部署、演示和作品化；不把前端推迟到本版本才开始 |

完整但不规定先后的知识范围见 [知识地图](knowledge-map.md)。
