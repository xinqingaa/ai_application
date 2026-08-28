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

> 我们可以继续讨论课程的上游设计吗？
我还在想 机制和框架怎么取舍？框架作为主线我觉得是必须要学习的。我可以接受28-43可以后置一些 早点完成rag-agent的第一个完整闭环；agent和tool、mcp可以和agentic rag 调整一下顺序；但是这个agent skills 就不能在这个位置了吧？前置倒挂也可以顺带着一起解决。
现在我觉得还是框架和现有课程设计的机制 我不好取舍，我想着有两个方案
1.维持现有上游的课程设计，可以新增几个章节 框架如何实现，定位也是机制篇，但是主要是讲这几个框架实现；
2.大幅的减少现在的纯原生机制讲解，从框架入手学习agent，而不是都靠机制，因为我的定位是大前端，我希望快速补齐agent应用开发的能力，用什么框架用什么机制实现其实都是一种手段，我可以从这几个框架里得到作者以及生态的帮助，是不是事半功倍呢？
对此请你详细分析一下 更适合我的方案是什么呢 是哪种呢 现有的上游课程设计 应该如何调整

> 结论先说：
更适合你的不是方案 1 或方案 2 的原样，而是“方案 2.5”：
以 LangChain、LangGraph、LangSmith 为主线快速形成 Agent 能力；保留少量但关键的原生机制，用来解释框架隐藏的运行过程、边界和失败原因。

如果必须二选一，我会选择方案 2，但要把“减少机制”改成“重排、合并和按需深入”，不能简单删除。
你是大前端背景，而且当前并不熟悉 Agent 开发。课程最重要的目标不是让你手写一个 Agent 框架，而是让你尽快具备：
- 能用成熟框架完成真实 Agent 应用；
- 能判断什么时候应该用 Agent，什么时候普通程序或固定 RAG 就够；
- 能定位模型、框架、Runtime、业务代码和外部服务分别出了什么问题；
- 能控制权限、状态、证据、成本、停止和恢复；
- 能在框架不适用时退回底层 API，而不是被框架绑死。
为什么方案 1 不适合直接采用
方案 1 是保留大量原生机制，再增加 LangChain、LangGraph、LangSmith 的实现章节。
它的优点是底层完整，但有几个明显问题：
1. 会出现两条平行学习路线。
   一条是：
   原生 API → 自己实现 Harness → 自己实现 Tool Runtime → 自己实现 Agent Loop
   另一条是：
   LangChain → LangGraph → LangSmith
   学习者会不断问：“前面自己实现的东西，后面框架是不是又实现了一遍？”
2. 会进一步推迟第一个完整 Agent。
   当前第 28–43 节已经先讲了大量 Harness、Tool、MCP、Browser、File、Code 等内容，到第 44 节才讲 Agent Loop，第 51 节才出现第一个 Agentic RAG 检查点。
   如果再增加完整框架章节，Agent 主线会更晚。
3. 容易把课程变成“框架源码阅读课”。
   LangChain、LangGraph 的内部实现复杂且变化快。学习者需要掌握的是它们的运行模型、责任边界和使用方式，不需要复刻它们的内部代码。
4. 会放大你最担心的心智负担。
   你现在不是缺少某一个 API，而是还没有 Agent 的整体运行直觉。先学习一整套原生抽象，再学习框架映射，容易在还没有产品结果之前陷入抽象。
