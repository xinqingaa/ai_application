# 03 RAG、LangChain 与单 Agent 知识助手大纲

## 课程定位

`03_rag` 是需求评审多 Agent 助手的知识系统与单 Agent RAG 主线。

这门课不是只学习“文档切分、向量化、检索、生成”这条固定流程，而是系统理解企业知识如何进入模型上下文，并进一步把固定 RAG 做成可引用、可拒答、可评估、可治理、可迭代、可追问的知识助手。

RAG 和 Agent 不应该被理解成完全割裂的两门课。固定 RAG 是知识注入和证据生成的基础能力；单 Agent RAG 是在固定 RAG 基础上，加入查询改写、知识源选择、检索质量判断、补检索和追问补全等能力。

本课程直接服务需求评审助手，知识源包括 PRD、接口文档、业务规则、历史评审记录、会议纪要、技术方案和验收标准。

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

代码不按章节机械堆脚本，而是围绕 `rag_core`、`rag_eval`、`rag_memory`、单 Agent RAG demo 和项目 app 组织。

## 与 02 / 04 / 05 的关系

`02_llm` 提供模型调用、Prompt、结构化输出、上下文工程和 harness 底座，不系统学习 LangChain。

`03_rag` 正式学习 LangChain 的 RAG 常用抽象，包括 Document、Loader、TextSplitter、Embeddings、VectorStore、Retriever、PromptTemplate、OutputParser、Runnable / LCEL 基础组合、Retriever as Tool 和简单单 Agent 知识助手。

`04_agent` 继续深入 Tool Runtime、Agent Loop、LangGraph、Workflow、Human-in-the-loop、Multi-Agent、MCP / A2A 和 Agent Skills。

`05_eval_observability` 系统学习 RAG、Agent、Workflow 和项目的评估、观测、trace、回归和质量工程。

## 完成标准

完成本课程后，应能做到：

- 判断什么时候用 Prompt、长上下文、固定 RAG、单 Agent RAG、Agentic RAG、Workflow 或人工处理。
- 构建文档处理、chunk、metadata、embedding、vector store、retrieval、context construction、generation 的主链路。
- 设计 Knowledgebase、File、Document、Paragraph、Chunk、Embedding、Citation、Feedback 的边界。
- 使用 LangChain 理解并实现主流 RAG 组件，而不是只会调框架 API。
- 生成带来源、可拒答、可追溯的结构化回答。
- 建立 RAG golden set、检索评估、生成评估和失败案例回流。
- 区分短期记忆、长期记忆、任务状态、用户记忆和知识库。
- 用单 Agent 做查询改写、知识源选择、检索质量判断、追问补全和 retriever 工具调用。
- 收敛出需求评审助手 V0-V3。

## 代码组织建议

```text
source/03_rag/
├── packages/
│   ├── rag_core/
│   ├── rag_eval/
│   └── rag_memory/
├── demos/
│   ├── minimal_rag/
│   ├── document_ingestion_pipeline/
│   ├── chunking_comparison/
│   ├── retrieval_comparison/
│   ├── sources_refusal_demo/
│   ├── rag_eval_demo/
│   └── single_agent_rag_demo/
├── apps/
│   └── review_assistant_v0/
└── README.md
```

`rag_core` 是主链路底座，`rag_eval` 是评估与回归底座，`rag_memory` 先保持轻量，`single_agent_rag_demo` 验证单 Agent 知识助手，`review_assistant_v0` 收敛需求评审助手的最小闭环。

## 专题目录

```text
course/03_rag/
├── 00_rag_and_agent_problem_space.md
├── 01_rag_architecture_and_boundary.md
├── 02_langchain_for_rag_basics.md
├── 03_document_loading_and_cleaning.md
├── 04_chunking_and_metadata.md
├── 05_knowledge_governance.md
├── 06_embedding_and_vector_store.md
├── 07_retrieval_strategies.md
├── 08_query_rewrite_and_source_routing.md
├── 09_context_construction_and_compression.md
├── 10_generation_sources_refusal.md
├── 11_rag_evaluation.md
├── 12_rag_memory.md
├── 13_single_agent_rag_assistant.md
├── 14_rag_failure_analysis.md
├── 15_review_assistant_project.md
└── outline.md
```

