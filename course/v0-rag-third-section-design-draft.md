# V0 第三段课程设计临时约束

> 本文件只服务第 7–16 步实施期的跨文档协调，不是课程正文、业务契约或阅读顺序真源。正式顺序以 [标准学习路径](learning-path.md) 为准，V0 业务契约与验收以 [V0 项目篇](project/stage-1-single-agent-rag/v0-fixed-rag.md) 为准。已经进入正文、代码、测试或 README 的内容不在这里重复维护；第 16 步完成并确认有效决策已被正式真源吸收后删除本文件。

## 本段只解决一个问题

第三段要让学习者理解：

> 外部资料怎样先成为可追踪知识，再经过 lexical、dense 与 RRF 形成可诊断候选，最终进入受控上下文和结构化评审？

第 7–16 步不增加第二套顺序：

```text
第 7 步建立系统边界
→ 第 8–9 步生产可检索知识
→ 第 10–14 步形成与诊断候选
→ 第 15 步装配模型上下文
→ 第 16 步基于候选证据生成
```

每篇正文仍按自身核心问题自由组织。本文不规定统一标题、固定讲解顺序或必须逐项出现的失败章节。

## 共同业务材料与数据流

所有机制继续使用 V0 项目篇定义的“售后入口与订单状态”垂直切片：

- Target Requirement：当前被评审的 PRD，直接进入评审请求。
- Reference Knowledge：当前有效的订单、接口和客户端规则。
- Historical Material：带历史属性的评审记录，不能自动覆盖现行规则。

固定问题覆盖词面一致、同义改写、精确标识、跨段约束、知识中无答案和噪声相似。具体数据集、证据资格、参数与验收门槛只由 V0 项目篇和实验配置维护。

```text
Reference Knowledge + Historical Material
→ KnowledgeDocument + DocumentElement
→ Chunk + Metadata
→ lexical index / embedding / vector index
→ LexicalHit + DenseHit
→ RRF Candidate
→ RetrievalResult + diagnostics

Target Requirement + RetrievalResult
→ ContextSource + ContextBuildReport
→ structured ReviewReport + Sources / Citation Candidate
```

## 实验和边界怎样进入正文

正文优先使用有效业务输入和正常策略变化观察机制，例如同义改写、精确字段、否定条件、top-k、阈值、过滤范围和上下文预算。

只有当前知识确实涉及对应问题时，才补充：

- 真实依赖故障：鉴权、限流、超时、端点或模型不支持，用于解释异常流和可观察性。
- 确定性契约测试：空输入、损坏文件、维度不一致、非法状态，用于测试应用不变量或稳定复现故障。

这两类内容不能代替正常输入下的机制观察，也不能成为每篇正文的固定栏目。Mock 只证明被模拟的确定性逻辑，不证明真实模型或检索质量。

## 代码和实验边界

第三段只维护一个 `rag_core`：

- `rag_ingestion_lab` 观察文档加载与 Chunking。
- `rag_retrieval_lab` 承接 Embedding、lexical、dense、RRF 与检索诊断。
- 第 15 步复用 `llm_core.context` 和 `llm_context_lab`，RAG 侧只增加必要适配。
- 第 16 步组合已有 Structured Output 与真实模型调用，不创建平行生成 package 或产品 app。

正文解释机制、关键数据变化、公共入口和不变量；完整命令、参数和读码顺序由 package / demo README 维护。

## 第 7–10 步的正式入口

这些步骤的稳定内容已经由正式真源承担，本草稿不再复制其正文设计：

- 第 7 步：[RAG 与外部知识的边界](concepts/rag-and-external-knowledge.md)
- 第 8 步：[文档内容识别、解析路由、结构还原与来源保留](mechanisms/document-loading-and-cleaning.md)
- 第 9 步：[Chunking、父子块与 Metadata](mechanisms/chunking-and-metadata.md)
- 第 10 步：[Embedding 表示与向量相似度](mechanisms/embedding-and-similarity.md)

## 第 11 步：Lexical Retrieval 与 PostgreSQL FTS

**核心问题**：词项检索怎样利用精确词面形成并排序候选，PostgreSQL FTS 与 BM25 的边界是什么？

必须建立的判断：

- 字符串包含、关键词搜索和 Lexical Retrieval 不是同一机制。
- 匹配决定候选，排序决定先后。
- BM25 是排序方法，不是全文检索的统称。
- PostgreSQL 使用 `tsvector`、`tsquery` 与 `ts_rank` / `ts_rank_cd`；产品不能把原生 rank 改名为 BM25 分数。
- 中文分词、英文标识符、下划线和大小写属于检索语义。

最小实验使用真实 PostgreSQL 和同一批 Chunk，比较精确接口名、同义改写与正常噪声文本。重点观察原生 term、候选和 rank；配置错误只作为诊断或契约测试，不作为词面检索效果证据。

**非目标**：不在 Python 内另造产品主路径 BM25，不提前融合 dense 结果。

## 第 12 步：pgvector 与 Dense Retrieval

