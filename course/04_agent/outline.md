# 04 Agent 工作流与工具系统大纲

## 课程定位

`04_agent` 是 AI 应用从“知识助手”走向“可控执行系统”的主线。

`03_rag` 已经把固定 RAG 做成了单 Agent 知识助手：能检索、能引用、能拒答、能查询改写、能选择知识源、能追问补全。

`04_agent` 在此基础上继续深入：模型如何连接外部工具，如何进行多步骤任务执行，如何进入状态工作流，如何人工确认，如何进行 Deep Research、多 Agent 协作和开放协议接入。

本课程服务两个长期项目：

- 将需求评审助手从单 Agent 知识助手升级为可控工作流。
- 为金融 Copilot 建立工具系统、工作流、多 Agent 和人机协作底座。

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

代码不按章节机械堆脚本，而是围绕 `agent_core`、`workflow_core`、关键 demo 和金融 Copilot 项目能力组织。

## 与 03 / 05 的关系

`03_rag` 的单 Agent RAG 助手关注知识问答完整性。

`04_agent` 关注工具运行时、Agent Loop、LangChain Agent、LangGraph Workflow、Human-in-the-loop、Deep Research、Multi-Agent、MCP / A2A 和 Agent Skills。

`05_eval_observability` 不重新实现 Agent，而是评估和观测 Agent 的工具轨迹、工作流状态、人工介入、成本、延迟和失败模式。

## 完成标准

完成本课程后，应能做到：

