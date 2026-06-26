# 07 需求评审助手项目化大纲

## 课程定位

`07_projects` 是需求评审助手的项目收敛层，也是整个仓库的作品化主线。

本课程不重新学习 02-06 的知识点，而是把它们组合成一个可运行、可展示、可讲述、可迭代的项目。

当前只维护一个长期主项目：

```text
需求评审助手
= LLM 应用底座
+ 企业知识库与 RAG
+ Sources / Refusal / Structured Review
+ RAG Eval / Bad Case
+ Single Agent RAG
+ Multi-Agent Review
+ Workflow / Human-in-the-loop
+ Trace / Observability
+ AI Native Workbench
+ PostgreSQL / pgvector / Redis / Docker Compose
```

## 学习链路

每个专题都遵循统一链路：

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

## 项目版本路线

```text
V0 固定 RAG
-> V1 引用 / 拒答 / 结构化评审
-> V2 评估 / bad case / feedback
-> V3 单 Agent RAG
-> V4 多 Agent 评审
-> V5 Workflow / Human Review
-> V6 工作台 / 质量面板 / Demo
```

## 完成标准

完成本课程后，应能做到：

- 讲清需求评审助手的业务价值、技术路线、阶段边界和能力演进（V0–V6）。
- 将 `llm_core`、`rag_core`、`agent_core`、`workflow_core`、`eval_core`、`trace_core` 和 AI UI 组件组合成项目。
- 用 Docker Compose + PostgreSQL / pgvector + Redis 体现真实工程能力。
- 提供可运行 demo、质量面板、部署方案和作品集表达。
- 说明 Agent Management Console、MCP Tool Ecosystem UI、Realtime Voice、多租户、K8s、CI/CD 等能力的未来边界，而不是过早深挖。

## 代码组织建议

```text
source/07_projects/
├── shared/
│   ├── llm_core/
│   ├── rag_core/
│   ├── agent_core/
│   ├── workflow_core/
│   ├── eval_core/
│   ├── trace_core/
│   └── ai_ui/
├── apps/
│   └── review_assistant/
├── infra/
│   ├── docker-compose.yml
│   ├── postgres/
│   ├── redis/
│   └── scripts/
└── README.md
```

## 专题目录

```text
course/07_projects/
├── 00_project_positioning_and_portfolio.md
├── 01_project_architecture_and_module_boundary.md
├── 02_shared_packages_and_infrastructure.md
├── 03_product_definition_and_review_scenarios.md
├── 04_knowledge_base_and_document_ingestion.md
├── 05_fixed_rag_v0.md
├── 06_sources_refusal_structured_review_v1.md
├── 07_rag_eval_bad_case_feedback_v2.md
├── 08_single_agent_rag_v3.md
├── 09_multi_agent_review_v4.md
├── 10_workflow_human_review_v5.md
├── 11_ai_native_workbench.md
├── 12_trace_quality_dashboard.md
├── 13_local_deployment_and_demo.md
├── 14_portfolio_resume_and_review.md
└── outline.md
```

## 00. Project Positioning 与 Portfolio

### 真实问题

如果项目目标过泛，会变成平台空谈；如果目标太窄，又无法承载 RAG、Agent、Workflow、Eval 和 AI Native 的完整能力。

### 基础原理

- 单项目主线。
- 业务价值。
- 技术路线。
- 阶段边界。
- 作品集叙事。
- 平台能力从项目自然长出来。

### 最小实现

- 写出一句话定位、目标用户、核心场景和不做什么。

### 主流框架实现

- Portfolio README。
- Architecture decision record。
- Project roadmap。

### 失败分析与能力边界

- 把项目写成泛化平台。
- 没有业务场景，只堆技术名词。
- 过早承诺多租户、工具市场、完整运营后台。

### 评估观测

- 项目是否可独立演示。
- 阶段目标是否清楚。
- 每阶段是否有可运行产物。

