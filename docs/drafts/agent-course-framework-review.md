# Agent 课程上游设计临时审查记录

> 状态：临时草案，不是课程顺序、知识范围、产品规格或工程方案的真源。
>
> 用途：冻结当前已经确认的问题、设计倾向和待决策项，供后续统一修改 `course/knowledge-map.md`、`course/learning-path.md`、`PLAN.md`、第二阶段项目篇及相关掌握标准。完成迁移并验证后删除本文。
>
> 审查日期：2026-08-27。

## 1. 当前共识与审查边界

- 第一阶段固定 RAG 仍是课程主线之一。当前已经完成的第 1–16 节没有方向性争议，不因 Agent 框架调整而推翻。
- 本轮只审查尚未编写的上游课程设计，重点是第二阶段 Agent 学习路径、知识范围、框架定位和工程边界，不修改现有正文与代码。
- 学习者当前不具备 Agent 开发经验。第二阶段应优先用成熟框架尽快形成可运行的完整 Agent，再沿真实运行拆解底层机制。
- 底层机制仍必须掌握，但不以长期维护一套自研 LangChain、LangGraph 或 LangSmith 等价实现作为学习证明。
- 课程最终仍围绕唯一产品“需求评审助手”，不增加平行框架项目或第二套产品。

## 2. 问题一：第一个完整 Agent 闭环出现过晚

当前学习路径从第 28 节进入第二阶段：

```text
28–33  Agent、Harness、Tool Schema、Tool Runtime 与安全边界
34–43  MCP、Search、Browser、File、Code Tool
44–50  Agent Loop、Retriever Tool、Routing 与 Skills
51     第一个最小 Agentic RAG 项目检查点
```

学习者进入第二阶段后，需要先学习大量组件与协议，直到第 44 节才正式进入 Agent Loop，到第 51 节才第一次组合出单 Agent 产品切片。

### 风险

- 学习过程呈现为技术组件目录，Agent 应用不是持续可见的主线。
- 学习者在没有完整运行直觉时先吸收 MCP、Browser、File、Code 等大量局部概念，认知负担过高。
- Harness、Tool Runtime、状态、事件和停止原因缺少一个早期真实运行承载，容易停留在抽象设计。
- 课程无法尽早比较固定 RAG 与单 Agent，复杂度准入缺少及时证据。

### 调整要求

- 第二阶段前部应尽快交付一个只包含少量受治理 Tool 的完整单 Agent。
- 第一个 Agent 切片至少具备真实模型、一个 Retriever Tool、一个确定性 Tool、最小 Run State、Tool 事件、停止原因、错误和 Trace。
- MCP、Browser、File、Code、Skills 等能力在最小 Agent 成立后逐项接入，每次扩展都回到同一运行入口验证。
- 固定 RAG 基线必须保留，用同一 Case 比较固定 RAG 与单 Agent，而不是通过更换案例证明 Agent 有效。

## 3. 问题二：运行时能力存在认知前置倒挂

当前路径在第 40 节学习 File Write 的确认、重试与幂等，在第 51 节形成最小 Agent，但 Run State、Event Stream 和运行界面位于第 52–60 节，Checkpoint、Interrupt、Human-in-the-loop 和恢复位于第 82–86 节。

### 风险

- Tool 已产生副作用，却还没有正式的等待确认、恢复和重复执行契约。
- 早期 Agent 实验缺少统一事件和 Trace，难以观察 Tool Call、状态变化、停止与失败。
- Deep Research 和 Multi-Agent 先于持久化、恢复和人工介入完成，长任务运行基础出现倒挂。
- 后续采用 LangGraph 时，课程可能重复讲一套自研状态机，再用框架重新实现一次。

### 调整要求

- 最小 Run State、Event、Trace 和停止原因随第一个 Agent 一起进入。
- 第一个有副作用的 Tool 之前必须已有最小 Approval / Interrupt 和幂等契约。
- 完整事件协议、SSE、重连和复杂 Workflow 可以后置深化，但不能把最小运行事实整体后置。
- Deep Research 或 Multi-Agent 进入长任务前，应先具备必要的 Checkpoint、Resume、取消传播和重复执行控制。

## 4. 问题三：缺少 LangChain、LangGraph 与 LangSmith 的正式框架主线

当前知识地图已经规划了这些框架背后的主要机制：

- LangChain 对应 Model、Message、Prompt、Structured Output、Tool、Middleware 和 Agent Harness。
- LangGraph 对应 State、Node、状态转换、持久化、Checkpoint、Interrupt、Resume、Streaming 和长任务运行。
- LangSmith 对应 Run、Trace、Dataset、Experiment、Evaluator、Regression、Feedback 和线上观测。

