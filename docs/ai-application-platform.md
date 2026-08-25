# 企业级 AI 应用平台能力地图

这份文档用于保持对企业级 AI 应用的长期视野。

它不是当前项目待办、课程目录或阶段验收清单。当前目标和阶段以 [strategy.md](strategy.md) 为准；能力是否进入项目，由真实阶段问题决定。

## 1. 核心判断

企业级 AI 应用不是一个聊天窗口，也不是单个 RAG 或 Tool Calling Demo。

完整平台通常需要整合：

- 模型与 Provider。
- 知识生产与检索。
- AI 应用运行时。
- Agent、Workflow 和工具。
- 评估、观测和运营。
- 权限、安全和审计。
- AI Native 前端控制面。

前端在这里不是普通展示层，而是用户理解证据、状态、风险、工具调用、人工介入和质量反馈的操作界面。

需求评审助手只按版本取用其中必要能力，不承担建设通用平台的任务。

## 2. 能力进入当前项目的过滤器

一项平台能力进入当前项目之前，应同时回答：

1. 当前阶段遇到了什么真实问题？
2. 现有简单方案为什么不足？
3. 最小可验证实现是什么？
4. 用什么结果、指标或失败案例证明价值？
5. 它是否迫使项目过早平台化？
6. 本次明确不实现什么？

如果无法回答，应保留为概念或机制认知，不进入当前项目代码。

## 3. 知识生产与治理

企业 RAG 的核心不只是向量查询，而是把资料生产为可追踪、可检索、可治理的知识。

长期能力包括：

- 多来源资料接入。
- 文件、知识文档和索引对象分离。
- PDF、Word、表格、图片和网页解析。
- 文档清洗、结构保留和版面信息。
- Chunk、父子块和 Metadata。
- Embedding、全文索引、向量索引和混合检索。
- 文档版本、更新、删除一致性和权限过滤。
- 入库任务、进度、失败、取消和重试。
- 检索测试、来源定位和知识回流。

对当前项目的启发：

- 第一阶段必须能区分原始资料、知识文档、Chunk 和检索结果。
- 第一阶段使用 PostgreSQL 全文检索、pgvector 和应用侧 RRF 建立多路召回基线，并显式观察 Top-k、阈值、过滤和每路排名。
- 检索和 Citation 必须可以观察；Reranker 等增强先通过机制实验和固定评估集证明收益，再决定是否进入产品。
- 复杂解析、连接器生态和完整权限体系按真实需求后置。

## 4. AI 应用运行时

企业 AI 应用需要把模型、知识、工具和交互配置组合成可运行产品。

长期能力包括：

- 应用对象和应用配置。
- 模型、知识库和工具绑定。
- Prompt、Schema 和检索策略版本。
- 草稿、发布、版本快照和回滚。
- 会话、任务和运行记录。
- 普通 API、SSE、OpenAI-compatible API 和嵌入入口。
- 成本、访问限制和基础运营统计。
- 配置依赖、删除检查和资源影响分析。

对当前项目的启发：

- `review_assistant/` 应从第一阶段就是产品真源。
- 应用配置不能全部散落在 Prompt 或 UI 中。
- 第一阶段先建立简单可用的 RAG 应用，不先建设通用应用管理平台。

## 5. Agent、Workflow 与工具

### Agent

长期能力包括：

- Agent 角色、目标和边界。
- Tool Schema、参数校验和 Tool Runtime。
- 最大步数、超时、预算和停止条件。
- 记忆、上下文、运行轨迹和失败记录。
- 知识库、工具和模型授权。

### Workflow

长期能力包括：

- 节点、边、状态和变量。
- 条件、循环、并行和子流程。
- 节点输入输出契约。
- Checkpoint、中断、恢复和重试。
- Human-in-the-loop。
- 草稿、发布、版本和运行调试。

### Multi-Agent

长期能力包括：

- Supervisor / Worker。
- 按角色、知识源、工具或责任拆分。
- 并行执行和依赖调度。
- 共享状态和证据。
- 结果合并、冲突处理和最终裁决。
- 多 Agent 质量、成本与延迟评估。

### 工具生态

长期能力包括：

- 内置工具和业务 API。
- MCP、A2A 和 Agent Skills。
- 工具权限、高风险确认和操作审计。
- 工具版本、执行记录和失败重试。

对当前项目的启发：

- 第一阶段用固定 RAG 建立可信检索、证据输出和最小产品闭环，不提前引入 Agent 编排。
- 第二阶段先建立单 Agent Harness、Tool Calling 和 Agentic RAG，再接入 MCP、Agent Skills 与 Deep Research，随后进入 Multi-Agent 和 A2A。
- 第二阶段将短期记忆和长期记忆纳入单 Agent 主线；长期记忆只保存用户明确确认且跨会话仍有效的偏好或约束，业务事实继续进入可引用知识。两类记忆都必须有作用域和治理，初期优先复用 PostgreSQL / pgvector，不把 Mem0 设为产品前置。
- Workflow 只承担多步协作确实需要的状态、分支、中断、恢复和人工确认，不单独扩展成一个大阶段。
- 不强迫所有业务进入可视化编排。
- 多 Agent 必须证明比单 Agent 基线更有价值。

