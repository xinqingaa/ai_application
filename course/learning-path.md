# 需求评审助手标准学习路径

本文是课程阅读顺序和课程序号的唯一真源。当前课程只有第一阶段、第二阶段和一套从 1 到 101 的连续编号。

一节课代表一个核心学习问题，可以同时包含概念或机制正文与配套实验篇。每节介绍说明学习者此刻的问题和本节交付；知识地图、目录、文件名和工程 `PLAN.md` 都不规定阅读顺序。

## 怎样学习一节课

```text
概念篇建立问题和边界
→ 机制篇理解数据或状态变化
→ 实验篇运行、观察和调试
→ 在检查点回到项目篇组合能力
```

状态：

- **可学习**：正文和必要实验已经存在。
- **待编写**：当前规划已经给出核心问题、交付和建议位置；正式写作时若发现认知前置、课程粒度或协议更新不再成立，应回到本路径调整。
- **等待前置**：材料存在，但需要先完成前面的课程或产品能力。

## 必备基础检查

必备基础不占课程序号。开始前确认能够使用 `uv run`，阅读 Python 类型、异常和异步代码，理解 HTTP、JSON、Schema、环境变量和流式响应。开始第 11 节前，还要理解 PostgreSQL Server、Database、Schema、Table、Role、migration 和基础 SQL；不足时回查 `source/python_base/` 与 PostgreSQL 概念篇。

# 第一阶段：RAG 应用基础

第一阶段回答：真实资料怎样成为可检索证据，固定 RAG 怎样形成可诊断、可引用、可拒答并能通过 API 与 Web 工作台交付的需求评审应用？

开始前先阅读[第一阶段项目篇](project/stage-1-rag-application/rag-review-assistant.md)中的业务场景、学习检查点和非目标，并了解根 [SPEC](../SPEC.md) 的第一阶段要求。

## 模型进入应用

这一单元先把不稳定的模型调用收敛成应用能够控制的任务、结果和错误契约，为后续 RAG 生成端提供稳定入口。

1. **[LLM 在 AI 应用中的位置与边界](concepts/llm-in-ai-applications.md)** · 可学习
   从普通确定性程序出发，区分 LLM、RAG、Agent 和 Workflow 分别解决什么问题。学完应能判断模型适合参与哪类判断，以及哪些责任必须留在应用。
2. **[模型输入输出契约：Prompt、Schema 与 Context](concepts/model-input-output-contracts.md)** · 可学习
   模型只接收输入并生成候选输出，任务、证据和业务结果必须由应用建立契约。本节形成 Prompt、Context 和 Schema 的最小关系图，为后续三个机制单元提供共同语言。
3. **[Model API、调用生命周期与 Provider 抽象](mechanisms/model-api-and-provider.md)** · 可学习
   一次模型调用会经过配置、请求、供应商、响应和错误转换；业务代码不应绑定某个 SDK 对象。本节建立稳定调用边界，并通过[真实模型与 Provider 实验](labs/model-api-and-provider.md)观察切换配置时哪些事实应变、哪些契约不变。
4. **[面向应用的 Prompt Engineering](mechanisms/prompt-engineering.md)** · 可学习
   随手拼接 Prompt 无法稳定比较和修改。本节把 Prompt 理解为版本化任务协议，区分任务、证据、约束和输出要求，并在[单变量对照实验](labs/prompt-engineering.md)中固定模型与样例只改变 Prompt。
5. **[Structured Output 与应用侧校验](mechanisms/structured-output.md)** · 可学习
   “返回了 JSON”不等于结果能进入业务。本节区分模型侧格式约束、JSON 解析、Schema 校验和业务校验，并在[结构化输出实验](labs/structured-output.md)中观察失败究竟发生在哪一层。
6. **[Reliability、错误分类与可见降级](mechanisms/reliability-and-errors.md)** · 可学习
   超时、限流、鉴权、能力不支持和 Schema 失败不能统一重试。本节建立错误分类、有限重试和显式降级边界，并在[可靠调用实验](labs/reliability-and-errors.md)中比较真实调用与稳定失败复现能够分别证明什么。

## 建立固定 RAG 核心链

这一单元沿同一份“售后入口与订单状态”资料，追踪文件怎样变成可检索候选、可装配 Context 和可检查来源的生成结果。

7. **[RAG 与外部知识的边界](concepts/rag-and-external-knowledge.md)** · 可学习
   模型参数知识无法承担当前业务规则和来源追踪。本节建立“资料 → 检索 → Context → 生成”的总图，区分固定 RAG、普通搜索和后续 Agentic RAG。
