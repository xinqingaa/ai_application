# AI Native 前端与 AI 应用闭环战略

这份文档是本仓库长期定位、学习目标和项目阶段的唯一真源。

它回答三个问题：

1. 为什么学习 AI 应用开发。
2. 最终要完成什么。
3. 两个阶段分别建立什么核心能力。

它不规定课程正文模板、代码目录细节和单节课的阅读顺序；这些分别由
[learning-guide.md](learning-guide.md) 和 [标准学习路径](../course/learning-path.md) 负责。

## 1. 背景与定位

当前能力基础主要来自前端、Flutter、跨端客户端和复杂业务交付：

- Web 前端、Flutter、H5、Uniapp、React 等多端开发经验。
- 金融交易 App、行情、K 线、长连接、交易链路等复杂业务经验。
- 混合开发、JS Bridge、Flutter 插件、原生能力接入、监控上报和工程化经验。
- AI Coding、研发提效和 AI Agent 辅助开发实践。

这些基础决定了本仓库的主方向不是纯算法、纯 AI Infra 或纯后端平台，而是：

> 以高级前端、Flutter 和跨端客户端能力为主场，补齐 LLM、RAG、Agent、Tool、Multi-Agent、必要 Workflow、评估观测和 AI Native 产品能力，形成完整 AI 应用闭环。

对应的职业定位是：

- AI Native 前端工程师。
- AI 应用前端工程师。
- 高级跨端客户端工程师 + AI 应用闭环能力。

需要补齐的核心短板包括：

- Python、HTTP、JSON、FastAPI 与配置等 AI 应用工程基础。
- 模型调用、上下文工程和模型能力边界。
- RAG、知识生产、检索与可信生成。
- Agent Harness、Tool Runtime、MCP、Agent Skills 和 Agentic RAG。
- Deep Research、Multi-Agent、A2A 与必要 Workflow 控制。
- 评估、观测、回归与 bad case 治理。
- AI 执行过程、证据和状态的产品化表达。

## 2. 唯一长期主目标

本仓库只维护一个主项目：

> **需求评审助手：从固定 RAG 应用演进为以 Agentic RAG 为知识基础的多 Agent 协作系统。**

项目围绕 PRD、业务规则、接口文档、客户端规则、会议纪要和历史评审记录，完成：

```text
真实资料进入系统
→ 知识解析、组织、检索与可信生成
→ 固定 RAG 需求评审应用
→ Agent Harness 与受治理 Tool Runtime
→ 单 Agent 动态改写、选源、检索、追问和停止
→ MCP、Agent Skills 与 Browser / Search / Code / File Tool
→ Deep Research 类型的多步研究任务
→ Multi-Agent 分工、并行、汇总与冲突处理
→ A2A 与必要 Workflow 控制
→ 可运行、可观察、可评估、可展示、可部署的产品
```

这里的“完整”指业务闭环完整，而不是平台功能数量多。项目必须同时具备：

- 真实业务输入与明确输出契约。
- 真实模型和真实外部服务调用。
- 可追溯的知识来源、工具结果和失败信息。
- 可解释的数据流、状态流和异常流。
- 明确的权限、停止、预算、恢复和人工确认边界。
- 与当前能力相称的最小评估和回归证据。
- 可交互的 AI Native 产品入口。

## 3. 两个项目阶段

课程与代码只围绕两个项目阶段展开。两个阶段是同一产品的能力递进，不是两套独立项目；课程不设置阶段内版本轴。

### 第一阶段：RAG 应用基础

第一阶段完成一个可运行、可诊断、具有最小可信证据的固定 RAG 需求评审助手。

核心目标：

- 使用真实模型完成结构化需求风险分析。
- 将 TXT、Markdown、DOCX 和文本型 PDF 等真实业务资料加工为可检索知识。
- 使用 PostgreSQL 全文检索、pgvector 和应用侧 RRF 建立可诊断的多路召回基线。
- 明确 Retriever、Context Builder 和 Generator 的责任边界。
- 输出结构化风险、Sources、Citation 和证据不足状态。
- 在证据不足时拒答或提出补充问题。
- 通过 FastAPI 和最小 Web 工作台交付结果、证据、状态与真实错误。
- 使用 Calling Harness、最小 Golden Set 和固定对照证明基线可比较。

