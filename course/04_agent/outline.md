# 04 Agent 工作流与多 Agent 需求评审大纲

## 课程定位

`04_agent` 是需求评审助手从「知识助手」走向「可控多 Agent 评审系统」的主线。

`03_rag` 已经把固定 RAG 做成了单 Agent 知识助手：能检索、能引用、能拒答、能查询改写、能选择知识源、能追问补全。

`04_agent` 在此基础上继续深入：模型如何连接外部工具，如何进行多步骤任务执行，如何把需求评审拆成多个专业 Agent，如何进入状态工作流，如何人工确认，如何记录工具轨迹和节点状态。

本课程服务唯一长期主项目：需求评审助手。

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

代码不按章节机械堆脚本，而是围绕 `agent_core`、`workflow_core`、关键 demo 和需求评审项目能力组织。

## 与 03 / 05 / 06 的关系

`03_rag` 的单 Agent RAG 助手关注知识问答完整性。

`04_agent` 关注工具运行时、Agent Loop、LangChain Agent、LangGraph Workflow、Human-in-the-loop、多 Agent 协作、MCP / A2A 和 Agent Skills。

`05_eval_observability` 不重新实现 Agent，而是评估和观测 Agent 的工具轨迹、角色输出、工作流状态、人工介入、成本、延迟和失败模式。

`06_ai_native` 展示多 Agent 过程、工具调用、工作流节点和人工确认。

## 完成标准

完成本课程后，应能做到：

- 判断 Chain、Workflow、单 Agent、多 Agent 的适用边界。
- 设计 Tool Schema、Tool Runtime、参数校验、权限确认和审计。
- 实现 Agent Loop、任务分解、工具调用、状态流转和人工接管。
- 使用 LangChain Tool 和 Agent patterns 构建可控工具调用。
- 使用 LangGraph 构建 State / Node / Edge / Conditional Edge / Checkpoint / Interrupt 工作流。
- 设计需求理解、知识检索、风险审查、技术影响、测试验收、追问、汇总评审等 Agent。
- 理解 Agentic RAG、Multi-Agent、MCP / A2A 和 Agent Skills 的关系与边界。
- 为需求评审助手设计可评估、可观测、可人工介入的 Agent 工作流。

## 代码组织建议

```text
source/04_agent/
├── packages/
│   ├── agent_core/
│   └── workflow_core/
├── demos/
│   ├── tool_calling_runtime/
│   ├── agent_loop_minimal/
│   ├── langchain_agent_patterns/
│   ├── langgraph_workflow/
│   ├── human_in_the_loop/
│   └── multi_agent_review_demo/
└── README.md
```

## 专题目录

```text
course/04_agent/
├── 00_agent_problem_space.md
├── 01_function_calling_and_tool_schema.md
├── 02_tool_runtime_permissions_audit.md
├── 03_agent_loop_planning_reflection.md
├── 04_langchain_agent_patterns.md
├── 05_langgraph_state_workflow.md
├── 06_human_in_the_loop.md
├── 07_agentic_rag_deepening.md
├── 08_multi_agent_review_collaboration.md
├── 09_workflow_as_tool_and_sub_agents.md
├── 10_agent_memory_and_context.md
├── 11_mcp_a2a_agent_skills.md
├── 12_agent_guardrails_and_safety.md
├── 13_deep_research_cognition.md
├── 14_agent_evaluation.md
├── 15_review_workflow_project.md
└── outline.md
```

## 00. Agent 问题空间

### 真实问题

单次模型调用和固定 RAG 只能解决有限问题。真实需求评审需要查询系统、选择知识源、分解任务、确认风险、调用多个工具、等待人工审批，并在失败后重试或降级。

### 基础原理

- Chain：固定流程。
- Workflow：可控状态流转。
- Agent：模型动态选择下一步动作。
- Multi-Agent：多个角色协同。
- 默认从简单方案开始，复杂度由真实问题触发。

### 最小实现

- 对需求摘要、风险识别、接口影响分析、测试验收点生成等任务判断使用 Chain、Workflow、单 Agent 还是 Multi-Agent。

### 主流框架实现