8. **[文档内容识别、解析路由、结构还原与来源保留](mechanisms/document-loading-and-cleaning.md)** · 可学习
   文件扩展名不能保证内容可用，提取出文字也不等于保留了业务结构和来源。本节解释格式识别、解析路线、清洗与统一文档表示，并在[真实文档解析实验](labs/document-loading-and-cleaning.md)中观察正常格式、warning 和确定性失败。
9. **[Chunking、父子块与 Metadata](mechanisms/chunking-and-metadata.md)** · 可学习
   `DocumentElement` 保留原文结构，却未必适合检索。本节解释 Chunk 边界、overlap、父子块、稳定身份和 Metadata 怎样影响后续召回，在[Chunk 策略实验](labs/chunking-and-metadata.md)中只改变组织策略观察差异。
10. **[Embedding 表示与向量相似度](mechanisms/embedding-and-similarity.md)** · 可学习
    词面不同的表达需要进入同一表示空间才能比较，但相似不等于业务正确。本节建立向量、距离、空间身份和批量调用边界，并在[真实 Embedding 实验](labs/embedding-and-similarity.md)中验证同义、相邻主题和无关文本的分数方向。
11. **[Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索](mechanisms/lexical-retrieval.md)** · 可学习
    精确字段、接口名和版本号需要按词找到候选。本节解释倒排索引、查询词法、候选范围与排序，并在[从空库到第一次按词检索](labs/lexical-retrieval.md)中完成 PostgreSQL 准备、入库、日志和单变量对照。
12. **[pgvector、Dense Retrieval 与向量索引](mechanisms/vector-store-and-pgvector.md)** · 可学习
    成对相似度还不能在资料库中完成检索。本节把向量表示接入 pgvector，区分 Embedding 服务与向量存储，，区分 exact 与 ANN、距离与相似度、空间身份与 Metadata Filter，并在[pgvector 实验](labs/vector-store-and-pgvector.md)中比较 exact、HNSW 和查询计划。
13. **[多路召回与 RRF 融合](mechanisms/multi-retrieval-and-rrf.md)** · 可学习
    Lexical 和 Dense 各自返回有序候选，却没有可直接相加的统一分数。本节解释统一候选契约、排名融合和路线状态，并在[RRF 对照实验](labs/multi-retrieval-and-rrf.md)中手算贡献、改变候选数量并观察失败路线。
14. **[Top-k、阈值、Metadata Filter 与 Retrieval 诊断](mechanisms/retriever-contract.md)** · 可学习
    “数据库中存在”不等于最终 Retriever 一定返回。本节固定过滤、每路候选、阈值、融合和最终截断的控制顺序，并在[Retriever 诊断实验](labs/retriever-contract.md)中定位候选在哪一层消失。
15. **[Context Engineering：输入装配、预算与证据边界](mechanisms/context-engineering.md)** · 可学习
    Retriever 找到候选后，应用仍要决定模型本轮真正看到什么。本节区分候选、Context、Prompt 和 Citation Candidate，解释分区、去重与预算，并在[Context 实验](labs/context-engineering.md)中观察来源信息怎样保留或丢失。
16. **[可信生成、Sources、Citation Candidate 与证据不足](mechanisms/trusted-generation.md)** · 可学习
    模型写出来源编号仍不能证明结论获得支持。本节解释候选来源、模型声明和应用校验的分层，并在[可信生成实验](labs/trusted-generation.md)中观察正常证据、噪声和空证据下的结构化结果。

## 完成可信 RAG 与产品交付

这一单元补齐“候选来源”之后的支持性、充分性、API 和交互，让固定 RAG 从机制链变成真实产品。

17. **Citation 支持性校验** · 待编写
    已知 Citation ID 合法仍不代表引用内容支持对应结论。本节建立声明、证据片段和支持关系的校验边界，向证据充分性判断交付已验证 Citation。
18. **证据充分性、Refusal 与补充问题** · 待编写
    部分引用正确时，系统仍可能缺少形成强结论的关键事实。本节判断何时继续回答、何时拒绝，以及怎样把缺口转成用户能够补充的具体问题。
19. **AI Native 界面与不确定性表达** · 待编写
    业务用户需要同时看到结论、证据、缺口和真实失败。本节建立结果优先、证据可回查和不确定性可操作的最小界面原则，不提前定义运行状态，也不建设通用 AI 工作台。
20. **FastAPI、Review API 与错误契约** · 待编写
    固定 RAG 需要从脚本进入稳定产品入口。本节定义 Review API 的请求、结果、错误与依赖边界，区分业务证据不足和系统执行失败。
