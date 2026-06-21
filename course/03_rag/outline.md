# 03 RAG、LangChain 与单 Agent 知识助手大纲

## 课程定位

`03_rag` 是 AI 应用的知识系统与单 Agent 知识助手主线。

这门课不是只学习“文档切分、向量化、检索、生成”这条固定流程，而是系统理解外部知识如何进入模型上下文，并进一步把固定 RAG 做成可引用、可拒答、可评估、可治理、可迭代、可追问的知识助手。

RAG 和 Agent 不应该被理解成完全割裂的两门课。固定 RAG 是知识注入和证据生成的基础能力；单 Agent 知识助手是在固定 RAG 基础上，加入查询改写、知识源选择、检索质量判断、补检索和追问补全等能力。

本课程直接服务第一个长期项目：

- 需求评审 RAG 助手 / 智能客服。

并为第二个长期项目提供知识底座：

- 金融 Copilot。

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

`04_agent` 继续深入 Tool Runtime、Agent Loop、LangGraph、Workflow、Human-in-the-loop、Deep Research、Multi-Agent、MCP / A2A 和 Agent Skills。

`05_eval_observability` 系统学习 RAG、Agent、Workflow 和项目的评估、观测、trace、回归和质量工程。

## 完成标准

完成本课程后，应能做到：

- 判断什么时候用 Prompt、长上下文、固定 RAG、单 Agent RAG、Agentic RAG 或微调。
- 构建文档处理、chunk、metadata、embedding、vector store、retrieval、context construction、generation 的主链路。
- 使用 LangChain 理解并实现主流 RAG 组件，而不是只会调框架 API。
- 生成带来源、可拒答、可追溯的结构化回答。
- 建立 RAG golden set、检索评估、生成评估和失败案例回流。
- 区分短期记忆、长期记忆、任务状态、用户记忆和知识库。
- 用单 Agent 做查询改写、知识源选择、检索质量判断、追问补全和 retriever 工具调用。
- 收敛出需求评审 RAG 助手 / 智能客服 V0-V3。

## 代码组织建议

```text
source/03_rag/
├── packages/
│   ├── rag_core/
│   ├── rag_eval/
│   └── rag_memory/
├── demos/
│   ├── minimal_rag/
│   ├── chunking_comparison/
│   ├── retrieval_comparison/
│   ├── sources_refusal_demo/
│   ├── rag_eval_demo/
│   └── single_agent_rag_demo/
├── apps/
│   └── review_assistant_v0/
└── README.md
```

`rag_core` 是主链路底座，`rag_eval` 是评估与回归底座，`rag_memory` 先保持轻量，`single_agent_rag_demo` 验证单 Agent 知识助手，`review_assistant_v0` 收敛项目一的最小闭环。

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

但只做固定 RAG 也不够。真实用户的问题经常模糊、跨知识源、缺少上下文，系统需要判断是否要改写问题、选择知识源、补充检索或追问用户。

### 基础原理

- RAG 解决知识注入和依据生成。
- Agent 解决动态决策和工具调度。
- 单 Agent RAG 助手是在固定 RAG 上加入有限、可控的决策能力。
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

本章输出项目知识边界、问题类型和单 Agent 能力边界。

## 01. RAG 架构与边界判断

### 真实问题

不是所有问题都应该用 RAG，也不是所有 RAG 问题都要上 Agent。项目中会遇到 Prompt、长上下文、固定 RAG、单 Agent RAG、Agentic RAG、Workflow、Multi-Agent 和微调等方案，必须先会判断。

### 基础原理

- Prompt：适合模型已具备能力、上下文短、无需外部知识。
- Long Context：适合材料少、临时分析、无需长期索引。
- Fixed RAG：适合知识量大、更新频繁、需要来源引用。
- Single Agent RAG：适合需要查询改写、知识源选择、追问补全的知识助手。
- Agentic RAG：适合多步骤检索、补检索、反思生成和动态质量判断。
- Workflow / Multi-Agent：适合状态流转、审批、多角色协作和复杂任务。
- Fine-tuning：更适合行为、格式、风格强化，不优先解决知识更新。

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
- 记录升级后是否真的提升命中率、拒答准确率或用户体验。

### 小项目实战

需求评审助手采用递进架构：

- V0：固定 RAG 问答。
- V1：Sources / Refusal / Structured Output。
- V2：RAG Eval / Bad Case 回流。
- V3：单 Agent 查询改写、知识源选择、追问补全。