- Function Calling。
- LangChain Tool / Agent。
- LangGraph Workflow。

### 失败分析与能力边界

- 所有任务都包装成 Agent。
- 需要审批的任务交给无约束 Agent。
- 没有评估和观测就增加工具数量。
- 多 Agent 不是多个聊天机器人，而是受控角色协作。

### 评估观测

- 记录架构选型理由。
- 记录任务是否需要工具、状态、人工确认和多角色协作。

### 小项目实战

为需求评审助手拆分任务：

- 知识问答。
- 风险识别。
- 技术影响分析。
- 测试验收建议。
- 缺失信息追问。
- 评审报告汇总。

### 项目收敛

输出 Agent / Workflow 选型清单。

## 01. Function Calling 与 Tool Schema

### 与 `02_llm/09` 的分工

- **`02_llm/09`** 已覆盖 Function Calling API 边界与一次最小调用验证。
- **本专题**在 Agent 语境下**系统展开** Tool Schema 设计、与 `agent_core.tool_schema` 的项目级沉淀；Tool Runtime 见专题 02。

### 真实问题

模型要调用外部能力，必须先把工具描述成模型可理解、应用可校验的数据结构。

### 基础原理

- Tool name。
- Description。
- JSON schema。
- Required fields。
- 参数约束。
- 模型选择工具，应用执行工具。

### 最小实现

- 定义一个查询业务规则的 tool schema。
- 让模型生成调用参数。
- 应用侧校验参数。

### 主流框架实现

- OpenAI tools。
- Anthropic / Gemini 工具调用差异认知。
- LangChain tool binding。

### 失败分析与能力边界

- 工具描述不清导致误调用。
- 参数 schema 太松导致执行失败。
- Tool schema 不等于 Tool runtime。

### 评估观测

- 工具选择正确率。
- 参数校验通过率。
- schema 失败类型。

### 小项目实战

为需求评审助手定义工具：

- 查询知识库。
- 查询接口文档。
- 查询历史评审。
- 创建待确认问题。
- 生成评审报告草稿。

### 项目收敛

沉淀 `agent_core.tool_schema`。

## 02. Tool Runtime、权限、确认与审计

### 真实问题

真实工具调用不能只停留在模型返回参数。应用必须执行工具、校验权限、处理失败、记录审计，并在高风险结论前要求人工确认。

### 基础原理

- Tool registry。
- Tool executor。
- 参数校验。
- 权限控制。
- Human confirmation。
- Audit log。
- Retry / fallback。

### 最小实现

- 实现一个 tool registry。
- 注册查询工具和创建待确认问题工具。
- 高风险工具执行前要求确认。

### 主流框架实现

- LangChain Tool。
- Pydantic schema。
- 自定义 runtime。

### 失败分析与能力边界

- 只有 schema，没有运行时控制。
- 工具越权。
- 工具失败后 Agent 继续编造。
- 没有审计记录，无法追踪风险操作。

### 评估观测

- 工具执行成功率。
- 权限拒绝次数。
- 人工确认触发次数。
- 工具失败原因。

### 小项目实战

需求评审工具必须记录：

- 谁触发。
- 输入是什么。
- 命中哪些知识或规则。
- 是否人工确认。
- 输出是否被采纳。

### 项目收敛

沉淀 `agent_core.tool_runtime`。

## 03. Agent Loop、Planning 与 Reflection

### 真实问题

Agent 不只是调用一次工具。它可能需要观察工具结果、判断是否继续、修正计划、补充检索、最终返回答案。

### 基础原理

- Agent Loop。
- Observe / Think / Act。
- ReAct。
- Planning。
- Reflection。
- Stop condition。

### 最小实现

- 让 Agent 在“检索、追问、回答、停止”之间选择下一步。
- 限制最大步骤数。
- 输出每一步动作记录。

### 主流框架实现

- LangChain AgentExecutor。
- ReAct pattern。
- LangGraph state loop。

### 失败分析与能力边界

- Agent 循环不停止。
- 工具结果错误仍继续推理。
- Planning 过度复杂，反而降低稳定性。

### 评估观测

- 平均步骤数。
- 工具调用成功率。
- stop reason。
- loop failure。