21. **Review 请求生命周期与状态契约** · 待编写
    一次评审不只有“成功或失败”。本节区分接收、处理、完成、证据不足、取消和失败状态，使 API、运行记录和界面共享同一事实。
22. **结构化风险、证据、Refusal 与补充信息交互** · 待编写
    本节把 Review API 接入最小 Web 工作台，让用户提交需求、查看风险和来源、回答补充问题并识别真实失败；不建设知识库运营后台。

## 建立最小比较能力

这一单元不建设完整质量平台，只建立后续每次增加复杂度都能回到的固定样例、运行记录和成本基线。

23. **[LLM Calling Harness 与最小回归](mechanisms/calling-harness-and-regression.md)** · 等待前置
    单次成功输出无法比较策略变化。本节固定 Case、Run Config 和 Record，让模型、Prompt、Schema 和结果可以在同一入口重复运行。
24. **[Token、成本、延迟与缓存边界](mechanisms/cost-latency-and-caching.md)** · 等待前置
    质量提升必须同时看到资源代价。本节记录 usage、成本、阶段耗时和缓存身份，区分真正节省调用与缓存掩盖实验变化。
25. **Evaluation Dataset 与最小 Golden Set** · 待编写
    探索样例不能直接承担验收。本节固定问题、期望来源、风险覆盖、无答案行为和数据集版本，区分 development 与 acceptance。
26. **直接 LLM、Lexical、Dense 与 RRF RAG 对比** · 待编写
    使用同一输入、生成模型、Prompt、Schema 和预算，只改变检索路线，比较质量、成本、延迟、空结果和失败，形成第一阶段基线。
27. **[第一阶段：固定 RAG 需求评审助手](project/stage-1-rag-application/rag-review-assistant.md)** · 等待前置
    回到项目篇完成固定 RAG 产品、真实 bad case、需求修改和冻结对照。阶段验收要求从资料身份追踪到 Citation，并能区分证据不足与系统失败。

# 第二阶段：Agent、Tools 与 Multi-Agent 系统

第二阶段回答：当查询、知识源、工具和协作步骤不能完全预先固定时，怎样让 Agent 动态行动，同时由应用控制权限、状态、停止、证据、恢复和评估？

第二阶段分为两个连续的学习里程碑，但不是两条互相替代的路线：

- **第 28–67 节：Agent 应用开发核心链路。** 从 LangChain Agent 出发，完成 Agentic RAG、Tool Runtime、LangGraph 的状态与恢复、MCP / File / Code、事件、运行界面和 LangSmith 观测评估的第一个可运行闭环。
- **第 68–101 节：高级 Agent 能力与完整体系。** 在核心闭环上继续学习 Agent Skills、Deep Research、Multi-Agent、A2A、复杂 Workflow、跨系统观测与回归。第 67 节是一个里程碑，不是课程终点；后续内容仍属于完整 Agent 开发知识范围。

开始第 28 节前，先阅读[第二阶段项目篇](project/stage-2-agent-system/agent-review-assistant.md)的贯穿场景、检查点和非目标。第二阶段继续复用“售后入口与订单状态”，增加 OpenAPI、Flutter / Web 客户端模型、配置、外部需求和定向验证，不更换基线案例。

框架不是附加在机制课程之外的第二条路线。框架能力本身进入机制篇：每个框架单元都以一个产品问题为入口，解释框架怎样实现当前能力、公开抽象怎样协作、应用还承担什么责任以及失败边界在哪里；具体安装、SDK 版本、完整调用、日志和调试进入配套实验。

## 真实 Agent 闭环

这一单元先用成熟框架跑通真实 Agent，再逐层补齐控制责任。LangChain 的 `create_agent` 本身构建在 LangGraph 运行时之上：本单元先只使用它的高层循环（模型决定—执行—回填—停止），30-38 节把责任收拢进 `agent_core`；43 节之后再下沉到 LangGraph 的显式状态、持久化和人工介入原语。全程都是同一个 Agent、同一套框架栈，只是从高层用法下沉到底层原语，不是先用一套运行时再迁移到另一套；最小原生 Loop 只作为对照，不发展成自研框架。

28. **从固定 RAG 到 Agent：选择结构与实现层次** · 待编写
    当固定程序无法预先决定查询、工具或停止路径时，本节先判断哪里需要模型动态决策，再建立一条责任图：Provider API 提供模型调用 → LangChain 的 `create_agent` 提供高层 Agent 与 Tool 组合 → 需要显式状态、持久化或人工介入时下沉到 LangGraph 原语 → `agent_core` 承接稳定契约与治理 → 产品领域组装承担评审策略。LangChain 与 LangGraph 是同一个运行时的两种使用深度，不是先后两套实现。学完应能为当前任务选择最小可行结构，并说明每一层解决什么问题。
