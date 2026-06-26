# 06 AI Native 体验与项目工程大纲

## 课程定位

`06_ai_native` 是需求评审助手的 AI Native 体验与项目工程主线。

这门课不是传统前端基础课，也不是后台运维大课。它关注两件事：一是前端如何承接 LLM / RAG / Agent / Workflow 的不确定输出、流式过程、工具轨迹、动态结果、人工确认和质量反馈；二是补齐项目必需的 FastAPI、PostgreSQL / pgvector、Redis、后台任务和 Docker Compose 等工程能力。

AI 体验与工程能力不会等到本课程才第一次出现。`03_rag` 中需要最小 RAG UI，`04_agent` 中需要最小 Agent UI，`05_eval_observability` 中需要最小评估面板。`06_ai_native` 的作用是系统化抽象这些能力，沉淀为需求评审助手的 AI Native 工作台与项目工程方案。

### 前端技术选型

- **协议与状态机优先**：SSE 事件格式、JSON Schema / UI Schema、AI response state machine 与具体 UI 框架解耦；这些协议在 `07_projects` 中可被 Flutter 工作台复用。
- **本课程默认实现栈：Vue 3**（管理端 / 工作台 demo 用 Vue 验证交互与组件边界，降低同时学 AI 链路与 Flutter 的并行成本）。
- **Flutter 定位**：作为需求评审助手 V6 工作台与作品集的主交付前端（跨端、复杂运行态 UI）；学习重点放在「同一套 event protocol + schema 如何在 Flutter 落地」，而非在本课程重复实现全部页面。
- **不要求** React / Vue / Flutter 三套都写一遍；Vue demo 证明协议，Flutter 在 `07_projects/11` 作品化收敛。

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

## 与 03 / 04 / 05 / 07 的关系

`03_rag` 提供 sources、refusal、retrieval debug、knowledge workbench 的最小场景。

`04_agent` 提供 tool call、multi-agent trajectory、workflow runtime、human approval 的最小场景。

`05_eval_observability` 提供 eval dashboard、trace viewer、bad case board、cost / latency panel 的最小场景。

`06_ai_native` 把这些场景系统化为 AI Native 体验能力与项目工程能力。

`07_projects` 把这些能力应用到需求评审助手。

## 完成标准

完成本课程后，应能做到：

- 设计 SSE / stream 前后端状态同步方案。
- 建立 AI response state machine，处理 streaming、tool call、workflow、cancel、retry、resume。
- 设计 JSON Schema / UI Schema 交互协议，并安全渲染结构化结果。
- 设计多 Agent UI / UX，展示工具轨迹但不制造噪声。
- 设计 Workflow Runtime UI，支持节点状态、失败重试、人工确认和运行日志。
- 设计 RAG knowledge workbench、eval feedback UI 和 trace viewer。
- 理解 FastAPI、PostgreSQL / pgvector、Redis、后台任务、Docker Compose 在当前项目中的职责。
- 为需求评审助手提供可复用的 AI Native 工作台体验模式。
- 用 Vue 实现至少一条完整 AI Native 交互链路（流式 + sources + 状态机）。
- 能说明同一套 SSE / schema 协议如何迁移到 Flutter 工作台（组件映射表或接口清单）。

## 代码组织建议

```text
source/06_ai_native/
├── packages/
│   ├── ai_ui_protocol/
│   ├── ai_state_machine/
│   └── ai_workbench_components/
├── demos/                          # 默认 Vue 3 实现
│   ├── streaming_state_sync/
│   ├── schema_driven_ui/
│   ├── structured_review_report_ui/
│   ├── multi_agent_timeline_ui/
│   ├── workflow_runtime_ui/
│   ├── knowledge_workbench_ui/
│   └── eval_feedback_ui/
└── README.md

# 07_projects 侧 Flutter workbench 复用 ai_ui_protocol，不重复发明事件格式
```

## 专题目录

```text
course/06_ai_native/
├── 00_ai_native_problem_space.md
├── 01_streaming_state_synchronization.md
├── 02_ai_response_state_machine.md
├── 03_schema_driven_interaction_protocol.md
├── 04_structured_review_report_ui.md
├── 05_multi_agent_ui_ux_patterns.md
├── 06_workflow_runtime_ui.md
├── 07_rag_knowledge_workbench.md
├── 08_eval_labeling_feedback_ui.md
├── 09_fastapi_service_layer_and_api_design.md
├── 10_postgres_pgvector_data_model.md
├── 11_redis_background_jobs_and_ingestion_tasks.md
├── 12_docker_compose_local_deployment.md
├── 13_engineering_observability_basics.md
├── 14_project_ai_native_architecture.md
└── outline.md
```