### 项目收敛

本章确定项目 V0-V3 的架构边界。

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
- 用于简单 single agent。
- 不在本阶段引入复杂 LangGraph 工作流。

### 项目收敛

沉淀 `rag_core.langchain_adapter`。

## 03. 文档加载与清洗

### 真实问题

RAG 的效果首先取决于文档质量。PRD、接口文档、Markdown、PDF、会议纪要、表格和历史记录格式不统一，直接切分会把噪声带入索引。

### 基础原理

- Loader。
- Parser。
- 清洗。
- 结构保留。
- 文档版本和来源。

### 最小实现

- 加载 Markdown / text / mock PDF 文档。
- 清理空行、页眉页脚、重复内容。
- 保留标题层级和来源路径。

### 主流框架实现

- LangChain document loaders。
- Unstructured / pymupdf 等文档解析工具认知。
- 后续可扩展到 OCR 和表格解析。

### 失败分析与能力边界

- PDF 解析顺序错乱。
- 表格结构丢失。
- 会议纪要噪声多。
- 文档版本混乱导致旧知识污染。

### 评估观测

- 抽样检查解析结果。
- 记录文档数量、字符数、清洗前后差异。
- 保存不可解析文档和异常原因。

### 小项目实战

建立需求评审助手的文档输入规范：

- PRD。
- API 文档。
- 业务规则。
- 评审记录。

### 项目收敛

沉淀 `rag_core.document_loader` 和文档清洗约定。

## 04. Chunking 与 Metadata

### 真实问题

切分太大，召回不精准；切分太小，语义不完整。没有 metadata，答案无法追溯、过滤、权限控制和版本治理。

### 基础原理

- chunk size。
- overlap。
- 结构化切分。
- metadata 作为检索、过滤、引用和治理的基础。

### 最小实现

- 对同一份 PRD 使用不同 chunk 策略。
- 对比 chunk 数量、语义完整性和召回结果。

### 主流框架实现

- RecursiveCharacterTextSplitter。
- Markdown header splitter。
- 自定义结构化 splitter。

### 失败分析与能力边界

- chunk 丢失标题上下文。
- overlap 过大增加噪声和成本。
- metadata 缺失导致无法引用。
- 权限信息不能只靠 prompt 控制。

### 评估观测

- 统计 chunk 长度分布。
- 抽查 chunk 是否保留完整语义。
- 检查 metadata 是否包含 source、section、doc_type、version。

### 小项目实战

为需求评审助手设计 metadata：

- `source`
- `doc_id`
- `doc_type`
- `section`
- `version`
- `created_at`
- `owner`
- `permission`

### 项目收敛

沉淀 `rag_core.chunker` 和 `rag_core.metadata`。

## 05. Knowledge Governance

### 真实问题

只会把文档放进向量库还不够。真实知识库需要处理版本、增量更新、删除一致性、权限过滤、知识过期和反馈回流，否则系统会引用旧知识或越权知识。

### 基础原理

- 知识源管理。
- 文档版本。
- 增量更新。
- 删除一致性。
- ACL / permission filter。
- 知识生命周期。

### 最小实现

- 为文档建立 `doc_id / version / status`。
- 模拟更新和删除文档。
- 检索时过滤已删除或无权限文档。

### 主流框架实现

- VectorStore metadata filter。
- pgvector / Chroma 过滤能力。
- LangChain retriever filter。

### 失败分析与能力边界

- 旧版本知识污染答案。
- 删除文档后向量仍可被召回。
- 权限过滤只靠 prompt，实际仍然泄露。
- 知识运营流程缺失导致坏案例无法回流。

### 评估观测

- 记录索引版本。
- 记录文档更新和删除操作。
- 检查检索结果是否符合版本和权限约束。

### 小项目实战

需求评审助手支持：

- 规则文档版本。
- 历史评审记录保留。
- 废弃文档不再召回。
- 按文档类型过滤检索。

### 项目收敛

沉淀 `rag_core.knowledge_store` 和知识治理约定。

## 06. Embedding 与 Vector Store

### 真实问题

文档进入向量库后才能做语义检索。Embedding 模型、向量库和索引策略会影响召回质量、成本、更新和部署方式。

### 基础原理

- Embedding 把文本映射成向量。
- 相似度检索。
- 向量库负责存储、索引、过滤和删除。