- 判断 Chain、Workflow、单 Agent、Multi-Agent 的适用边界。
- 设计 Tool Schema、Tool Runtime、参数校验、权限确认和审计。
- 实现 Agent Loop、任务分解、工具调用、状态流转和人工接管。
- 使用 LangChain Tool 和 Agent patterns 构建可控工具调用。
- 使用 LangGraph 构建 State / Node / Edge / Conditional Edge / Checkpoint / Interrupt 工作流。
- 理解 Agentic RAG 深化、Deep Research、Multi-Agent、Agent Skills、MCP / A2A 的关系。
- 为金融 Copilot 设计可评估、可观测、可人工介入的 Agent 工作流。

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
│   └── deep_research_demo/
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
├── 08_deep_research_workflow.md
├── 09_multi_agent_collaboration.md
├── 10_agent_memory_and_context.md
├── 11_mcp_a2a_agent_skills.md
├── 12_agent_evaluation_safety.md
├── 13_financial_copilot_project.md
└── outline.md
```

## 00. Agent 问题空间

### 真实问题

单次模型调用和固定 RAG 只能解决有限问题。真实业务里，AI 需要查询系统、选择工具、分解任务、确认风险、调用多个服务、等待人工审批，并在失败后重试或降级。

### 基础原理

- Chain：固定流程。
- Workflow：可控状态流转。
- Agent：模型动态选择下一步动作。
- Multi-Agent：多个角色协同。
- 默认从简单方案开始，复杂度由真实问题触发。

### 最小实现

- 对需求评审、客服查询、合规审核、公告解读等任务判断使用 Chain、Workflow、Agent 还是 Multi-Agent。

### 主流框架实现

- Function Calling。
- LangChain Tool / Agent。
- LangGraph Workflow。

### 失败分析与能力边界

- 所有任务都包装成 Agent。
- 需要审批的任务交给无约束 Agent。
- 没有评估和观测就增加工具数量。

### 评估观测

- 记录架构选型理由。
- 记录任务是否需要工具、状态、人工确认和多角色协作。

### 小项目实战

为金融 Copilot 拆分任务：

- 知识问答。
- 合规审核。
- 公告解读。
- 人工审批。
- 多角色协作。

### 项目收敛

本章输出 Agent / Workflow 选型清单。

## 01. Function Calling 与 Tool Schema

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

- 定义一个查询规则文档的 tool schema。
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

为金融 Copilot 定义工具：

- 查询知识库。
- 查询产品规则。
- 检查合规风险。
- 创建人工审核任务。

### 项目收敛

沉淀 `agent_core.tool_schema`。

## 02. Tool Runtime、权限、确认与审计

### 真实问题

真实工具调用不能只停留在模型返回参数。应用必须执行工具、校验权限、处理失败、记录审计，并在高风险操作前要求人工确认。

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
- 注册查询工具和创建审核任务工具。
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

金融 Copilot 的合规审核工具必须记录：

- 谁触发。
- 输入是什么。
- 命中哪些规则。
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
- Iteration limit。

### 最小实现

- 构建一个最多 3 步的 Agent loop。
- 每一步记录 thought label、tool call、observation、next action。

### 主流框架实现

- LangChain Agent patterns。
- 自定义 loop。
- LangGraph loop 在后续章节系统展开。

### 失败分析与能力边界

- 无限循环。
- 重复调用工具。
- 计划过度复杂。
- 反思阶段编造理由。

### 评估观测

- 迭代次数。
- 工具调用次数。
- 任务完成率。
- 是否触发 stop condition。

### 小项目实战

金融 Copilot 对“这段营销话术能不能发”进行：

- 提取风险点。
- 查询合规规则。
- 生成修改建议。
- 判断是否需要人工审核。

### 项目收敛

沉淀 `agent_core.agent_loop`。

## 04. LangChain Agent Patterns

### 真实问题

LangChain 提供了常用 Agent 和 Tool 抽象。需要理解它们如何组合，而不是只复制示例代码。

### 基础原理

- Tool。
- tool binding。
- Agent executor / runnable agent。
- 工具轨迹。
- Agent 与 retriever / RAG 的组合。

### 最小实现

- 将 RAG retriever 包装成 Tool。
- 将合规检查包装成 Tool。
- 构建一个简单 LangChain Agent。

### 主流框架实现

- LangChain tools。
- create tool calling agent 类模式认知。
- callbacks / trace 基础。

### 失败分析与能力边界

- Agent 黑盒化。
- 默认 prompt 不适合业务。
- 工具描述过多导致选择混乱。

### 评估观测

- 输出工具轨迹。
- 记录每个工具输入输出。
- 对比自定义 loop 和 LangChain Agent。

### 小项目实战

需求评审助手升级：

- retriever tool。
- query rewrite tool。
- rule lookup tool。
- human review tool。

### 项目收敛

沉淀 `agent_core.langchain_adapter`。

## 05. LangGraph State 与 Workflow

### 真实问题

复杂任务需要状态、分支、循环、检查点和人工介入。单纯 Agent loop 难以表达可控业务流程。

### 基础原理

- State。
- Node。
- Edge。
- Conditional Edge。
- Checkpoint。
- Interrupt。
- Workflow 编排。

### 最小实现

- 构建一个合规审核 LangGraph：输入 -> 检索规则 -> LLM 审核 -> 条件分支 -> 人工确认或返回结果。

### 主流框架实现

- LangGraph StateGraph。
- checkpoint saver。
- interrupt / resume。

### 失败分析与能力边界

- 图结构过度复杂。
- 状态定义混乱。
- 节点副作用不可追踪。
- 条件分支没有测试样例。

### 评估观测

- 节点耗时。
- 分支命中率。
- 中断和恢复次数。
- 状态变化日志。

### 小项目实战

金融 Copilot 合规工作流：

- 草稿输入。
- 风险识别。
- 规则检索。
- 修改建议。
- 人工审批。
- 审计记录。

### 项目收敛

沉淀 `workflow_core.graphs`。

## 06. Human-in-the-loop

### 真实问题

金融和企业业务中，高风险输出不能由 AI 自动决定。系统需要在关键节点请求人工确认、允许修改、记录结果，并把反馈回流。

### 基础原理

- Human approval。
- Interrupt。
- Review queue。
- Editable draft。
- Audit trail。
- Feedback loop。

### 最小实现

- 在 LangGraph 中加入人工确认节点。
- 人工选择通过、驳回、修改或要求补充信息。

### 主流框架实现

- LangGraph interrupt / resume。
- 审核任务队列。
- 前端工作台在 `06_ai_native_frontend` 展开。

### 失败分析与能力边界

- 人工确认节点太多导致效率低。
- 高风险节点没有人工确认。
- 人工修改没有回流评估。

### 评估观测

- 人工介入率。
- AI 建议采纳率。
- 修改原因分类。
- 高风险漏拦截率。

### 小项目实战

合规审核 Copilot：

- 低风险自动给建议。
- 中风险人工确认。
- 高风险必须审核。

### 项目收敛

沉淀 `workflow_core.human_review`。

## 07. Agentic RAG 深化

### 真实问题

`03_rag` 已经实现单 Agent RAG 助手，但复杂场景还需要多步检索、动态补检索、结果反思和跨知识源综合。

### 基础原理

- Retrieve -> Judge -> Rewrite -> Retrieve again。
- 多跳检索。
- 检索质量评估。
- 反思生成。
- RAG as tool in workflow。

### 最小实现

- 对一个跨规则和历史评审的问题执行两轮检索。
- 第一轮不足时自动改写并补检索。

### 主流框架实现

- LangGraph 编排 Agentic RAG。
- Retriever tools。
- evaluator node。

### 失败分析与能力边界

- 多轮检索成本增加。
- 反思节点可能过度否定正确结果。
- 补检索没有停止条件。

### 评估观测

- 补检索触发率。
- 补检索后命中率提升。
- 额外成本和延迟。
- 最终答案 groundedness。

### 小项目实战

需求评审助手升级：

- 多知识源检索。
- 检索质量判断。
- 自动补检索。
- 最终带依据回答。

### 项目收敛

沉淀 `workflow_core.agentic_rag`。

## 08. Deep Research Workflow

### 真实问题

公告、财报、竞品资料、政策文件等复杂材料需要搜索、阅读、筛选、综合、引用和报告生成，不是一次 RAG 可以完成。

### 基础原理

- Research planning。
- Search。
- Read。
- Extract。
- Synthesize。
- Cite。
- Review。

### 最小实现

- 对一个公告解读任务生成 research plan。
- 读取多份材料并输出带引用摘要。

### 主流框架实现

- LangGraph research workflow。
- Search / file / retriever tools。
- report generator。

### 失败分析与能力边界

- 搜索结果质量差。
- 报告引用不可靠。
- 综合时混淆来源。
- 任务耗时和成本较高。

### 评估观测

- 来源覆盖率。
- 引用正确率。
- 报告完整性。
- 成本和耗时。

### 小项目实战

金融 Copilot 的公告 / 财报解读：

- 抽取事件。
- 识别影响。
- 输出风险点。
- 生成待确认问题。

### 项目收敛

沉淀 `workflow_core.deep_research`。

## 09. Multi-Agent Collaboration

### 真实问题

复杂任务可能天然存在多个角色：客服、检索员、合规审核员、总结员、人工审批员。单 Agent 承担全部职责时容易失控。

### 基础原理

- Role separation。
- Supervisor / Worker。
- Debate / Review。
- Handoff。
- Shared state。

### 最小实现

- 构建 supervisor + reviewer 两角色流程。
- 一个生成答案，一个审核风险。

### 主流框架实现

- LangGraph multi-agent。
- supervisor pattern。
- handoff pattern。

### 失败分析与能力边界

- 角色拆得太细。
- Agent 之间互相重复工作。
- 协作成本超过收益。
- 共享状态污染。

### 评估观测

- 每个角色贡献。
- 角色间冲突。
- 总成本和延迟。
- 最终质量是否提升。

### 小项目实战

金融 Copilot 多角色：

- 客服回答 Agent。
- 合规审核 Agent。
- 公告解读 Agent。
- Supervisor。

### 项目收敛

沉淀 `workflow_core.multi_agent`。

## 10. Agent Memory 与 Context

### 真实问题

Agent 执行多步骤任务时需要状态、任务记忆、工具观察和用户上下文。它和 RAG memory 不同，更强调执行过程和状态恢复。

### 基础原理

- Agent state。
- Working memory。
- Episodic memory。
- Tool observations。
- Checkpoint memory。
- Context budget。

### 最小实现

- 保存 Agent 执行轨迹。
- 恢复中断任务。
- 对工具观察做摘要。

### 主流框架实现

- LangGraph state。
- Checkpoint saver。
- Conversation / vector memory 边界认知。

### 失败分析与能力边界

- 历史工具结果污染新任务。
- 状态过大导致成本升高。
- checkpoint 中保存敏感数据。

### 评估观测

- 状态大小。
- 恢复成功率。
- 记忆命中是否相关。
- 状态泄露风险。

### 小项目实战

金融 Copilot 支持：

- 审核任务恢复。
- 用户修改意见保留。
- 工具结果摘要。

### 项目收敛

沉淀 `workflow_core.memory`。

## 11. MCP、A2A 与 Agent Skills

### 真实问题

Agent 需要连接越来越多工具和外部系统。只靠手写工具注册会变得难维护，因此需要理解开放协议和技能封装的定位。

### 基础原理

- MCP：模型上下文与工具连接协议。
- A2A：Agent 间协作协议认知。
- Agent Skills：可复用能力封装。
- Tool discovery。
- 安全边界。

### 最小实现

- 将一个本地工具封装为可复用 skill 的设计草图。
- 理解 MCP server / client 的职责。

### 主流框架实现

- MCP 基础认知。
- Codex / Cursor 等工具生态认知。
- A2A 概念边界。

### 失败分析与能力边界

- 为了协议而协议。
- 工具权限不清。
- 自动发现工具后缺少审计和确认。

### 评估观测

- 工具发现记录。
- 工具调用权限。
- skill 成功率。
- 协议接入失败原因。

### 小项目实战

为金融 Copilot 预留：

- 文档检索 skill。
- 合规审核 skill。
- 审批任务 skill。

### 项目收敛

沉淀开放协议与 skill 的使用边界，不在本阶段做完整平台。

## 12. Agent Evaluation 与 Safety

### 真实问题

Agent 的失败不只体现在最终答案，还体现在工具轨迹、越权调用、循环、错误审批和成本失控。

### 基础原理

- Trajectory evaluation。
- Tool call evaluation。
- Safety policy。
- Guardrails。
- Budget limit。
- Human override。

### 最小实现

- 为 Agent 建立 20 条 golden cases。
- 每条包含 expected outcome、allowed tools、forbidden tools、是否需人工确认。

### 主流框架实现

- 自定义 eval。
- LangSmith / trace 工具认知。
- `05_eval_observability` 系统展开。

### 失败分析与能力边界

- 最终答案正确但工具轨迹错误。
- 工具越权。
- 人工确认缺失。
- 成本过高。

### 评估观测

- 工具轨迹正确率。
- forbidden tool call rate。
- human confirmation accuracy。
- max iteration breach。

### 小项目实战

金融 Copilot 的 Agent eval：

- 正常客服问题。
- 高风险合规问题。
- 需要人工确认的问题。
- 工具失败问题。

### 项目收敛

将 Agent eval 接入 `05_eval_observability`。

## 13. 金融 Copilot 项目

### 真实问题

金融客服、运营、审核和合规场景需要可引用、可审核、可人工介入、可追踪的 AI 工作台。

### 基础原理

金融 Copilot 不是一个聊天机器人，而是由 RAG、工具调用、Agent 工作流、合规审核、人机协作、评估观测和前端工作台组成的系统。

### 最小实现

V0：金融知识问答 Copilot。

- 复用 `03_rag` 的知识系统。
- 接入规则和 FAQ。
- 输出带来源答案。

### 主流框架实现

V1-V3：

- Tool Runtime。
- LangChain Agent。
- LangGraph Workflow。
- Human-in-the-loop。
- Multi-Agent。

### 失败分析与能力边界

- 不替代合规最终责任。
- 高风险输出必须人工确认。
- 多 Agent 不作为默认方案。
- 协议和 skill 不提前平台化。

### 评估观测

- 工具轨迹。
- 合规审核准确性。
- 人工采纳率。
- 工作流失败节点。
- 成本和延迟。

### 小项目实战

金融 Copilot 阶段：

- V0：金融知识问答。
- V1：合规审核。
- V2：公告 / 财报解读。
- V3：多 Agent 协同和人工审批。

### 项目收敛

本课程最终把需求评审助手升级经验迁移到金融 Copilot，为 `07_projects` 的完整作品化打基础。
