# 06 AI Native 前端、Agent UI 与生成式交互大纲

## 课程定位

`06_ai_native_frontend` 是 AI 应用前端运行时、交互协议、Agent UI/UX、生成式 UI、多模态任务交互和企业 AI 平台前端能力主线。

这门课不是传统前端基础课，也不是后台管理页面课。它关注的是：前端如何承接 LLM / RAG / Agent / Workflow 的不确定输出、流式过程、工具轨迹、动态 UI、协议化交互、多模态任务和企业级 AI 平台配置。

AI 前端展示不会等到本课程才第一次出现。`03_rag` 中已经需要最小 RAG UI，`04_agent` 中已经需要最小 Agent UI，`05_eval_observability` 中已经需要最小评估面板。`06_ai_native_frontend` 的作用是系统化抽象这些能力，把它们沉淀成可复用的 AI Native 前端模式。

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

`04_agent` 提供 tool call、agent trajectory、workflow runtime、human approval 的最小场景。

`05_eval_observability` 提供 eval dashboard、trace viewer、bad case board、cost / latency panel 的最小场景。

`06_ai_native_frontend` 把这些场景系统化为 AI Native 前端能力。

`07_projects` 把这些能力应用到需求评审 RAG 助手 / 智能客服和金融 Copilot。

## 完成标准

完成本课程后，应能做到：

- 设计 SSE / stream 前后端状态同步方案。
- 建立 AI response state machine，处理 streaming、tool call、workflow、cancel、retry、resume。
- 设计 JSON Schema / UI Schema 交互协议，并安全渲染动态 UI。
- 理解 Generative UI / Dynamic Components / Flutter GenUI / Web GenUI 的边界。
- 设计 Agent UI / UX，展示工具轨迹但不制造噪声。
- 设计 Workflow Runtime UI，支持节点状态、失败重试、人工确认和运行日志。
- 设计 RAG knowledge workbench、Agent management console、MCP tool config UI。
- 设计实时语音、多模态文档智能体、PDF / PPT / Word / Image 交互。
- 为两个主项目提供可复用的 AI 前端体验模式。

## 代码组织建议

```text
source/06_ai_native_frontend/
├── packages/
│   ├── ai_ui_protocol/
│   ├── ai_state_machine/
│   └── ai_workbench_components/
├── demos/
│   ├── streaming_state_sync/
│   ├── schema_driven_ui/
│   ├── agent_timeline_ui/
│   ├── workflow_runtime_ui/
│   ├── multimodal_document_ui/
│   └── realtime_voice_ui/
└── README.md
```

## 专题目录

```text
course/06_ai_native_frontend/
├── 00_ai_native_frontend_problem_space.md
├── 01_streaming_state_synchronization.md
├── 02_ai_response_state_machine.md
├── 03_schema_driven_interaction_protocol.md
├── 04_generative_ui_dynamic_components.md
├── 05_agent_ui_ux_patterns.md
├── 06_workflow_runtime_ui.md
├── 07_rag_knowledge_workbench.md
├── 08_agent_management_console.md
├── 09_mcp_tool_ecosystem_ui.md
├── 10_multimodal_document_agent_ui.md
├── 11_realtime_voice_interaction.md
├── 12_eval_labeling_feedback_ui.md
├── 13_enterprise_ai_frontend_architecture.md
└── outline.md
```

## 00. AI Native 前端问题空间

### 真实问题

企业真正需要的 AI 前端，不只是把模型回答展示出来，而是把模型、知识库、工作流、智能体、工具生态、评估和业务系统整合成稳定、可配置、可管理的平台。

### 基础原理

- AI 输出具有不确定性。
- AI 执行过程是事件流，不只是一次 HTTP 响应。
- AI UI 需要表达过程、依据、风险、状态、权限和人工协作。
- AI 前端从页面开发升级为运行时、协议和工作台设计。

### 最小实现

- 展示一次 AI 请求的状态变化：idle -> streaming -> tool_calling -> waiting_review -> completed / failed。

### 主流框架实现

- React / Vue / Flutter 都可以承载 AI Native UI。
- 重点不是框架选择，而是协议、状态机、组件边界和交互模式。

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

- 流式回答。
- sources。
- risk badge。
- tool timeline。
- feedback。

### 项目收敛

本章输出 AI Native 前端能力地图。

## 01. Streaming State Synchronization

### 真实问题

AI 应用最基础的前端能力是流式状态同步。模型 token、工具调用、工作流节点、错误、取消、重连都可能通过事件流到达前端。

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