### 小项目实战

写出定位：

> 面向研发团队的需求评审助手，通过企业知识库、RAG、多 Agent 协作和人工确认，帮助团队发现需求风险、追溯依据并生成结构化评审报告。

### 项目收敛

输出项目定位、目标用户和作品集叙事。

## 01. Project Architecture 与 Module Boundary

### 真实问题

需求评审助手不是一个聊天页面，而是由模型调用、知识库、工具系统、工作流、评估观测、前端工作台和基础设施组成的系统。

### 基础原理

- API layer。
- LLM layer。
- RAG layer。
- Agent / Workflow layer。
- Eval / Observability layer。
- AI Native Workbench。
- Infra layer。
- **运营对象层**：ReviewApplication、ReviewConfig、ReviewRun、ReviewRunVersion、ChatRecord、ToolRecord。

### 运营对象（架构层）

| 对象 | 职责 |
| --- | --- |
| `ReviewApplication` | 应用配置容器 |
| `ReviewConfig` | 当前生效配置（model / prompt / retriever / workflow） |
| `ReviewRun` | 一次评审运行 |
| `ReviewRunVersion` | 本次 run 绑定的配置版本快照，用于复现与 eval |
| `ChatRecord` | 会话消息、token、引用、反馈 |
| `ToolRecord` | 工具调用审计 |

目的不是做 MaxKB 式平台，而是保证一次评审可复现、可评估。

### 最小实现

- 画出总体架构图。
- 标注请求流、事件流和数据流。

### 主流框架实现

- FastAPI。
- PostgreSQL / pgvector。
- Redis。
- LangChain / LangGraph。
- Web / Flutter 前端。

### 失败分析与能力边界

- 前后端接口没有统一事件协议。
- AI 运行态无法追踪。
- 数据库、向量库和缓存职责混乱。
- 权限和审计后补导致重构。

### 评估观测

- 关键链路是否可追踪。
- 模块边界是否清晰。
- 失败是否能定位到层级。

### 小项目实战

定义项目共同架构：

- document API。
- knowledge API。
- review API。
- agent API。
- workflow API。
- eval API。

### 项目收敛

输出项目架构图、模块边界和请求数据流。

## 02. Shared Packages 与 Infrastructure

### 真实问题

项目需要共享能力，但不能过早做成通用平台。基础设施也要真实体现，但不能把学习方向带偏成后端运维。

### 基础原理

- Shared packages。
- Service boundaries。
- Docker Compose。
- PostgreSQL / pgvector。
- Redis。
- Background jobs。
- File storage。
- Environment config。
- **应用运营对象**：ReviewApplication / ReviewConfig / ReviewRun / ReviewRunVersion。
- **会话与审计**：ChatRecord（V0 起最小实现）、ToolRecord。
- **配置版本快照**：一次评审可复现 model、prompt、retriever、workflow 版本。

### 应用产品对象建模

对标 MaxKB 的 Application / Version / ChatRecord 思路，收敛为项目必需的最小集：

- `ReviewConfig` 变更产生新版本哈希。
- `ReviewRun` 绑定 `ReviewRunVersion`。
- eval 对比必须能关联配置版本。
- 不做应用发布市场、API Key 平台或嵌入页。

### 基础设施优先级（对齐 strategy P0 / P1）