### 小项目实战

实现一个最小评审 Agent：

- 分析用户问题。
- 决定是否检索。
- 调用检索工具。
- 判断证据是否足够。
- 输出结论或追问。

### 项目收敛

沉淀 `agent_core.loop`。

## 04. LangChain Agent Patterns

### 真实问题

LangChain 提供了常见 Agent 工具封装和执行模式，但不能替代业务边界、权限控制和评估。

### 基础原理

- Tool。
- StructuredTool。
- tool binding。
- agent executor。
- retriever as tool。
- 自定义 runtime 与框架 runtime 的边界。

### 最小实现

- 用 LangChain 绑定一个检索工具。
- 让 Agent 基于用户问题调用工具。
- 输出工具调用过程。

### 主流框架实现

- LangChain Tool。
- OpenAI Functions Agent。
- LCEL。
- LangSmith trace 认知。

### 失败分析与能力边界

- 框架默认 Agent 不一定适合项目。
- 只看最终回答无法调试工具轨迹。
- 权限和审计仍需应用侧处理。

### 评估观测

- 对比自定义 runtime 和 LangChain Agent 的可调试性。
- 记录工具轨迹是否完整。

### 小项目实战

用 LangChain 实现需求评审检索 Agent，并对比自定义 runtime。

### 项目收敛

确定 LangChain 在项目中的使用边界。

## 05. LangGraph State 与 Workflow

### 真实问题

需求评审不是一次对话，而是一条有状态的流程：提交材料、理解需求、检索证据、多 Agent 分析、人工确认、生成报告。

### 基础原理

- State。
- Node。
- Edge。
- Conditional Edge。
- Checkpoint。
- Interrupt。
- Resume。
- Streaming events。

### Workflow 上下文与节点输出契约

对标 MaxKB `NodeResult.write_context` / 全局变量思路；LangGraph 的 State 需显式设计为「可引用、可流式、可中断恢复」。

- **State 分层**：
  - `run_context`：run_id、review_config_version、当前节点、workflow path。
  - `node_outputs`：按 `node_id` 存结构化输出（如 `requirement_summary`、`retrieved_evidence`）。
  - `global_vars`：跨节点共享变量（如 `risk_level`、`pending_clarifications`）；命名空间与类型必须在 graph 设计时固定。
- **节点 IO 契约**：每个 Node 声明 `input_keys` / `output_schema`；下游只读声明字段，禁止隐式读全量 state。
- **NodeResult 模式**：节点执行产出 `{ status, output, error, partial_stream }` 写入 state；失败时保留已产出字段供 interrupt / retry。
- **流式 partial output**：长生成节点通过 event stream 推送 partial；前端 Workflow UI 按 `runtime_node_id` 更新（见 `06_ai_native/06`）。
- **Interrupt 与 Resume**：interrupt 时持久化 state snapshot；resume 从 checkpoint 恢复 `node_outputs` 与 `global_vars`，不丢人工编辑。
- **版本绑定**：`ReviewRun` 绑定 workflow graph version + config snapshot，保证 eval 可复现（见 `07_projects/02`）。

### 最小实现

- 用 LangGraph 实现三节点流程：理解需求 -> 检索证据 -> 生成报告。
- 在 state 中保存 `node_outputs` 与至少一个 `global_var`（如 `evidence_sufficient: bool`）。
- 验证下游节点能通过 `node_id` 引用上游结构化输出。
- 模拟一个节点失败 + interrupt/resume，确认上下文不丢失。

### 主流框架实现

- LangGraph StateGraph。
- checkpoint。
- interrupt / resume。
- event streaming。

### 失败分析与能力边界

- State 设计混乱导致节点耦合。
- 节点输出不能被后续节点稳定引用。
- Workflow 过早可视化会掩盖业务边界。
- 所有 Agent 中间结果堆进单一字符串字段，导致无法 eval、无法 UI 分块展示。
- interrupt 后 resume 未加载人工修改，产生「确认无效」。

### 评估观测

- 节点成功率。
- 节点耗时。
- 中断和恢复次数。
- workflow path。

### 小项目实战

实现需求评审 Workflow：