- 后端发送 `message_start / token / tool_call / error / done`。
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
- 工具调用中状态。
- 失败重试。

### 项目收敛

沉淀 `ai_state_machine.streaming`。

## 02. AI Response State Machine

### 真实问题

AI 请求不是 loading / success / error 三态。真实任务可能经历排队、检索、生成、工具调用、人工确认、中断、恢复、失败、重试和完成。

### 基础原理

- Response state machine。
- Task state。
- Message state。
- Tool state。
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

金融 Copilot 的任务状态：

- drafting。
- retrieving。
- checking_compliance。
- waiting_human_review。
- approved。
- rejected。

### 项目收敛

沉淀 `ai_state_machine.core`。

## 03. Schema Driven Interaction Protocol

### 真实问题

AI 应用需要动态表单、动态卡片、工具参数配置、结构化结果展示和生成式 UI。前后端不能只靠自然语言传输，必须建立 JSON Schema / UI Schema 交互协议。

### 基础原理

- JSON Schema。
- UI Schema。
- Tool input schema。
- Structured output schema。
- Action schema。
- Schema -> Form / Card / Table / Action。

### 最小实现

- 后端返回一个 review result schema。
- 前端根据 schema 渲染风险卡片、引用列表和操作按钮。

### 主流框架实现

- JSON Schema form。
- Zod / Pydantic schema 对齐。
- Schema registry。
- 白名单组件渲染。

### 失败分析与能力边界

- 模型直接生成任意 UI 不安全。
- schema 版本不兼容。
- 动态字段缺少校验。
- 前端渲染能力暴露过大。

### 评估观测

- schema validation pass rate。
- UI render error。
- schema version mismatch。

### 小项目实战

需求评审助手使用 schema 展示：

- risks。
- questions。
- suggestions。
- citations。
- actions。

### 项目收敛

沉淀 `ai_ui_protocol.schema`。

## 04. Generative UI 与 Dynamic Components

### 真实问题

生成式 UI 不是让模型随意写页面，而是让模型在安全协议内选择合适的组件、填充结构化数据、生成交互动作。

### 基础原理

- Generative UI。
- Dynamic Components。
- Component registry。
- UI intent。
- Safe rendering。
- Flutter GenUI / Web GenUI 思路。

### 最小实现

- 定义组件白名单：risk_card、source_list、review_form、chart_card。
- 模型输出 UI intent。
- 前端根据 schema 渲染动态组件。

### 主流框架实现

- Vercel AI SDK UI 思路认知。
- Flutter GenUI 方向认知。
- 自定义 component registry。

### 失败分析与能力边界

- 模型生成不可控 UI。
- 动态 UI 破坏产品一致性。
- 组件能力过大导致安全风险。

### 评估观测

- component selection accuracy。
- render success rate。
- 用户是否能完成任务。

### 小项目实战

金融 Copilot 根据任务类型生成：

- 问答卡片。
- 合规风险卡片。
- 公告解读卡片。
- 审核表单。

### 项目收敛

沉淀 `ai_workbench_components.dynamic_ui`。

## 05. Agent UI / UX Patterns

### 真实问题

Agent 不是聊天框。用户需要知道 Agent 正在做什么、调用了什么工具、是否需要自己介入，但不需要被内部推理噪声淹没。

### 基础原理

- Agent step timeline。
- Tool call disclosure。
- Plan / Action / Observation 的展示边界。
- Progressive disclosure。
- User intervention。

### 最小实现

- 展示一个 Agent 执行时间线。
- 每步包括状态、工具名、摘要、耗时、结果。
- 支持展开 tool input / output。

### 主流框架实现

- Timeline UI。
- Trace viewer。
- Agent run panel。

### 失败分析与能力边界

- 展示过多内部推理。
- 工具失败原因不可见。
- 用户不知道何时可以介入。

### 评估观测

- 用户能否理解当前步骤。
- 用户是否能定位失败节点。
- 工具轨迹是否和 trace 对齐。

### 小项目实战

需求评审助手展示：

- 问题改写。
- 知识源选择。
- 检索结果检查。
- 最终回答生成。

### 项目收敛

沉淀 `ai_workbench_components.agent_timeline`。

## 06. Workflow Runtime UI

### 真实问题

LangGraph / Workflow 的运行态需要可视化：节点状态、分支、失败、重试、中断、恢复、人工确认和运行日志。

### 基础原理