所以，方案 1 只有在“原生机制已经很短、框架作为实现映射”时才成立。如果是完整保留现有原生路线，再新增框架路线，我不建议。
为什么方案 2 的方向是对的，但不能过度削减机制
方案 2 更符合你的目标：
先用框架完成真实 Agent
→ 观察真实运行
→ 理解框架隐藏的机制
→ 用少量原生代码做对照
→ 回到框架实现状态、权限、评估和产品能力
它能带来几个实际收益：
- 更早得到可运行结果；
- 更快建立 Agent 的整体心智模型；
- 直接使用生态中的 Tool、Integration、Middleware、Tracing 和 Eval；
- 遇到问题时可以参考官方文档、社区案例和成熟实现；
- 课程成果更接近真实工作中的 Agent 开发。
但如果“大幅减少机制”变成只学框架 API，会有四个风险：
1. 不知道模型为什么反复调用 Tool。
2. 不知道 Structured Output 失败发生在模型、解析器还是业务校验。
3. 不知道 LangGraph 的 State、Checkpoint 和产品数据库分别负责什么。
4. 不知道什么时候框架增加了复杂度，反而应该退回普通函数或固定 Workflow。
因此，应该减少的是“重复实现和重复解释”，不是减少关键机制。
框架和原生 API 的真实关系
你之前把它类比成原生 JS 和 Vue/React，这个类比有一部分成立，但不完全准确。
更准确的分层是：
Provider 原生 API
    ↓
LangChain：模型、消息、Prompt、Tool、Structured Output、Agent Harness
    ↓
LangGraph：有状态运行、节点、状态转换、Checkpoint、Interrupt、Resume
    ↓
LangSmith：Trace、调试、Dataset、Experiment、Evaluator、线上反馈
同时，产品业务策略横向贯穿这些层：
产品 Schema、权限、证据、Citation、Refusal、审批、业务状态
具体来说：
层次	主要解决的问题	不应该承担的责任
原生 Provider API	请求模型、接收结果、处理基础错误	产品业务流程
LangChain	组合 Model、Tool、Prompt、Structured Output 和基础 Agent	产品权限、Citation、业务验收
LangGraph	管理有状态、可恢复、可中断的 Agent Runtime	产品长期记忆和业务数据库
LangSmith	记录 Trace、调试运行、做 Dataset 和评估	业务状态、Citation、最终产品事实
rag_core	文档、检索、Context、来源和证据校验	Agent 动态编排
review_assistant	业务规则、权限、审批、输出和用户交互	通用框架能力