## 00. RAG 与 Agent 问题空间

### 真实问题

LLM 自身不了解企业内部需求、接口文档、历史评审记录、业务规则和会议纪要。需求评审助手如果只靠 Prompt，很容易编造、遗漏依据或给出无法追溯的建议。

### 基础原理

- RAG 解决知识注入和依据生成。
- Agent 解决动态决策和工具调度。
- 单 Agent RAG 是在固定 RAG 上加入有限、可控的决策能力。
- 复杂 Agent Loop、LangGraph 和 Multi-Agent 放到 `04_agent` 深入。

### 最小实现

- 准备 3 段需求文档片段。
- 根据用户问题检索最相关片段。
- 当问题模糊时生成追问，而不是强行回答。

### 主流框架实现

- LangChain Document / Retriever / Runnable。
- Retriever as Tool。
- 简单单 Agent 知识助手。

### 失败分析与能力边界

- RAG 不能保证答案一定正确。
- 单 Agent 不能替代完整工作流和权限审计。
- 动态决策越多，越需要评估和观测。

### 评估观测

- 建立最小 golden set。
- 标记正常问答、无答案、需追问、跨知识源问题。
- 记录是否检索正确、是否拒答正确、是否追问合理。

### 小项目实战

定义需求评审助手的知识范围和单 Agent 能力范围：

- PRD。
- 接口文档。
- 业务规则。
- 历史评审记录。
- 会议纪要。
- 查询改写。
- 知识源选择。
- 缺失信息追问。

### 项目收敛

输出项目知识边界、问题类型和单 Agent 能力边界。

## 01. RAG 架构与边界判断

### 真实问题

不是所有问题都应该用 RAG，也不是所有 RAG 问题都要上 Agent。项目中会遇到 Prompt、长上下文、固定 RAG、单 Agent RAG、Agentic RAG、Workflow、Multi-Agent 和人工处理等方案，必须先会判断。

### 基础原理

- Prompt：适合模型已具备能力、上下文短、无需外部知识。
- Long Context：适合材料少、临时分析、无需长期索引。
- Fixed RAG：适合知识量大、更新频繁、需要来源引用。
- Single Agent RAG：适合需要查询改写、知识源选择、追问补全的知识助手。
- Workflow / Multi-Agent：适合状态流转、审批、多角色协作和复杂任务。

### 最小实现

- 为 8 个需求评审问题选择方案：Prompt、Long Context、Fixed RAG、Single Agent RAG、Workflow 或人工处理。

### 主流框架实现

- 2-step RAG。
- Hybrid RAG。
- Retriever as Tool。
- LangChain RAG chain。
- 完整 LangGraph workflow 放到 `04_agent`。

### 失败分析与能力边界

- 把知识更新问题交给微调。
- 把简单固定任务过度做成 Agent。
- 把需要审批和状态流转的任务交给无约束 Agent。
- 没有评估集时盲目升级架构。

### 评估观测

- 建立方案选择记录。
- 每次从 Fixed RAG 升级到 Single Agent RAG 前说明触发原因。
- 记录升级后是否提升命中率、拒答准确率或用户体验。

### 小项目实战

需求评审助手采用递进架构：

- V0：固定 RAG 问答。
- V1：Sources / Refusal / Structured Output。
- V2：RAG Eval / Bad Case 回流。
- V3：单 Agent 查询改写、知识源选择、追问补全。

### 项目收敛

确定项目 V0-V3 的架构边界。

## 02. LangChain for RAG 基础

### 真实问题

LangChain 在 RAG 和 Agent 项目里非常常见，但如果一开始就学习全家桶，会增加心智负担。更合理的是在 RAG 场景中学习真正需要的组件。

### 基础原理

- LangChain 是 AI 应用组件组合框架。
- RAG 中最常用的是 Document、Loader、TextSplitter、Embeddings、VectorStore、Retriever、PromptTemplate、OutputParser、Runnable / LCEL。
- 学 LangChain 的重点是理解数据流和组合边界，不是背 API。

### 最小实现

- 用原生代码实现最小 RAG。
- 用 LangChain 实现同一条链路。
- 对比输入、输出和中间对象。