- Workflow run。
- Node status。
- Edge path。
- Interrupt / resume。
- Retry failed node。
- Run log。
- Version。

### 最小实现

- 展示一个合规审核 workflow 的节点状态。
- 失败节点可重试。
- 人工确认节点可提交意见。

### 主流框架实现

- DAG / flow viewer。
- Timeline + graph hybrid UI。
- React Flow / Flutter graph view 思路。

### 失败分析与能力边界

- 只画节点，不展示运行态。
- 节点状态和后端 run state 不一致。
- 失败后无法重试或恢复。

### 评估观测

- 节点状态同步准确率。
- resume 成功率。
- 用户定位失败节点耗时。

### 小项目实战

金融 Copilot 合规审核流程：

- 输入草稿。
- 检索规则。
- 风险判断。
- 人工确认。
- 发布建议。

### 项目收敛

沉淀 `ai_workbench_components.workflow_runtime`。

## 07. RAG Knowledge Workbench

### 真实问题

企业级 RAG 前端不是文件上传 + 问答。还需要知识库创建、文档分类、解析进度、切片管理、权限隔离、检索测试和引用溯源。

### 基础原理

- Knowledge base。
- Document lifecycle。
- Parse status。
- Chunk view。
- Metadata editor。
- Retrieval test。
- Citation preview。

### 最小实现

- 上传文档。
- 展示解析状态。
- 预览 chunk。
- 输入问题测试检索。
- 展示命中来源。

### 主流框架实现

- Admin workbench。
- Search debug panel。
- Source preview drawer。

### 失败分析与能力边界

- 用户看不到解析失败原因。
- chunk 不可检查。
- 权限和版本不可见。
- 检索测试无法复现线上结果。

### 评估观测

- 文档解析成功率。
- chunk 质量反馈。
- 检索测试命中率。

### 小项目实战

需求评审助手知识工作台：

- PRD。
- API 文档。
- 规则文档。
- 历史评审记录。

### 项目收敛

沉淀 `ai_workbench_components.knowledge_workbench`。

## 08. Agent Management Console

### 真实问题

企业中的智能体通常不是一个聊天窗口，而是一套可以统一创建、配置、发布和管理的数字员工。

### 基础原理

- Agent profile。
- Model config。
- Prompt config。
- Knowledge binding。
- Tool authorization。
- Parameters。
- Version publish。
- Run records。

### 最小实现

- 创建一个客服助手配置页。
- 绑定模型、知识库和工具。
- 发布版本并查看运行记录。

### 主流框架实现

- Agent console。
- Versioned config。
- Permission-aware tool binding。

### 失败分析与能力边界

- 配置过多导致用户无法理解。
- 发布版本不可回滚。
- 工具授权不透明。

### 评估观测

- 配置校验错误。
- 发布成功率。
- 版本回滚次数。
- 工具授权变更记录。

### 小项目实战

金融 Copilot 支持：

- 客服 Agent。
- 合规 Agent。
- 公告解读 Agent。
- Supervisor。

### 项目收敛

沉淀 `ai_workbench_components.agent_console`。

## 09. MCP 与 Tool Ecosystem UI

### 真实问题

智能体需要调用数据库、搜索、文件系统、企业接口和第三方服务。前端需要支持工具接入、参数配置、权限控制、连接测试、调用记录和异常状态展示。

### 基础原理

- Tool catalog。
- MCP server config。
- Tool parameter form。
- Permission scope。
- Connection test。
- Call log。
- Human confirmation。

### 最小实现

- 展示工具目录。
- 配置一个 mock 工具。
- 测试连接。
- 查看调用记录。

### 主流框架实现

- MCP 工具配置面板。
- JSON Schema form。
- Tool audit log。

### 失败分析与能力边界

- 工具权限过大。
- 连接失败原因不清。
- 高风险工具缺少确认。
- 调用记录不可追溯。

### 评估观测

- connection success rate。
- tool call failure rate。
- permission denial。
- human confirmation trigger。

### 小项目实战

金融 Copilot 工具生态：

- 知识检索工具。
- 合规检查工具。
- 审批任务工具。
- 文件解析工具。

### 项目收敛

沉淀 `ai_workbench_components.tool_ecosystem`。

## 10. Multimodal Document Agent UI

### 真实问题

企业 AI 应用经常处理 PDF、PPT、Word、图片、表格和公告截图。前端需要展示上传、解析、定位、引用、预览和多模态结果，而不是只传一个文件给后端。

