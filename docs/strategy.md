# AI Native 前端与 AI 应用闭环战略

这份文档用于沉淀本仓库长期有效的学习定位、职业判断和能力建设方向。

它不记录实时学习进度，也不作为简历文案，而是用于反复校准：为什么学习 AI 应用开发、学到什么程度、如何和既有前端 / Flutter / 客户端经验结合。

## 背景

当前基础主要来自前端、Flutter、跨端客户端和复杂业务交付：

- Web 前端、Flutter、H5、Uniapp、React 等多端开发经验。
- 金融交易 App、行情、K 线、长连接、交易链路等真实业务经验。
- 混合开发、JS Bridge、Flutter 插件、原生能力接入、监控上报、动态化、工程化等经历。
- AI Coding、研发提效、AI Agent 辅助开发等方向的探索。

这些经历说明，当前最强的基础不是纯后端、算法或 AI Infra，而是复杂客户端工程、跨端交付、AI 产品交互和研发提效工具落地。

## 当前优势

- 前端与跨端客户端工程能力。
- 产品与交互设计理解。
- 复杂业务交付经验。
- 金融业务场景经验。
- 工程化、组件化和多端适配经验。
- 能把能力做成可交互、可展示、可交付的产品体验。

## 当前短板

- 后端体系化能力不足。
- Python 与 FastAPI 工程经验仍需积累。
- 对模型能力边界、失败模式和评估方法理解不够系统。
- RAG / Agent / Workflow 的工程经验不足。
- 生产级 AI 应用的观测、调试、回归和成本治理经验不足。

## 职业定位

当前主定位是：

- AI Native 前端
- AI 应用前端工程师
- 高级跨端客户端 + AI 应用闭环能力

更准确的描述是：

> 以高级 Flutter / 跨端客户端为主场，以 LLM、RAG、Agent、FastAPI 和评估观测能力补齐 AI 应用闭环，把 AI 能力做成可用、可控、可展示、可交付的产品体验。

当前不以这些方向作为主目标：

- 纯 AI 应用后端工程师
- 大模型算法工程师
- AI Infra 工程师
- 检索平台工程师
- Agent 平台工程师

这些能力可以学习和理解，但不是现阶段最适合正面竞争的主战场。

## 学习目标

长期目标是建立完整 AI 应用闭环能力，并把 RAG、Agent、评估观测和产品体验作为核心主线。

基础目标：

- 能使用 Python / FastAPI 构建 AI 应用后端。
- 能稳定调用多平台 LLM API，并理解供应商差异、成本、延迟和能力边界。
- 能设计 Prompt、结构化输出、上下文管理和模型调用 harness。
- 能通过最小实现、框架实现、评估观测和项目收敛验证一个能力是否真正掌握。

RAG 与知识系统目标：

- 能实现 RAG 主链路，并能处理文档、索引、检索、引用、拒答和评估问题。
- 能理解 chunk、metadata、embedding、retrieval、rerank、context construction、context compression 对效果的影响。
- 能设计短期记忆、长期记忆、记忆写入、记忆检索、遗忘机制和反馈回流。
- 能把 RAG 从“能回答”推进到“有依据、可评估、可治理、可迭代”。

Agent 核心目标：

- 能判断 Chain、Workflow、单 Agent、Multi-Agent 的适用边界。
- 能设计 Tool Schema、Tool Runtime、权限确认、失败兜底和人工接管。
- 能实现 Agent Loop、任务分解、工具调用、状态流转和可干预工作流。
- 能理解 Agentic RAG、Deep Research、Memory、Multi-Agent、Agent Skills、MCP / A2A 等能力之间的关系。
- 能用 LangGraph 构建可观测、可回归、可调试的 Agent 工作流。
- 能评估 Agent 的工具轨迹、任务完成率、成本、延迟和安全边界。

产品化目标：

- 能建立 evaluation、observability、trace、回归测试和失败案例回流机制。
- 能把 AI 执行过程、证据链、风险提示、工具调用和人工协作状态做成前端 / 客户端体验。
- 能围绕真实业务问题完成可运行、可展示、可评估、可迭代的 AI 应用项目。