### 最小实现

- 对 chunks 生成 mock embedding 或真实 embedding。
- 存入本地向量库。
- 对用户问题做 top-k 检索。

### 主流框架实现

- Chroma。
- FAISS。
- pgvector。
- LangChain VectorStore。

### 失败分析与能力边界

- Embedding 模型语言能力不匹配。
- 向量库删除和更新不一致。
- 只用向量检索可能漏掉编号、术语、接口名。
- 本地向量库和生产方案的边界不同。

### 评估观测

- 记录 embedding 模型和维度。
- 记录 top-k 召回来源。
- 对比不同向量库或 embedding 的召回差异。

### 小项目实战

需求评审助手 V0 使用轻量向量库跑通：

- 本地开发优先 Chroma / FAISS。
- 未来项目化可评估 pgvector。

### 项目收敛

沉淀 `rag_core.vector_store`。

## 07. Retrieval Strategies

### 真实问题

检索失败是 RAG 最常见失败源。只做 similarity search 往往不够，真实项目需要根据问题类型选择检索策略。

### 基础原理

- Similarity search。
- MMR。
- Metadata filter。
- Hybrid search。
- Rerank。
- 多查询检索。

### 最小实现

- 对同一批问题比较 similarity、MMR、metadata filter 的结果。
- 记录命中来源和排名。

### 主流框架实现

- LangChain retriever。
- BM25 / keyword search。
- Reranker。
- MultiQueryRetriever。

### 失败分析与能力边界

- 用户问题太短或太模糊。
- 关键词、接口名、编号不适合纯向量检索。
- top-k 太小漏召回，太大污染上下文。
- rerank 增加成本和延迟。

### 评估观测

- Recall@k。
- MRR。
- expected source hit。
- bad case 分类。

### 小项目实战

需求评审助手支持：

- 普通语义问题。
- 规则类问题。
- 接口字段类问题。
- 模糊追问。

### 项目收敛

沉淀 `rag_core.retriever` 和 `rag_eval.retrieval_metrics`。

## 08. Query Rewrite 与 Knowledge Source Routing

### 真实问题

用户问题经常模糊、口语化、缺少上下文，或者需要从 PRD、接口文档、业务规则、历史评审记录中选择合适知识源。固定 RAG 如果只做一次检索，容易召回错误材料。

### 基础原理

- Query rewrite。
- Query decomposition。
- Knowledge source routing。
- Retriever selection。
- 检索质量判断。

### 最小实现

- 将用户模糊问题改写成更适合检索的问题。
- 根据问题类型选择 PRD / API / Rule / History 知识源。
- 检索后判断结果是否足够回答。

### 主流框架实现

- LangChain query transform。
- MultiQueryRetriever。
- Router chain。
- Retriever as Tool。
- 单 Agent 选择 retriever。

### 失败分析与能力边界

- 改写偏离原意。
- 路由到错误知识源。
- 多次检索增加成本和延迟。
- 检索质量判断本身也可能出错。

### 评估观测

- 记录原始问题、改写问题、路由知识源和召回结果。
- 评估改写是否提高 expected source hit。
- 记录路由错误案例。

### 小项目实战

需求评审助手支持：

- “这个字段合理吗？”改写为包含上下文的接口字段问题。
- “之前怎么评的？”路由到历史评审记录。
- “这个规则有没有风险？”路由到业务规则。

### 项目收敛

沉淀 `rag_core.query_planner` 和单 Agent 的 retriever 选择能力。

## 09. Context Construction 与 Compression

### 真实问题

检索到片段不等于可以直接塞给模型。上下文需要排序、去重、压缩、格式化，并且要明确告诉模型如何使用这些材料。

### 基础原理

- Context budget。
- 文档片段排序。
- 去重。
- 压缩。
- 引用编号。
- prompt 中的知识边界。

### 最小实现

- 将 top-k chunks 格式化为 numbered context。
- 超出 token budget 时按 score、doc_type、section 优先级裁剪。
- 对长片段进行摘要压缩。

### 主流框架实现

- LangChain document combine。
- Contextual compression retriever。
- 自定义 context builder。

### 失败分析与能力边界

- 无关片段污染回答。
- 片段顺序改变导致结论不同。
- 引用编号和实际来源错位。
- 压缩丢失关键条件。

### 评估观测