所以它不完全像 React。
React 主要抽象 UI 渲染；LangChain 抽象的是模型调用和工具编排；LangGraph 更像有状态任务运行时；LangSmith 更接近“分布式 Trace + 实验评估 + 质量反馈系统”。
另外，框架和原生 API 不是互斥关系。LangChain 最终仍然调用底层模型 API。你应该学会：
框架默认路径
→ 框架扩展点
→ 必要时下沉到原生 API
而不是把两者当成两套完全独立的技术。
哪些机制必须保留
第一阶段第 1–16 节固定 RAG 应保持不变。这部分已经形成稳定基础，尤其是：
- Model 输入输出契约；
- Prompt、Schema、Context；
- Structured Output 和应用侧校验；
- 错误分类和显式失败；
- Retriever Contract；
- Citation、证据不足和拒答。
这些内容正好是 Agent 后续必须复用的边界。
第二阶段必须保留，但可以通过框架运行来讲的机制包括：
1. 模型决策和应用执行的分离；
2. Tool Schema、参数校验和结构化错误；
3. Agent Loop、预算、停止和无进展检测；
4. 权限、超时、取消、审计和副作用；
5. Retriever 作为 Tool 后如何保留来源和 Citation；
6. Run State、Event、Trace 和停止原因；
7. Checkpoint、Interrupt、Resume 和幂等；
8. Agent、Workflow、Multi-Agent 的选择边界；
9. Tool、Skill、MCP、Memory 和业务知识的区别；
10. Agent 轨迹、成本、延迟和质量评估。
这些是 Agent 工程能力，不属于某个框架的可有可无的 API。
可以压缩、后置或改成对照实验的内容包括：
- 完整手写通用 Agent Harness；
- 完整手写通用 Tool Runtime；
- 先于 Agent 的大量 MCP 协议细节；
- 先于第一个 Agent 的 Memory 深化；
- 早期的 Agent Skills 格式和脚本执行；
- 没有业务收益证明之前的 Multi-Agent、A2A 和复杂 Workflow；
- 将 LangChain、LangGraph 源码内部逐行讲解。
原生实现建议只保留两类：
- 一个最小原生 Tool Loop，用来观察模型提出 Tool Call、应用执行、结果回填和停止；
- 一个原生与框架的单变量对照，用来确认框架没有改变你的业务契约。
不需要自己实现一个可长期维护的“LangChain 替代品”。
Agent Skills 确实不应该放在当前这个位置
你这个判断是对的。
当前第 48–50 节把 Agent Skills 放在 Agentic RAG 单元里，但它的前置关系其实更靠后：
Agent Loop
→ Tool Runtime
→ Context Budget
→ State / Memory
→ Skill 发现与加载
→ Skill 脚本治理
Skill 不是 Agent 的核心运行机制，它更像一种可复用的任务说明、资源和流程知识封装。
如果在第一个 Agent 之前讲 Skill，学习者很容易产生三个误解：
- 把 Skill 当成更大的 Prompt；
- 把 Skill 当成 Tool；
- 认为 Skill 自带执行权限。
建议把 Agent Skills 移到：
第一个 Agentic RAG 闭环
→ Context、Conversation、Memory
→ Tool 权限和受治理执行
→ Agent Skills
→ Deep Research
如果 Skill 只包含说明和参考资料，可以作为扩展能力；如果包含脚本，则必须放在 Tool Runtime、沙箱、权限和审计之后。
建议的第二阶段重排
不必立刻确定最终编号，但认知顺序建议改成下面这样：
固定 RAG 基线
→ 原生 API、LangChain、LangGraph、LangSmith 的分层关系
→ LangChain 最小 Agent
→ 从真实运行理解 Agent Loop
→ Tool Schema、Runtime、错误和停止
→ Retriever as Tool
→ Query Rewrite、Source Routing、补检索和追问
→ 最小 State、Event、Trace 与 Eval
→ 第一个完整 Agentic RAG 检查点
→ LangGraph State、Node、状态转换
→ Checkpoint、Interrupt、Resume、幂等
→ MCP 边界、能力发现和真实接入
→ Search、Browser、File Read
→ File Write、Approval、Code Tool 和沙箱
→ Context、Conversation、Memory
→ Agent Skills
→ Deep Research
→ Multi-Agent、A2A
→ 必要 Workflow
→ LangSmith 深化评估、Regression 和 Feedback
→ 最终项目验收
可以进一步对应到当前课程：
- 当前 28 的结构选择和框架边界：保留，但加入 LangChain/LangGraph/LangSmith 总览；
- 当前 29–33：不要先独立讲完整 Harness，改成从 LangChain Agent 的真实运行中拆解；
- 当前 44–47：提前到第一个框架 Agent 之后，形成 Agentic RAG；
- 当前 51：提前，作为第二阶段早期的第一个完整检查点；
- 当前 52、55、56：把最小 State、Event、Trace 提前到第一个 Agent 检查点之前；
- 当前 83–85：把最小 Checkpoint、Interrupt、Resume、幂等提前到 File Write 和 Deep Research 之前；
- 当前 34–43：大部分 MCP、Browser、File、Code 后置到 Agentic RAG 基线成立之后；
- 当前 48–50：移出 Agentic RAG，放到 Context、Memory 和 Runtime 治理之后；
- 当前 61–69：保留 Deep Research，但建立在已有 Agent、Tool、证据和恢复能力上；
- 当前 70–86：Multi-Agent、A2A 和复杂 Workflow 继续后置；
- 当前 87–91：保留 LangSmith 的深度评估和质量收束，但 LangSmith 的最小 Trace 必须提前。
这样可以把第一个完整 Agent 从当前第 51 节左右提前到第二阶段前半段，同时不牺牲后续的深度。
推荐的课程比例
不建议按“原生课程”和“框架课程”各自占一半，因为这会产生重复。
更适合你的重心是：
框架和产品实践：约三分之二
机制解释和原生对照：约三分之一
但这三分之一不是单独再造一条课程，而是嵌入框架课程：
一节关于 LangChain Agent 的课程，应该同时回答：
- LangChain 把哪些对象组合起来；
- 一次运行中 Model、Tool、Result 和 Stop 怎样流动；
- 哪些错误由框架处理，哪些必须由应用处理；
- 如何观察和修改这次运行；
- 如果不用 LangChain，哪些业务契约仍然必须保持。
一节关于 LangGraph 的课程，应该回答：
- State、Node、Edge 和 Checkpoint 分别是什么；
- 哪些节点由模型决定，哪些节点必须确定性执行；
- Interrupt 和 Resume 如何工作；
- 重试和恢复为什么可能重复产生副作用；
- Checkpoint 为什么不能代替产品 Run Record 或业务数据库。
一节关于 LangSmith 的课程，应该回答：
- Trace、Run、Span 和业务结果是什么关系；
- Trace 能定位什么，不能证明什么；
- 如何把真实 bad case 固定成 Dataset；
- 如何做 Experiment、Evaluator 和 Regression；
- LangSmith 不可用时，本地运行记录如何继续保留。
对正式上游文档的具体调整建议
后续修改时，建议不是简单新增三节“LangChain 入门”“LangGraph 入门”“LangSmith 入门”，而是同时调整四个真源：
1. course/knowledge-map.md
   增加明确的框架分层：
   - LangChain：高层 Agent Harness 与组件组合；
   - LangGraph：有状态、可恢复 Agent Runtime；
   - LangSmith：Trace、Evaluation 和质量反馈；
   - 原生 API：底层对照和逃生通道；
   - 框架不能替代产品业务契约。