第一阶段不建设完整知识平台、完整评估平台、通用 Workflow、Multi-Agent 或企业级部署体系。Reranker、GraphRAG、OCR/VLM 和复杂知识治理先以扩展机制判断是否值得进入产品。

第一阶段完成后，固定 RAG 必须已经是可运行产品，并且 Retriever 具备稳定输入、输出、诊断和错误契约，可以在第二阶段直接作为 Tool 使用。

### 第二阶段：Agent、Tools 与 Multi-Agent 系统

第二阶段在第一阶段固定 RAG 基线上增加动态决策、工具执行、研究能力和多 Agent 协作。

核心目标：

- 建立 Agent Harness，承载模型、上下文、工具、状态、权限、循环、停止和观测。
- 使用 Function Calling、Tool Schema 和 Tool Runtime 管理模型提出的行动。
- 将 Retriever 作为受治理 Tool，完成 Query Rewrite、Source Routing、补检索和追问。
- 区分 Run State、Conversation、短期记忆、长期偏好和可引用业务知识。
- 使用 SSE 和结构化事件协议表达工具调用、证据变化、等待、停止与错误。
- 学习并接入 MCP、Agent Skills 和 Browser / Search / Code / File Tool。
- 使用 Planning 与 Deep Research 完成可追踪的多步研究任务。
- 为多个 Agent 划分真实责任、上下文、工具和输出契约。
- 支持任务分配、并行执行、失败隔离、证据合并和冲突裁决。
- 理解并按真实边界使用 A2A。
- 使用必要 Workflow 机制处理显式状态、恢复、人工介入和有副作用节点。
- 比较固定 RAG、单 Agent 和 Multi-Agent 的质量、成本、延迟与失败定位难度。

Multi-Agent 是第二阶段核心，但不能只把一个 Prompt 拆成多个 Prompt。每个 Agent 的存在必须由独立责任、上下文、工具、输出契约或可验证协作收益支撑。

Workflow 不单独占据一个项目阶段。Multi-Agent 所需的共享状态、并行、失败隔离和汇总在协作问题中学习；Checkpoint、Interrupt、Resume、Human-in-the-loop 和副作用恢复作为必要控制机制进入。

## 4. 课程与项目顺序

课程只有一条面向学习者的连续编号，由 `course/learning-path.md` 维护：

```text
第一阶段：第 1 节连续到第一阶段综合项目
→ 第二阶段：从下一编号继续，直到最终综合项目
```

不为阶段内部建立另一套版本号，也不让知识地图、目录顺序、文件名或项目检查点形成竞争课表。

项目篇按阶段维护业务契约、设计选择、综合任务和验收。同一阶段可以在学习路径中多次返回同一项目篇完成集成检查点，但这些检查点不是产品版本。

## 5. 能力优先级

课程和产品实现的主优先级是：

```text
RAG 应用基础
→ Agent Harness 与 Tools
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ 完整质量工程
```

这不是说质量最后才出现。每一层都必须保留与当前复杂度相称的最小证据：

- 固定 RAG 使用最小 Golden Set 和固定检索对照。
- 单 Agent 检查 Tool Call、轨迹、停止原因和记忆污染。
- Multi-Agent 比较分工收益、成本、延迟、证据一致性和失败定位。
- Trace、Regression、Human Eval 和 Feedback 在第二阶段后部统一收束。

可信结构化评审分布在模型契约、可信 RAG 和跨阶段质量工程中：

- Schema 与本地校验属于模型输出契约。
- Sources、Citation、证据充分性和 Refusal 属于可信 RAG 输出边界。
- Golden Set、Trace、Regression、Bad Case 和 Feedback 属于跨阶段质量工程。

## 6. 能力组织

### 项目主线能力

