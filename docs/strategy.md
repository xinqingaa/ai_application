# AI Native 前端与 AI 应用闭环战略

这份文档是本仓库长期定位、学习目标和项目阶段的唯一真源。

它回答三个问题：

1. 为什么学习 AI 应用开发。
2. 最终要完成什么。
3. 当前主线做到什么程度，哪些方向暂不展开。

它不规定课程正文模板、代码目录细节和单个项目版本的实现任务；这些分别由 [learning-guide.md](learning-guide.md) 和后续项目篇负责。

## 1. 背景与定位

当前能力基础主要来自前端、Flutter、跨端客户端和复杂业务交付：

- Web 前端、Flutter、H5、Uniapp、React 等多端开发经验。
- 金融交易 App、行情、K 线、长连接、交易链路等复杂业务经验。
- 混合开发、JS Bridge、Flutter 插件、原生能力接入、监控上报和工程化经验。
- AI Coding、研发提效和 AI Agent 辅助开发实践。

这些基础决定了本仓库的主方向不是纯算法、纯 AI Infra 或纯后端平台，而是：

> 以高级前端、Flutter 和跨端客户端能力为主场，补齐 LLM、RAG、Agent、Workflow、FastAPI、评估观测和 AI Native 产品能力，形成完整 AI 应用闭环。

对应的职业定位是：

- AI Native 前端工程师。
- AI 应用前端工程师。
- 高级跨端客户端工程师 + AI 应用闭环能力。

需要补齐的核心短板包括：

- Python 与 FastAPI 应用工程。
- 模型调用、上下文工程和模型能力边界。
- RAG、知识治理与可信回答。
- Agent、Workflow 和人工协作。
- 评估、观测、回归与 bad case 治理。
- AI 执行过程、证据和状态的产品化表达。

## 2. 唯一长期主目标

本仓库只维护一个主项目：

> **需求评审助手：从可信 RAG + 单 Agent 演进为多 Agent + Workflow 的完整 AI 应用。**

项目围绕 PRD、业务规则、接口文档、客户端规则、会议纪要和历史评审记录，完成：

```text
真实资料进入系统
→ 知识解析、组织与检索
→ 结构化需求评审
→ 来源引用、证据校验、拒答与追问
→ 评估、bad case 和反馈回流
→ 单 Agent 动态补检索与知识源选择
→ Workflow 状态、分支和人工介入
→ 多 Agent 分工、协作、汇总与冲突处理
→ 可运行、可观察、可展示、可部署的产品
```

这里的“完整”指业务闭环完整，而不是平台功能数量多。项目必须同时具备：

- 真实业务输入与明确输出契约。
- 真实模型和真实外部服务调用。
- 可追溯的知识来源和失败信息。
- 可重复的运行、评估和回归方式。
- 可解释的数据流、状态流和异常流。
- 可交互的 AI Native 产品入口。

## 3. 两个项目阶段

课程与代码围绕两个项目阶段展开。两个阶段是产品能力的递进，不是两套独立项目。

### 阶段一：可信 RAG + 单 Agent 需求评审助手

阶段一先把一个可用、可信、可评估的需求评审助手做出来。

核心目标：

- 使用真实模型完成需求风险分析。
- 将业务资料加工为可检索知识。
- 区分检索失败、上下文失败和生成失败。
- 输出结构化评审结果、Sources 和 Citation。
- 证据不足时拒答或提出补充问题。
- 建立最小 Golden Set、bad case 和反馈回流。
- 使用单 Agent 处理查询改写、知识源选择、补检索和追问补全。
- 从 V0 开始提供最小但可用的产品交互入口，并随 V1 的可信证据、V2 的质量闭环和 V3 的 Agent 运行逐步演进。

阶段一完成后，项目必须已经能够运行和使用，不能把“产品成立”推迟到多 Agent 阶段。

### 阶段二：Workflow + 多 Agent 评审系统

阶段二在阶段一可信基线上增加可控流程和多角色协作。

核心目标：

- 将评审过程建模为显式状态、节点、分支和循环。
- 支持 Human-in-the-loop、中断、恢复、重试和人工修改。
- 为不同 Agent 划分真实职责、上下文、工具和输出契约。
- 支持并行或按条件执行的评审任务。
- 处理 Agent 结果汇总、证据合并、意见冲突和最终裁决。
- 比较单 Agent 与多 Agent 的质量、成本、延迟和失败定位难度。
- 完善工作台、运行轨迹、质量面板、部署和作品化表达。

多 Agent 是明确的长期目标，但不能只把一个 Prompt 拆成多个 Prompt。每个 Agent 的存在必须由责任边界或可验证收益支撑。

## 4. 项目版本 V0–V6

V0–V6 是唯一项目里程碑顺序；每个版本内部的认知前置和正文顺序由 `course/learning-path.md` 定义。