### 主流框架实现

- Document。
- Loader。
- TextSplitter。
- VectorStoreRetriever。
- ChatPromptTemplate。
- LCEL Runnable。
- Structured output parser。

### 失败分析与能力边界

- 只会调框架，不知道底层数据流。
- 默认参数不适合项目。
- 抽象太多导致调试困难。
- LangChain 不是替代评估和观测的工具。

### 评估观测

- 保留原生实现和 LangChain 实现的中间结果。
- 确认同一套 golden set 可以跑两种实现。
- 对比 trace 和日志可读性。

### 小项目实战

为需求评审助手确定 LangChain 使用边界：

- 用于 RAG 组件组合。
- 用于 retriever / prompt / output parser。
- 不替代知识库领域模型和评估体系。

### 项目收敛

沉淀 LangChain 最小可用模式。

## 03. Document Loading 与 Cleaning

### 真实问题

需求评审资料来源复杂。PRD、接口文档、业务规则、历史评审、会议纪要、PDF、表格和 Markdown 的结构差异很大，解析质量直接决定检索质量。

### 基础原理

- File 不等于 Document，Document 是进入知识库后的知识资产。
- 文档入库是任务链路，包括上传、解析、清洗、切分、向量化和状态更新。
- 不同文档类型需要不同解析策略和 metadata。

### 最小实现

- 读取 Markdown PRD、接口文档和历史评审记录。
- 清理目录、页眉页脚、空行和无意义标记。
- 生成带 doc_id、doc_type、source 的 Document。

### 主流框架实现

- LangChain loaders。
- Unstructured / PDF parser 认知。
- 文档入库任务队列认知。

### 失败分析与能力边界

- PDF 表格、图片和扫描件解析质量不稳定。
- 文档结构丢失会导致 chunk 和引用不可用。
- 上传成功不代表知识库可检索。

### 评估观测

- 记录文档解析状态。
- 记录文档 token 数、chunk 数、失败原因。
- 抽样检查解析文本和原文是否一致。

### 小项目实战

准备需求评审最小数据集：

- 2 份 PRD。
- 2 份接口文档。
- 1 份业务规则。
- 2 份历史评审。
- 1 份会议纪要。

### 项目收敛

沉淀 `rag_core.ingestion` 和文档状态模型。

## 04. Chunking 与 Metadata

### 真实问题

chunk 切得不好，检索再强也会失败。需求评审场景需要保留章节、模块、接口、业务规则、角色、页码和来源信息。

### 基础原理

- Paragraph、Chunk、Embedding 是不同层级。
- 一个段落可能生成多个向量 chunk。
- metadata 决定过滤、排序、引用和前端展示能力。

### 最小实现

- 对同一份 PRD 分别使用固定长度、标题层级和语义切分。
- 给每个 chunk 添加 doc_type、section、module、page、source_id。

### 主流框架实现

- LangChain TextSplitter。
- Markdown header splitter。
- parent-child chunking。
- metadata filter。

### 失败分析与能力边界

- chunk 过大导致召回不精确。
- chunk 过小导致语义不完整。
- metadata 缺失会导致无法按知识源过滤和正确引用。

### 评估观测

- 对比不同 chunk 策略的 source hit。
- 观察引用片段是否可读。
- 记录 chunk 数量、平均长度和重叠比例。

### 小项目实战

为需求评审助手定义 metadata：

- source。
- doc_type。
- section。
- module。
- api_name。
- owner。
- version。
- page。

### 项目收敛

确定需求评审助手的 chunk 与 metadata 标准。

## 05. Knowledge Governance

### 真实问题

知识库不是上传文件夹，也不是一个 vector collection。它需要业务边界、权限、版本、统计、状态、重建和反馈机制。

### 基础原理

- Knowledgebase 是业务资产，绑定 embedding model、chunk 策略、检索参数和权限。
- 文档有生命周期：待处理、解析中、向量化中、完成、失败、重建中。
- 知识反馈和 bad case 要能回流到知识资产。

### 最小实现

- 设计 Knowledge、Document、Chunk、Embedding、Citation、Feedback 的最小表结构。
- 支持文档状态更新和重新向量化。