## 00. AI Native 问题空间

### 真实问题

需求评审助手不是普通聊天 UI。用户需要看到依据、风险、Agent 分工、工具调用、节点状态、人工确认、质量反馈和最终报告。

### 基础原理

- AI 输出具有不确定性。
- AI 执行过程是事件流，不只是一次 HTTP 响应。
- AI UI 需要表达过程、依据、风险、状态、权限和人工协作。
- AI Native 前端要和后端任务、trace、workflow 状态对齐。

### 最小实现

- 展示一次 AI 请求的状态变化：idle -> retrieving -> analyzing -> waiting_review -> completed / failed。

### 主流框架实现

- **本课程专题 demo：Vue 3**（Composition API + 按 event type 更新 store）。
- **项目作品化：Flutter**（`07_projects/11`；复用本课程定义的 protocol，不重复发明事件格式）。
- React 仅作生态对照认知，不作为本仓库默认实现栈。

### 失败分析与能力边界

- 把 AI 应用做成普通聊天框。
- 只展示最终答案，不展示依据和状态。
- 暴露过多内部过程，反而干扰用户。

### 评估观测

- 用户是否能理解 AI 正在做什么。
- 用户是否能找到依据和风险。
- 用户是否能在关键节点干预。

### 小项目实战

为需求评审助手定义最小 AI Native UI：

- 文档上传。
- 流式状态。
- sources。
- risk badge。
- multi-agent timeline。
- feedback。

### 项目收敛

输出需求评审助手 AI Native 能力地图。

## 01. Streaming State Synchronization

### 真实问题

AI 应用最基础的前端能力是流式状态同步。模型 token、检索、Agent step、工具调用、工作流节点、错误、取消、重连都可能通过事件流到达前端。

### 基础原理

- SSE。
- fetch stream。
- WebSocket。
- Token stream。
- Event stream。
- Tool stream。
- Workflow stream。
- 前后端消息一致性。

### 最小实现

- 后端发送 `message_start / retrieval_start / agent_step / tool_call / workflow_node / token / error / done`。
- 前端按事件更新 UI 状态。
- 支持 cancel / retry。

### 主流框架实现

- EventSource。
- fetch ReadableStream。
- Flutter stream。
- WebSocket 用于双向实时任务。

### 失败分析与能力边界

- token 到达顺序错乱。
- 刷新页面后状态丢失。
- 取消请求后后端仍在执行。
- 网络中断后重复消息。

### 评估观测

- 首 token 时间。
- 流中断率。
- 重连成功率。
- 前后端状态一致性。

### 小项目实战

需求评审助手支持：

- 流式回答。
- 检索中状态。
- Agent 分析中状态。
- 工具调用中状态。
- 失败重试。

### 项目收敛

沉淀 `ai_state_machine.streaming`。

## 02. AI Response State Machine

### 真实问题

AI 请求不是 loading / success / error 三态。真实任务可能经历上传、入库、检索、生成、工具调用、人工确认、中断、恢复、失败、重试和完成。

### 基础原理

- Response state machine。
- Task state。
- Message state。
- Tool state。
- Agent state。
- Workflow state。
- Review state。

### 最小实现

- 定义 AI response 状态机。
- 前端根据状态渲染不同组件。
- 支持暂停、恢复、取消和失败重试。

### 主流框架实现

- XState 思路。
- 前端 store。
- 后端 task id / run id。
- LangGraph run state 对接。

### 失败分析与能力边界

- 多个状态源互相覆盖。
- 前端显示 completed，但后端任务仍在运行。
- 人工确认状态没有持久化。

### 评估观测

- 状态转移是否合法。
- 异常状态是否可恢复。
- 用户是否知道当前任务卡在哪里。

### 小项目实战

需求评审助手任务状态：

- uploading。
- indexing。
- retrieving。
- analyzing。
- waiting_human_review。
- generating_report。
- completed / failed / canceled。

### 项目收敛

沉淀 `ai_state_machine.core`。

## 03. Schema Driven Interaction Protocol

### 真实问题

