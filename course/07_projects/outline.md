# 07 项目平台化与作品化大纲

## 课程定位

`07_projects` 是两个长期项目的收敛层，也是企业级 AI 应用平台雏形的作品化主线。

本课程不重新学习 02-06 的知识点，而是把它们组合成可运行、可展示、可讲述、可迭代的项目。

长期维持两个项目更适合学习推进和简历表达：

- 项目一：需求评审 RAG 助手 / 智能客服。
- 项目二：金融 Copilot。

这两个项目不是割裂关系。项目一是可独立展示的 RAG + 单 Agent 知识助手项目，也可以作为项目二中的知识型子 Agent / 子模块复用。项目二在项目一基础上扩展为金融场景的多 Agent Copilot 与企业级 AI 应用平台雏形。

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

## 项目关系

```text
项目一：需求评审 RAG 助手 / 智能客服
= RAG + LangChain + 单 Agent + Sources / Refusal + Eval + 最小 AI Native UI

项目二：金融 Copilot
= 项目一的知识助手能力
+ Tool Runtime
+ LangGraph Workflow
+ Multi-Agent
+ MCP / Tool Ecosystem
+ Human-in-the-loop
+ Eval / Observability
+ AI Native Frontend
+ Enterprise AI Platform
```

## 完成标准

完成本课程后，应能做到：

- 讲清两个项目的业务价值、技术路线、阶段边界和复用关系。
- 将 `llm_core`、`rag_core`、`rag_eval`、`rag_memory`、`agent_core`、`workflow_core`、`eval_core`、`trace_core` 和 AI UI 组件组合成项目。
- 用 Docker Compose + PostgreSQL / pgvector + Redis 体现真实工程能力。
- 为两个项目提供可运行 demo、质量面板、部署方案和作品集表达。
- 说明 K8s、CI/CD、多租户、灰度发布等能力的认知边界，而不是过早深挖。

## 代码组织建议

```text
source/07_projects/
├── shared/
│   ├── llm_core/
│   ├── rag_core/
│   ├── agent_core/
│   ├── workflow_core/
│   ├── eval_core/
│   └── ai_ui/
├── apps/
│   ├── review_assistant/
│   └── financial_copilot/
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
├── 00_project_portfolio_and_platform_strategy.md
├── 01_enterprise_ai_application_architecture.md
├── 02_shared_packages_and_infrastructure.md
├── 03_requirement_review_assistant_product.md
├── 04_requirement_review_assistant_delivery.md
├── 05_customer_service_rag_agent_extension.md
├── 06_financial_copilot_product.md
├── 07_financial_copilot_agent_workflows.md
├── 08_visual_workflow_builder.md
├── 09_enterprise_knowledge_base_platform.md
├── 10_agent_management_platform.md
├── 11_mcp_tool_ecosystem_platform.md
├── 12_agent_runtime_observability_center.md
├── 13_data_labeling_evaluation_platform.md
├── 14_security_ops_cost_governance.md
├── 15_deployment_demo_portfolio.md
└── outline.md
```

## 00. Project Portfolio 与 Platform Strategy

### 真实问题

如果只做一个大项目，学习战线会过长，迟迟难以展示。如果完全做两个割裂项目，又会浪费复用能力，简历叙事也不够集中。

### 基础原理

- 两项目递进。
- 项目一快速闭环。
- 项目二体现上限。
- 项目一作为项目二的知识型子 Agent / 子模块复用。
- 共享底座沉淀能力，而不是每个项目重新造轮子。

### 最小实现

- 画出两个项目关系图。
- 标注能力复用：LLM、RAG、Agent、Eval、AI UI、Infra。

### 主流框架实现

- Portfolio README。
- Architecture decision record。
- Project roadmap。

### 失败分析与能力边界

- 做成一个巨型项目导致无法闭环。
- 两个项目完全重复实现。
- 平台化过早导致业务价值不清。

### 评估观测

- 项目一是否可独立演示。
- 项目二是否复用项目一能力。
- 每阶段是否有可运行产物。

### 小项目实战

定义作品集叙事：

- 项目一展示 RAG + 单 Agent 知识助手闭环。
- 项目二展示金融场景多 Agent Copilot 和企业平台能力。

### 项目收敛

本章输出项目组合战略。

## 01. Enterprise AI Application Architecture

### 真实问题

企业级 AI 应用不是聊天机器人，而是由模型调用、知识库、工具系统、工作流、评估观测、前端工作台、权限审计和部署基础设施组成的系统。

### 基础原理

- API layer。
- LLM layer。
- RAG layer。
- Agent / Workflow layer。
- Eval / Observability layer。
- AI Native Frontend layer。
- Infra layer。

### 最小实现

- 画出项目一和项目二的分层架构。
- 标注请求数据流和事件流。