| 优先级 | 能力 | 本项目落点 | V 阶段 |
| --- | --- | --- | --- |
| **P0 必做** | FastAPI 服务与 API 分层 | chat / rag / review / agent / eval | V0+ |
| **P0** | PostgreSQL 业务表 + pgvector | Document、Chunk、Embedding、ReviewRun | V0+ |
| **P0** | 环境变量与密钥管理 | `.env` + 配置 schema | V0 |
| **P0** | 文件上传与本地存储目录 | upload API + storage path | V0 |
| **P0** | 基础日志与统一错误响应 | request_id、结构化 log | V0 |
| **P0** | 后台任务：解析、索引、批量 eval | IngestionJob + worker（见 `03_rag/06`） | V0–V2 |
| **P0** | Docker Compose 本地一键启动 | API + Postgres + Redis（+ 前端） | V6 demo |
| **P1 逐步** | Redis：任务状态、缓存、限流 | job status、可选 session | V1+ |
| **P1** | 任务队列方案择一 | Celery / RQ / arq | V1+ |
| **P1** | 对象存储认知 | 本地目录先行；MinIO/S3 作 P1 扩展 | V4+ |
| **P1** | 基础监控：耗时、成本、失败率 | 接入 `trace_core` / 质量面板 | V2+ |
| **P2 仅认知** | K8s、CI/CD、灰度、多租户、完整告警 | 不在当前交付范围 | — |

**检查清单（§02 完成标准）**：Docker Compose 一键启动成功；upload → IngestionJob → completed 可观测；ReviewRun 可关联 Config 版本；不在 P0 阶段引入 K8s / 多租户。

### 最小实现

- 用 Docker Compose 启动 API + PostgreSQL（pgvector）+ Redis + worker。
- 建立环境变量配置。
- 跑通一次文档索引后台任务。

### 主流框架实现

- FastAPI。
- SQLAlchemy / SQLModel。
- pgvector。
- Redis。
- Celery / RQ / arq 认知。

### 失败分析与能力边界

- 每个模块重复封装 LLM / RAG / Agent。
- Redis 和后台任务过早复杂化。
- K8s 过早引入。
- 基础设施成为主线，掩盖 AI 应用能力。

### 评估观测

- 一键启动成功率。
- 后台任务成功率。
- 索引构建耗时。
- 服务错误日志。

### 小项目实战

共享 package：

- `llm_core`
- `rag_core`
- `agent_core`
- `workflow_core`
- `eval_core`
- `trace_core`
- `ai_ui`

### 项目收敛

输出项目基础设施和共享底座方案。

## 03. Product Definition 与 Review Scenarios

### 真实问题

企业需求评审涉及 PRD、接口文档、业务规则、历史评审和会议纪要。人工容易遗漏依据、风险和历史经验。

### 基础原理

- 产品定位。
- 用户角色。
- 业务主链路。
- 输入输出。
- 不解决什么问题。
- MVP 范围。
- **评审维度矩阵**（前端 / Flutter 差异化，贯穿 Prompt、Agent、Golden Set 标签）：

| 维度 | 典型关注点 |
| --- | --- |
| 页面交互风险 | 空态、加载态、状态可回退 |
| 状态流转风险 | 多步骤、草稿、并发编辑 |
| 接口兼容风险 | 字段变更、版本兼容 |
| 埋点与监控风险 | 关键链路可观测 |
| 权限与敏感信息 | 脱敏、越权、审计 |
| 多端一致性 | Flutter / H5 / Native 差异 |
| 异常 / 弱网 / 长连接 | 超时、重连、幂等 |
| 测试验收点 | 可执行 case |
| 发布灰度与回滚 | 开关、回滚路径 |

### 最小实现

- 定义用户角色：产品、前端、后端、测试、评审负责人。
- 定义核心场景：需求问答、风险识别、缺失信息追问、评审摘要。

### 主流框架实现

- RAG + Single Agent。
- Sources / Refusal。
- Structured output。
- Eval + Feedback。
- 最小 AI Native UI。

### 失败分析与能力边界

- 试图替代人工评审结论。
- 没有明确知识范围。
- 把项目做成泛用聊天助手。

### 评估观测

- 场景是否有真实输入输出。
- 用户是否能理解 AI 结论依据。
- 需求评审报告是否可复用。

### 小项目实战

定义核心场景：

- 需求问答。
- 风险识别。
- 缺失信息追问。
- 接口影响分析。
- 测试验收点生成。
- 评审报告生成。
- 按评审维度为 golden set 和 Prompt 打标签。