需求评审助手需要动态表单、结构化结果展示、工具参数配置、人工确认和反馈表单。前后端不能只靠自然语言传输，必须建立 JSON Schema / UI Schema 交互协议。

### 基础原理

- JSON Schema。
- UI Schema。
- Form schema。
- Result schema。
- Tool argument schema。
- Validation。
- Safe rendering。

### 最小实现

- 定义一个风险项 schema。
- 前端根据 schema 渲染风险卡片。
- 对用户反馈表单做校验。

### 主流框架实现

- JSON Schema。
- react-jsonschema-form / formily 认知。
- Zod / Pydantic schema 对齐。

### 失败分析与能力边界

- 后端 schema 和前端类型不一致。
- 动态 UI 渲染不安全。
- 模型输出字段变化导致 UI 崩溃。

### 评估观测

- schema validation 成功率。
- UI 渲染错误率。
- 字段缺失率。

### 小项目实战

设计交互协议：

- 需求提交表单。
- 缺失信息追问表单。
- 风险项 schema。
- 评审报告 schema。
- feedback schema。

### 项目收敛

沉淀 `ai_ui_protocol.schema`。

## 04. Structured Review Report UI

### 真实问题

最终报告不能只是 Markdown。用户需要按模块查看摘要、风险、证据、建议、待确认问题和验收点。

### 基础原理

- Structured result rendering。
- Risk cards。
- Citation panel。
- Editable report。
- Confidence display。
- Export。
- Human correction。

### 最小实现

- 用结构化 JSON 渲染评审报告。
- 支持展开引用来源。
- 支持人工修改报告内容。

### 主流框架实现

- React / Vue component。
- Markdown + structured blocks。
- PDF / Markdown export 认知。

### 失败分析与能力边界

- 只展示 Markdown，无法定位字段。
- 引用和风险项脱离。
- 人工修改没有记录。

### 评估观测

- 报告字段完整率。
- 引用点击率。
- 人工修改类型。
- 导出成功率。

### 小项目实战

实现结构化评审报告 UI：

- 需求摘要。
- 风险列表。
- 技术影响。
- 测试验收点。
- 待确认问题。
- 引用来源。
- 人工修改记录。

### 项目收敛

沉淀评审报告组件。

## 05. Multi-Agent UI / UX Patterns

### 真实问题

多 Agent 运行过程如果完全隐藏，用户不信任；如果全部暴露，又会制造噪声。

### 基础原理

- Agent timeline。
- Role status。
- Tool call summary。
- Evidence handoff。
- Conflict marker。
- Supervisor decision。
- Progressive disclosure。

### 最小实现

- 展示 3 个 Agent 的运行状态。
- 每个 Agent 只展示状态、摘要和关键引用。

### 主流框架实现

- Timeline。
- Stepper。
- Trace tree。
- Collapsible panel。

### 失败分析与能力边界

- 把内部推理全部暴露给用户。
- Agent 状态太细导致噪声。
- 工具失败没有清晰反馈。

### 评估观测

- 用户是否理解当前进度。
- 用户是否能找到失败原因。
- timeline 是否帮助定位问题。

### 小项目实战

展示多 Agent 运行轨迹：

- 需求理解 Agent 完成。
- 知识检索 Agent 命中来源。
- 风险审查 Agent 输出风险。
- 技术影响 Agent 输出影响点。
- 测试验收 Agent 输出验收建议。
- 汇总 Agent 生成报告。

### 项目收敛

沉淀 multi-agent timeline 组件。

## 06. Workflow Runtime UI

### 真实问题

Workflow 需要让用户知道任务卡在哪里，为什么需要人工确认，失败后能否重试。

### 基础原理

- Node state。
- Edge transition。
- Interrupt。
- Resume。
- Retry。
- Failure reason。
- Run log。
- Human approval。

### 最小实现

- 展示当前节点、已完成节点和失败节点。
- 人工确认后继续执行。

### 主流框架实现

- LangGraph event stream。
- Workflow stepper。
- Run log panel。

### 失败分析与能力边界

- 节点状态与后端不一致。
- 人工确认表单没有持久化。
- 失败重试重复执行高风险步骤。

### 评估观测

- 节点状态一致性。
- retry 成功率。
- 用户确认耗时。

### 小项目实战

实现需求评审 Workflow UI：

