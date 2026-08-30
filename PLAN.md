# 需求评审助手工程实现方案

本文说明怎样在 `source/` 中实现 [SPEC.md](SPEC.md)。它是稳定的工程分解，不记录实时进度，不替代 `course/learning-path.md` 的学习顺序。

## 1. 代码结构

```text
source/
├── packages/
│   ├── llm_core/
│   ├── rag_core/
│   ├── agent_core/       # 第二阶段通用 Agent 运行、治理与框架适配
│   └── eval_core/        # 真实需要时建立
├── demos/                # 机制实验代码
├── apps/
│   └── review_assistant/ # 唯一产品
└── python_base/
```

每个能力域只维护一个 package。demo 和产品通过 import 复用，不复制实现。

## 2. 第一阶段实现顺序

```text
LLM 调用与结构化输出
→ 文档解析、Chunk 与 Metadata
→ Lexical / Dense Retrieval
→ RRF 与 Retriever Contract
→ Context 与可信生成（含结构化增量流式与最终校验边界）
→ Citation、证据充分性与 Refusal
→ 身份认证与角色（普通评审 / 管理员）
→ 知识管理后台（上传、暂存、发布、dataset_version）
→ Review API（含 SSE 事件契约）
→ Web 工作台
→ Golden Set 与固定对照
→ Docker Compose 打包（应用 + Postgres/pgvector）
```

第一阶段结束时，Retriever 必须可以作为稳定 Tool 被第二阶段直接调用；身份认证与角色边界必须与第二阶段 Tool 权限保持概念上的独立，不能被后者直接复用或替代。

## 3. 第二阶段实现顺序

```text
框架分层、agent_core 与 LangChain 首个真实 Agent
→ Tool Schema、Tool Runtime 与 Retriever Tool
→ 最小 Run State、Event、停止原因与 LangSmith Trace
→ Agent 运行契约与框架适配收束
→ LangGraph State、Checkpoint、Interrupt 与恢复
→ MCP 与 Search / Browser / File / Code Tool
→ Conversation、短期记忆、长期偏好、完整事件和运行界面
→ Agent Skills
→ Deep Research
→ 框架内 Multi-Agent 基线
→ 独立 A2A 互操作
→ 复杂 Workflow 组合
→ Trace、Regression 与 Feedback
```

该顺序是工程依赖关系，不是第二套课程编号。LangChain 与 LangGraph 是同一个 Agent 运行时的两种使用深度——`create_agent` 本身构建在 LangGraph 之上；这条顺序是从高层用法逐步下沉到底层原语，不是先实现一套运行时再迁移到另一套。

## 4. Package 边界

### `llm_core`

负责模型 Provider、Prompt、Structured Output、Context、Calling Harness、成本和基础事件，不承载产品业务流程。

### `rag_core`

负责解析、Chunk、Embedding、Lexical / Dense Retrieval、RRF、Retriever Contract、Context 适配、可信生成和证据校验。

### `agent_core`

一句话定义：`agent_core` = 对 LangChain / LangGraph 的产品向适配与治理层。框架负责循环、工具调度、图执行和持久化；`agent_core` 负责稳定请求/结果契约、权限/超时/错误、与 `rag_core` 的 Retriever 复用、Run 记录；产品 `agent/` 负责评审领域行为。`agent_core` 随课程能力逐步扩展，但永不替换框架运行时。

`agent_core` 随第二阶段 Agent 框架接入建立，是通用 Agent 运行、治理和框架适配的唯一 package。稳定依赖方向是“产品领域组装 → `agent_core` 契约与适配 → LangChain / LangGraph”。LangChain 提供高层 Agent 与 Tool 组合，LangGraph 提供图执行、Checkpoint、Resume 和 Interrupt——二者是同一个运行时的两种深度，不是两套并行实现；`agent_core` 组合这些能力并向产品提供一致的请求结果、Tool、状态、停止、事件和观测边界。LangSmith 是课程主线的真实 Trace / Eval 实验与产品条件接入项，本地 RunRecord 始终存在。

`agent_core` 的通用职责包括：

- `AgentRequest`、`AgentResult`、通用 Tool Schema、结构化结果与错误。
- Tool 权限、超时、取消、审计、副作用和确认接口。
- 通用 `RunState`、`StopReason`、事件信封、运行身份，以及本地 `RunRecord` 与 Trace 的关联。
- LangChain / LangGraph 适配边界，以及后续 MCP、A2A 的协议映射和治理入口。
- 随课程能力扩展的 Skill 加载、Research 运行记录和 Multi-Agent 任务、委派、结果契约。