但这些关系没有正式进入知识地图节点、学习路径编号、`PLAN.md` 的实现选择和第二阶段项目检查点。现有 `agent_core` 规划为自行负责 Harness、Tool Runtime、Agent Loop、状态、Memory、Research、Multi-Agent 和 Workflow，存在重复实现成熟框架的明显风险。

### 框架定位

| 能力 | 课程定位 | 建议产品关系 |
| --- | --- | --- |
| 原生 Provider API、Prompt、Schema、Context | 主线机制 | 保留现有 `llm_core`，不能删除 |
| 原生最小 Tool Loop | 受控机制实验 | 只用于看清循环，不成为长期产品 Runtime |
| LangChain | Agent 框架主线 | 第二阶段高层 Harness、Model、Tool、Structured Output 与 Middleware 的主要实现 |
| LangGraph | Agent Runtime 主线 | 状态化编排、持久化、Checkpoint、Interrupt、Resume 和复杂 Workflow 的主要实现 |
| LangSmith | Observability / Evaluation 主线 | 必须完成真实 Trace 与 Eval 实验；通过适配器接入，不作为业务状态唯一真源 |
| OpenAI Agents SDK 等替代方案 | 边界认知或受控对照 | 用于理解框架选择，不建设第二套完整产品 |

### 设计倾向

第二阶段采用“框架优先、机制深化”的学习方式：

```text
先用成熟框架运行最小 Agent
→ 观察模型、Tool、State、Event 与 Trace
→ 沿真实运行拆解 Harness、Loop、Context 和停止机制
→ 用最小原生实现做单变量对照
→ 回到框架完成权限、持久化、恢复与评估
```

这里的“框架优先”不表示跳过机制，也不表示照抄框架教程。学习者必须能够解释框架隐藏了什么、哪些业务责任仍由应用承担、错误在哪一层产生，以及移除或替换框架时哪些契约应保持。

## 5. RAG 与框架的关系

固定 RAG 不因引入 LangChain 而改成框架黑盒。第一阶段继续由 `rag_core` 唯一实现文档解析、Chunk、Metadata、PostgreSQL FTS、pgvector、RRF、Retriever Contract、Context 和证据校验。

第二阶段的框架集成遵守：

- 将既有 `rag_core` Retriever 包装为受治理 Tool，不使用另一套 LangChain Retriever 复制产品主链。
- LangChain 的 Loader、Splitter、Vector Store 和 Retriever 作为框架能力认知或受控对照，不替换已经形成的 RAG 机制真源。
- 比较原生实现与 LangChain 适配时固定资料、模型、Prompt、Schema、Retriever 参数和预算，只改变框架路径。
- 框架接入不能改变 Citation Candidate、支持性、证据充分性、Refusal 和来源身份契约。

## 6. 候选的第二阶段学习主线

下面只表达认知依赖，不是新的编号真源：

```text
固定 RAG 产品基线
→ 原生 API、Agent SDK、LangChain、LangGraph、LangSmith 的边界
→ LangChain 最小 Agent：Model + Tool + Structured Output
→ 从运行反推 Harness、Tool Schema、Tool Runtime 与 Agent Loop
→ Retriever as Tool + 最小 Run State、Event、Trace、停止与评估
→ 第一个固定 RAG vs 单 Agent 项目检查点
→ MCP、Search、Browser、File Read
→ File Write、Code Tool、Approval、Interrupt 与幂等
→ Agent Context、Skills、Conversation 与 Memory
→ LangGraph 持久化、Checkpoint、Resume 与运行界面
→ Deep Research
→ Multi-Agent、Subgraph、Delegation 与 A2A
→ LangSmith Dataset、Experiment、Evaluator、Regression 与线上观测
→ 最终项目验收
```

LangSmith 的最小 Trace 应随第一个 Agent 引入；Dataset、Evaluator、线上评估和 Feedback 在质量收束阶段深化。LangGraph 的最小 State 与 Checkpoint 应早于长任务；复杂 Workflow 和 Subgraph 可以后置。

## 7. 候选工程边界

`agent_core` 不应成为自研通用 Agent 框架，而应维护产品可控的稳定 Facade、治理契约和框架适配：

```text
review_assistant
→ 产品 Schema、证据、权限、停止和交互策略
→ agent_core facade
   → LangChain Model / Agent / Tool adapter
   → LangGraph Runtime / Checkpointer adapter
   → rag_core Retriever Tool
   → LangSmith Trace / Eval adapter
```

需要守住的所有权：

- `llm_core` 维护统一 Provider 配置身份、Prompt、业务 Schema 和原生调用机制；LangChain 适配不能维护第二份模型配置真源。
- LangChain Tool 只是框架入口，实际调用仍必须经过应用认可的 Schema、权限、超时、取消、审计和副作用边界。
- `rag_core` 保持 Retriever 唯一实现，Agent 不复制 Retrieval 算法。
- LangGraph Checkpoint 保存可恢复执行状态，但不能自动代替产品 Run Record、Conversation、长期偏好或业务数据库。
- LangSmith Trace 是诊断和评估记录，不是 Citation、业务状态或产品验收数据的唯一真源。
- 缺少 LangSmith Key、服务失败或能力不支持必须显式暴露；本地结构化 Run Record 仍要存在，不能伪造 Trace 成功。