### 主流框架实现

- FastAPI。
- PostgreSQL / pgvector。
- Redis。
- Docker Compose。
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

定义两个项目共同架构：

- chat API。
- rag API。
- agent API。
- workflow API。
- eval API。
- admin API。

### 项目收敛

本章输出总体架构图和模块边界。

## 02. Shared Packages 与 Infrastructure

### 真实问题

两个项目需要共享能力，但不能过早做成通用平台。基础设施也要真实体现，但不能把学习方向带偏成后端运维。

### 基础原理

- Shared packages。
- Service boundaries。
- Docker Compose。
- PostgreSQL / pgvector。
- Redis。
- Background jobs。
- File storage。
- Environment config。

### 最小实现

- 用 Docker Compose 启动 API + PostgreSQL + Redis。
- 建立环境变量配置。
- 跑通一次文档索引后台任务。

### 主流框架实现

- FastAPI。
- SQLAlchemy / SQLModel。
- pgvector。
- Redis。
- Celery / RQ / arq 认知。

### 失败分析与能力边界

- 每个项目重复封装 LLM / RAG / Agent。
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
- `rag_eval`
- `rag_memory`
- `agent_core`
- `workflow_core`
- `eval_core`
- `trace_core`
- `ai_ui`

### 项目收敛

本章输出项目基础设施和共享底座方案。

## 03. 需求评审 RAG 助手产品定义

### 真实问题

企业需求评审涉及 PRD、接口文档、业务规则、历史评审和会议纪要。人工容易遗漏依据、风险和历史经验。

### 基础原理

- 产品定位。
- 用户角色。
- 业务主链路。
- 输入输出。
- 不解决什么问题。

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

- 不替代最终评审责任。
- 不保证文档缺失时能回答。
- 高风险结论需要人工确认。

### 评估观测

- 用户是否能定位依据。
- 风险项是否可用。
- 无依据问题是否拒答。

### 小项目实战

定义项目一 PRD。

### 项目收敛

本章输出项目一产品定义。

## 04. 需求评审 RAG 助手交付路线

### 真实问题

项目一需要快速闭环，又要为项目二复用能力。阶段划分必须清楚，避免一开始就做完整平台。

### 基础原理

- V0 固定 RAG。
- V1 Sources / Refusal / Structured Output。
- V2 Eval / Bad Case。
- V3 Single Agent RAG。
- V4 Workflow / Human-in-the-loop。
- V5 Workbench。

### 最小实现

- V0：上传文档、构建索引、问答、sources。

### 主流框架实现

- LangChain RAG。
- Retriever as Tool。
- LangGraph workflow。
- Eval dashboard。
- AI Native UI。

### 失败分析与能力边界

- 阶段目标过大。
- V0 没有评估。
- V3 单 Agent 没有工具轨迹。
- V5 工作台过早平台化。

### 评估观测

- 每个版本都有 golden set。
- 每个版本都有可演示入口。
- 每个版本记录新增能力和失败边界。

### 小项目实战

输出项目一交付 roadmap。

### 项目收敛

项目一最终作为项目二的 knowledge agent / review agent 复用。

## 05. 智能客服 RAG Agent 扩展

### 真实问题

智能客服和需求评审助手共享知识问答、来源引用、拒答、追问和反馈能力，但客服更强调多轮意图、话术生成和人工接管。

### 基础原理

- Intent recognition。
- Knowledge retrieval。
- Reply draft。
- Risk hint。
- Handoff。
- Feedback。

### 最小实现

- 基于同一套 RAG + 单 Agent，支持客服问答。
- 生成客服回复草稿和依据。

### 主流框架实现

- Single Agent RAG assistant。
- Human handoff。
- Conversation state。

### 失败分析与能力边界

- 用户意图识别错误。
- 客服回复过度承诺。
- 人工接管不及时。

### 评估观测

- 问答准确率。
- 追问合理性。
- 人工接管率。
- 客服采纳率。

### 小项目实战

将项目一扩展为智能客服模块。

### 项目收敛

智能客服能力成为金融 Copilot 的客服子 Agent。

## 06. 金融 Copilot 产品定义

### 真实问题

金融客服、运营、审核、合规和知识运营需要一个能理解问题、引用依据、识别风险、辅助决策和支持人机协作的 Copilot。

### 基础原理

- 核心角色。
- 金融知识类型。
- 合规风险。
- 人工协作。
- 审计要求。

### 最小实现

- 定义角色：客服、运营、合规审核、知识运营、管理员。
- 定义场景：知识问答、合规审核、公告解读、人工审批。

### 主流框架实现

- Multi-Agent。
- LangGraph Workflow。
- MCP / Tool ecosystem。
- AI Native Frontend。

### 失败分析与能力边界