- 当前节点。
- 已完成节点。
- 失败节点。
- 人工确认节点。
- 继续执行。
- 重新运行节点。

### 项目收敛

沉淀 workflow runtime 组件。

## 07. RAG Knowledge Workbench

### 真实问题

用户需要管理知识库，观察文档状态，调试检索结果，否则 RAG 质量无法持续提升。

### 基础原理

- Knowledge list。
- Document ingestion。
- Document status。
- Chunk preview。
- Metadata editing。
- Retrieval test。
- Citation preview。
- Re-index。

### 最小实现

- 展示文档列表和入库状态。
- 预览 chunk。
- 输入问题测试检索。

### 主流框架实现

- 数据表格。
- 文件上传。
- 检索调试面板。
- 后台任务状态轮询 / 事件流。

### 失败分析与能力边界

- 只允许上传，不展示入库状态。
- 用户无法判断为什么检索不到。
- metadata 无法修正。

### 评估观测

- 文档入库成功率。
- 检索测试命中率。
- re-index 成功率。

### 小项目实战

实现需求评审知识库工作台：

- 上传 PRD / API 文档 / 规则 / 历史评审。
- 查看解析和向量化状态。
- 预览 chunk。
- 测试检索。
- 查看引用片段。

### 项目收敛

沉淀 knowledge workbench。

## 08. Eval、Labeling 与 Feedback UI

### 真实问题

质量工程需要用户和开发者能够查看样本、标注结果、管理 bad case 和反馈修复状态。

### 基础原理

- Golden set UI。
- Eval run report。
- Trace viewer。
- Bad case board。
- Feedback form。
- Annotation workflow。

### 最小实现

- 展示一次 eval run 结果。
- 展示失败样本和 bad case 状态。

### 主流框架实现

- Dashboard。
- Labeling table。
- Trace detail drawer。
- Feedback form。

### 失败分析与能力边界

- 面板只有指标，没有样本。
- bad case 无法回流。
- 用户反馈太粗，无法修复。

### 评估观测

- 标注完成率。
- bad case 修复率。
- feedback 有效率。

### 小项目实战

实现最小质量面板：

- 检索命中率。
- 引用正确率。
- 拒答准确率。
- 风险覆盖率。
- Agent 工具调用成功率。
- bad case 状态。

### 项目收敛

沉淀 eval feedback UI。

## 09. FastAPI Service Layer 与 API Design

### 真实问题

AI Native 前端需要可靠 API 支撑。当前阶段需要基础后端能力，但不转向复杂后端平台。

### 基础原理

- FastAPI。
- API layer。
- Service layer。
- Request / response schema。
- Error handling。
- Auth placeholder。
- Event endpoint。
- Background task endpoint。

### 最小实现

- 建立 FastAPI app。
- 实现一个文档上传 API 和一个 review run API。
- 定义统一错误返回。

### 主流框架实现

- FastAPI。
- Pydantic。
- SQLAlchemy / SQLModel 认知。
- SSE endpoint。

### 失败分析与能力边界

- API 直接写业务细节，难以复用。
- 后端状态和前端状态不一致。
- 错误处理不统一。

### 评估观测

- API 成功率。
- 错误类型。
- event endpoint 稳定性。

### 小项目实战

设计项目 API：

- document API。
- knowledge API。
- review run API。
- chat / event API。
- feedback API。
- eval API。

### 项目收敛

沉淀当前项目后端 API 边界。

## 10. PostgreSQL / pgvector Data Model

### 真实问题

业务数据、知识库元数据与向量需要清晰的数据模型，避免 Redis、向量库与业务表职责混乱。

### 基础原理

- PostgreSQL 保存 Document、ReviewRun、ChatRecord 等业务数据。
- pgvector 保存 Embedding。
- 表结构与 `07_projects` 运营对象对齐。

### 最小实现

- 定义 Document、Chunk、Embedding 最小表结构。
- 完成一次向量写入与查询。

### 主流框架实现

- PostgreSQL、pgvector。
- SQLAlchemy / SQLModel。

### 失败分析与能力边界

- 向量与文档状态不一致。
- 过早引入复杂分库分表。

### 评估观测

- 数据一致性检查。
- 索引构建耗时。

### 小项目实战

实现需求评审助手最小数据模型，含 ChatRecord 与 ReviewRun 关联。

### 项目收敛

沉淀项目数据模型文档。