```text
submit_requirement
-> understand_requirement
-> retrieve_evidence
-> run_review_agents
-> collect_conflicts
-> human_confirm
-> generate_report
```

### 项目收敛

沉淀 `workflow_core.graph` 与 `workflow_core.context`（state schema、node IO 契约、NodeResult 写入约定）。

## 06. Human-in-the-loop

### 真实问题

AI 不能替代所有评审决策。证据不足、影响范围大、风险等级高或 Agent 结论冲突时，需要人工介入。

### 基础原理

- Interrupt。
- Approval。
- Clarification。
- Edit before submit。
- Human decision record。
- Resume workflow。

### 最小实现

- 在 Workflow 中插入人工确认节点。
- 用户确认后继续生成报告。

### 主流框架实现

- LangGraph interrupt。
- 前端表单确认。
- 审计日志。

### 失败分析与能力边界

- 人工确认状态没有持久化。
- 用户修改后没有进入后续上下文。
- 高风险结论未触发确认。

### 评估观测

- 人工确认触发率。
- resume 成功率。
- 用户修改类型。
- 高风险漏确认次数。

### 小项目实战

设计人工确认节点：

- 缺失信息追问。
- 高风险结论确认。
- Agent 冲突处理。
- 报告发布前编辑。

### 项目收敛

沉淀 `workflow_core.human_review`。

## 07. Agentic RAG 深化

### 真实问题

需求评审的知识检索不一定一次完成。系统可能需要多轮检索、补检索、对比证据和判断证据质量。

### 基础原理

- Query planning。
- Multi-hop retrieval。
- Evidence checking。
- Self-correction。
- Retrieval retry。
- Refusal / clarification。

### 最小实现

- 让 Agent 先选择知识源，再检索，再判断是否补检索。
- 证据不足时提出追问。

### 主流框架实现

- Retriever as Tool。
- LangGraph retrieval node。
- Agentic RAG pattern。

### 失败分析与能力边界

- 补检索次数过多。
- Agent 忽略证据质量。
- 过度反思导致延迟和成本增加。

### 评估观测

- 补检索次数。
- source hit 提升。
- 追问合理率。
- 平均耗时。

### 小项目实战

让知识检索 Agent 能够：

- 判断问题类型。
- 选择知识源。
- 多查询检索。
- 判断证据是否足够。
- 请求追问或补检索。

### 项目收敛

把 `03_rag` 的单 Agent RAG 升级为可被多 Agent 调用的知识服务。

## 08. Multi-Agent 需求评审协作

### 真实问题

需求评审本身就是多角色协作。一个超级 Agent 处理所有任务会导致 Prompt 过长、职责混乱、评估困难。

### 基础原理

- Agent role。
- Agent input / output contract。
- Shared state。
- Supervisor / coordinator。
- Conflict detection。
- Aggregation。

### 最小实现

- 定义 3 个 Agent：需求理解、风险审查、汇总评审。
- 让它们通过结构化状态传递结果。

### 主流框架实现

- LangGraph 多节点。
- Supervisor pattern。
- Crew / AutoGen 等框架认知。

### 失败分析与能力边界

- 多 Agent 不等于多个独立聊天。
- 角色边界不清会重复或冲突。
- 汇总 Agent 可能丢失证据。

### 评估观测

- 各 Agent 输出完整率。
- 冲突发现率。
- 最终报告引用保留率。
- 多 Agent 相比单 Agent 的收益。

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

输出多 Agent 分工、数据契约和协作流程。

## 09. Workflow as Tool 与子 Agent

### 真实问题

复杂评审流程可以被主 Agent 调用，也可以拆成子流程和子 Agent。这样比一个超级 Agent 管所有能力更容易治理。

### 基础原理

- Workflow tool。
- Sub-agent。
- Sub-application。
- Tool composition。
- Node output reference。
- Workflow version。

### 最小实现

- 把“接口变更评审流程”包装成一个 tool。
- 主流程按需求类型选择是否调用。

### 主流框架实现

- LangChain StructuredTool。
- LangGraph subgraph。
- workflow tool pattern。

### 失败分析与能力边界