### 项目收敛

输出项目 PRD 与评审维度矩阵。

## 04. Knowledge Base 与 Document Ingestion

### 真实问题

需求评审助手的质量首先取决于知识库。没有可靠的文档入库、状态管理、metadata 和检索测试，后面 Agent 再复杂也不可靠。

### 基础原理

- Knowledgebase。
- File / Document / Chunk / Embedding。
- Ingestion job。
- Parsing status。
- Metadata。
- Re-index。
- Retrieval test。

### 最小实现

- 上传一份 PRD。
- 解析、切分、向量化。
- 查看文档状态和 chunk。

### 主流框架实现

- FastAPI upload。
- PostgreSQL metadata。
- pgvector。
- Redis / worker。
- knowledge workbench。

### 失败分析与能力边界

- 上传成功但入库失败。
- 文档状态不可见。
- chunk 无法预览。
- metadata 缺失导致检索和引用失败。

### 评估观测

- 文档入库成功率。
- chunk 数量。
- 向量化耗时。
- 检索测试命中率。

### 小项目实战

实现知识库和文档入库：

- 上传 PRD。
- 上传接口文档。
- 上传业务规则。
- 上传历史评审。
- 查看状态。
- 预览 chunk。
- 测试检索。

### 项目收敛

完成知识库工作台和入库链路。

## 05. Fixed RAG V0

### 真实问题

项目第一阶段必须先跑通最小 RAG 闭环，而不是一开始就做多 Agent。

### 基础原理

- Question。
- Retrieval。
- Context construction。
- Generation。
- Answer。
- Source id。

### 最小实现

- 用户提问。
- 检索知识库。
- 构造上下文。
- 生成回答。

### 主流框架实现

- LangChain Retriever。
- LCEL RAG chain。
- FastAPI endpoint。

### 失败分析与能力边界

- 固定 RAG 无法处理模糊问题。
- 没有引用就无法信任。
- 没有评估就无法优化。

### 评估观测

- retrieval latency。
- top-k source。
- answer latency。
- token usage。

### 小项目实战

实现固定 RAG 问答：

- 用户提问。
- 检索知识库。
- 构造上下文。
- 生成回答。
- 记录 ChatRecord（V0 最简：问题、回答、来源、token）。

### 项目收敛

完成 V0 可运行版本。

## 06. Sources / Refusal / Structured Review V1

### 真实问题

没有引用、拒答和结构化输出，需求评审助手就无法可信地用于真实场景。

### 基础原理

- Citation。
- Source panel。
- Refusal。
- Clarification。
- Structured risk output。
- Review report schema。

### 最小实现

- 每条回答带来源。
- 无依据时拒答。
- 输出结构化风险项。

### 主流框架实现

- Structured Outputs。
- Pydantic schema。
- citation checker。
- 前端 source panel。

### 失败分析与能力边界

- 引用不存在。
- 有依据却拒答。
- 无依据却强答。
- 结构化字段不稳定。

### 评估观测

- citation correctness。
- refusal accuracy。
- schema success rate。
- user feedback。

### 小项目实战

升级 V1：

- 每条回答带来源。
- 无依据时拒答。
- 证据不足时追问。
- 输出结构化风险项。
- 生成评审报告草稿。

### 项目收敛

完成可信回答和结构化评审输出。

## 07. RAG Eval / Bad Case / Feedback V2

### 真实问题

项目不能靠感觉迭代。V2 要建立最小质量闭环。

### 基础原理

- Golden set。
- Retrieval eval。
- Citation eval。
- Refusal eval。
- Bad case board。
- Feedback loop。

### 最小实现

- 创建 30 条样本。
- 跑一次 eval。
- 标记 5 个 bad case。

### 主流框架实现

- pytest eval。
- 自定义 metrics。
- dashboard。

### 失败分析与能力边界

- 样本过少。
- bad case 没有归因。
- 反馈没有进入回归集。