- 真实模型调用、Provider、Prompt、Structured Output 和 Context Engineering。
- 文档解析、Chunk、Metadata、Embedding、Lexical / Dense Retrieval、RRF 和检索诊断。
- Sources、Citation、Refusal 和可信生成。
- Agent Harness、Tool Schema、Tool Runtime、权限、停止和 Guardrails。
- Agentic RAG、Conversation、Memory、Streaming 和运行状态。
- MCP、Agent Skills、Browser / Search / Code / File Tool 和 Deep Research。
- Multi-Agent、任务委派、A2A、证据合并和冲突裁决。
- 必要 Workflow、人工介入、恢复、重试和幂等。
- Evaluation、Trace、Bad Case 和 Feedback。
- AI Native 的证据、事件、轨迹和人工协作界面。

### 必备工程基础

- Python、HTTP、JSON、异步与配置。
- FastAPI 与 SSE。
- PostgreSQL / pgvector。
- 测试、错误处理、日志、成本和延迟分析。

学习者已经具备时可以通过检查直接进入主线，但这些能力不是可选项。

### 扩展能力

- Reranker、RAPTOR、GraphRAG、Neo4j 多跳检索。
- OCR/VLM、音频 ASR 和复杂多模态知识生产。
- 完整知识治理、后台入库任务和通用文件存储。
- 完整评估平台、通用质量工作台和低代码 Workflow 平台。

扩展能力只有在真实问题和收益证据成立时才进入产品，不阻塞主线。

### 远期认知能力

- 完整多租户和企业权限中台。
- 通用知识库运营平台。
- 通用 Agent 管理与工具市场。
- Kubernetes、灰度发布和企业级告警体系。

远期能力地图见 [ai-application-platform.md](ai-application-platform.md)。它用于保持视野，不是当前项目验收清单。

## 7. 从 RAGFlow 与 MaxKB 吸收什么

RAGFlow 的主要启发是：

- 文件、知识文档、Chunk 和索引是不同对象。
- 知识生产、检索和回答生成应有清晰边界。
- 入库任务、解析状态、检索结果和引用需要可观察。
- 评估与检索测试是 RAG 闭环的一部分。

MaxKB 的主要启发是：

- 先让简单 RAG 应用成立，再增加动态决策和复杂编排。
- 应用、知识库、模型和工具是产品资源，而不是散落在 Prompt 中的配置。
- 简单模式与编排模式应共享底层能力，但不强迫所有场景进入 Workflow。
- 前端需要呈现来源、状态、运行过程、失败和反馈。

本项目吸收这些架构边界和演进方式，不复制完整平台规模。

## 8. 明确非目标

当前不以这些方向为主目标：

- 纯 AI 后端、模型算法或 AI Infra 岗位。
- 通用 RAGFlow、MaxKB 或 Dify 替代品。
- 完整多租户知识平台或 Agent 平台。
- 为展示复杂度而引入 Multi-Agent。
- 为覆盖框架 API 而建设庞大 Workflow。
- 只有聊天 UI 的模型调用 Demo。
- 只有文件上传和问答的 RAG Demo。
- 与需求评审助手无关的多个平行项目。

项目外但重要的知识可以进入概念篇、机制篇或知识地图扩展区，不要求立即进入产品代码。

## 9. 最终能力标准

完成主线后，应能够：

- 判断一个问题需要普通程序、固定 RAG、单 Agent、Multi-Agent 还是必要 Workflow。
- 解释模型、检索、上下文、工具、状态、协议和前端之间的完整链路。
- 设计可引用、可拒答、可比较的知识应用。
- 设计可治理、可停止、可观察的 Agent Harness 与 Tool Runtime。
- 接入 MCP 和 Agent Skills，并判断协议、工具与领域能力的责任边界。
- 构建可追踪来源的 Deep Research 应用。
- 为 Multi-Agent 划分责任、上下文、工具和输出契约，并处理失败与冲突。
- 判断 A2A 和 Workflow 是否真正必要。
- 用评估和 trace 定位失败，而不是只凭主观感受调 Prompt。
- 把 AI 的证据、过程、风险和人工协作做成产品体验。
- 在业务变化时知道应该修改数据、Prompt、Retriever、Tool、Agent、Workflow 还是 UI。

最终竞争力来自三项能力的结合：

1. 复杂前端、Flutter 和跨端工程经验。
2. RAG、Agent、Tool、Multi-Agent 和质量工程能力。
3. 将 AI 能力做成可用、可控、可展示、可交付产品的能力。
