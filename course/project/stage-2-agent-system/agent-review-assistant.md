# 第二阶段：Agent 协作需求评审系统

本文是第二阶段综合实践教材。产品要求以根 [SPEC](../../../SPEC.md) 为准，工程实现边界以 [PLAN](../../../PLAN.md) 为准，学习顺序回到[标准学习路径](../../learning-path.md)。

## 业务目标

第一阶段固定 RAG 已经能从内部资料中检索证据并生成可信评审。第二阶段处理无法完全预先固定的任务：问题可能需要改写、选择知识源、补检索、搜索外部资料、调用工具、追问用户或由多个评审角色协作。

最终产品仍是同一个需求评审助手，不新建第二个应用。

## 贯穿场景

第二阶段继续使用第一阶段“售后入口与订单状态”基线，不通过更换案例规避固定 RAG、单 Agent 和 Multi-Agent 的比较。新增任务是评审“售后接口 v2 与多端契约一致性”：需求要求增加或收紧 `source_channel`，并要求 Web 与 Flutter 客户端使用一致的入口可见性规则。

一次评审可以收到：

- 当前 PRD 与会议纪要。
- OpenAPI 或 JSON Schema 接口契约。
- Flutter / Web 客户端模型和相关配置。
- 项目已有的契约校验、静态检查或定向测试入口。
- 外部需求系统中的 issue、验收条件和关联资料。
- 需要回查的官方 SDK 文档或版本说明。

这些输入共同构成受控评审工作区，但证据资格不同：当前 PRD 是评审主体，内部现行规则来自 RAG，外部资料来自 MCP 或 Browser，文件和代码执行结果是 Tool Evidence。任何来源都不能仅因被 Agent 读取或执行成功就自动成为已校验 Citation。

## 已有能力

进入本阶段前必须已经具备：

- 稳定的文档、Chunk、Embedding 与检索链。
- Retriever 输入、输出、诊断和错误契约。
- Context、Structured Output、Citation、Refusal 和补充问题。
- Review API、最小工作台和固定 RAG 基线。
- Golden Set、成本和延迟记录。

## 本阶段新增结果

```text
固定 RAG
→ Tool Runtime 与受控外部能力
→ MCP、Search、Browser、File 与 Code
→ Retriever Tool、可停止 Agent 与 Agent Skills
→ Conversation、短期与长期记忆、可观察事件与运行界面
→ Deep Research
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ 统一回归与反馈
```

## 项目职责

### Agent Harness

承载模型、上下文、工具、状态、权限、循环、停止、事件和观测。模型提出行动，应用负责执行与控制。

### MCP

产品首先作为 MCP Client 消费一个真实、只读、可观察的外部需求或资料能力，例如读取需求系统中的 issue、验收条件和关联资料。MCP 负责协议请求、能力描述与结果交换；内部 Tool Runtime 继续负责 Schema、权限、超时、取消、审计和错误转换。产品必须记录采用的协议修订和 SDK 版本，更换 MCP Server 或协议版本不应悄悄改变内部 Tool 契约和证据模型。

### 通用 Tool

- Search：根据研究问题发现候选来源，不把搜索摘要直接当作最终证据。
- Browser：打开候选来源，提取官方文档、版本说明或接口规范，并保留 URL、标题、时间和内容定位。
- File Read：在批准的工作区中选择性读取 PRD、OpenAPI、客户端模型、配置和测试入口，保留相对路径、内容哈希和定位。
- File Write：用户确认后，只向运行级暂存区写入评审报告、补充问题、证据清单或带批注需求副本；不直接覆盖原始需求和代码。
- Code：当专用 Validator 不足而需要运行项目已有检查时，在受控沙箱中执行允许的契约校验、静态检查或定向测试。

Code Tool 第一版不接受任意 Shell，也不让模型自由生成并执行代码。应用选择允许的 `command_ref`，只读挂载输入工作区、隔离输出、默认禁网并限制时间、资源、环境和产物。执行结果保留退出码、stdout、stderr、耗时、超时和产物身份。

这些工具在本项目中都有真实职责，但仍要优先使用更窄的专用能力。例如只需校验 OpenAPI 时使用专用 Validator；只有需要运行项目现有脚本或测试体系时才使用 Code Tool。

### Agent Skills

至少建立一个需求评审领域 Skill，例如“客户端兼容性评审”或“接口契约评审”。Skill 提供说明、参考资源和必要脚本，按需加载，不直接绕过 Tool Runtime 执行高风险动作。

### State 与 Memory

Conversation、Run State、短期摘要、长期偏好和可引用业务知识必须分别建模。长期记忆是本阶段必接能力，但只保存用户明确确认的跨会话偏好；产品记录来源、作用域和版本，并提供查看、更新、删除和关闭入口。模型推断、会话摘要、PRD 事实和 Tool Result 不能自动进入长期记忆，偏好也不能作为 Citation。