- 子流程过多导致状态难追踪。
- 子 Agent 权限边界不清。
- Workflow 工具化后更需要版本和审计。

### 评估观测

- 子流程调用次数。
- 子流程成功率。
- 工具输入输出完整性。
- 版本变化对结果的影响。

### 小项目实战

把固定流程包装成工具：

- `review_api_change_workflow`
- `review_data_change_workflow`
- `review_user_experience_workflow`

### 项目收敛

为后续项目保留“子流程作为工具”的扩展点。

## 10. Agent Memory 与 Context

### 真实问题

多 Agent 协作会产生大量中间状态。如果不管理上下文，最终汇总 Agent 会被噪声淹没。

### 基础原理

- Shared state。
- Per-agent state。
- Task memory。
- Conversation history。
- Long-term memory。
- Context compression。
- Evidence store。

### 最小实现

- 为多 Agent 流程设计 shared state。
- 每个 Agent 只读取自己需要的字段。

### 主流框架实现

- LangGraph state。
- Memory store 认知。
- Context compression。

### 失败分析与能力边界

- 共享状态过大导致上下文污染。
- Agent 读写同一字段导致覆盖。
- 长期记忆不适合作为项目事实来源。

### 评估观测

- 上下文字段使用情况。
- 中间结果丢失率。
- 汇总报告是否保留关键证据。

### 小项目实战

设计多 Agent 共享状态：

- requirement_summary。
- retrieved_evidence。
- risk_findings。
- technical_impacts。
- test_points。
- clarification_questions。
- human_decisions。

### 项目收敛

沉淀 `agent_core.context`。

## 11. MCP、A2A 与 Agent Skills

### 真实问题

Agent 生态正在走向开放协议和技能化。但当前项目不需要优先做工具生态平台，需要先理解协议边界和未来扩展点。

### 基础原理

- MCP 是工具接入协议。
- A2A 是 Agent 间协作方向。
- Agent Skills 是能力封装方式。
- 当前阶段只做认知和最小接入实验。

### 最小实现

- 选择一个低风险工具做协议化封装，例如查询本地示例文档。

### 主流框架实现

- MCP server / client 认知。
- A2A 概念认知。
- Skill manifest 认知。

### 失败分析与能力边界

- 协议接入不能替代工具权限和审计。
- 工具生态 UI 当前不是主线。
- 外部工具越多，评估和安全边界越重要。

### 评估观测

- 工具发现是否正确。
- 工具调用是否可追踪。
- 失败是否可恢复。

### 小项目实战

为需求评审助手保留一个外部工具接入实验，不进入主项目交付路径。

### 项目收敛

MCP / A2A / Skills 保持认知和未来扩展，不作为当前核心交付。

## 12. Agent Guardrails 与 Safety

### 真实问题

Agent 系统更容易遭受 Prompt Injection、工具越权、敏感信息泄露和高风险结论未确认等问题。安全不能只靠 Prompt，需要输入防护、工具权限、审计和拒答降级协同。

### 基础原理

- Prompt Injection / Indirect Prompt Injection。
- 敏感信息输入输出与日志脱敏。
- 工具最小权限、高风险确认、审计日志。
- 拒答、降级与人工接管策略。
- 安全 golden set。

### 最小实现

- 建立安全样例集：注入尝试、越权工具调用、敏感字段泄露。
- 实现基础输入检查与高风险工具确认门禁。

### 主流框架实现

- Guardrails 设计模式。
- LangGraph interrupt 与人工确认。
- 自定义 tool runtime 权限层。

### 失败分析与能力边界

- 安全规则过严会损害可用性。
- 只靠输出过滤无法阻止越权工具执行。
- 完整企业安全中台不是当前交付范围。

### 评估观测

- 注入拦截率。
- 越权拒绝率。
- 高风险确认触发率。
- 安全样例通过率。

### 小项目实战

为需求评审助手定义安全边界：哪些结论必须人工确认、哪些工具只读、哪些输入应拒答或脱敏。

### 项目收敛

沉淀 `agent_core.guardrails`，与安全 eval 样本进入 `05_eval_observability`。

## 13. Deep Research 认知

### 真实问题