29. **用 LangChain 跑通第一个真实 Agent** · 待编写
    使用真实模型和一个确定性只读 Tool，通过 LangChain 的 `create_agent` 跑通第一个真实 Agent，观察“模型决定—应用执行—结果回填—停止”的完整闭环。`create_agent` 本身已经运行在 LangGraph 之上，但本课只掌握它的高层循环，不涉及显式状态或持久化；需求评审助手同时用 `agent_core` 落地最小通用入口——`AgentRequest` / `AgentResult` 契约、一个最小 `StopReason` 枚举，以及只读 Tool 的最小执行边界，权限、审计和事件推迟到 30-38 节。配套实验通过直接调用框架和最小原生 Loop 对照框架承担的工作。
30. **Agent Harness：框架运行时与应用控制面** · 待编写
    框架可以提供循环和调度，但上下文、权限、预算、停止、事件和产品责任仍需应用定义。本节围绕同一个 `create_agent` 建立 Harness 的责任图，明确哪些交给 LangChain 运行时，哪些留给本地治理层——这是把课 29 的最小入口稳定化，不是为另一套运行时预先适配。
31. **Tool Call 与 Schema 校验** · 待编写
    模型生成的工具名和参数只是候选调用。本节解释 Tool Schema 怎样约束名称、参数和结果形状，以及它为什么仍不能代替权限和执行。
32. **Tool Runtime：执行生命周期、超时、取消与结构化错误** · 待编写
    本节跟踪一次 Tool Call 从参数校验、开始执行、超时或取消、结果转换到错误回填的完整生命周期，并说明框架 Tool 接口怎样映射到应用的稳定执行契约。
33. **Tool 权限、确认与审计** · 待编写
    工具可被调用不等于本次运行有权执行。本节建立读取、写入和外部行动的最小权限、人工确认与审计规则，使每次授权决定都能说明依据并被追踪。
34. **Prompt Injection 与应用控制边界** · 待编写
    文件、网页和外部 Tool Result 都可能包含诱导模型越权的文本。本节区分业务内容与控制指令，说明框架中间件可以辅助防护，但不能替代应用权限和参数校验。
35. **Retriever Tool：复用固定 RAG 契约** · 待编写
    固定 RAG 的 Retriever 已有稳定输入、输出和诊断。本节把它接入框架 Tool Runtime，保留来源身份、空结果和路线失败，不让 Agent 绕过检索契约。
36. **首个 Agent 闭环的最小运行事实** · 待编写
    可运行 Agent 还需要留下可解释事实。本节只引入首个闭环所需的运行身份、步骤、Tool 调用、预算、基础事件与停止原因，为恢复和界面提供共同事实。
37. **LangSmith Trace 与本地运行记录的关联** · 待编写
    本节使用 LangSmith 观察模型、Tool 与 Loop，并将托管 Trace 和本地运行记录 `RunRecord` 通过稳定身份关联。Trace 用于定位运行过程，不替代产品日志、数据治理或质量验收。
38. **Agent 运行契约与框架适配** · 待编写
    在 LangChain Agent、Tool Runtime 和最小运行事实已经跑通后，本节收束请求结果、Tool、Run State、停止原因、事件与 Trace 的通用契约，说明 `agent_core` 怎样组合并治理同一个由 LangGraph 驱动的运行时——当前只用到 LangChain 高层原语，后续下沉更多 LangGraph 原语时这套契约不变，以及评审领域组装为什么仍位于产品层。
39. **第一个受治理 Agentic RAG 项目检查点** · 待编写
    回到项目篇，用 `agent_core` 组合 LangChain Agent、唯一 Retriever 与一个确定性只读 Tool，实现可停止、可追踪、可解释失败的最小 Agentic RAG。这里的最小定义是：模型能够动态决定是否调用 Retriever Tool，并根据工具结果决定继续、回答或停止；Query Rewrite、Source Routing 和补检索属于后续深化。40-47 节仍在同一个 Agent 和同一套框架栈上继续，不是运行时搬家。使用同一 Case 与固定 RAG 比较，并验证产品领域行为仍位于 `review_assistant/agent/`。

## Agentic RAG 深化与可恢复运行