## 能力路线

当前能力路线按七层组织。七层不是彼此割裂的课程边界，而是从基础能力、知识系统、Agent 系统、评估观测到项目作品的递进关系。

这份文档需要长期维护每一层的学习目标、阶段边界和与当前主项目的关系。企业级 AI 应用平台的完整能力地图放在 [ai-application-platform.md](ai-application-platform.md)，但它是远期方向参考，不替代这里的课程路线。

### 1. 应用工程基础层

这一层解决 AI 应用开发的基础工程能力。

- Python
- FastAPI
- HTTP / JSON / SSE
- 异步任务基础
- 配置与密钥管理
- 日志与异常处理
- 基础测试
- 本地开发、Docker 与部署认知

这一层的目标不是成为纯后端专家，而是能独立写出 AI 应用后端的最小服务。

### 2. 模型交互与上下文工程层

这一层解决如何稳定、可控、低成本地使用模型。

- 多平台 LLM API
- OpenAI SDK 风格封装
- Provider 抽象与模型切换
- Prompt Engineering
- Structured Outputs
- 流式输出
- 多轮对话
- Context Engineering
- 上下文裁剪、摘要与压缩
- Token、成本、延迟控制
- Prompt Caching
- Harness Engineering
- 输出校验、重试、降级
- 最小评估样例与调用回归
- Function Calling 的 API 形态与边界认知

Function Calling 在这一层只学习 API 形态和基本概念；工具系统、运行时、权限、Agent loop 放到 Agent 层系统学习。

### 3. RAG、LangChain 与单 Agent 知识助手层

这一层解决外部知识如何进入模型上下文，并进一步把固定 RAG 做成可用的单 Agent 知识助手。

RAG 不应该和 Agent 完全割裂。固定 RAG 负责知识接入、检索、引用、拒答和评估；单 Agent 负责在知识助手场景中进行查询改写、知识源选择、检索质量判断、补检索和追问补全。学完这一层，需求评审助手应该已经是一个完整的初级 AI 应用，而不是等待 Agent 课程补完的半成品。

- RAG 问题空间与架构边界
- LangChain for RAG 基础
- Document / Loader / TextSplitter
- 文档加载与清洗
- 文档结构保留
- Chunk 策略
- Metadata 设计
- Knowledge Governance
- 增量更新、删除一致性、版本管理、权限过滤
- Embedding
- Vector Store
- Retriever
- Hybrid Search
- Rerank
- Query Rewrite
- Knowledge Source Routing
- Context Construction
- Context Compression
- Sources / Citation
- Refusal
- Structured RAG Output
- RAG Evaluation
- Bad Case 回流
- 短期记忆
- 长期记忆
- 记忆写入策略
- 记忆检索策略
- 遗忘机制
- 用户反馈回流
- Retriever as Tool
- 单 Agent RAG 助手

这一层正式学习 LangChain 的 RAG 常用抽象，包括 Document、Loader、TextSplitter、Embeddings、VectorStore、Retriever、PromptTemplate、OutputParser、Runnable / LCEL 基础组合、Retriever as Tool 和简单单 Agent 知识助手。

这一层不深入复杂 Tool Runtime、LangGraph 状态机、Checkpoint / Interrupt、Multi-Agent、Deep Research、MCP / A2A。这些进入 `04_agent` 系统展开。

### 4. Agent 工作流与工具系统层

这一层解决模型如何从“会回答”升级为“会判断、会调用工具、会执行多步骤任务、会进入可控工作流”。

`03_rag` 中的单 Agent 知识助手解决的是 RAG 项目完整性；`04_agent` 解决的是 Agent 系统能力，包括工具运行时、权限确认、状态流转、LangGraph 工作流、复杂任务执行、多 Agent 协作和开放协议。

