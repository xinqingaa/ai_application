# 需求评审助手工程实现方案

本文说明怎样在 `source/` 中实现 [SPEC.md](SPEC.md)。它是稳定的工程分解，不记录实时进度，不替代 `course/learning-path.md` 的学习顺序。

## 1. 代码结构

```text
source/
├── packages/
│   ├── llm_core/
│   ├── rag_core/
│   ├── agent_core/       # 真实需要时建立
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
→ Context 与可信生成
→ Citation、证据充分性与 Refusal
→ Review API
→ Web 工作台
→ Golden Set 与固定对照
```

第一阶段结束时，Retriever 必须可以作为稳定 Tool 被第二阶段直接调用。

## 3. 第二阶段实现顺序

```text
Agent Harness
→ Tool Schema 与 Tool Runtime
→ Tool 权限、Prompt Injection 与副作用治理
→ MCP 与真实外部能力接入
→ Search / Browser / File / Code Tool
→ Retriever as Tool、Agent Loop 与 Agent Skills
→ Conversation、短期记忆、长期偏好记忆、事件和运行界面
→ Deep Research
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ Trace、Regression 与 Feedback
```

该顺序是工程依赖关系，不是第二套课程编号。

## 4. Package 边界

### `llm_core`

负责模型 Provider、Prompt、Structured Output、Context、Calling Harness、成本和基础事件，不承载产品业务流程。

### `rag_core`

负责解析、Chunk、Embedding、Lexical / Dense Retrieval、RRF、Retriever Contract、Context 适配、可信生成和证据校验。

### `agent_core`

在第二阶段真实实现开始时建立，负责 Agent Harness、Tool Runtime、权限与副作用控制、Agent Loop、状态与记忆、MCP 与 A2A 适配、Skills、Research、Multi-Agent 与必要 Workflow 原语。

Tool Runtime 统一接收 Tool Schema、经过校验的参数、运行权限和取消信号，并返回结构化结果或错误。MCP、Search、Browser、File、Code 和 Retriever 都通过这一边界接入；不能让某种连接器绕过统一权限、超时、审计和事件。

File Tool 的通用部分负责受控工作区、路径解析、来源身份、读取结果、暂存写入、原子写入和幂等。Code Tool 的通用部分负责允许命令、隔离执行、资源限制、取消和结构化执行结果。具体允许读取什么、运行哪些验证和写出哪些产物属于产品策略。

状态与记忆的通用部分负责 Conversation、Run State、短期摘要和长期偏好记录的稳定身份、版本与生命周期。哪些偏好允许保存、怎样取得用户确认、保留多久以及如何在界面中查看、更新、删除和关闭，属于产品策略；业务资料和模型推断不得写成长期偏好。

### `eval_core`

在跨产品复用需求成立时建立，负责数据集、运行记录、评估器、回归和反馈模型；仅有产品局部逻辑时先留在产品内。

## 5. 产品边界

`source/apps/review_assistant/` 负责：

- FastAPI 和产品服务。
- Web 工作台。
- 产品 Schema、状态和组合流程。
- 产品测试、fixtures、eval 和数据库 migration。
- 第二阶段评审工作区策略、允许路径、允许命令、人工确认和运行产物。
- 长期偏好的可保存范围、确认流程、管理界面与审计策略。
- 本地 Delegation 与远程 A2A 共用的责任契约、获准输入和结果校验策略。
- 安装、配置、运行和部署。

通用算法进入 package，产品业务取舍留在 app。

第二阶段继续复用“售后入口与订单状态”垂直切片，并增加可执行的多端契约工作区。真实实现到达对应能力时，产品 fixture 至少覆盖 PRD、OpenAPI、Flutter / Web 客户端模型、配置、定向验证入口和预期失败；fixture、Tool 实现、实验和测试一起落地，不提前创建空目录。

File Read 默认只访问本次运行批准的工作区；File Write 默认只访问 `run_id` 隔离的暂存输出。Code Tool 默认只读挂载输入、隔离输出、禁用网络，并使用命令和环境白名单。产品若扩大路径、命令或网络能力，必须先更新 SPEC 的安全与验收边界。

## 6. 实验边界

`source/demos/` 只用于观察机制、对照变量和稳定复现失败。实验操作教材位于 `course/labs/`；demo README 只维护代码入口和测试索引。

## 7. 实现准入

新增能力前依次确认：

1. 它解决 SPEC 中哪个真实问题。
2. 最简单结构是否足够。
3. 通用能力还是产品取舍。
4. 输入、输出、状态、错误和权限是否明确。
5. 怎样用实验、测试或评估证明。

没有真实职责和收益证据时，不提前建立 Multi-Agent、完整 Workflow、平台化连接器或评估平台。

## 8. 验证要求

- 主路径使用真实模型与真实外部服务。
- 单元测试只证明确定性契约。
- 集成测试验证数据库、Provider 或协议边界。
- 固定数据集比较质量、成本和延迟。
- 重要变更同步更新 SPEC、项目篇、产品 README、测试和评估样例中真正受影响的真源。
