# 03 RAG 与知识系统大纲

## 课程定位

`03_rag` 是 AI 应用的知识系统主线。

这门课不是只学习“文档切分、向量化、检索、生成”这条固定流程，而是系统理解外部知识如何进入模型上下文，并形成可引用、可拒答、可评估、可治理、可迭代的知识系统。

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

代码不按章节机械堆脚本，而是围绕 `rag_core`、`rag_eval`、`rag_memory`、关键 demo 和项目 app 组织。

## 完成标准

完成本课程后，应能做到：

- 判断什么时候用 Prompt、长上下文、RAG、Agentic RAG 或微调。
- 构建文档处理、chunk、metadata、embedding、vector store、retrieval、context construction、generation 的主链路。
- 生成带来源、可拒答、可追溯的回答。
- 建立 RAG golden set、检索评估、生成评估和失败案例回流。
- 理解短期记忆、长期记忆、记忆检索和遗忘机制与知识库的区别。
- 使用 LangChain 理解主流 RAG 封装，但不被框架牵着走。
- 收敛出需求评审 RAG 助手 V0-V2。

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
│   └── rag_eval_demo/
├── apps/
│   └── review_assistant_v0/
└── README.md
```

`rag_core` 是主链路底座，`rag_eval` 是评估与回归底座，`rag_memory` 先保持轻量，不提前做复杂长期记忆系统。

## 专题目录

```text
course/03_rag/
├── 00_rag_problem_space.md
├── 01_rag_architecture_and_boundary.md
├── 02_document_loading_and_cleaning.md
├── 03_chunking_and_metadata.md
├── 04_embedding_and_vector_store.md
├── 05_retrieval_strategies.md
├── 06_context_construction.md
├── 07_generation_sources_refusal.md
├── 08_rag_evaluation.md
├── 09_rag_memory.md
├── 10_langchain_rag.md
├── 11_rag_failure_analysis.md
├── 12_review_assistant_project.md
└── outline.md
```

## 00. RAG 问题空间

### 真实问题

LLM 自身不了解企业内部需求、接口文档、历史评审记录、业务规则和会议纪要。需求评审助手如果只靠 Prompt，很容易编造、遗漏依据或给出无法追溯的建议。

### 基础原理

- RAG = Retrieval-Augmented Generation。
- 检索解决知识接入，生成解决表达与综合。
- RAG 的核心价值是知识可更新、答案可追溯、失败可评估。

### 最小实现

- 准备 3 段需求文档片段。
- 根据用户问题检索最相关片段。
- 把片段和问题一起传给模型生成回答。

### 主流框架实现

- LangChain Document / Retriever / Chain。
- Chroma / FAISS / pgvector。
- Hosted file search 的定位认知。

### 失败分析与能力边界

- RAG 不能保证一定正确。
- 检索不到时应该拒答或提示补充材料。
- 文档质量差会直接影响生成质量。
- RAG 不等于 Agent，不负责复杂动态决策。

### 评估观测

- 从第一天建立最小 golden set。
- 每个问题记录期望答案和期望来源。
- 观察答案是否来自检索上下文。

### 小项目实战

定义需求评审 RAG 助手的知识范围：

- PRD。
- 接口文档。
- 业务规则。
- 历史评审记录。
- 会议纪要。

### 项目收敛

本章输出项目知识边界和最小问题集。

## 01. RAG 架构与边界判断

### 真实问题

不是所有问题都应该用 RAG。项目中可能遇到直接 Prompt、长上下文、已有搜索系统、RAG、Agentic RAG 和微调等方案，必须先会判断。

### 基础原理

- Prompt：适合模型已具备能力、上下文短、无需外部知识。
- 长上下文：适合材料少、临时分析、无需索引。
- RAG：适合知识量大、更新频繁、需要引用来源。
- Agentic RAG：适合多知识源路由、查询改写、动态检索。
- 微调：更适合行为、格式、风格强化，不优先解决知识更新。

### 最小实现

- 为 5 个需求评审问题选择方案：Prompt、长上下文、RAG、Agentic RAG 或人工处理。

### 主流框架实现

- 2-step RAG。
- Hybrid RAG。
- Hosted file search。
- Agentic RAG 在 `04_agent` 深入。

### 失败分析与能力边界

- 把知识更新问题交给微调。
- 把简单固定任务过度做成 Agent。
- 在没有评估集时盲目优化检索策略。

### 评估观测

- 建立方案选择记录。
- 每次升级架构前说明触发原因。

### 小项目实战

需求评审助手先采用固定 RAG：

- 先召回。
- 再构造上下文。
- 再生成带依据回答。
- 暂不引入多 Agent。

### 项目收敛

本章确定项目 V0-V2 的架构边界。

## 02. 文档加载与清洗

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

## 03. Chunking 与 Metadata

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

## 04. Embedding 与 Vector Store

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

## 05. Retrieval Strategies

### 真实问题

检索失败是 RAG 最常见失败源。只做 similarity search 往往不够，真实项目需要根据问题类型选择检索策略。

### 基础原理

- Similarity search。
- MMR。
- Metadata filter。
- Hybrid search。
- Query rewrite。
- Rerank。

### 最小实现

- 对同一批问题比较 similarity、MMR、metadata filter 的结果。
- 记录命中来源和排名。

### 主流框架实现

- LangChain retriever。
- BM25 / keyword search。
- Reranker。
- 多查询检索。

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

## 06. Context Construction

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

## 07. Generation、Sources 与 Refusal

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

## 08. RAG Evaluation

### 真实问题

没有评估集，RAG 优化就是凭感觉。每次改 chunk、embedding、retriever、prompt、rerank，都需要知道是否真的变好。

### 基础原理

- Golden set。
- Retrieval eval。
- Generation eval。
- Refusal eval。
- Bad case 回流。

### 最小实现

- 建立 20 条需求评审问题。
- 每条包含 expected answer、expected sources、是否应拒答。
- 跑一次固定链路并记录结果。

### 主流框架实现

- 自定义 eval 脚本。
- RAGAS / LangSmith 等工具认知。
- 后续 `05_eval_observability` 系统展开。

### 失败分析与能力边界

- 评估样本太少。
- expected answer 写得过死。
- 只评最终答案，不评检索。
- LLM-as-judge 不稳定。

### 评估观测

- source hit rate。
- retrieval recall。
- answer correctness。
- citation correctness。
- refusal accuracy。
- latency / cost。

### 小项目实战

需求评审助手建立 V0 golden set：

- 正常问答。
- 多文档问题。
- 无答案问题。
- 高风险问题。
- 信息缺失问题。

### 项目收敛

沉淀 `rag_eval` package。

## 09. RAG Memory

### 真实问题

需求评审和客服都不是单轮问答。系统需要处理当前会话状态、用户补充信息、历史偏好和长期知识，但 memory 和 knowledge base 不能混为一谈。

### 基础原理

- 短期记忆。
- 长期记忆。
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
- LangGraph checkpoint / state。
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

## 10. LangChain RAG

### 真实问题

主流项目经常使用 LangChain 构建 RAG，但学习重点不是背 API，而是理解它如何封装 Document、Retriever、Runnable 和 Chain。

### 基础原理

- Document。
- Retriever。
- Runnable。
- LCEL。
- Chain composition。

### 最小实现

- 用原生代码实现一次最小 RAG。
- 再用 LangChain 实现同一条链路。
- 对比抽象边界。

### 主流框架实现

- LangChain document loader。
- VectorStoreRetriever。
- LCEL RAG chain。
- Structured output integration。

### 失败分析与能力边界

- 只会调框架，不知道底层数据流。
- 框架默认参数不适合项目。
- 抽象太多导致调试困难。

### 评估观测

- 对比原生实现和 LangChain 实现的输入输出。
- 保留 trace 和中间结果。
- 确认评估集可复用。

### 小项目实战

需求评审助手提供两种实现路径：

- 原生最小链路。
- LangChain 版本。

### 项目收敛

沉淀 `rag_core.langchain_adapter`。

## 11. RAG 失败分析

### 真实问题

RAG 的困难不在于跑通 demo，而在于系统性定位失败原因。一个坏答案可能来自文档、切分、embedding、检索、上下文、prompt、模型或评估任一环节。

### 基础原理

- RAG failure taxonomy。
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
- rerank 失败。
- 上下文污染。
- 引用错误。
- 幻觉。
- 过度拒答。
- 评估不稳定。

### 评估观测

- 失败类型统计。
- 修复前后对比。
- 记录实验配置。

### 小项目实战

需求评审助手建立 bad case review 流程：

- 收集失败问题。
- 定位失败环节。
- 制定修复策略。
- 回归验证。

### 项目收敛

沉淀 `rag_eval.bad_cases`。

## 12. 需求评审 RAG 助手项目

### 真实问题

需求评审需要理解 PRD、业务规则、接口文档、历史记录和会议纪要。人工评审容易遗漏上下文和历史经验，AI 可以辅助总结、问答、风险识别和追问。

### 基础原理

项目不是单个 RAG demo，而是由文档接入、知识索引、检索、上下文构造、带依据生成、拒答、评估和前端展示组成的闭环。

### 最小实现

V0：

- 上传或读取固定文档。
- 构建索引。
- 用户提问。
- 返回带来源回答。

### 主流框架实现

V1：

- 使用 `rag_core`。
- 可选 LangChain adapter。
- 结构化输出 sources / risks / missing_info。

### 失败分析与能力边界

- 不替代最终评审责任。
- 无依据时拒答。
- 高风险结论需要人工确认。
- 文档缺失时提示补充资料。

### 评估观测

V2：

- 建立 golden set。
- 记录检索命中率、引用正确率、拒答正确率。
- 建立 bad case 回流。

### 小项目实战

阶段目标：

- V0：固定 RAG 问答。
- V1：Sources / Refusal / Structured Output。
- V2：RAG Eval / Bad Case 回流。
- V3：单 Agent 增强，放到 `04_agent`。
- V4：前端工作台，放到 `06_ai_native_frontend`。

### 项目收敛

本课程最终收敛为：

- `rag_core`
- `rag_eval`
- `rag_memory`
- `review_assistant_v0`

这些产物进入 `07_projects`，继续扩展为完整项目。