## 6. 评估、观测与运营

企业 AI 应用不能只靠人工试问。

长期能力包括：

- Evaluation Dataset 和 Golden Set。
- Retrieval、Generation、Citation 和 Refusal Eval。
- Agent Trajectory、Tool Call 和 Workflow Eval。
- LLM-as-Judge 与人工评审。
- Trace、Span 和版本对比。
- Bad Case、反馈、标注和回归。
- Token、成本、延迟、失败率和成功率。
- Prompt、Retriever、Model、Tool 和 Workflow 版本关联。

对当前项目的启发：

- 评估从第一阶段进入，不是独立到最后才学习。
- 每个集成检查点保留最小质量证据。
- 第二阶段增加 Agent 轨迹、工具调用和多 Agent 协作评估。
- 完整实验平台和运营体系后置。

## 7. AI Native 前端控制面

AI Native 前端需要表达不确定性、证据和执行过程。

长期能力包括：

- 流式文本与结构化事件。
- 任务状态和响应状态机。
- Sources、Citation、检索片段和证据定位。
- Tool Call、Agent 轨迹和 Workflow 节点状态。
- 中断、人工确认、修改和恢复。
- 错误原因、重试和降级提示。
- 知识库、评估和 bad case 工作台。
- 成本、延迟和质量面板。

对当前项目的启发：

- 第一阶段就提供最小可用交互，不把前端推迟到课程末尾。
- 第二阶段进一步呈现 Agent 轨迹、工具调用、多 Agent、必要的 Workflow 状态和人工协作。
- UI 不伪造服务端状态，也不隐藏真实失败。

## 8. 数据、安全与基础设施

长期能力包括：

- PostgreSQL、pgvector、Redis 和对象存储。
- 后台任务、队列、锁和幂等。
- 用户、角色、资源和知识权限。
- 审计、脱敏、内容安全和高风险操作确认。
- 多环境配置、Docker、监控和告警。
- 多租户、灰度、扩容和灾备。

当前项目按需取用：

- 第一阶段优先配置、文件、PostgreSQL/pgvector、基础日志和可运行部署。
- 第二阶段按 Agent 状态、必要的 Workflow 控制、后台任务和产品化需要增加 Redis、任务系统和更完整观测。
- 多租户、权限中台、Kubernetes 和企业级告警保留为远期认知。

## 9. RAGFlow 的核心经验

RAGFlow 更值得学习的是知识生产与检索上下文，而不是功能数量：

- 文件不等于知识文档。
- Knowledgebase 是带配置和生命周期的业务对象。
- 文档解析和索引构建是可观察任务。
- Chunk、全文索引、向量索引和 Rerank 有独立边界。
- 检索结果、阈值、权重和 Citation 可调试。
- 评估数据集与运行结果进入平台模型。

当前不复制：

- 全格式复杂解析平台。
- 完整 Connector 生态。
- GraphRAG、RAPTOR 等高级索引体系。
- 多租户和大规模任务执行平台。

## 10. MaxKB 的核心经验

MaxKB 更值得学习的是从 RAG 能力到可发布应用的产品化：

- 简单应用和 Workflow 应用是不同产品形态。
- 简单模式覆盖主要 RAG 场景，复杂流程再进入编排。
- Application、Knowledge、Model、Tool 和 Version 是显式资源。
- 应用发布、会话、API、嵌入和运行记录形成产品闭环。
- PostgreSQL + pgvector 有利于业务数据和向量状态协同。

当前不复制：

- 通用应用市场和工具市场。
- 完整低代码 Workflow 画布。
- 多工作空间和企业资源治理。
- 完整 Celery 任务平台和私有化安装体系。

## 11. 当前阶段的采用边界

### 第一阶段优先取用

- 文档、Chunk、Metadata 和入库状态。
- PostgreSQL 全文检索、pgvector、应用侧 RRF，以及 Top-k、阈值、过滤和 Retrieval 诊断。
- Sources、Citation、Refusal。
- 最小评估集、trace 和 bad case。
- 简单 AI 应用入口和可观察交互。

### 第二阶段优先取用

- Agent Harness、Tool Runtime、Agentic RAG 和记忆治理。
- MCP、Agent Skills、浏览器、搜索、代码与文件工具，以及 Deep Research。
- 多 Agent 职责、共享状态、汇总和 A2A 协议边界。
- 必要的 Workflow State、分支、Human-in-the-loop、中断和恢复。
- Agent、Tool、Multi-Agent 与必要 Workflow 的轨迹和质量评估。
- 工作台、质量面板和部署。

### 远期保留

- 通用低代码平台。
- 完整知识运营平台。
- MCP / Tool 生态平台。
- 多租户、权限中台和企业运营体系。

这份地图的作用是帮助做边界判断。它不能替代 [strategy.md](strategy.md) 的当前目标，也不能替代 `course/project/` 的阶段验收。