## 11. Redis、Background Jobs 与 Ingestion Tasks

### 真实问题

文档入库、向量化、评审运行和质量记录需要后台任务与任务状态管理。

### 基础原理

- Redis 用于任务状态、缓存或轻量队列。
- 后台任务处理解析、embedding、评估运行。
- 不过早引入复杂分布式系统。

### 最小实现

- 用 Redis 记录 ingestion job 状态。
- 跑通 upload → parse → chunk → embed → update status。

### 主流框架实现

- Redis。
- Celery / RQ / arq 认知。

### 失败分析与能力边界

- Redis 和数据库职责混乱。
- 后台任务失败没有重试。

### 评估观测

- job 成功率。
- embedding 耗时。

### 小项目实战

实现最小任务链路：

```text
upload document
-> create ingestion job
-> parse document
-> chunk
-> embed
-> update status
```

### 项目收敛

沉淀基础任务与队列组合。

## 12. Docker Compose Local Deployment

### 真实问题

作品化项目必须能在本地稳定启动，而不是只靠零散脚本。

### 基础原理

- Dockerfile。
- docker-compose。
- environment variables。
- database migration。
- service health check。
- local seed data。
- start / stop / reset。

### 最小实现

- 用 docker-compose 启动 API、PostgreSQL 和 Redis。
- 提供初始化脚本。

### 主流框架实现

- Docker Compose。
- Makefile / scripts。
- `.env`。
- healthcheck。

### 失败分析与能力边界

- 环境变量散落。
- 初始化步骤依赖人工记忆。
- 本地和演示环境不一致。

### 评估观测

- 一键启动成功率。
- 初始化耗时。
- 服务健康检查结果。

### 小项目实战

一键启动：

- API。
- PostgreSQL / pgvector。
- Redis。
- 前端。
- worker。

### 项目收敛

输出本地部署方案。

## 13. Engineering Observability Basics

### 真实问题

项目工程需要基础可观测：请求日志、健康检查、配置管理与统一错误返回，才能与 AI trace 衔接。

### 基础原理

- 结构化日志与请求 ID。
- Health check endpoint。
- 环境变量与配置分层。
- 与 `05_eval_observability` trace 的分工。

### 最小实现

- 为 FastAPI 增加 health check 与请求日志中间件。
- 统一错误响应格式。

### 主流框架实现

- logging、middleware。
- OpenTelemetry 认知。

### 失败分析与能力边界

- 工程日志与 AI span 混淆。
- 过早做完整告警平台。

### 评估观测

- 健康检查通过率。
- 错误日志可定位率。

### 小项目实战

为需求评审 API 增加 health、request id 和基础日志字段。

### 项目收敛

沉淀工程观测最小规范。

## 14. Project AI Native Architecture

### 真实问题

当前需要的是需求评审助手项目架构，而不是泛化企业 AI 平台架构。

### 基础原理

- Frontend workbench。
- Backend API。
- LLM layer。
- RAG layer。
- Agent / Workflow layer。
- Eval / Trace layer。
- Infra layer。
- Future extension boundary。

### 最小实现

- 画出需求评审助手架构图。
- 标注请求流、事件流、数据流。

### 主流框架实现

- FastAPI、PostgreSQL / pgvector、Redis、LangChain / LangGraph。
- 前端：Vue（本课程验证）→ Flutter（项目 V6 工作台交付）。

### 失败分析与能力边界

- 架构图画成泛化平台大图。
- 忽略当前项目主链路。
- 过早做 Agent 管理平台、MCP 工具市场或实时语音。

### 评估观测

- 架构是否能解释一次完整评审请求。
- 模块边界是否清晰。
- 失败是否能定位到层级。

### 小项目实战

画出需求评审助手架构：

```text
Workbench
-> API / Event Stream
-> LLM Core
-> RAG Core
-> Agent / Workflow Core
-> Eval / Trace Core
-> PostgreSQL / pgvector / Redis
```

### 项目收敛

本课程最终产出 AI Native 工作台设计、前后端协议、基础工程方案和当前项目架构图，进入 `07_projects` 完整作品化。

## 参考设计映射

### MaxKB

- 应用工作台、会话记录、Workflow 节点流式输出、知识库管理、PostgreSQL / pgvector / Redis / 任务队列组合。

### RAGFlow

- 知识库工作台、检索调试、Agent Canvas 运行态和评估入口设计。