- Function Calling 深入
- Tool Calling
- Tool Schema 设计
- Tool Runtime
- 工具参数校验
- 工具权限、确认与审计
- Agent Loop
- ReAct
- Planning
- Reflection
- Task Decomposition
- LangChain Tool
- LangChain Agent Patterns
- LangGraph State / Node / Edge
- Conditional Edge
- Checkpoint
- Interrupt
- Human-in-the-loop
- Workflow 编排
- Agentic RAG 深化
- Deep Research Workflow
- Deep Agent
- Multi-Agent
- Supervisor / Worker 模式
- Agent Memory 与 Context 管理
- MCP
- A2A
- Agent Skills
- 多模态 Agent
- Browser / Code / File / Search 等工具型 Agent
- Agent 安全边界

这一层的核心不是一上来追求复杂 Agent，而是能判断什么时候用 Chain、Workflow、单 Agent、多 Agent，以及如何让 Agent 的工具调用、状态变化和人工介入可控。

### 5. 评估、可观测与质量工程层

这一层解决 AI 应用如何持续迭代，而不是靠手感调 Prompt、调检索、调 Agent。

`04_agent` 学工作流怎么设计和实现；`05_eval_observability` 学工作流怎么评估、追踪、回归和优化。这里不再承担 LangChain 主学习，而是覆盖 RAG、Agent、Workflow 和项目的质量工程。

- Evaluation Dataset
- Golden Set
- RAG Retrieval Evaluation
- RAG Generation Evaluation
- Citation Evaluation
- Refusal Evaluation
- Bad Case Management
- Agent Trajectory Evaluation
- Tool Call Evaluation
- Workflow Evaluation
- Human Review Evaluation
- Observability
- Trace
- Span
- Prompt / Retriever / Tool / Graph 版本对比
- 成本统计
- 延迟统计
- 命中率
- 失败率
- 回归测试
- LLM-as-Judge
- 人工评审样本
- 线上反馈闭环

这一层要能回答：RAG 改了 chunk 策略有没有变好，换 embedding 模型有没有变好，Agent 工具调用轨迹是否合理，LangGraph 工作流哪一步失败了，哪些 bad case 应该回流到知识库、Prompt、Retriever、Tool 或 Graph 设计。

### 6. AI Native 前端、运行态 UI 与基础工程层

这一层解决 AI 应用前端如何承接模型流式输出、RAG 证据链、Agent 工具轨迹、Workflow 运行态、多模态任务和企业平台配置，同时补齐当前项目所需的基础后端工程能力。

它不是重新学习传统前端，也不是转向纯后端工程，而是围绕 AI 应用特有的协议、状态、运行时、动态 UI、Agent UX、多模态交互、基础服务和本地部署能力沉淀 AI Native 应用能力。

- SSE / Stream 前后端状态同步
- AI Response State Machine
- Event Stream / Tool Stream / Workflow Stream
- JSON Schema / UI Schema 交互协议
- Structured Output 到动态 UI 的映射
- Generative UI / Dynamic Components
- Flutter GenUI / Web GenUI 思路
- Agent UI / UX
- Tool Call Timeline
- Plan / Action / Observation 展示边界
- Workflow Runtime UI
- Interrupt / Resume / Retry / Cancel
- RAG Knowledge Workbench
- Agent Management Console
- MCP / Tool Config UI
- Realtime Voice Interaction
- Multimodal Document Agent UI
- PDF / PPT / Word / Image 文件智能交互
- Eval / Labeling / Feedback UI
- Enterprise AI Frontend Architecture
- Redis / 后台任务基础
- Docker / docker-compose 本地部署
- PostgreSQL / pgvector 项目化认知

这一层是当前职业定位的差异化优势：不是普通前端页面能力，也不是完整后端平台能力，而是把 LLM、RAG、Agent、Workflow、Eval 和基础工程能力变成可配置、可运行、可干预、可追踪的 AI 产品体验。

### 7. 项目平台化与作品化层

这一层解决如何把前面能力收敛为一个长期主项目，并逐步形成可展示、可复盘、可继续演进的作品。

当前主项目是需求评审 RAG 助手。现阶段不并行维护第二项目，避免学习战线过长。