2. course/learning-path.md
   重排第二阶段，使第一个 Agentic RAG 检查点提前。
   不建立第二套编号，而是合并重复机制、移动现有编号内容，再保持全局连续编号。
3. PLAN.md
   将 agent_core 从“自研 Agent 平台”明确改为：
   产品 Facade
   + LangChain 适配
   + LangGraph Runtime 适配
   + Tool 治理
   + 业务状态与事件边界
   agent_core 不应重新实现一套 LangChain 或 LangGraph。
4. 第二阶段项目篇
   把第一个检查点改成早期的“框架 Agentic RAG 闭环”，至少要求：
   - LangChain 真实模型；
   - 受治理 Retriever Tool；
   - 一个确定性 Tool；
   - Tool 参数和错误；
   - 最小停止原因；
   - 最小 Run State；
   - LangSmith Trace；
   - 固定 RAG 与 Agentic RAG 的对照。
最终建议
你的课程应该采用下面的主线：
固定 RAG 打基础
→ LangChain 快速完成第一个 Agent
→ 用运行结果理解 Agent 机制
→ LangGraph 补齐状态、恢复和人工介入
→ MCP、Tools 和 Skills 扩展能力边界
→ Deep Research 和 Multi-Agent
→ LangSmith 贯穿观测、评估和回归
所以答案不是“框架取代机制”，而是：
框架负责让你尽快具备生产能力，机制负责让你拥有判断、调试和迁移能力。

这对你的背景最合适。当前上游设计不需要推翻第一阶段 RAG，而是要把第二阶段从“先讲完所有原语，再组合 Agent”改成“先用框架完成一个小闭环，再围绕真实运行补齐机制”。

## 12. 本轮结论：冻结第一阶段，重构第二阶段

审查结论已形成共识：当前课程不需要重新审查或推翻第一阶段固定 RAG 的原理与机制。第 1–16 节已经建立了模型输入输出、结构化结果、可靠调用、文档处理、检索、Context、来源和可信生成的稳定基础，后续 Agent 课程应直接复用这些契约。

本轮需要调整的是第二阶段的学习顺序、框架定位和机制粒度，而不是第一阶段的技术方向。第二阶段采用“框架优先、机制深化”的主线：先用成熟框架完成一个真实的 Agentic RAG 闭环，再沿真实运行拆解必要机制，并用少量原生实现做受控对照。

### 已冻结的设计原则