它复用框架已有的运行时、图执行器和持久化能力，不重复实现这些基础设施。评审 Prompt、风险 Schema、Citation 策略、允许路径与命令、长期偏好策略和具体 Agent 角色留在产品 `agent/` 目录。替代框架和观测后端只在真实迁移、数据编排或部署治理需求成立时评估，不在工程主路径并行维护。

Tool Runtime 统一接收 Tool Schema、经过校验的参数、运行权限和取消信号，并返回结构化结果或错误。MCP、Search、Browser、File、Code 和 Retriever 都通过这一边界接入；不能让某种连接器绕过统一权限、超时、审计和事件。

File Tool 的通用部分负责受控工作区、路径解析、来源身份、读取结果、暂存写入、原子写入和幂等。Code Tool 的通用部分负责允许命令、隔离执行、资源限制、取消和结构化执行结果。具体允许读取什么、运行哪些验证和写出哪些产物属于产品策略。

状态与记忆的通用部分只负责 Conversation、Run State、短期摘要和长期偏好记录的稳定身份、版本与生命周期接口。具体状态字段、摘要策略、哪些偏好允许保存、怎样取得用户确认、保留多久以及如何在界面中管理，属于产品策略；业务资料和模型推断不得写成长期偏好。

### `eval_core`

在跨产品复用需求成立时建立，负责数据集、运行记录、评估器、回归和反馈模型；仅有产品局部逻辑时先留在产品内。

## 5. 产品边界

`source/apps/review_assistant/` 负责：

- FastAPI 和产品服务。
- Web 工作台。
- 身份认证、会话或令牌生命周期，以及普通评审 / 管理员两个最小角色的路由与动作边界。这是产品领域策略，不进入通用 package；也不与第二阶段 `agent_core` 的 Tool 权限模块合并。
- 知识管理后台：知识资料上传、解析诊断展示、入库暂存、管理员发布与 `dataset_version` 记录。发布动作是唯一能够改变检索候选池版本的入口，上传和暂存不直接生效。
- 产品 Schema、状态和组合流程。
- `agent/` 中的评审 Prompt、领域 Agent 组装、引用与证据策略、记忆策略和角色设计。
- 产品测试、fixtures、eval 和数据库 migration。
- 第二阶段评审工作区策略、允许路径、允许命令、人工确认和运行产物。
- 长期偏好的可保存范围、确认流程、管理界面与审计策略。
- 本地 Delegation 与远程 A2A 共用的责任契约、获准输入和结果校验策略。
- 安装、配置、运行和部署。

通用算法进入 package，产品业务取舍留在 app。

第二阶段继续复用“售后入口与订单状态”垂直切片，并增加可执行的多端契约工作区。真实实现到达对应能力时，产品 fixture 至少覆盖 PRD、OpenAPI、Flutter / Web 客户端模型、配置、定向验证入口和预期失败；fixture、Tool 实现、实验和测试一起落地，不提前创建空目录。

File Read 默认只访问本次运行批准的工作区；File Write 默认只访问 `run_id` 隔离的暂存输出。Code Tool 默认只读挂载输入、隔离输出、禁用网络，并使用命令和环境白名单。产品若扩大路径、命令或网络能力，必须先更新 SPEC 的安全与验收边界。

MCP 与 A2A 优先通过官方 SDK 或成熟适配器实现协议连接，不在 `agent_core` 重写协议栈。MCP 能力和 A2A 远程任务进入产品前，仍须映射为内部权限、状态、错误、证据与审计契约。

## 6. 实验边界

`source/demos/` 只用于观察机制、对照变量和稳定复现失败。实验操作教材位于 `course/labs/`；demo README 只维护代码入口和测试索引。

## 7. 实现准入

新增能力前依次确认：

1. 它解决 SPEC 中哪个真实问题。
2. 最简单结构是否足够。
3. 通用能力还是产品取舍。
4. 输入、输出、状态、错误和权限是否明确。
5. 怎样用实验、测试或评估证明。

涉及框架时还要确认：框架已经提供哪些运行能力，哪些通用契约、治理和适配进入 `agent_core`，哪些 Prompt、权限和业务策略留在产品；本地层复用框架能力，不复制框架运行时。

没有真实职责和收益证据时，不提前建立 Multi-Agent、完整 Workflow、平台化连接器或评估平台。

## 8. 验证要求

- 主路径使用真实模型与真实外部服务。
- 单元测试只证明确定性契约。
- 集成测试验证数据库、Provider 或协议边界。
- 固定数据集比较质量、成本和延迟。
- 重要变更同步更新 SPEC、项目篇、产品 README、测试和评估样例中真正受影响的真源。