- 需求评审 RAG 助手
- 需求文档、业务规则、接口文档、会议纪要和历史评审记录
- 固定 RAG 问答
- Sources / Refusal / 结构化评审输出
- 检索评估与 bad case 回流
- 单 Agent 查询改写、知识源选择和追问补全
- Workflow / Human-in-the-loop
- AI Native 工作台
- 共享 package 与平台底座
- 企业级 RAG 知识库雏形
- 基础评估、观测和质量面板
- 基础权限、审计和成本意识
- Docker Compose + PostgreSQL / pgvector + Redis
- 部署、演示与作品化表达

项目层不承担所有知识点的第一次学习，而是负责把 LLM、RAG、Agent、Workflow、评估观测、AI Native 前端和基础设施组合成可运行、可展示、可讲述的完整闭环。

## 课程主线

后续课程按新的能力路线组织：

```text
course/
├── 00_archive/
├── 01_python/
├── 02_llm/
├── 03_rag/
├── 04_agent/
├── 05_eval_observability/
├── 06_ai_native_frontend/
├── 07_projects/
└── 99_foundation/
```

`source/` 目录可以与课程主线保持同构：

```text
source/
├── 00_archive/
├── 01_python/
├── 02_llm/
├── 03_rag/
├── 04_agent/
├── 05_eval_observability/
├── 06_ai_native_frontend/
├── 07_projects/
└── 99_foundation/
```

`01_python` 和 `02_llm` 代表已经完成或需要补强的基础层。`02_llm` 后续应覆盖模型交互与上下文工程，不只是 API 调用入门。

`03_rag` 是 RAG、LangChain 与单 Agent 知识助手主线。它不只学习固定 RAG，也要把需求评审助手做到可引用、可拒答、可评估，并具备查询改写、知识源选择、检索质量判断和追问补全等单 Agent 能力。

`04_agent` 是 Agent 工作流与工具系统主线，系统学习 Function Calling 深入、Tool Runtime、Agent Loop、LangChain Agent、LangGraph Workflow、Human-in-the-loop、Agentic RAG 深化、Deep Research、Multi-Agent、Agent Skills、MCP 和开放 Agent 协议。

`05_eval_observability` 是评估、可观测与质量工程主线。它既服务 RAG，也服务 Agent、Workflow 和项目，重点是 golden set、trace、bad case、回归测试、成本延迟指标和线上反馈闭环。

`06_ai_native_frontend` 是 AI Native 前端、运行态 UI 与基础工程能力主线，承接前端 / Flutter / 跨端优势，也补齐 Redis、Docker、后台任务、本地部署等项目必需的后端基础认知。后续目录名可以评估是否调整为 `06_ai_native`。重点沉淀 SSE 状态同步、Schema 驱动交互、Agent UX、Workflow Runtime UI、知识工作台、评测反馈界面和 AI 应用工程化能力。

`07_projects` 围绕需求评审 RAG 助手收敛，不再无限扩展零散项目。项目代码和文档可以逐步吸收 `02_llm`、`03_rag`、`04_agent`、`05_eval_observability`、`06_ai_native_frontend` 的阶段成果。

`99_foundation` 是非主线知识补充区。LLM 原理、微调、私有化部署、LangChain 底层抽象等内容只在 RAG / Agent / 项目学习中遇到具体理解障碍时回看，不作为前置课程。

`00_archive/` 中保留的早期课程式文档和代码不作为当前主线，后续新内容以 `docs/` 下当前规范为准。

## 文档与代码关系

文档建设优先于代码堆叠，但代码仍然是学习闭环不可缺少的部分。

后续不再要求每个章节都对应多个脚本。学习链路保留为：

```text
真实问题
-> 基础原理
-> 最小实现
-> 主流框架实现
-> 失败分析与能力边界
-> 评估观测
-> 小项目实战
-> 项目收敛
```

更合适的代码组织方式是：

- 专题文档负责讲清真实问题、基础原理、实现路径、失败边界和项目入口。
- 示例代码负责验证关键机制，不追求覆盖每一个知识点。
- Package 负责沉淀可复用能力，例如 `llm_client`、`rag_core`、`rag_eval`、`agent_core`。
- Demo 负责验证单个能力组合，例如最小 RAG、检索对比、单 Agent 查询改写。
- App 负责收敛为完整项目，当前主项目是需求评审 RAG 助手。