### 主流框架实现

- PostgreSQL 保存元数据。
- pgvector 保存向量。
- 后台任务处理解析和向量化。
- 知识库统计和状态面板。

### 失败分析与能力边界

- 没有文档状态就无法定位入库失败。
- 没有权限边界会导致检索越权。
- 知识库配置和文档配置混乱会导致结果不可复现。

### 评估观测

- 文档入库成功率。
- 向量化失败率。
- 知识库文档数、chunk 数、token 数。
- 重建耗时和失败原因。

### 小项目实战

设计需求评审知识库：

- 产品需求库。
- 接口文档库。
- 业务规则库。
- 历史评审库。
- 会议纪要库。

### 项目收敛

输出知识库领域模型和最小管理能力。

## 06. Embedding 与 Vector Store

### 真实问题

Embedding 模型、向量库和索引策略会影响召回质量、成本和工程复杂度。

### 基础原理

- embedding model 应与知识库绑定，避免不同向量空间混用。
- 向量检索适合语义相似，关键词检索适合精确术语。
- PostgreSQL + pgvector 适合当前中小规模学习项目。

### 最小实现

- 对 chunk 生成 embedding。
- 写入 pgvector。
- 根据问题向量检索 top-k。

### 主流框架实现

- LangChain VectorStore。
- pgvector。
- FAISS / Milvus 认知。
- HNSW 索引认知。

### 失败分析与能力边界

- embedding 模型切换后必须重建向量。
- 向量检索对精确接口名和字段名不一定稳定。
- 向量库不是知识治理系统。

### 评估观测

- source hit。
- Recall@k。
- 检索耗时。
- 索引构建耗时。

### 小项目实战

用 pgvector 建立需求评审最小向量库，完成文档入库和检索。

### 项目收敛

沉淀 `rag_core.vector_store`。

## 07. Retrieval Strategies

### 真实问题

需求评审问题可能需要查多个知识库。单一 top-k 向量检索很容易漏掉业务规则、接口约束或历史经验。

### 基础原理

- similarity search。
- keyword search。
- hybrid search。
- rerank。
- metadata filter。
- 多知识库检索与合并。
- 权限过滤。

### 最小实现

- 实现向量检索、关键词检索和 metadata filter。
- 对同一问题比较不同检索结果。

### 主流框架实现

- LangChain Retriever。
- BM25 认知。
- Reranker 认知。
- Hybrid Retriever。

### 失败分析与能力边界

- 只用向量检索容易漏掉精确术语。
- 多知识库结果合并可能引入噪声。
- rerank 不能修复文档解析和 chunk 错误。

### 评估观测

- retrieval recall。
- MRR。
- source hit。
- rerank 前后变化。
- latency / cost。

### 小项目实战

比较以下检索策略：

- 只查 PRD。
- PRD + 接口文档。
- PRD + 业务规则 + 历史评审。
- query rewrite 后检索。
- rerank 后检索。

### 项目收敛

输出需求评审助手检索策略基线。

## 08. Query Rewrite 与 Source Routing

### 真实问题

用户的问题经常模糊，例如“这个需求有什么问题”。系统需要判断要查哪些知识源，并把问题改写成适合检索的查询。

### 基础原理

- 查询改写提升检索命中。
- source routing 决定查哪个知识库。
- 追问判断避免证据不足时强答。

### 最小实现

- 将用户问题改写为 3 个检索查询。
- 根据问题类型选择 PRD、接口文档、业务规则或历史评审。

### 主流框架实现

- Multi-query retriever。
- Self-query retriever。
- Retriever as Tool。
- 简单 router chain。

### 失败分析与能力边界

- 查询改写可能偏离用户意图。
- source routing 错误会导致漏检索。
- 追问过多会损害体验。

### 评估观测

- 改写前后 source hit。
- 知识源选择正确率。
- 追问合理率。

### 小项目实战

为需求评审问题路由到不同知识源：

- 查 PRD。
- 查接口文档。
- 查业务规则。
- 查历史评审。
- 查会议纪要。

### 项目收敛

沉淀单 Agent RAG 的 query planner。

## 09. Context Construction 与 Compression

### 真实问题