- 不提供投资建议。
- 不替代合规最终责任。
- 高风险内容必须人工确认。

### 评估观测

- 合规审核准确性。
- 工具轨迹合理性。
- 人工采纳率。
- 审计完整性。

### 小项目实战

定义项目二 PRD。

### 项目收敛

本章输出金融 Copilot 产品定义。

## 07. 金融 Copilot Agent Workflows

### 真实问题

金融 Copilot 需要多个 Agent 和 Workflow 协作，而不是一个大而全的聊天助手。

### 基础原理

- Customer service agent。
- Compliance agent。
- Research agent。
- Supervisor。
- Human approval。
- Shared state。

### 最小实现

- 构建客服回答 + 合规审核两节点 workflow。
- 高风险答复进入人工确认。

### 主流框架实现

- LangGraph。
- Multi-Agent supervisor。
- Tool Runtime。
- Agentic RAG。

### 失败分析与能力边界

- 多 Agent 角色拆分过度。
- Supervisor 决策不透明。
- Workflow 状态不可恢复。

### 评估观测

- Agent 轨迹。
- Workflow path。
- Human review trigger。
- 节点耗时和失败率。

### 小项目实战

金融 Copilot V1-V3：

- V1 合规审核。
- V2 公告 / 财报解读。
- V3 多 Agent 协同。

### 项目收敛

本章输出项目二 Agent 工作流设计。

## 08. Visual Workflow Builder

### 真实问题

企业 AI 平台需要让用户配置模型调用、条件判断、知识检索、工具执行和结果输出。前端不只是画节点，还要处理校验、版本、发布、调试、日志和失败重试。

### 基础原理

- Node definition。
- Edge rule。
- Schema validation。
- Version publish。
- Run debug。
- Failed node retry。

### 最小实现

- 支持一个固定节点库。
- 拖拽配置一个审核流程。
- 校验节点参数和连线规则。

### 主流框架实现

- React Flow / 图编辑器。
- JSON workflow schema。
- LangGraph backend mapping。

### 失败分析与能力边界

- 只做画布，不做运行时。
- 节点配置无法校验。
- 发布版本不可追踪。

### 评估观测

- 配置校验错误率。
- 发布成功率。
- 运行失败节点统计。

### 小项目实战

金融 Copilot 工作流设计器：

- 检索节点。
- 模型节点。
- 工具节点。
- 条件节点。
- 人工审核节点。

### 项目收敛

工作流编排作为项目二的平台化能力。

## 09. Enterprise Knowledge Base Platform

### 真实问题

企业级知识库需要管理创建、文档分类、解析进度、切片管理、权限隔离、检索测试、引用溯源和知识回流。

### 基础原理

- Knowledge base management。
- Document lifecycle。
- Chunk management。
- ACL。
- Retrieval test。
- Source tracing。

### 最小实现

- 创建知识库。
- 上传文档。
- 查看解析和 chunk。
- 测试检索。

### 主流框架实现

- pgvector / vector store。
- Metadata filter。
- Knowledge workbench UI。

### 失败分析与能力边界

- 无权限隔离。
- 文档删除不一致。
- 检索测试不可复现。

### 评估观测

- 文档解析成功率。
- 检索命中率。
- 知识更新延迟。

### 小项目实战

项目一和项目二共享企业知识库平台。

### 项目收敛

知识库平台成为两个项目的通用底座。

## 10. Agent Management Platform

### 真实问题

企业智能体需要统一创建、配置、发布和管理，而不是散落在代码里的 prompt 和工具绑定。

### 基础原理

- Agent profile。
- Model config。
- Prompt version。
- Knowledge binding。
- Tool authorization。
- Release version。
- Run record。

### 最小实现

- 创建一个客服 Agent。
- 绑定知识库和工具。
- 发布版本。
- 查看运行记录。

### 主流框架实现

- Agent console。
- Schema driven config。
- Tool authorization UI。

### 失败分析与能力边界

- 配置项过多。
- 工具授权不透明。
- 发布无法回滚。

### 评估观测

- agent run success rate。
- config validation errors。
- version rollback count。

### 小项目实战

金融 Copilot 支持：

- 客服 Agent。
- 合规 Agent。
- Research Agent。
- Supervisor。

### 项目收敛

智能体管理平台成为项目二核心能力。

## 11. MCP Tool Ecosystem Platform

### 真实问题

智能体需要连接数据库、搜索、文件系统、企业接口和第三方服务。平台需要管理工具接入、参数配置、权限、连接测试、调用记录和异常状态。

### 基础原理

- Tool catalog。
- MCP server config。
- Tool schema。
- Permission scope。
- Connection test。
- Audit log。
- Human confirmation。

### 最小实现

- 接入一个 mock MCP tool。
- 配置参数。
- 测试连接。
- 记录调用。