Deep Research、Agentic RAG 和 Multi-Agent 都涉及多步检索与分析，但解决的问题不同。需要知道 Deep Research 适合什么、需求评审助手何时不需要它。

### 基础原理

- Deep Research：跨多文档综合、长链路研究、迭代检索与综合。
- 与 Agentic RAG、Multi-Agent、Workflow 的边界。
- 需求评审助手 V4 前不实现；可作为远期扩展认知。

### 最小实现

- 对比 3 个问题：固定 RAG、Agentic RAG、Deep Research 各自是否合适。

### 主流框架实现

- RAGFlow Agent Canvas 研究型编排认知。
- 多 hop retrieval + synthesis 模式认知。

### 失败分析与能力边界

- Deep Research 成本高、延迟大、评估难。
- 单次 PRD 风险点检查通常不需要 Deep Research。
- 不能用 Deep Research 掩盖 RAG 基础问题。

### 评估观测

- 方案选型是否有 eval 与成本依据。

### 小项目实战

写需求评审助手「不引入 Deep Research」的决策说明，保留 V4+ 可选研究子流程扩展点。

### 项目收敛

Deep Research 保持认知层，不作为当前核心交付。

## 14. Agent Evaluation

### 真实问题

Agent 系统更容易失败：工具选错、参数错、循环、越权、证据不足却强答、多个 Agent 结论冲突。不能只评最终报告。

### 基础原理

- Tool selection accuracy。
- Tool argument correctness。
- Trajectory evaluation。
- Workflow path evaluation。
- Conflict evaluation。
- Human approval rate。

### 最小实现

- 为 20 条需求评审任务标注 expected tools、expected agents、expected workflow path。

### 主流框架实现

- 自定义 eval runner。
- LangSmith trace 认知。
- LLM-as-judge 辅助判断。

### 失败分析与能力边界

- 只评最终报告无法发现轨迹错误。
- LLM judge 不稳定。
- Agent eval 在 `05_eval_observability` 系统化。

### 评估观测

- 工具选择正确率。
- Agent 输出完整率。
- 冲突发现率。
- 人工确认触发率。

### 小项目实战

为多 Agent 需求评审建立评估项：角色输出完整、工具选择正确、引用真实、必要追问、冲突发现、报告 grounded。

### 项目收敛

把 Agent 评估指标与样本交给 `05_eval_observability` 系统化。

## 15. 需求评审 Workflow 项目

### 真实问题

课程最终必须把多 Agent 和 Workflow 落到需求评审助手，而不是停在框架 demo。

### 基础原理

- 项目从单 Agent RAG 升级为多 Agent 评审。
- Workflow 控制流程，Agent 完成认知任务。
- Human-in-the-loop 处理高风险、缺失信息和冲突结论。

### 最小实现

- 实现多 Agent 评审 demo。
- 使用 Workflow 串联提交、检索、分析、确认和报告。

### 主流框架实现

- LangGraph。
- FastAPI event stream。
- 前端运行态 UI。
- 自定义 trace。

### 失败分析与能力边界

- 多 Agent 过早引入会掩盖 RAG 问题。
- Workflow 不是低代码平台。
- 人工确认不能后补，必须进入状态机。

### 评估观测

- Agent 轨迹。
- Workflow path。
- 人工确认。
- 报告质量。
- 成本和延迟。

### 小项目实战

实现需求评审多 Agent Workflow：

- 需求提交。
- 自动理解需求。
- 多知识源检索。
- 多 Agent 分析。
- 结论冲突检测。
- 缺失信息追问。
- 人工确认。
- 结构化评审报告。

### 项目收敛

完成后进入 `05_eval_observability`，为 RAG、多 Agent 和 Workflow 建立质量工程闭环。

## 参考设计映射

- 参考 MaxKB 的简单 pipeline 与 Workflow 并存、节点输出可引用、工具运行记录和 Workflow 工具化思路。
- 参考 MaxKB WorkflowManage 的 NodeResult、全局上下文变量、流式 NodeChunk 与 ChatRecord 落库思路。
- 参考 RAGFlow 的 Agent / Workflow 编排、工具调用、状态流和知识库复用方式。