首个闭环成立后，再增强动态检索，并尽早下沉到 `create_agent` 底层已经运行的 LangGraph 状态、恢复和人工介入原语——这些能力此刻才被显式使用，但运行时从课 29 起就没有换过。这样后续 File Write、长研究和 Multi-Agent 不会建立在仅存于内存的脆弱循环上。

40. **Query Rewrite：原问题保留与改写边界** · 待编写
    用户问题不一定适合直接检索。本节解释改写目标、原问题保留、技术标识保护和无新增信息边界，并要求每次改写可回查。
41. **证据缺口驱动的检索决策** · 待编写
    Agent 先在已有 Retriever、不同查询表达和用户补充之间选择下一步。本节根据证据缺口建立“继续检索、换一种检索、请求补充或停止”的统一决策契约；后续 Search、Browser、File 接入时只扩展可用来源，不改变这套路由语义。
42. **固定 RAG 与 Agentic RAG 评估检查点** · 待编写
    使用相同问题、Retriever、模型和预算比较固定 RAG 与单 Agent，检查改写、路由、工具选择、空结果、追问、停止、成本和延迟；比较用于理解动态路线的适用边界，没有收益时保留固定路径。
43. **LangGraph State、Node 与状态转换** · 待编写
    本节把需要稳定执行的 Agent 步骤映射为显式 State、Node 和合法转换，区分模型决策与确定性节点。产品定义状态语义，LangGraph 负责图执行；这一步是把同一个 Agent 下沉到框架已有的图原语，不是切换到新运行时。
44. **Checkpoint、持久化与 Resume** · 待编写
    长任务和外部等待不能只存在进程内。本节使用框架 Checkpointer 保存可恢复状态，并处理输入、代码或配置版本变化后的恢复边界，不自行实现持久化引擎。
45. **Interrupt 与 Human-in-the-loop** · 待编写
    高风险动作需要把等待确认、批准、拒绝、修改和超时表达为正式状态。本节使用 LangGraph Interrupt 建立可恢复人工节点，而不是依赖聊天约定。
46. **重放安全：重试、执行记录与幂等** · 待编写
    图恢复或重放不能重复产生外部行动。本节区分纯计算、可重试读取和有副作用操作，用执行记录和幂等键决定一次操作能否安全重试；无法用幂等消除影响时，再把补偿作为显式业务边界。
47. **可恢复 Agent Runtime 项目检查点** · 待编写
    验收同一个 Agentic RAG 开始显式使用 LangGraph 的可恢复能力与人工节点——不是迁移到新运行时，而是深度从高层循环下沉到图原语。验证中断、恢复、取消、重复请求和框架版本身份，同时保持 `agent_core` 契约与产品输出不变。

## MCP 与通用工具

有了受治理且可恢复的 Runtime 后，再接入真实外部能力。MCP、Search、Browser、File 和 Code 各自解决不同问题，框架适配器负责连接，`agent_core` 继续负责内部治理。

48. **MCP 与内部 Tool Runtime 的责任边界** · 待编写
    本节从跨应用连接工具和资源的问题出发，区分 MCP Host、Client、Server、Function Calling 与内部 Tool Runtime 的责任。学完应能说明 MCP 怎样交换能力，以及连接后的权限、执行和产品语义为何仍由应用承担。
49. **MCP 能力发现与内部 Tool 映射** · 待编写
    使用官方 SDK 或成熟框架适配器发现 Tool、Resource、Prompt 等能力，再映射成内部 Schema、来源、权限和结构化结果；能力存在不等于可信或已获授权。
50. **MCP 请求生命周期与真实接入** · 待编写
    本节按明确规范修订跟踪发现、请求、结果、错误和取消。配套实验固定 SDK 与协议版本，接入真实只读 MCP，并观察版本、鉴权或能力不兼容怎样显式失败。
51. **Search Tool：发现候选来源** · 待编写
    Search 负责发现候选来源和查询方向，不负责证明网页内容。本节建立查询、结果、来源候选和重复域名边界，为 Browser 和 Deep Research 提供入口。
52. **Browser Tool：读取与定位来源** · 待编写
    Browser 打开候选页面并提取可回查内容。本节解释导航状态、页面来源、内容定位、动态页面和 Prompt Injection 边界，不把搜索摘要当作已读取证据。
53. **File Tool：受控读取与来源身份** · 待编写
    Agent 需要选择性读取 PRD、OpenAPI、客户端模型和配置，而不是把整个目录塞进 Context。本节建立获准根目录、路径校验、内容哈希、定位、大小限制和读取错误。