- 记录进入 prompt 的最终 context。
- 检查答案引用是否来自 context。
- 对比不同 context builder 的生成效果。

### 小项目实战

需求评审助手构造上下文：

- 当前问题。
- 相关需求片段。
- 业务规则。
- 历史评审记录。
- 引用编号。

### 项目收敛

沉淀 `rag_core.context_builder`。

## 10. Generation、Sources 与 Refusal

### 真实问题

RAG 项目不能只回答“看起来合理”的自然语言。它必须展示来源，在依据不足时拒答，并把风险提示交给用户或人工确认。

### 基础原理

- Grounded generation。
- Citation。
- Refusal。
- Risk note。
- Structured answer。

### 最小实现

- 基于 context 生成回答。
- 输出引用来源。
- 当 context 不包含答案时拒答。

### 主流框架实现

- Prompt + structured output。
- LangChain RAG chain。
- 自定义 answer schema。

### 失败分析与能力边界

- 引用不存在的来源。
- 明明无依据却强答。
- 过度拒答。
- 答案遗漏条件和风险。

### 评估观测

- citation correctness。
- refusal correctness。
- groundedness。
- answer completeness。

### 小项目实战

需求评审助手输出：

- answer。
- sources。
- risks。
- missing_info。
- need_human_review。

### 项目收敛

沉淀 `rag_core.generator` 和 answer schema。

## 11. RAG Evaluation

### 真实问题

没有评估集，RAG 优化就是凭感觉。每次改 chunk、embedding、retriever、prompt、rerank、query rewrite，都需要知道是否真的变好。

### 基础原理

- Golden set。
- Retrieval eval。
- Generation eval。
- Citation eval。
- Refusal eval。
- Bad case 回流。

### 最小实现

- 建立 20 条需求评审问题。
- 每条包含 expected answer、expected sources、是否应拒答、是否需追问。
- 跑一次固定链路并记录结果。

### 主流框架实现

- 自定义 eval 脚本。
- RAGAS / LangSmith 等工具认知。
- 后续 `05_eval_observability` 系统展开。

### 失败分析与能力边界

- 评估样本太少。
- expected answer 写得过死。
- 只评最终答案，不评检索和引用。
- LLM-as-judge 不稳定。

### 评估观测

- source hit rate。
- retrieval recall。
- answer correctness。
- citation correctness。
- refusal accuracy。
- rewrite success rate。
- latency / cost。

### 小项目实战

需求评审助手建立 V0-V3 golden set：

- 正常问答。
- 多文档问题。
- 无答案问题。
- 高风险问题。
- 信息缺失问题。
- 需要查询改写的问题。
- 需要知识源选择的问题。

### 项目收敛

沉淀 `rag_eval` package。

## 12. RAG Memory

### 真实问题

需求评审和客服都不是单轮问答。系统需要处理当前会话状态、用户补充信息、历史偏好和长期知识，但 memory、agent state 和 knowledge base 不能混为一谈。

### 基础原理

- 短期记忆。
- 长期记忆。
- 任务状态。
- 用户记忆。
- 记忆写入。
- 记忆检索。
- 遗忘机制。
- Memory vs Knowledge Base。

### 最小实现

- 保存当前评审会话摘要。
- 根据新问题检索相关会话记忆。
- 超过预算时压缩或遗忘低价值信息。

### 主流框架实现

- Conversation summary memory。
- Vector memory。
- LangGraph checkpoint / state 的边界认知。
- 复杂 Agent memory 放到 `04_agent` 继续深入。

### 失败分析与能力边界

- 把临时会话写入长期知识库。
- 旧记忆污染新任务。
- 隐私和权限问题。
- 记忆越多不代表效果越好。

### 评估观测

- 记录 memory write 触发条件。
- 检查 memory retrieval 是否相关。
- 检查遗忘后是否影响任务完成。

### 小项目实战

需求评审助手支持：

- 当前需求评审会话状态。
- 用户补充信息。
- 已确认问题。
- 已拒答问题。

### 项目收敛

沉淀轻量 `rag_memory`，不提前做复杂长期记忆平台。

## 13. Single Agent RAG Assistant

### 真实问题

一个可用的需求评审助手 / 智能客服不能只做一次固定检索。它需要判断用户是否问得清楚，应该查哪个知识源，检索结果是否足够，是否需要补检索，是否应该追问。

### 基础原理