检索命中不代表上下文构造正确。上下文太多会污染回答，太少会缺失证据。

### 基础原理

- context packing。
- 去重和排序。
- evidence grouping。
- 引用编号。
- 上下文压缩。
- source id 保留。

### 最小实现

- 将检索结果按知识源和风险类型分组。
- 生成带引用编号的上下文。
- 控制上下文 token 预算。

### 主流框架实现

- LangChain document formatter。
- Contextual compression retriever。
- map-rerank 思路。

### 失败分析与能力边界

- 重复片段会浪费上下文。
- 压缩可能丢失关键证据。
- 引用 id 丢失会导致前端无法追溯。

### 评估观测

- 上下文 token 数。
- expected source 是否进入上下文。
- 回答 groundedness。

### 小项目实战

为评审报告构造上下文：

- 按风险类型分组证据。
- 保留引用来源。
- 去除重复片段。
- 对长片段做压缩。

### 项目收敛

沉淀 `rag_core.context_builder`。

## 10. Generation、Sources 与 Refusal

### 真实问题

RAG 应用最重要的不是“说得像”，而是是否有依据、引用是否正确、无依据时是否拒答或追问。

### 基础原理

- Grounded generation。
- Citation。
- Source mapping。
- Refusal。
- Evidence insufficient。
- Structured review output。

### 最小实现

- 基于检索上下文生成回答。
- 每条结论绑定 source id。
- 无引用时返回拒答或追问。

### 主流框架实现

- RetrievalQA / LCEL chain。
- structured output parser。
- citation checker。

### 失败分析与能力边界

- 引用不存在的 source。
- 有依据却拒答。
- 无依据却强答。
- 引用正确但解释错误。

### 评估观测

- citation correctness。
- citation coverage。
- refusal accuracy。
- over-refusal / under-refusal。

### 小项目实战

生成需求评审回答：

- 每条风险带引用。
- 无依据时明确拒答。
- 证据不足时提出追问。
- 输出结构化评审项。

### 项目收敛

沉淀 sources / refusal / structured answer 标准。

## 11. RAG Evaluation

### 真实问题

RAG 失败时，需要知道是检索错了、上下文错了、生成错了，还是引用错了。

### 基础原理

- Retrieval eval。
- Generation eval。
- Citation eval。
- Refusal eval。
- Golden set。
- Bad case。

### 最小实现

- 建立 30 条需求评审 RAG 样本。
- 标注 expected sources。
- 跑检索和生成评估。

### 主流框架实现

- pytest 参数化。
- 自定义 metrics。
- RAGAS / LangSmith 认知。

### 失败分析与能力边界

- 只评答案不评 source。
- LLM judge 不稳定。
- 样本只覆盖简单问题。

### 评估观测

- Recall@k。
- MRR。
- source hit。
- groundedness。
- citation correctness。
- refusal accuracy。

### 小项目实战

建立需求评审 RAG 样本：

- 有明确答案。
- 无答案。
- 证据不足。
- 需追问。
- 跨知识源。
- 历史经验类。

### 项目收敛

沉淀 `rag_eval`，进入 `05_eval_observability` 系统化。

## 12. RAG Memory

### 真实问题

聊天历史、任务状态、用户偏好和长期记忆不是一回事。需求评审助手当前阶段不应该过早做复杂长期记忆。

### 基础原理

- Conversation history 是对话上下文。
- Task state 是当前评审任务状态。
- Knowledge base 是企业知识资产。
- Long-term memory 是可检索、可治理的长期信息。

### 最小实现

- 保存当前评审任务状态。
- 记录用户已确认的问题。
- 不把所有历史对话塞进上下文。

### 主流框架实现

- LangChain memory 认知。
- LangGraph state。
- 向量记忆认知。

### 失败分析与能力边界

- 长期记忆可能污染项目事实。
- 未治理的记忆会带来隐私和权限问题。
- 当前项目优先使用任务状态而不是个性化记忆。

### 评估观测

- 任务状态是否完整。
- 记忆是否被错误引用。
- 上下文是否包含过期信息。

### 小项目实战

只保留当前评审任务所需状态：

- 当前需求材料。
- 已检索证据。
- 已生成风险。
- 待确认问题。
- 用户反馈。

