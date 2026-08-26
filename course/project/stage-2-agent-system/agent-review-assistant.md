# 第二阶段：Agent 协作需求评审系统

本文是第二阶段综合实践教材。产品要求以根 [SPEC](../../../SPEC.md) 为准，工程实现边界以 [PLAN](../../../PLAN.md) 为准，学习顺序回到[标准学习路径](../../learning-path.md)。

## 业务目标

第一阶段固定 RAG 已经能从内部资料中检索证据并生成可信评审。第二阶段处理无法完全预先固定的任务：问题可能需要改写、选择知识源、补检索、搜索外部资料、调用工具、追问用户或由多个评审角色协作。

最终产品仍是同一个需求评审助手，不新建第二个应用。

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
→ 受治理 Retriever Tool
→ 可停止的单 Agent
→ MCP、通用 Tool 与 Agent Skills
→ 可观察事件与运行界面
→ Deep Research
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ 统一回归与反馈
```

## 项目职责

### Agent Harness

承载模型、上下文、工具、状态、权限、循环、停止、事件和观测。模型提出行动，应用负责执行与控制。

### MCP

产品首先作为 MCP Client 消费一个真实、只读、可观察的 Tool 或 Resource。MCP 负责连接、能力发现与结果交换；内部 Tool Runtime 继续负责 Schema、权限、超时、取消、审计和错误转换。

### 通用 Tool

- Browser / Search：外部研究和来源回查，不替代内部 RAG。
- File：读取项目资料；写入需要独立权限。
- Code：只在受控沙箱中完成明确的分析或验证任务。

课程必须实验这些工具类别；产品只启用有真实业务职责并满足权限要求的能力。

### Agent Skills

至少建立一个需求评审领域 Skill，例如“客户端兼容性评审”或“接口契约评审”。Skill 提供说明、参考资源和必要脚本，按需加载，不直接绕过 Tool Runtime 执行高风险动作。

### Deep Research

用于需要多步搜索、来源验证和综合的评审问题。每条关键结论必须能回到来源，运行必须有预算和停止条件。

### Multi-Agent

只有单 Agent 基线暴露真实不足后才拆分。每个 Agent 必须具有独立责任、上下文、工具或输出契约；建议从客户端影响、接口契约和证据审查等真实责任中选择最小组合。

### A2A 与 Workflow

A2A 在本地责任契约成立后用于交换任务、状态、结果和错误。Workflow 只管理需要显式状态、恢复、人工确认或副作用幂等的部分。

## 状态与输出契约

每次运行至少保留：

- `run_id` 与原始任务。
- 当前目标、步骤和状态。
- Tool Call、参数、结果和错误。
- 当前证据与来源身份。
- 累计成本、延迟和预算。
- Agent 分工、局部结果和冲突。
- 最终停止原因。

最终业务输出继续沿用第一阶段的结构化风险、Sources、Citation、Refusal 和补充问题，不让 Agent 中间文本绕过产品契约。

## 集成检查点

### 最小 Agentic RAG

- Retriever 已成为受治理 Tool。
- Agent 可以改写 Query、选择来源、补检索和停止。
- 工具失败、需要补充和达到预算有不同停止原因。
- 保留固定 RAG 基线。

### MCP、Tools 与 Skills

- 接入一个真实 MCP Tool 或 Resource。
- Browser/Search、File、Code 的权限和失败边界可观察。
- 至少一个领域 Skill 能按需加载。
- MCP 失败不会绕过内部 Runtime 或伪装成空结果。

### 状态、事件与单 Agent 评估

- Conversation、Run State、短期记忆和业务知识没有混用。
- SSE 事件能表达 Tool、证据、等待、停止、错误和取消。
- 工作台能还原运行状态。
- 对 Tool 选择、参数、轨迹和停止进行固定样例评估。

### Deep Research

- 研究任务能拆解、迭代搜索、积累证据和停止。
- 来源质量、重复来源和冲突证据可见。
- 最终综合能回查 Citation。

### Multi-Agent 与 A2A

- 每个 Agent 的职责和非职责明确。
- 并行、依赖、取消和局部失败可观察。
- 汇总保留证据归属和不可自动裁决的冲突。
- 完成一次 A2A 任务生命周期互操作。
- 与单 Agent 比较质量、成本、延迟和失败定位。

### 最终交付

- 必要 Workflow 支持 Checkpoint、恢复和人工介入。
- 日志、Metrics、Trace、版本和运行记录可以关联。
- Bad Case 能进入固定样例和回归。
- 完成根 SPEC 的第二阶段验收。

## 需要作出的设计选择

学习者必须说明：

1. 为什么固定 RAG 不足，哪些步骤仍保持确定性。
2. MCP 连接哪项真实外部能力，为什么不直接写专用 API。
3. 哪些 Tool 进入产品，权限和副作用怎样控制。
4. Skill 为什么不是 Prompt、Tool 或 MCP Server。
5. Deep Research 在什么条件下启动和停止。
6. 为什么需要多个 Agent，各自责任是什么。
7. A2A 和 Workflow 分别解决哪一个边界。

## 自然 bad case

至少观察并定位一类真实边界，例如：

- Agent 反复改写 Query 却没有新增证据。
- MCP Server 可连接但能力 Schema 不兼容。
- Search 返回多个互相转载的弱来源。
- Skill 占用 Context 却没有被当前任务使用。
- 某个 Agent 失败后汇总器误把缺失结果当成无风险。
- 两个 Agent 引用不同版本资料并给出冲突结论。

## 需求变更题

新增“客户端最低版本兼容性评审”：

- 判断应修改知识、Skill、Tool、Agent 责任还是输出 Schema。
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