### Deep Research

用于需要多步搜索、来源验证和综合的评审问题，例如核对外部 SDK 的最低版本、跨端支持范围或互相冲突的版本说明。普通内部规则查询继续使用 RAG；一次官方文档回查使用 Search / Browser；只有需要计划、多个来源、证据积累或冲突处理时才进入 Deep Research。每条关键结论必须回到来源，运行必须有预算和停止条件。

### Multi-Agent

只有单 Agent 基线暴露真实不足后才拆分。每个 Agent 必须具有独立责任、上下文、工具或输出契约；建议从客户端影响、接口契约和证据审查等真实责任中选择最小组合。

### A2A

A2A 在本地责任契约成立后用于跨进程或跨系统交换任务、状态、结果和错误。本项目的最小真实场景是把已经建立输入输出契约的“接口契约评审”责任交给一个独立远程 Agent：主应用通过 Agent Card 识别能力，只发送获准的 OpenAPI、客户端模型证据和任务约束，并通过 Message、Task、Part 与 Artifact 接收进度和契约差异产物。主应用仍负责证据校验、冲突处理和最终业务结果，远程实现可以替换；没有跨系统边界时继续使用本地 Delegation 基线。协议版本、绑定和鉴权差异必须显式处理。

### Workflow

Workflow 只管理需要显式状态、恢复、人工确认或副作用幂等的部分，不替代 Agent 的动态决策，也不替代 A2A 的跨边界任务协议。

## 状态与输出契约

每次运行至少保留：

- `run_id` 与原始任务。
- 当前目标、步骤和状态。
- Tool Call、参数、结果和错误。
- 当前证据与来源身份。
- 本轮使用的短期摘要、已确认长期偏好和记忆变更结果。
- 累计成本、延迟和预算。
- Agent 分工、局部结果和冲突。
- 最终停止原因。

最终业务输出继续沿用第一阶段的结构化风险、Sources、Citation、Refusal 和补充问题，不让 Agent 中间文本绕过产品契约。

## 集成检查点

### Agent Harness 与 Tool Runtime

- 模型提出的 Tool Call 先经过 Schema 校验、权限判断和统一执行生命周期。
- 读取、写入和外部行动具有不同权限与确认边界。
- 超时、取消、安全阻止和真实执行失败返回不同结构化结果。
- 文件、网页和外部能力返回的内容不能改变系统权限或执行策略。

### MCP 与通用工具

- 接入一个真实 MCP Tool 或 Resource，并记录协议修订、SDK 和服务身份。
- Search 结果与 Browser 实际打开的来源分开记录，搜索摘要不直接成为 Citation。
- File Read 能从工作区追踪 OpenAPI、客户端模型和配置的路径、哈希与定位，并拒绝路径穿越、越权和超限。
- File Write 只能写运行级暂存产物；覆盖、确认、原子写入和重复请求可观察。
- Code Tool 至少完成一次接口或客户端契约验证，并展示成功、校验失败、超时或权限拒绝中的多种结果。
- Code 执行不能访问工作区外文件、秘密环境变量或未批准网络，也不能把非零退出码伪装为空结果。
- MCP 失败、版本不兼容或能力 Schema 不兼容不会绕过内部 Runtime，也不会伪装成空结果。

### 最小 Agentic RAG 与 Agent Skills

- Retriever 已成为受治理 Tool。
- Agent 可以改写 Query、选择来源、补检索和停止。
- 工具失败、需要补充和达到预算有不同停止原因。
- 保留固定 RAG 基线。
- 至少一个领域 Skill 能按需加载，并记录格式、资源和版本身份。
- Skill 脚本仍经过受治理执行边界，不能因来自 Skill 而获得额外权限。

### 状态、事件与单 Agent 评估

- Conversation、Run State、短期记忆、长期偏好和业务知识没有混用。
- 长期偏好只有经用户确认才写入，并保留来源、作用域和版本；用户可以查看、更新、删除和关闭。
- 删除或关闭长期记忆后，后续运行不再注入对应偏好；偏好不进入 Citation。
- SSE 事件能表达 Tool、证据、等待、停止、错误和取消。
- 工作台能还原运行状态。
- 对 Tool 选择、参数、轨迹和停止进行固定样例评估。

### Deep Research

- 能判断普通 RAG、单次 Browser 回查和 Deep Research 的启动边界。
- 研究任务能建立计划、迭代搜索、维护 Evidence Ledger、重新规划和停止。
- 来源质量、权威性、独立性、重复来源、交叉验证和冲突证据可见。
- 最终综合能回查 Citation。

### Multi-Agent

- 每个 Agent 的职责和非职责明确。
- 并行、依赖、取消和局部失败可观察。
- 汇总保留证据归属和不可自动裁决的冲突。
- 与单 Agent 比较质量、成本、延迟和失败定位。

### A2A 互操作