**核心问题**：怎样把真实 Embedding 与 Chunk 身份、模型空间和可见范围绑定，并用一致的距离语义完成向量检索？

必须建立的判断：

- Embedding Provider、Vector Store、Vector Index 和 Dense Retriever 责任不同。
- exact search 与 ANN 的差异是速度和召回取舍，不会改善向量语义。
- cosine distance、inner product 和 L2 的方向与数值语义不能混写成含糊的 `score`。
- query 与 document 必须属于兼容的 Embedding 空间；模型或预处理变化需要重建。
- Metadata Filter 决定允许参与检索的范围，应在候选形成前生效。

最小实验先保留 exact baseline，再用同义问题、否定条件和精确字段观察 Dense Retrieval 的正常强弱项。索引未启用、维度不匹配等进入结构化诊断和测试。

**非目标**：不把 ANN 当作无质量损失的默认优化，不在本步引入 RRF。

## 第 13 步：多路召回与 RRF

**核心问题**：lexical 与 dense 原生分数不可直接比较时，怎样通过排名融合保留两路互补价值？

必须建立的判断：

- 多路召回、Score Fusion、Rank Fusion 与 Reranker 是不同操作。
- RRF 使用名次贡献，不把 PostgreSQL rank 和向量距离变成可比较分数。
- 融合使用稳定 `chunk_id` 识别候选，并保留每路排名和贡献。
- 单路正常无结果与单路执行失败必须区分。
- RRF 改善候选覆盖与排名，不自动证明证据正确或生成质量提高。

最小实验比较 lexical、dense 和 RRF 在精确字段、同义改写和噪声样例上的排名。正常互补、单路弱项与一路真实故障分别解释，不通过篡改候选列表制造效果。

**非目标**：V0 不接 Reranker，不归一化相加不同检索器原始分数。

## 第 14 步：Retriever 控制与诊断

**核心问题**：候选经过哪些控制才成为最终 `RetrievalResult`，正确 Chunk 消失时怎样定位？

必须建立的判断：

- Metadata Filter、route threshold、`candidate_k` 和 `final_top_k` 责任不同。
- 阈值属于具体检索器的原生分数空间，必须记录名称、方向和执行位置。
- 控制顺序会改变候选集合，是 Retriever 契约的一部分。
- “无结果”应区分知识中无答案、可见范围为空、匹配失败、阈值淘汰、单路错误和最终截断。

V0 默认顺序：

```text
pre-filter
→ lexical / dense candidate_k
→ route threshold
→ RRF
→ final_top_k
→ RetrievalResult + RetrievalReport
```

最小实验一次只改变一个正常变量，观察候选数量、淘汰原因和最终排名。方向写反、错误被静默吞掉等属于不变量测试，不应包装成策略实验。

**非目标**：不把本轮参数写成永久门槛；具体数值在实验运行前登记。

## 第 15 步：从 RetrievalResult 到模型上下文

**核心问题**：Retriever 已经产生候选后，应用怎样决定模型本轮真正看到什么？

复用现有 [Context Engineering](mechanisms/context-engineering.md)，只补 RAG 所需的对象映射：

```text
RetrievalHit
→ ContextSource
→ included / dropped / compressed source
→ BuiltContext + ContextBuildReport
```

必须保留 `chunk_id`、document locator、route ranks 和原生分数，但检索分数不能直接变成来源权威性或事实优先级。`RetrievalReport` 回答“找到了什么”，`ContextBuildReport` 回答“模型看到了什么”。

最小实验使用正常预算、去重和 history 变化，观察正确候选是否因上下文选择而丢失。映射字段缺失、source id 冲突等由适配器测试阻止。

**非目标**：不重新实现 Retriever，不在本步完成 Citation 支持性校验。

## 第 16 步：可信生成与 V0 证据边界

**核心问题**：模型怎样基于受控上下文生成结构化评审，同时让来源候选、材料外结论和证据不足保持可见？

必须区分：

```text
Source
→ Retrieved Candidate
→ Citation Candidate
→ Claimed Citation
→ Validated Citation（V1）
```

V0 只检查模型声明的 source id 是否属于本轮 Citation Candidate，不宣称来源真正支持结论。严格 Citation 支持性校验、Refusal 和补充问题进入 V1。

最小实验使用同一问题比较直接 LLM、正确 evidence、正常噪声 evidence 和空 evidence。重点观察检索无结果、上下文无证据、模型未引用与模型声明未知 source id 的区别；只有真实运行中出现的模型行为才能作为模型边界证据，Schema 和引用存在性由确定性测试固化。

**非目标**：不提前实现 V1 的证据充分性闭环。

## 退出条件

第 11–16 步实施时，稳定结论分别进入：

- 课程正文：机制与判断。
- `source/packages/`：通用能力。
- `source/demos/`：实验变量与观察。
- `review_assistant/`：产品组合与固定业务材料。
- 测试和 eval：不变量与可重复证据。
- README：真实运行和读码入口。

第 16 步完成后确认上述真源已经承接有效内容，然后删除本文件；不把临时设计稿继续维护成第四类课程文档。