- 单 Agent 知识助手。
- Retriever as Tool。
- Query rewrite as Tool / Step。
- Source routing。
- Retrieval quality check。
- Clarifying question。

### 最小实现

- 定义 PRD retriever、API retriever、Rule retriever、History retriever。
- 让单 Agent 根据问题选择一个或多个 retriever。
- 检索不足时生成追问或补检索。

### 主流框架实现

- LangChain Tool。
- Tool binding。
- 简单 Agent executor / runnable loop。
- 更复杂 LangGraph loop 放到 `04_agent`。

### 失败分析与能力边界

- 单 Agent 可能误选工具。
- 多次检索可能失控。
- 工具调用需要次数限制、日志和评估。
- 涉及审批、权限、复杂状态时进入 `04_agent`。

### 评估观测

- 工具选择正确率。
- 查询改写成功率。
- 检索质量提升。
- 追问是否必要。
- 最大工具调用次数。

### 小项目实战

需求评审助手 V3：

- 单 Agent 判断问题类型。
- 单 Agent 选择知识源。
- 单 Agent 改写问题。
- 单 Agent 判断是否追问。
- 最终仍输出带 sources / refusal / risks 的结构化答案。

### 项目收敛

沉淀 `single_agent_rag_demo` 和 `review_assistant_v0` 的 V3 版本。

## 14. RAG 失败分析

### 真实问题

RAG 的困难不在于跑通 demo，而在于系统性定位失败原因。一个坏答案可能来自文档、切分、embedding、检索、query rewrite、source routing、上下文、prompt、模型、Agent 决策或评估任一环节。

### 基础原理

- RAG failure taxonomy。
- Agent decision failure。
- 从输入到输出逐层定位。
- Bad case 回流。

### 最小实现

- 对 10 个失败样本分类。
- 标记失败来源和修复策略。

### 主流框架实现

- Trace。
- Eval dashboard。
- 后续 `05_eval_observability` 深入。

### 失败分析与能力边界

- 文档解析失败。
- 切分失败。
- 召回失败。
- query rewrite 失败。
- source routing 失败。
- rerank 失败。
- 上下文污染。
- 引用错误。
- 幻觉。
- 过度拒答。
- 单 Agent 误判工具。
- 评估不稳定。

### 评估观测

- 失败类型统计。
- 修复前后对比。
- 记录实验配置。
- 记录 Agent 工具轨迹。

### 小项目实战

需求评审助手建立 bad case review 流程：

- 收集失败问题。
- 定位失败环节。
- 制定修复策略。
- 回归验证。

### 项目收敛

沉淀 `rag_eval.bad_cases`。

## 15. 需求评审 RAG 助手 / 智能客服项目

### 真实问题

需求评审需要理解 PRD、业务规则、接口文档、历史记录和会议纪要。人工评审容易遗漏上下文和历史经验，AI 可以辅助总结、问答、风险识别、追问和依据展示。

### 基础原理

项目不是单个 RAG demo，而是由文档接入、知识治理、索引构建、检索、查询改写、知识源选择、上下文构造、带依据生成、拒答、评估、单 Agent 决策和前端展示组成的闭环。

### 最小实现

V0：固定 RAG 问答。

- 上传或读取固定文档。
- 构建索引。
- 用户提问。
- 返回带来源回答。

### 主流框架实现

V1：Sources / Refusal / Structured Output。

- 使用 `rag_core`。
- 可选 LangChain adapter。
- 结构化输出 sources / risks / missing_info。

### 失败分析与能力边界

- 不替代最终评审责任。
- 无依据时拒答。
- 高风险结论需要人工确认。
- 文档缺失时提示补充资料。
- 复杂审批、权限审计和多 Agent 协作进入 `04_agent`。

### 评估观测

V2：RAG Eval / Bad Case 回流。

- 建立 golden set。
- 记录检索命中率、引用正确率、拒答正确率、query rewrite 成功率。
- 建立 bad case 回流。

### 小项目实战

V3：单 Agent 知识助手。

- 查询改写。
- 知识源选择。
- 检索质量判断。
- 追问补全。
- Retriever as Tool。

### 项目收敛

本课程最终收敛为：

- `rag_core`
- `rag_eval`
- `rag_memory`
- `single_agent_rag_demo`
- `review_assistant_v0`

这些产物进入 `07_projects`，继续扩展为完整项目。