### 评估观测

- source hit。
- citation correctness。
- refusal accuracy。
- bad case 修复率。

### 小项目实战

实现质量闭环：

- 创建样本集。
- 跑 eval。
- 查看指标。
- 标记 bad case。
- 根据 bad case 修复知识库或 Prompt。

### 项目收敛

完成 V2 质量基线。

## 08. Single Agent RAG V3

### 真实问题

固定 RAG 对模糊问题和跨知识源问题能力有限，需要单 Agent 做查询改写、知识源选择和追问。

### 基础原理

- Query rewrite。
- Source routing。
- Retrieval quality check。
- Clarification。
- Retriever as tool。

### 最小实现

- Agent 判断问题类型。
- 选择知识库。
- 检索并判断证据是否足够。

### 主流框架实现

- LangChain Agent。
- LangGraph state。
- Retriever as Tool。

### 失败分析与能力边界

- Agent 过度检索。
- 查询改写偏离意图。
- 证据不足时强答。

### 评估观测

- source routing accuracy。
- query rewrite lift。
- clarification accuracy。
- step count。

### 小项目实战

实现单 Agent RAG：

- 判断问题类型。
- 选择知识库。
- 改写查询。
- 检查证据是否足够。
- 必要时追问。

### 项目收敛

完成 V3 智能检索助手。

## 09. Multi-Agent Review V4

### 真实问题

需求评审天然是多角色任务。一个 Agent 负责所有事情会职责混乱、难以评估。

### 基础原理

- Agent role。
- Input / output contract。
- Supervisor。
- Conflict detection。
- Aggregation。
- Role-level eval。

### 最小实现

- 实现需求理解、风险审查、汇总评审 3 个 Agent。
- 使用 shared state 传递结构化输出。

### 主流框架实现

- LangGraph 多节点。
- Supervisor pattern。
- 多 Agent 框架认知。

### 失败分析与能力边界

- 多 Agent 只是重复调用模型。
- 角色职责重叠。
- 汇总时丢失引用。

### 评估观测

- 角色输出完整率。
- 冲突发现率。
- 最终报告 groundedness。
- 成本和耗时。

### 小项目实战

实现多 Agent 评审：

- 需求理解 Agent。
- 知识检索 Agent。
- 风险审查 Agent。
- 技术影响 Agent。
- 测试验收 Agent。
- 追问 Agent。
- 汇总评审 Agent。

### 项目收敛

完成 V4 多 Agent 需求评审。

## 10. Workflow / Human Review V5

### 真实问题

多 Agent 输出仍需要流程控制。证据不足、高风险结论、Agent 冲突和报告发布前都需要人工确认。

### 基础原理

- Workflow state。
- Node。
- Conditional edge。
- Interrupt。
- Human approval。
- Resume。
- Audit。

### 最小实现

- 在多 Agent 流程后增加人工确认节点。
- 用户确认后生成最终报告。

### 主流框架实现

- LangGraph。
- FastAPI event stream。
- 前端 workflow runtime。

### 失败分析与能力边界

- 人工确认状态未持久化。
- 高风险未中断。
- resume 后上下文丢失。

### 评估观测

- workflow path。
- interrupt rate。
- resume success。
- human edit record。

### 小项目实战

实现 Workflow：

```text
submit_requirement
-> understand
-> retrieve
-> multi_agent_review
-> conflict_check
-> human_confirm
-> generate_report
-> feedback
```

### 项目收敛

完成 V5 可控工作流。

## 11. AI Native Workbench

### 真实问题

项目需要一个能承载 RAG、Agent、Workflow 和 Eval 的工作台，而不是只有聊天框。

### 基础原理

- Document workbench。
- Review run page。
- Source panel。
- Multi-agent timeline。
- Workflow runtime。
- Report editor。
- Feedback entry。

### 最小实现

- 实现文档列表、评审运行页和报告页。

### 主流框架实现