代码可以少而精，但必须能运行、能解释、能观察关键输出。

## 基础设施策略

服务端通用知识需要在项目中体现，但不单独展开成后端运维大课。

P0 必须进入项目：

- FastAPI
- PostgreSQL / pgvector
- Docker / docker-compose
- 环境变量与密钥管理
- 文件上传与存储目录
- 基础日志
- 后台任务：文档解析、索引构建、批量评估
- API 分层：chat、rag、agent、eval、admin

P1 在项目推进中逐步加入：

- Redis：缓存、任务状态、stream 状态、限流、会话短期状态
- 后台任务队列：Celery / RQ / arq 等方案择一认知
- 对象存储：文档、PDF、解析结果、导出报告
- Nginx / 反向代理认知
- 基础监控：请求耗时、模型调用成本、失败率
- Docker Compose 一键启动：API + DB + Redis + Vector Store

P2 保持认知，不作为当前必做项：

- Kubernetes
- CI/CD
- 灰度发布
- 多租户
- 权限中台
- 完整告警体系

当前优先使用 PostgreSQL / pgvector，而不是把 MySQL 作为主线数据库。Kubernetes 只做部署形态认知，不作为学习阶段的项目必要实现。

## RAG / Agent 的学习定位

学习 RAG 和 Agent 不是为了放弃前端，转向纯 AI 后端岗位。

RAG 和 Agent 也不应该被理解成完全割裂的两门课。`03_rag` 负责把固定 RAG 做成可用的单 Agent 知识助手；`04_agent` 再系统展开工具运行时、工作流、LangGraph、Deep Research、多 Agent 和开放协议。

它们的作用是补齐 AI 应用主链路，让前端能力不只停留在“接接口和做页面”，而是能理解：

- 模型为什么会输出不稳定。
- Prompt、结构化输出和上下文工程如何影响前端体验。
- SSE 流式响应如何设计交互。
- RAG 的 sources、metadata、score 如何展示为证据链。
- 记忆写入、记忆检索和上下文压缩如何影响多轮体验。
- Agent 工具调用过程如何可视化。
- Deep Research、多模态 Agent、Agent Skills 和开放协议适合解决什么问题。
- 什么时候需要人工确认、拒答、降级和重试。
- 如何通过评估集判断 AI 应用效果有没有变好。

## 项目方向

长期项目围绕需求评审 RAG 助手展开。

### 需求评审 RAG 助手

这个项目服务于企业内部需求评审和知识辅助场景，围绕 PRD、业务规则、接口文档、会议纪要和历史评审记录，输出带依据的问答、结构化评审结果、缺失信息追问和风险提示。

它主要用于打牢 RAG、LangChain 与单 Agent 知识助手能力，可以逐步演进：

- V0：固定 RAG 问答。
- V1：Sources / Refusal / 结构化输出。
- V2：检索评估与失败案例回流。
- V3：单 Agent 增强，包括查询改写、知识源选择、追问补全。
- V4：可控工作流与人工确认，包括风险审核、状态流转和人工介入。
- V5：前端工作台，包括证据链、风险提示、人工反馈和知识运营入口。

这个项目自然承接：

- LLM API
- Context Engineering
- RAG
- FastAPI
- Structured Outputs
- Sources / Citation
- Refusal
- RAG Evaluation
- Frontend Workbench
- 单 Agent 增强
- LangChain RAG
- Workflow / Human-in-the-loop

## 长期方向

最终路线不是“前端转 AI 后端”，而是：

> AI Native 前端 + AI 应用闭环能力。

核心竞争力来自三件事的结合：

1. 复杂前端 / 客户端 / 跨端工程能力。
2. LLM / RAG / Agent / Workflow / Evaluation / Observability 的应用链路理解。
3. 能把 AI 能力产品化、可视化、可评估、可交付。