## 8. 建议补充的核心课程问题

不按框架 API 机械扩课，优先增加或重组下面四个核心问题：

1. 原生模型 API、Agent SDK、LangChain、LangGraph 和 LangSmith 分别负责什么，何时选择哪一层？
2. LangChain 怎样把 Model、Message、Tool、Structured Output、Middleware 和 Loop 组合成 Agent Harness，哪些责任仍属于应用？
3. LangGraph 怎样把 Agent State、确定性节点、模型节点、Checkpoint、Interrupt 和 Resume 组合成可恢复 Runtime？
4. LangSmith 怎样把 Trace 转成 Dataset、Experiment、Evaluator、Regression 和线上质量信号？

建议的真实对照实验：

- 使用同一模型、Prompt、Schema 和 Case，对比现有原生 Structured Output 与 LangChain Structured Output，观察请求、校验、错误和配置身份。
- 使用同一 Retriever Tool 与确定性 Tool，对比最小原生 Loop 与 LangChain Agent，观察 Tool Call、结果回填、停止和失败。
- 使用同一状态流运行 LangGraph 正常、Interrupt、Resume、超时和重复请求，验证 Checkpoint 与副作用边界。
- 同时追踪原生调用和 LangChain / LangGraph 运行，把一个真实 bad case 提升为 LangSmith Dataset，完成一次离线 Experiment 与 Regression 对照。

## 9. 上游文档的候选修改面

后续统一调整时依次处理：

1. `course/knowledge-map.md`：增加框架分层、LangChain Harness、LangGraph Runtime、LangSmith Observability / Evaluation 和框架迁移边界。
2. `course/learning-path.md`：重排尚未编写的第二阶段，让完整单 Agent、最小 State、Trace 和评估提前。
3. `PLAN.md`：明确 `agent_core` 是稳定 Facade 与框架适配层，不重复实现 LangGraph；明确 LangSmith 接入边界。
4. 第二阶段项目篇：增加框架选择题、固定对照、真实 Trace、Checkpoint / Resume 和 LangSmith Eval 检查点。
5. `docs/ai-coding-mastery.md`：增加框架代码所有权标准，包括定位 Provider、框架、应用、状态和观测层失败，以及替换框架时保持业务契约。
6. `docs/learning-guide.md`：只在现有快速演进框架规则不足时补充“框架优先、机制可解释、实验锁版本”的通用规则。

`SPEC.md` 默认不写 LangChain、LangGraph 或 LangSmith 名称，因为它维护产品做什么，而框架属于工程选择。只有框架接入改变产品输入输出、外部依赖、安全、状态或验收时才更新 SPEC。

## 10. 待决策项

- 第二阶段产品是否固定采用 Python LangChain + LangGraph，还是先通过框架准入实验再冻结；倾向前者，但仍需记录版本和替代边界。
- LangChain 是直接使用 `create_agent`，还是只使用 Model / Tool 组件并由 LangGraph 直接编排；应由最小 Agent 与复杂状态需求分别决定。
- LangSmith 是产品必接外部服务，还是课程必做真实实验、产品条件接入；倾向后者，同时保留本地 Run Record。
- 哪些现有 `agent_core` 责任由框架承担，哪些必须由应用 Facade 保留，尤其是 Tool Runtime、事件 Schema、停止原因和权限。
- 是否调整第二阶段总节数，还是通过合并现有机制题和重排编号吸收框架课程；不能建立第二套阅读顺序。
- 是否把 LangGraph 的最小 State / Checkpoint 提前，而将复杂 Workflow、Subgraph 和完整恢复留在后部深化。

## 11. 官方定位依据

正式改写框架课程时需要重新核对当前官方版本；本文只记录本次审查所依据的入口：

- [LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview)：LangChain Agent 是可配置 Harness，当前 Agent 构建在 LangGraph 之上。
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)：低层、有状态、长期运行的 Agent 编排 Runtime，支持持久化、Streaming 和 Human-in-the-loop。
- [LangSmith Observability](https://docs.langchain.com/langsmith/observability)：跨框架 Trace、调试、监控与反馈。
- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation)：Dataset、Experiment、离线/线上 Evaluation 与 Regression。
- [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents)：对照由应用自己管理 Loop 与由 SDK 管理 Agent Runtime 的边界。

实验篇必须固定实际使用的 LangChain、LangGraph、LangSmith SDK 和 Provider 版本；机制篇只维护跨版本稳定职责、状态变化和边界。