### 主流框架实现

- MCP server / client 认知。
- Tool registry。
- Schema driven config。

### 失败分析与能力边界

- 工具越权。
- 高风险工具缺少人工确认。
- 工具异常不可见。

### 评估观测

- tool call success rate。
- permission denial。
- audit completeness。

### 小项目实战

金融 Copilot 工具生态：

- 知识检索。
- 文件解析。
- 合规检查。
- 审批任务。

### 项目收敛

工具生态平台支撑多 Agent 工作流。

## 12. Agent Runtime Observability Center

### 真实问题

企业用户关心任务执行到了哪一步、调用了什么工具、耗时多少、失败原因是什么，以及能否重试。

### 基础原理

- Run center。
- Trace viewer。
- Tool call log。
- Workflow path。
- Error node。
- Retry。
- Cost / latency。

### 最小实现

- 展示一次 Agent run。
- 查看工具调用、节点状态、耗时和错误。
- 支持失败节点重试。

### 主流框架实现

- Trace UI。
- Workflow runtime UI。
- Eval dashboard。

### 失败分析与能力边界

- 只能看最终结果。
- 不能定位失败节点。
- trace 和业务任务无法关联。

### 评估观测

- run success rate。
- node failure rate。
- retry success rate。
- cost per run。

### 小项目实战

金融 Copilot 运行中心：

- 客服 run。
- 合规 run。
- Research run。
- Multi-Agent run。

### 项目收敛

运行观测中心成为项目二作品化亮点。

## 13. Data Labeling 与 Evaluation Platform

### 真实问题

企业上线 AI 产品后，需要持续判断模型回答是否准确、引用是否正确、工具调用是否合理，并通过人工标注和问题回流持续优化。

### 基础原理

- QA data management。
- Human labeling。
- Model comparison。
- Score statistics。
- Bad case feedback。
- Regression suite。

### 最小实现

- 展示问答样本。
- 人工标注准确性、引用、风险。
- 加入回归集。

### 主流框架实现

- Labeling queue。
- Eval dashboard。
- Human review workflow。

### 失败分析与能力边界

- 标注标准不一致。
- 反馈不能转化为修复动作。
- 只统计分数不看 bad case。

### 评估观测

- labeling throughput。
- agreement rate。
- regression pass rate。
- bad case fix rate。

### 小项目实战

两个项目共享评测平台。

### 项目收敛

数据标注与评测平台支撑持续迭代。

## 14. Security、Ops 与 Cost Governance

### 真实问题

企业级 AI 应用不只要能运行，还要安全、稳定、可控制、可追踪、可预算。

### 基础原理

- User permission。
- Data isolation。
- Sensitive data masking。
- Audit log。
- Rate limit。
- Token cost。
- Alert。
- Deployment environment。

### 最小实现

- 基础用户权限。
- API key 环境变量。
- 调用成本统计。
- 操作审计日志。

### 主流框架实现

- FastAPI middleware。
- PostgreSQL audit table。
- Redis rate limit。
- Docker Compose。
- K8s 认知。

### 失败分析与能力边界

- 密钥泄露。
- 工具越权。
- 成本失控。
- 日志泄露敏感信息。
- 过早投入 K8s。

### 评估观测

- rate limit hits。
- cost per user。
- audit completeness。
- sensitive data exposure。

### 小项目实战

项目基础治理：

- 权限。
- 审计。
- 成本。
- 限流。
- 告警认知。

### 项目收敛

本章让项目具备企业工程可信度。

## 15. Deployment、Demo 与 Portfolio

### 真实问题

项目最终需要可运行、可演示、可讲述。只有代码没有演示路径，简历和面试价值都会下降。

### 基础原理

- Local demo。
- Docker Compose demo。
- Cloud deployment strategy。
- Demo script。
- Project README。
- Portfolio story。

### 最小实现

- 本地一键启动。
- 准备演示数据。
- 跑通核心链路。
- 输出项目 README。

### 主流框架实现

- Docker Compose。
- Vercel / Cloudflare Pages。
- FastAPI 本地或低成本托管。
- Supabase / PostgreSQL。

### 失败分析与能力边界

- 演示依赖手工步骤太多。
- 数据准备不稳定。
- 缺少失败案例和质量面板。
- 作品集只讲功能，不讲架构和取舍。

### 评估观测

- demo setup time。
- demo success rate。
- 核心链路可复现。
- README 是否讲清价值和边界。

### 小项目实战

两个项目演示路径：

- 需求评审助手：上传文档 -> 问答 -> sources -> 单 Agent 追问 -> eval。
- 金融 Copilot：客服问题 -> 合规审核 -> 人工确认 -> trace -> 质量面板。

### 项目收敛

本课程最终输出两个可展示项目和一套清晰的作品集叙事。