54. **MCP 与只读外部工具项目检查点** · 待编写
    接入真实只读 MCP，用 Search / Browser 回查公共来源、File 追踪多端资料，验证所有结果都经过同一 Tool 治理、事件和 Trace 边界。
55. **File Tool：写入、暂存、确认与幂等** · 待编写
    用户需要可交付报告，但原始文件不能被 Agent 任意覆盖。本节只允许向运行级暂存区原子写入，并复用 Interrupt、确认、版本冲突和幂等机制。
56. **Code Tool：准入判断、任务契约与专用工具边界** · 待编写
    解析 OpenAPI 应优先使用专用 Validator，只有需要运行项目已有脚本或测试时才进入 Code Tool。本节定义允许任务、命令引用、输入快照和结果契约。
57. **Code Tool：执行沙箱、资源、超时与副作用** · 待编写
    本节解释只读输入、隔离输出、默认禁网、环境白名单和 CPU、内存、进程、时间限制，并区分非零退出、超时、取消和安全阻止。
58. **副作用工具与定向验证项目检查点** · 待编写
    用受确认 File Write 交付评审产物，并用受控 Code Tool 验证至少一项接口或客户端契约差异；重复与恢复不能造成二次写入或越权执行。

## 状态、记忆、事件与产品运行

最小 Run State 已随首个 Agent 建立，本单元继续区分会话、记忆和业务知识，并把事件一致地传到产品界面。

59. **Run State、Conversation、Memory 与业务知识边界** · 待编写
    本节区分当前运行事实、会话消息、压缩后的短期记忆、长期偏好和可引用业务知识，防止框架消息历史、摘要或偏好冒充证据。
60. **短期记忆、摘要与 Context Budget** · 待编写
    长会话不能无限进入模型。本节解释窗口、摘要、保留事实和预算分配，并说明摘要怎样失真、何时应回查原消息。
61. **长期偏好记忆、确认与治理** · 待编写
    本节只保存用户明确确认的跨会话偏好，记录来源、作用域和版本，支持查看、更新、删除和关闭；偏好不能冒充业务证据。
62. **Token Stream 与 Event Stream 的边界** · 待编写
    Token 只表示文本增量，Agent 还需要表达 Tool、证据、等待、错误和停止。本节建立两类 Stream 的边界和组合方式。
63. **Agent Event 类型、身份、顺序与版本** · 待编写
    本节完善事件信封、`run_id`、序号、时间、事件类型和版本，使框架、Tool、产品后端和 UI 能解释同一运行事实。
64. **取消、重复消费、迟到结果与一致性** · 待编写
    在选择传输方式前，先定义取消传播、重复事件、顺序和迟到 Tool 结果的处理，防止 UI、Run State 与副作用记录分叉。
65. **SSE 传输、断线与重连** · 待编写
    事件协议确定“传什么”，SSE 只负责“怎样传”。本节解释连接、心跳、游标和重连边界，不把传输成功当作业务完成。
66. **从 Agent Event 到运行界面** · 待编写
    本节把事件还原为可操作界面状态，区分运行、等待补充、等待确认、部分完成、取消、失败和完成，并展示证据与 Tool 过程。
67. **Agent 应用开发核心链路检查点** · 待编写
    串联 LangChain Agent、Agentic RAG、Tool Runtime、LangGraph State / Checkpoint / Interrupt、MCP / File / Code、Event / SSE、运行界面以及 LangSmith Trace / Dataset / Experiment / Evaluator 的最小闭环。使用固定样例验证工具选择、参数、停止、事件还原、真实错误和固定 RAG 对照；完成本节表示核心 Agent 应用开发链路已经闭环，68-101 节继续学习更高级、更完整的 Agent 体系。

## Agent Skills 与高级 Agent 体系

第 67 节完成核心 Agent 应用开发里程碑后，继续学习 Agent Skills、Deep Research、Multi-Agent、A2A 和复杂 Workflow。它们不是第 67 节的前置条件，但都是建立完整 Agent 知识和体系的重要内容，不能因为核心闭环完成就停止学习。

Skills 在 Agent Loop、Context Budget 和 Tool 治理都成立后加入。它不依赖先掌握 MCP，也不能因包含脚本而绕过 Runtime。

68. **Agent Skills 与 Prompt、Tool、MCP 的边界** · 待编写
    Skill 提供某类任务的可复用说明、资源和流程知识，但不等于 Prompt、可执行 Tool 或外部连接协议。本节建立四者的职责关系和准入判断。