### 基础原理

- File task。
- Parse pipeline。
- Page / slide / block。
- OCR / vision result。
- Citation location。
- Document preview。
- Multimodal response。

### 最小实现

- 上传 PDF / PPT。
- 展示解析进度。
- 预览页码和片段。
- 答案引用定位到页面或幻灯片。

### 主流框架实现

- PDF viewer。
- PPT preview。
- Image annotation。
- Document intelligence workflow。

### 失败分析与能力边界

- 文件解析长时间无反馈。
- 引用不能定位到原文。
- OCR 错误不可见。
- 多模态结果和文本索引不一致。

### 评估观测

- parse success rate。
- page citation accuracy。
- upload failure rate。
- user correction rate。

### 小项目实战

金融 Copilot 支持：

- 公告 PDF 解读。
- 财报表格定位。
- PPT 资料问答。
- 截图风险识别。

### 项目收敛

沉淀 `ai_workbench_components.document_agent`。

## 11. Realtime Voice Interaction

### 真实问题

部分 AI Copilot 场景需要实时语音输入、语音打断、实时转写、语音回复和多模态协作。

### 基础原理

- Realtime audio。
- ASR。
- TTS。
- Duplex / half-duplex。
- Interrupt。
- Turn detection。
- Voice state。

### 最小实现

- 实时录音。
- 展示转写文本。
- 支持打断和停止。
- 将语音输入转为任务事件。

### 主流框架实现

- WebRTC 认知。
- Realtime API 认知。
- Flutter audio stream。

### 失败分析与能力边界

- 延迟过高。
- 打断失败。
- 转写错误导致任务错误。
- 金融高风险场景不适合自动语音确认。

### 评估观测

- end-to-end latency。
- transcription accuracy。
- interruption success rate。
- user correction rate。

### 小项目实战

客服 Copilot 支持语音输入：

- 客服口述问题。
- 自动转写。
- 检索知识。
- 生成回复草稿。

### 项目收敛

沉淀 `ai_workbench_components.voice_interaction`。

## 12. Eval、Labeling 与 Feedback UI

### 真实问题

企业上线 AI 后，需要持续判断回答是否准确、引用是否正确、工具调用是否合理，并把人工标注和用户反馈回流。

### 基础原理

- Labeling task。
- Human eval。
- Feedback form。
- Bad case board。
- Model comparison。
- Regression summary。

### 最小实现

- 展示一条问答样本。
- 人工标注答案准确性、引用质量和风险提示。
- 将问题加入 bad case。

### 主流框架实现

- Labeling UI。
- Eval dashboard。
- Review queue。

### 失败分析与能力边界

- 反馈字段太粗。
- 标注标准不一致。
- 反馈无法路由到修复项。

### 评估观测

- labeling throughput。
- agreement rate。
- actionable feedback rate。
- bad case fix rate。

### 小项目实战

需求评审助手支持：

- 答案有用 / 无用。
- 引用错误。
- 风险遗漏。
- 需要补充知识。

### 项目收敛

沉淀 `ai_workbench_components.eval_feedback`。

## 13. Enterprise AI Frontend Architecture

### 真实问题

企业级 AI 前端不是几个页面，而是长期演进的平台工程。它需要多环境配置、权限体系、菜单路由、接口规范、状态管理、异常处理、日志监控、组件复用、多人协作和持续迭代。

### 基础原理

- Module architecture。
- Route and permission。
- API contract。
- State store。
- Error boundary。
- Feature flag。
- Logging。
- Component system。
- Deployment environments。

### 最小实现

- 设计 AI workbench 前端模块结构。
- 划分 chat、knowledge、agent、workflow、eval、admin 模块。
- 定义统一 API event contract。

### 主流框架实现

- Web admin architecture。
- Flutter cross-platform architecture。
- Monorepo / package 分层认知。

### 失败分析与能力边界

- 普通后台架构无法承接流式任务和运行态 UI。
- AI 事件协议分散在页面里。
- 组件复用不围绕 AI 场景。

### 评估观测

- 模块边界清晰度。
- 事件协议复用率。
- 组件复用率。
- 错误恢复能力。

### 小项目实战

设计金融 Copilot 前端架构：

- Chat / Copilot。
- Knowledge workbench。
- Agent console。
- Workflow runtime。
- Eval dashboard。
- Admin / security。

### 项目收敛

本课程最终产出 AI Native 前端架构图、协议设计和核心组件清单，进入 `07_projects` 实战。