1. **第一阶段保持不变**：第 1–16 节固定 RAG 不新增框架替代路线，不因引入 LangChain 而改写 `rag_core` 的检索、来源、Citation、Refusal 和证据边界。
2. **框架成为第二阶段主线**：LangChain 负责高层 Agent Harness 与 Model、Tool、Structured Output 等组合；LangGraph 负责有状态运行、Checkpoint、Interrupt 和 Resume；LangSmith 负责 Trace、Dataset、Experiment、Evaluator 和线上质量反馈。
3. **机制按需进入**：保留 Tool 契约、Agent Loop、停止、权限、错误、状态、事件、证据、恢复和评估等不可替代机制；删除或合并重复的通用框架实现，不再把自研 LangChain 或 LangGraph 等价物当作学习目标。
4. **首个完整 Agent 提前**：在第二阶段前部先完成 LangChain 驱动的最小 Agentic RAG，至少包含真实模型、受治理 Retriever Tool、一个确定性 Tool、最小 State、停止原因、结构化错误和 LangSmith Trace，并与固定 RAG 做同 Case 对照。
5. **Agent Skills 后置**：Agent Skills 不再与最初的 Agentic RAG 核心并列。它依赖已经成立的 Agent Loop、Tool Runtime、Context Budget 和安全边界，应放在首个单 Agent 闭环以及 Context / Memory 之后；包含脚本时还必须以后置的沙箱、权限、确认和审计为前置。
6. **解决运行能力前置倒挂**：最小 State、Event、Trace 和停止事实随首个 Agent 提前；LangGraph 的最小状态运行和 Checkpoint / Interrupt / Resume 早于长任务、File Write、Deep Research 和 Multi-Agent。复杂 SSE、Workflow、A2A 和完整质量平台继续后置深化。
7. **MCP 与通用工具后置到基线之后**：内部 Tool 和 Agentic RAG 基线成立后，再学习 MCP、Search、Browser、File、Code 等外部能力。File Read 可以先进入，File Write 和 Code Tool 必须建立确认、幂等、沙箱和资源边界后再进入。
8. **`agent_core` 不做通用框架**：它只维护产品 Facade、治理契约、事件和框架适配；`rag_core` 仍是 Retriever 唯一实现；LangGraph Checkpoint 不替代产品 Run Record；LangSmith Trace 不替代业务状态、Citation 或产品验收数据。

### 推荐的第二阶段依赖顺序

后续修改正式学习路径时，按下列认知依赖重排现有课程并重新连续编号，不建立第二套课程顺序：

```text
固定 RAG 基线
→ 框架分层：原生 API、LangChain、LangGraph、LangSmith
→ LangChain 最小 Agent
→ 从真实运行理解 Agent Loop、Tool Call 和停止
→ Tool Schema、Runtime、错误、权限和预算
→ Retriever as Tool
→ Query Rewrite、Source Routing、补检索和追问
→ 最小 State、Event、Trace 与评估
→ 第一个完整 Agentic RAG 检查点
→ LangGraph State、Node、状态转换
→ Checkpoint、Interrupt、Resume、重试和幂等
→ MCP、Search、Browser、File、Code 等受治理能力
→ Context、Conversation、Memory
→ Agent Skills 的发现、加载和受治理执行
→ Deep Research
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ LangSmith 深化评估、Regression、Feedback 与最终验收
```

### 框架课程的写作边界

框架课程不是 API 清单或源码复刻。每个框架主题都必须同时说明：它解决的具体问题、抽象对应的运行机制、一次运行中的数据或状态流、框架负责与应用负责的边界、正常和失败路径，以及移除或替换框架后仍必须保持的业务契约。

原生机制保留为短小的对照实验：一个最小原生 Tool Loop，以及必要的原生与框架单变量比较。实验必须锁定 SDK、Provider 和协议版本；机制正文维护跨版本稳定的责任和不变量，避免把快速变化的框架 API 写成长期真源。

本结论作为后续正式修改 `course/knowledge-map.md`、`course/learning-path.md`、`PLAN.md`、第二阶段项目篇和掌握标准的依据。正式迁移完成并验证后，删除本临时文档。