69. **Skill 发现、匹配与渐进加载** · 待编写
    Skill 先用最小元数据声明用途和适用任务，匹配后才加载说明与必要的参考资料、脚本或资产。本节跟踪“发现—匹配—激活—按需读取”的数据流，区分稳定格式、客户端扩展和 Context Budget。
70. **Skill 脚本的受治理执行** · 待编写
    Skill 可以携带脚本，但脚本仍须转换为受控任务并经过 Tool Runtime、权限确认、沙箱和审计。本节建立 Skill 与资源版本、运行输入、结构化结果和兼容性失败的关联，使按需加载不会变成额外执行权限。
71. **领域 Skill 项目检查点** · 待编写
    为多端契约评审建立按需加载的领域 Skill，验证未激活时不占用无关 Context、激活后不改变 Tool 权限，并与普通 Prompt 方案做同任务对照。

## Deep Research

Deep Research 只处理普通 RAG 或一次网页回查不足的问题。本单元围绕研究任务契约、计划、证据账本、来源判断、冲突、综合和停止形成完整闭环。

72. **Deep Research 的启动条件、任务契约与边界** · 待编写
    判断何时使用内部 RAG、单次 Search / Browser，何时值得启动 Research，并固定研究问题、期望输出、允许来源、预算和非目标。
73. **Research Planning：拆解可验证子问题** · 待编写
    一个复杂问题需要拆成可验证子问题，而不是生成装饰性计划。本节建立子问题、依赖、预期证据和完成条件。
74. **迭代搜索、进度检查与重新规划** · 待编写
    搜索结果会暴露新术语、缺口和无效方向。本节解释查询怎样迭代、进度怎样更新，以及何时调整计划而不是重复搜索。
75. **Evidence Ledger：积累可回查证据** · 待编写
    Research 需要把发现保存为可去重、可回查的证据记录。本节建立来源身份、定位、声明、支持关系、获取时间和研究问题关联。
76. **来源质量、权威性、独立性与重复来源** · 待编写
    多个链接可能只是转载同一弱来源。本节判断来源权威性、时效、独立性和重复关系，不用来源数量代替证据强度。
77. **交叉验证、冲突证据与不确定性** · 待编写
    可信来源也可能基于不同版本或条件给出冲突结论。本节保留冲突、适用条件和不可裁决状态，决定继续研究还是交给用户确认。
78. **从证据账本到带来源综合** · 待编写
    本节把证据账本转成结构化结论，要求每个外部事实能够回到来源，并区分来源支持、合理推断和未解决缺口。
79. **覆盖、预算与停止条件** · 待编写
    根据子问题覆盖、新增证据、冲突、成本、时间和硬上限决定完成、部分完成、等待补充或达到上限。
80. **Deep Research 评估与项目检查点** · 待编写
    在外部 SDK 兼容性或版本要求场景中，比较一次网页回查与完整 Research 的来源覆盖、冲突处理、Citation、成本、恢复和停止质量。

## Multi-Agent 基线

只有单 Agent 基线暴露真实责任冲突或并行收益后才拆分。本单元先用框架已有的子 Agent、路由和委派原语建立本地协作，不把一个 Prompt 机械拆成多个 Prompt。

81. **Multi-Agent 的拆分条件** · 待编写
    判断客户端影响、接口契约和证据审查是否具有独立责任与收益，区分并行子任务、普通函数和真正 Agent 角色。
82. **角色、上下文、工具与输出契约** · 待编写
    每个 Agent 必须说明负责什么、不负责什么、能看到什么、能调用什么以及交付什么，避免共享全部上下文后产生角色幻觉。
83. **框架内的 Multi-Agent 协作模式** · 待编写
    本节比较框架可直接使用的协作原语，跟踪任务怎样被路由、委派、拒绝、重派和回收；产品仍必须定义角色契约与最终责任。
84. **共享状态、私有上下文与证据** · 待编写
    Agent 可以共享任务和已批准证据，但私有上下文和工具权限不能无边界扩散。本节建立共享、隔离和状态映射规则。
85. **并行、依赖、取消与失败隔离** · 待编写
    本节处理可并行任务、依赖任务、全局取消和局部失败，防止一个 Worker 失败后汇总器把缺失结果解释为无风险。
86. **结果合并、证据归属与冲突裁决** · 待编写
    不同 Agent 的风险项可能重复、冲突或引用不同版本。本节保留来源与责任人，区分可自动合并和必须暴露的分歧。
87. **Multi-Agent 基线、运行观测与项目检查点** · 待编写
    使用同一需求、工具、数据和预算比较单 Agent 与 Multi-Agent 的质量、成本、延迟、证据一致性和失败定位，并用运行界面展示角色、进度、局部失败、证据和冲突。收益不足时保留单 Agent，不以角色数量证明能力。

