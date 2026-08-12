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

## 第 7–15 步的正式入口

这些步骤的稳定内容已经由正式真源承担，本草稿不再复制其正文设计：

- 第 7 步：[RAG 与外部知识的边界](concepts/rag-and-external-knowledge.md)
- 第 8 步：[文档内容识别、解析路由、结构还原与来源保留](mechanisms/document-loading-and-cleaning.md)
- 第 9 步：[Chunking、父子块与 Metadata](mechanisms/chunking-and-metadata.md)
- 第 10 步：[Embedding 表示与向量相似度](mechanisms/embedding-and-similarity.md)
- 第 11 步：[Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索](mechanisms/lexical-retrieval.md)
- 第 12 步：[pgvector、Dense Retrieval 与向量索引](mechanisms/vector-store-and-pgvector.md)
- 第 13 步：[多路召回与 RRF 融合](mechanisms/multi-retrieval-and-rrf.md)
- 第 14 步：[Top-k、阈值、Metadata Filter 与 Retrieval 诊断](mechanisms/retriever-contract.md)
- 第 15 步：[Context Engineering：从检索候选到模型真正看到的证据](mechanisms/context-engineering.md)

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