- React / Vue / Flutter。
- SSE。
- 前端状态机。
- schema-driven UI。

### 失败分析与能力边界

- 页面只展示最终答案。
- 运行态和后端状态不同步。
- 反馈入口缺失。

### 评估观测

- 用户是否能完成评审流程。
- sources 是否可访问。
- workflow 状态是否清晰。

### 小项目实战

实现工作台页面：

- 知识库。
- 提交评审。
- 运行详情。
- 评审报告。
- bad case。
- 质量面板。

### 项目收敛

完成 V6 工作台体验。

## 12. Trace 与 Quality Dashboard

### 真实问题

作品化项目需要能展示系统如何判断、哪里失败、如何改进。

### 基础原理

- Trace viewer。
- RAG metrics。
- Agent metrics。
- Workflow metrics。
- Cost / latency。
- Bad case status。

### 最小实现

- 展示一次评审 run 的完整 trace。
- 展示核心质量指标。

### 主流框架实现

- 自定义 trace_core。
- OpenTelemetry 认知。
- dashboard。

### 失败分析与能力边界

- 只有指标没有样本。
- trace 太细无法阅读。
- 面板不支持修复闭环。

### 评估观测

- trace 完整率。
- bad case 修复率。
- 指标趋势。

### 小项目实战

实现质量面板：

- 检索命中率。
- 引用正确率。
- 拒答准确率。
- 风险覆盖率。
- 工具调用成功率。
- 人工确认触发率。
- token 和耗时。

### 项目收敛

完成可观测作品化能力。

## 13. Local Deployment 与 Demo

### 真实问题

项目必须能稳定运行和演示。

### 基础原理

- Local setup。
- env。
- docker-compose。
- seed data。
- demo script。
- reset script。
- troubleshooting。

### 最小实现

- 用 docker-compose 启动 API、数据库、Redis 和前端。
- 导入一批示例文档。

### 主流框架实现

- Docker Compose。
- Makefile / scripts。
- README demo guide。

### 失败分析与能力边界

- 本地启动步骤过多。
- 示例数据不可复现。
- 演示链路依赖人工操作记忆。

### 评估观测

- 一键启动成功率。
- demo 完成耗时。
- reset 是否可靠。

### 小项目实战

准备演示链路：

- 导入示例文档。
- 提交需求评审。
- 展示检索引用。
- 展示多 Agent 轨迹。
- 人工确认。
- 生成报告。
- 查看质量面板。

### 项目收敛

完成可运行 demo。

## 14. Portfolio、Resume 与 Review

### 真实问题

项目最终需要能讲清楚，而不是只堆功能。

### 基础原理

- 项目 README。
- Architecture doc。
- Demo guide。
- Technical highlights。
- Trade-offs。
- Future roadmap。
- 简历表达。

### 最小实现

- 写出项目 README。
- 准备一条 demo 脚本。
- 总结 5 个技术亮点。

### 主流框架实现

- README。
- ADR。
- demo video script。
- portfolio case study。

### 失败分析与能力边界

- 只列技术栈，不讲业务价值。
- 只讲结果，不讲取舍。
- 未来规划过大，显得不落地。

### 评估观测

- 是否能 3 分钟讲清项目。
- 是否能演示完整链路。
- 是否能说明技术取舍。

### 小项目实战

整理作品集材料：

- 项目背景。
- 架构图。
- 核心链路。
- 多 Agent 分工。
- 质量工程。
- 工程部署。
- 未来方向。

### 项目收敛

完成需求评审助手的作品化表达。

## 参考设计映射

### MaxKB（应用产品层）

- Application / Version、ChatRecord、ToolRecord、配置版本、运行记录与反馈统计；本项目收敛为 ReviewApplication / ReviewRun / ReviewConfig 等运营对象。

### RAGFlow（知识生产 + 评测）

- 企业知识库、复杂文档处理、检索评估、运行态与质量治理。