### 项目收敛

`rag_memory` 先保持轻量，复杂长期记忆放到未来方向。

## 13. Single Agent RAG Assistant

### 真实问题

固定 RAG 无法处理所有模糊问题。系统需要有限度地判断是否改写、查哪个库、是否补检索、是否追问。

### 基础原理

- 单 Agent RAG 是受控决策层。
- Retriever 可以作为工具。
- Agent 的动作空间必须有限。
- 证据不足时应追问或拒答。

### 最小实现

- 让 Agent 在查询、检索、追问、回答之间选择下一步。
- 限制最大步骤数。
- 输出每一步动作记录。

### 主流框架实现

- LangChain agent。
- Retriever as Tool。
- LangGraph 简单状态机。

### 失败分析与能力边界

- Agent 可能过度检索。
- Agent 可能在证据不足时强答。
- 自由 Agent 不适合直接进入生产。

### 评估观测

- 工具选择正确率。
- 追问合理率。
- 检索次数。
- 最终回答 groundedness。

### 小项目实战

实现单 Agent RAG 助手：

- 识别问题类型。
- 选择知识库。
- 改写查询。
- 检索并判断证据是否足够。
- 必要时追问。

### 项目收敛

完成需求评审助手 V3，为 `04_agent` 多 Agent 升级做准备。

## 14. RAG Failure Analysis

### 真实问题

RAG 质量优化的难点不是发现“答错了”，而是定位错在哪里。

### 基础原理

- 文档解析、chunk、metadata、embedding、retriever、context、generation、citation 都可能失败。
- bad case 需要归因，而不是只保存截图。
- 修复动作必须能回归验证。

### 最小实现

- 为 10 个错误样本标注失败原因。
- 将失败原因映射到修复动作。

### 主流框架实现

- bad case table。
- trace viewer。
- eval run diff。

### 失败分析与能力边界

- 多个原因可能叠加。
- LLM judge 不能完全替代人工诊断。
- 没有 trace 很难定位中间步骤。

### 评估观测

- bad case 数量。
- 失败类型分布。
- 修复后回归通过率。

### 小项目实战

建立 bad case 分类表，并把每个问题归因到：

- 知识库。
- 文档解析。
- chunk。
- metadata。
- retriever。
- prompt。
- model。
- workflow。
- 人工流程。

### 项目收敛

输出 RAG 失败分析手册。

## 15. 需求评审助手项目

### 真实问题

课程最终必须落到项目，而不是停在组件学习。需求评审助手需要从固定 RAG 逐步升级为可评估、可追问、可被多 Agent 调用的知识服务。

### 基础原理

- 项目版本应该围绕能力递进。
- 每一版都要有可运行产物和完成标准。
- RAG 先可靠，再引入更复杂的 Agent 和 Workflow。

### 最小实现

- V0 固定 RAG 问答。
- V1 Sources / Refusal / Structured Output。
- V2 RAG Eval / Bad Case 回流。
- V3 单 Agent RAG。

### 主流框架实现

- FastAPI + LangChain。
- PostgreSQL / pgvector。
- 简单前端工作台。
- 自定义 eval runner。

### 失败分析与能力边界

- 过早做多 Agent 会掩盖 RAG 基础问题。
- 没有引用和拒答的 RAG 不可信。
- 没有评估的 RAG 难以持续优化。

### 评估观测

- 检索命中率。
- 引用正确率。
- 拒答准确率。
- bad case 修复率。

### 小项目实战

完成需求评审助手 RAG 能力：

- 文档入库。
- 知识库管理。
- 多知识源检索。
- 引用来源。
- 拒答和追问。
- 结构化评审输出。
- RAG 评估。

### 项目收敛

完成后进入 `04_agent`，把需求评审助手升级为多 Agent 与 Workflow 系统。

## 参考设计映射

- 参考 RAGFlow 的 Knowledgebase、Document、chunk、citation、evaluation 和复杂文档处理思路。
- 参考 MaxKB 的 Document / Paragraph / Embedding 状态、PostgreSQL + pgvector、ChatRecord、反馈和简单 pipeline 到 Workflow 的递进方式。