## A2A 互操作

A2A 是独立协议与 SDK 生态，不是 LangChain 或 LangGraph 自带能力的别名。只有本地 Agent 契约稳定后，才把同一责任扩展到远程 Agent。

88. **A2A 的角色、适用边界与本地协作差异** · 待编写
    本节从跨进程或跨系统委派任务的问题出发，区分 A2A Client、Remote Agent、本地 Delegation 与 MCP。学完应能判断什么时候需要互操作协议，什么时候继续使用进程内框架协作。
89. **Agent Card 与远程能力发现** · 待编写
    Agent Card 声明远程 Agent 的身份、能力、端点和安全要求。本节建立发现、筛选与准入边界，并明确其中的能力 Skill 描述不等于 Agent Skills 文件格式或本地执行授权。
90. **A2A 消息、任务与产物模型** · 待编写
    建立交互消息、可跟踪任务、内容片段和任务产物的关系，说明对话内容、执行状态和可交付结果分别由哪种对象承载。
91. **A2A Task 生命周期、进度、输入、取消与错误** · 待编写
    跟踪任务提交、执行、等待输入或鉴权、完成、失败、拒绝和取消，并区分任务状态、流式更新和传输连接状态。
92. **A2A 协议绑定、安全、版本与真实 SDK 接入** · 待编写
    区分抽象数据模型与具体传输、鉴权和版本协商。配套实验固定官方规范与 SDK 版本，验证两个实现能否一致解释任务、产物、状态和错误，并把远程状态映射到既有运行事件与界面。
93. **本地 Delegation 与远程 A2A 对照检查点** · 待编写
    将一个已有责任在本地框架委派与远程 A2A 路径间做同契约对照，验证互操作没有改变证据归属、权限、错误和最终责任。

## 必要 Workflow 深化

LangGraph 的恢复原语已经前置。本单元只处理 Research 或多 Agent 出现的复杂图组合，不建设低代码画布或第二套运行时。

94. **复杂图、Subgraph 与 Agent / Workflow 组合边界** · 待编写
    判断何时把固定子流程建成 Subgraph、Workflow as Tool 或 Agent 内部节点，明确状态所有权、循环所有权和输入输出契约。
95. **可恢复 Workflow 项目检查点** · 待编写
    将 Research 或协作中确实需要等待、恢复和确认的片段放入最小图，验证中断、拒绝、重试、恢复和重复请求不会破坏产品结果。

## 质量收束与最终交付

质量证据已经贯穿各检查点；这一单元统一跨框架运行关联、版本、回归、自动与人工判断以及 bad case 流转，不建设完整评估平台。

96. **结构化日志、Metrics 与事件关联** · 待编写
    让请求、模型、检索、Tool、Agent、状态和错误能够通过稳定身份关联，同时区分面向用户的结果和面向调试的诊断。
97. **跨系统 Trace 与运行关联** · 待编写
    深化 LangSmith Trace、本地 RunRecord、LangGraph Checkpoint 和 A2A Task 的关联，说明 Trace 能帮助定位什么、不能替代什么质量判断，并形成跨系统运行身份与链接规则。
98. **版本化实验与回归** · 待编写
    固定模型、Prompt、Schema、Retriever、Tool、Skill、框架、Workflow 和数据版本，建立运行身份、实验对照和回归规则，防止新结果覆盖旧证据。
99. **LLM-as-Judge 的人工校准** · 待编写
    自动 Judge 可以扩大评估规模，但会继承模型偏差。本节定义适用任务、评分契约、校准样例和人工复核，不让 Judge 替代产品验收责任。
100. **从 Bad Case 到反馈闭环** · 待编写
    把线上失败、人工反馈和研究缺口转成可复现 Case，经过分类、修复、回归和版本记录进入质量闭环，而不是只保存聊天截图。
101. **[第二阶段：Agent 协作需求评审系统](project/stage-2-agent-system/agent-review-assistant.md)** · 等待前置
    完成框架驱动的 `agent_core`、Agentic RAG、LangGraph 恢复、真实 MCP、Search、Browser、File、Code、Agent Skills、Deep Research、Multi-Agent、A2A、运行界面和统一回归。最终产品必须在同一多端契约案例上展示证据、权限、停止、冲突、恢复以及与固定 RAG、单 Agent 等基线的可解释差异。

完整能力范围、扩展知识和实现位置见[知识地图](knowledge-map.md)。