| 阶段 | 版本 | 核心结果 |
| --- | --- | --- |
| 阶段一 | V0 固定 RAG 基线 | 跑通真实资料、检索、上下文、评审 API 和最小工作台；直接 LLM 仅作为效果对照 |
| 阶段一 | V1 可信结构化评审 | Structured Output、Sources、Citation 校验、Refusal、补充问题和可信证据界面 |
| 阶段一 | V2 质量闭环 | Golden Set、检索与生成评估、bad case、feedback、回归和最小质量工作台 |
| 阶段一 | V3 单 Agent RAG | Query Rewrite、Source Routing、补检索、质量判断、追问补全和 Agent 运行界面 |
| 阶段二 | V4 可控 Workflow | 显式状态、分支、人工审核、中断、恢复和重试 |
| 阶段二 | V5 多 Agent 评审 | 多角色协作、并行评审、结果汇总、证据合并和冲突处理 |
| 阶段二 | V6 产品化 | 整合并完善已有工作台和质量面板，补齐本地部署、演示和作品化 |

版本只描述产品演进到哪里。学习者从 `course/README.md` 进入，正向阅读顺序由 `course/learning-path.md` 唯一定义；`course/project/` 在必要概念和机制之后负责综合实现、设计选择和版本验收。

## 5. 能力组织

LLM、RAG、Agent、Workflow、Eval 和 AI Native 是能力域，不是必须依次通关的课程门禁。学习顺序由当前项目版本反推。

### 项目主线能力

- 真实模型调用与 Provider 边界。
- Prompt、Structured Output 和 Context Engineering。
- 文档解析、Chunk、Metadata、Embedding 和 Retrieval。
- Sources、Citation、Refusal 和可信生成。
- 单 Agent、Tool Runtime、Workflow 和 Multi-Agent。
- Evaluation、Trace、Bad Case 和 Feedback。
- SSE、任务状态、证据展示、人工介入和 AI Native 交互。

### 项目支撑能力

- Python、FastAPI、HTTP、JSON、SSE 和异步基础。
- PostgreSQL / pgvector。
- 文件存储、后台任务、日志和配置管理。
- Redis、Docker Compose 和基础部署。
- 测试、错误处理、成本和延迟分析。

这些能力按项目实际问题进入，不单独扩展成后端或运维大课。

### 远期认知能力

- 完整多租户和企业权限中台。
- 通用知识库运营平台。
- 可视化低代码 Workflow 平台。
- 通用 Agent 管理与工具市场。
- 完整 MCP / A2A 生态平台。
- Kubernetes、灰度发布和企业级告警体系。

远期能力地图见 [ai-application-platform.md](ai-application-platform.md)。它用于保持视野，不是当前项目验收清单。

## 6. 从 RAGFlow 与 MaxKB 吸收什么

RAGFlow 的主要启发是：

- 文件、知识文档、Chunk 和索引是不同对象。
- 知识生产、检索和回答生成应有清晰边界。
- 入库任务、解析状态、检索结果和引用需要可观察。
- 评估与检索测试是 RAG 闭环的一部分。

MaxKB 的主要启发是：

- 先让简单 RAG 应用成立，再升级为 Workflow 应用。
- 应用、知识库、模型和工具是产品资源，而不是散落在 Prompt 中的配置。
- 简单模式与编排模式应共享底层能力，但不应强迫所有场景进入 Workflow。
- 前端需要呈现来源、状态、运行过程、失败和反馈。

本项目吸收这些架构边界和演进方式，不复制完整平台规模。

## 7. 明确非目标

当前不以这些方向为主目标：

- 纯 AI 后端、模型算法或 AI Infra 岗位。
- 通用 RAGFlow、MaxKB 或 Dify 替代品。
- 完整多租户知识平台或 Agent 平台。
- 为展示复杂度而引入 Multi-Agent。
- 只有聊天 UI 的模型调用 Demo。
- 只有文件上传和问答的 RAG Demo。
- 与需求评审助手无关的多个平行项目。

项目外但重要的知识可以进入概念篇或机制篇，不要求立即进入项目代码。

## 8. 最终能力标准

完成主线后，应能够：

- 判断一个问题需要普通程序、LLM、RAG、Workflow、单 Agent 还是多 Agent。
- 解释模型、检索、上下文、工具、状态和前端之间的完整链路。
- 设计可引用、可拒答、可评估的知识应用。
- 构建可控、可观测、可人工介入的 Agent Workflow。
- 用评估和 trace 定位失败，而不是只凭主观感受调 Prompt。
- 把 AI 的证据、过程、风险和人工协作做成产品体验。
- 在业务变化时知道应该修改数据、Prompt、Retriever、Tool、Agent、Workflow 还是 UI。

最终竞争力来自三项能力的结合：

1. 复杂前端、Flutter 和跨端工程经验。
2. LLM、RAG、Agent、Workflow 和质量工程能力。
3. 将 AI 能力做成可用、可控、可展示、可交付产品的能力。