- 能通过 Agent Card 识别远程 Agent 的身份、能力、端点和安全要求。
- Message、Task、Part 与 Artifact 的语义没有混用。
- 提交、执行、等待输入或鉴权、完成、失败、拒绝和取消能够映射为一致任务状态。
- 固定规范修订、SDK 和协议绑定，完成两个实现之间的真实互操作。
- 同一接口契约评审责任可以在本地 Delegation 与远程 A2A 路径间对照；远程 Agent 只收到获准输入，返回产物仍保留 Task、证据和责任归属。
- Agent Card 中的能力 Skill 不会被当作 Agent Skills 文件格式或本地执行授权。

### 最终交付

- 必要 Workflow 支持 Checkpoint、恢复和人工介入。
- 日志、Metrics、Trace、版本和运行记录可以关联。
- Bad Case 能进入固定样例和回归。
- 完成根 SPEC 的第二阶段验收。

## 需要作出的设计选择

学习者必须说明：

1. 为什么固定 RAG 不足，哪些步骤仍保持确定性。
2. MCP 连接哪项真实外部能力，为什么不直接写专用 API。
3. Search 与 Browser 为什么分开，哪些结果可以成为候选证据。
4. File Read 为什么需要来源身份，File Write 为什么只能进入暂存区。
5. 哪些校验使用专用 Tool，哪些确实需要 Code Tool，允许命令怎样控制。
6. Skill 为什么不是 Prompt、Tool 或 MCP Server。
7. 哪些长期偏好允许保存，用户怎样确认、管理和关闭，为什么它们不能成为业务证据。
8. Deep Research 在什么条件下启动和停止。
9. 为什么需要多个 Agent，各自责任是什么。
10. 为什么需要 A2A 而不是本地 Delegation，采用的规范版本和协议绑定是什么。
11. Workflow 只接管哪些需要恢复、确认或副作用治理的路径。

## 自然 bad case

至少观察并定位一类真实边界，例如：

- Agent 反复改写 Query 却没有新增证据。
- MCP 请求能够到达服务，但协议版本或能力 Schema 不兼容。
- Search 返回多个互相转载的弱来源。
- 文件路径通过 `..` 或符号链接逃逸获准工作区。
- Agent 试图覆盖原始 PRD，或重试导致同一报告重复写入。
- OpenAPI 声明 `source_channel` 必填，但 Flutter 模型或 Web 类型缺少该字段。
- Code Tool 超时、返回非零退出码，或尝试读取未授权环境变量。
- Skill 占用 Context 却没有被当前任务使用。
- 模型把未经确认的推断写成长期偏好，或用户删除偏好后旧值仍被注入。
- 某个 Agent 失败后汇总器误把缺失结果当成无风险。
- 两个 Agent 引用不同版本资料并给出冲突结论。
- Agent Card 声明的能力、端点或安全要求与真实服务不一致。
- A2A 双方协议版本或绑定不兼容，或者已取消的 Task 仍收到迟到 Artifact。
- 远程 Agent 的过程 Message 被误当作最终 Artifact，导致汇总器提前结束任务。

## 需求变更题

新增“客户端最低版本兼容性评审”：

- 判断应修改知识、Skill、Tool、Agent 责任还是输出 Schema。
- 使用 MCP 或 Browser 回查官方版本要求，使用 File Tool 定位当前客户端配置，必要时使用 Code Tool 运行已有兼容性检查。
- 保留旧 Golden Set，新增覆盖新问题的样例。
- 比较固定 RAG、单 Agent 和 Multi-Agent 的变化。
- 证明没有破坏 Citation、Refusal、停止和权限边界。

## 代码入口

```text
source/packages/                 通用能力
source/demos/                    机制实验
source/apps/review_assistant/    唯一产品
```

产品运行、配置、API 和测试见 `source/apps/review_assistant/README.md`。

## 明确不做

- 通用 Agent 平台或工具市场。
- 任意 MCP Server 自动获得信任。
- 无沙箱的 Code Tool。
- 任意 Shell、任意工作目录、默认联网或读取秘密环境变量的 Code Tool。
- 让 File Tool 任意覆盖原始 PRD、代码或配置。
- 把所有步骤都交给模型。
- 为展示复杂度增加没有独立责任的 Agent。
- 完整低代码 Workflow 画布。
- 完整多租户、企业权限中台和大规模部署平台。

## 阶段验收

- 产品主路径真实运行，没有平行实现。
- 能解释数据流、状态流、工具流、证据流和异常流。
- 能展示正常完成、追问、等待确认、达到上限、工具失败和取消。
- MCP、Skill、Tool、A2A 与 Workflow 的责任边界清楚。
- Multi-Agent 相对单 Agent 有固定证据，而不是只增加 Prompt 数量。
- 能完成自然 bad case、需求变更和回归。
- 最终结果可引用、过程可观察、失败可定位、改动可验证。
