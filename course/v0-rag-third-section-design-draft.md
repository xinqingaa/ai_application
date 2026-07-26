# V0 第三段 7-16 课程设计评审稿

> 本文件是讨论用草稿，不是课程真源，不规定新的阅读顺序。正式顺序仍以仓库中的 `course/learning-path.md` 为准。

## 结论

第三段暂时不增加第二篇概念篇。第 8-16 步都能形成真实、边界清楚的机制实验，符合机制篇准入条件；再插入一篇“检索概念总览”会与第 7、10-14 步重复。

真正的问题是第 7 步目前主要完成了“为什么使用 RAG、与相近方案有什么区别”，尚未充分承担第三段总认知地图。应深化第 7 步，而不是增加新入口。

第 7 步需要补齐五组概念层内容：

1. **对象地图**：File、KnowledgeDocument、DocumentElement、Chunk、Embedding Record、Retrieval Hit、Context Source、Review Result 分别是什么。
2. **三条流**：知识生产流、在线检索流、证据进入生成流；每条流的输入、输出和责任边界。
3. **检索心智模型**：表示、匹配、排名、过滤、融合和最终选择是不同操作。
4. **质量坐标**：可解析、可检索、相关、可进入上下文、能支撑结论不是同一个“准确率”。
5. **第三段导航**：8-9 生产知识，10-14 找到候选，15 选择上下文，16 约束生成。

补齐后，第 7 步仍是概念篇：只建立对象、关系、选型和失败地图，不讲解析库 API、相似度公式推导、SQL、索引参数或 RRF 实现。

## 第三段共同主线

全部机制使用同一组“售后入口与订单状态”资料和同一批问题，避免每篇换案例：

```text
TXT / Markdown / DOCX / PDF
→ KnowledgeDocument + DocumentElement
→ Chunk + Metadata
→ lexical index / embedding / vector index
→ LexicalHit + DenseHit
→ RRF Candidate
→ RetrievalResult + diagnostics
→ ContextSource + ContextBuildReport
→ structured ReviewReport + Sources / Citation Candidate
```

固定问题至少覆盖：

- 词面一致：“售后接口 v2 必填什么字段？”
- 同义改写：“哪些订单可以发起逆向服务？”
- 精确标识：“`source_channel` 在什么情况下必填？”
- 跨段约束：“入口展示条件与状态机是否一致？”
- 无答案：“退款到账时间是多少？”
- 噪声相似：“历史售前活动规则是否应该命中？”

代码只维护一个 `rag_core`。实验最多复用两个 lab：

- `rag_ingestion_lab`：服务第 8、9 步。
- `rag_retrieval_lab`：从第 10 步持续扩展到第 16 步。

第 15 步继续复用现有 `llm_context_lab` 和 `llm_core.context`，不创建第二个 Context Builder。

## 8. 文档加载、清洗与来源保留

**篇型**：机制篇。

**核心问题**：不同文件格式怎样进入同一个知识文档契约，同时不丢失可回查的原始位置？

**输入输出**：

```text
FileArtifact + LoaderConfig
→ format-specific parser
→ DocumentElement[]
→ deterministic cleaning
→ KnowledgeDocument + LoadReport
```

**正文解释顺序**：

1. 用“文件上传成功但 PDF 提取为空”说明文件不等于知识。
2. 区分原始文件、业务文档、解析元素和后续 Chunk。
3. 分别解释 TXT 行、Markdown 标题层级、DOCX 段落/表格、PDF 页面的来源能力。
4. 解释清洗会改变文本，因此每项清洗都必须可说明、可测试，不能破坏定位。
5. 建立 `document_id`、`document_version`、content hash、locator 和解析报告。
6. 比较格式解析库封装了什么，以及扫描 PDF、复杂表格和图片语义仍未解决。

**代码与实验**：新建 `rag_core/ingestion` 和共享类型；使用四种格式表达同一份规则，打印元素文本、结构路径、页码/段落/行号和警告。解析库通过根 `uv` 依赖加入。

**主动失败**：扫描 PDF、损坏 DOCX、非预期编码 TXT、空 Markdown、PDF 文本顺序错误。错误必须区分 format detection、parse、cleaning 和 empty content。

**非目标**：不做 Chunk、不做 OCR/VLM、不做对象存储和后台入库任务。

**掌握标准**：能从解析结果回到原文件位置，并解释为什么不能把所有格式强行伪装成统一页码。

## 9. Chunking、父子块与 Metadata

**篇型**：机制篇。

**核心问题**：怎样把文档元素变成既容易召回、又能保留完整语义和来源关系的检索单元？

**输入输出**：

```text
KnowledgeDocument + DocumentElement[] + ChunkPolicy
→ boundary detection
→ split / overlap / parent-child assembly
→ Metadata inheritance
→ Chunk[] + ChunkReport
```

**正文解释顺序**：

1. 对比整篇入库、固定字符切分和按结构切分的失败。
2. 区分字符、Token、句子、段落、标题结构和语义边界。
3. 解释 chunk size 与 overlap 如何同时影响召回、噪声、成本和 Citation 定位。
4. 用父块提供完整语境、子块承担精确召回，但不宣称父子块总是更好。
5. 区分来源 Metadata、业务过滤 Metadata 和运行诊断；模型推测不能写入来源事实。
6. 建立稳定 `chunk_id`、策略版本和重新切分后的更新语义。

**代码与实验**：扩展 `rag_core/chunking`，复用第 8 步 fixtures；比较 small、large、structure-aware、parent-child 四组策略，输出块数量、Token 分布、来源跨度和固定问题的可命中范围。

**主动失败**：状态条件与例外被拆开、标题成为孤块、表格行失去表头、overlap 产生大量重复、策略变化却复用旧 ID。

**非目标**：不提前用最终回答判断策略优劣；不引入语义 Chunking 服务作为默认方案。

**掌握标准**：能预测某个切分配置会让哪类问题变好或变坏，并能从 Chunk 回到 DocumentElement。

## 10. Embedding 表示与向量相似度

**篇型**：机制篇。

**核心问题**：文本怎样变成可比较的向量，相似度分数能说明什么、不能说明什么？

**输入输出**：

```text
text[] + EmbeddingConfig
→ real embedding provider
→ vector[] + model / dimension / latency metadata
→ similarity comparison
```

**正文解释顺序**：

1. 从“申请售后”和“发起逆向服务”词面不同但语义接近切入。
2. 先用空间方向建立直觉，再解释高维稠密向量，不从公式开始。
3. 解释 cosine、dot product、Euclidean distance 的方向和归一化关系。
4. 区分相似度、相关性和事实正确性。
5. 解释 query/document 必须使用兼容模型、维度和预处理版本。
6. 解释批处理、Token 限制、真实服务错误和调用记录。

**代码与实验**：实现 `rag_core/embedding` 的 Provider 契约和 OpenAI-compatible 真实调用；固定中文短句比较同义、否定、精确标识、数字变化和无关文本。Mock 只测试批处理、维度校验和错误映射。

**主动失败**：缺少 key、限流、超长文本、空文本、维度改变、模型更换后混用旧向量、语义相似但约束相反。

**非目标**：本篇不接 pgvector、不宣称某个相似度阈值是全局正确答案。

**掌握标准**：能解释分数方向、模型一致性和“高相似不等于能支撑结论”。

## 11. Lexical Retrieval、BM25 边界与 PostgreSQL FTS

**篇型**：机制篇。

**核心问题**：词项检索怎样利用精确词面找到候选，BM25 与 PostgreSQL FTS 排序到底有什么区别？

**输入输出**：

```text
query + visible Chunk pool + lexical config
→ tokenize / normalize
→ PostgreSQL tsvector / tsquery match
→ LexicalHit[] + native rank + diagnostics
```

**正文解释顺序**：

1. 用接口名、状态码、字段名说明词项检索不可替代。
2. 解释倒排索引、词频、文档频率和长度归一化为什么影响排序。
3. 用自然语言解释 BM25，再明确产品没有使用 BM25 实现。
4. 解释 PostgreSQL `tsvector`、`tsquery`、词典和 `ts_rank` / `ts_rank_cd`。
5. 比较中文分词、英文标识符、大小写和符号对命中的影响。
6. 保留 PostgreSQL 原生 rank 名称与方向，不包装成统一“相关度”。

**代码与实验**：扩展 `rag_core/retrieval/lexical`，连接真实 PostgreSQL；在相同 Chunk 上观察精确接口名、同义改写和噪声词的排名。

**主动失败**：中文分词配置错误、`source_channel` 被错误拆分、同义表达无命中、旧版本 Chunk 未过滤、把 `ts_rank` 标成 BM25。

**非目标**：不在 Python 内另造一套伪 BM25 作为产品主路径；原理对照可以最小化实现但不得与 PostgreSQL 结果混称。

**掌握标准**：能查看 SQL 与原生 rank，解释词面检索为什么擅长精确标识却漏掉同义改写。

## 12. pgvector、Dense Retrieval 与向量索引

**篇型**：机制篇。

**核心问题**：怎样把真实 Embedding 存入 pgvector，并用一致的距离语义完成可诊断 Dense Retrieval？

**输入输出**：

```text
query
→ query embedding
→ pgvector distance search over visible chunks
→ DenseHit[] + native distance / similarity + diagnostics
```

**正文解释顺序**：

1. 从第 10 步的内存相似度进入持久化向量检索。
2. 建立 Chunk、Embedding Record、模型版本和向量维度的数据关系。
3. 解释 pgvector 的 cosine distance、inner product、L2 操作符及方向。
4. 先观察 exact search，再解释 HNSW / IVFFlat 的近似、构建和召回取舍。
5. 解释 Metadata Filter 应先限定可见候选范围，不能先全库召回再补权限。
6. 明确模型或维度变化必须重建索引。

**代码与实验**：实现迁移和 `rag_core/retrieval/dense`；复用第 10 步真实 Embedding，比较同义问题、否定条件和精确字段名。

**主动失败**：扩展未启用、维度不匹配、距离方向读反、查询与文档模型不同、索引未重建、过滤发生在召回之后。

**非目标**：不把近似索引默认当成更快且无质量损失；小数据集先保留 exact baseline。

**掌握标准**：能解释 SQL 操作符、分数方向、索引策略和一次 Dense miss 的优先排查位置。

## 13. 多路召回与 RRF 融合

**篇型**：机制篇。

**核心问题**：lexical 与 dense 各有弱项时，怎样融合排名而不直接相加不可比的原始分数？

**输入输出**：

```text
LexicalHit[] + DenseHit[] + RRFConfig
→ stable chunk identity merge
→ reciprocal rank contribution
→ FusedHit[] + route ranks + contribution report
```

**正文解释顺序**：

1. 用精确字段和同义改写展示两路互补。
2. 解释为什么 `ts_rank=0.3` 与 cosine similarity `0.8` 不能直接相加。
3. 从排名投票直觉进入 RRF 公式及 `rrf_k`。
4. 解释同一 Chunk 的稳定身份、去重和每路贡献保留。
5. 比较单路命中、两路命中、一路噪声和一路失败。
6. 明确融合改善候选覆盖，不自动改善生成答案。

**代码与实验**：实现应用侧 `rag_core/retrieval/fusion`；使用同一 Case 比较 lexical、dense、RRF 的排名并打印每路贡献。

**主动失败**：用文本而非 `chunk_id` 去重、一路重复结果刷高贡献、输入列表已被错误截断、`rrf_k` 变化未记录、一路错误被静默当空结果。

**非目标**：V0 不接 Reranker；不归一化并相加不同检索器原始分数。

**掌握标准**：能手算小型 RRF 示例，并指出结果来自哪一路、哪一名次。

## 14. Top-k、阈值、Metadata Filter 与 Retrieval 诊断

**篇型**：机制篇。

**核心问题**：检索候选经过哪些控制才成为最终 RetrievalResult，为什么无结果必须说明原因？

**输入输出**：

```text
query + knowledge_scope + RetrieverConfig
→ pre-filter
→ lexical / dense candidate_k and native thresholds
→ RRF
→ final_top_k
→ RetrievalResult + RetrievalReport
```

**正文解释顺序**：

1. 区分 `candidate_k`、每路阈值和 `final_top_k`，不能都叫 top-k。
2. 解释 Metadata Filter 的业务范围与权限意义，以及为什么两路必须使用同一可见文档池。
3. 解释阈值属于各自原生分数空间，方向不能混用。
4. 固定 V0 的执行顺序：pre-filter → route threshold → RRF → final top-k。
5. 建立 `RetrievalResult`、候选、淘汰原因、耗时和结构化错误。
6. 将“知识中无答案”“过滤后无可见资料”“阈值过高”“某一路失败”区分开。

**代码与实验**：建立统一 Retriever facade 与 report；一次只改变一个变量，观察候选数、命中、淘汰和最终排名。

**主动失败**：top-k 太小、top-k 太大、dense 阈值方向写反、filter 排除正确版本、融合后再使用含义不明的统一阈值、单路超时被伪装为正常无结果。

**非目标**：本篇不建立永久数值门槛；具体阈值在实验运行前登记。

**掌握标准**：能根据报告回答“正确 Chunk 在哪一步消失”，而不是只看最终无结果。

## 15. Context Engineering：输入装配、预算与证据边界

**篇型**：机制篇，复用现有正文，不创建 `context-construction.md`。

**核心问题**：Retriever 已经产生候选后，应用怎样决定哪些材料真正进入模型输入，并保留选择、压缩和 Citation Candidate 诊断？

**输入输出**：

```text
ReviewRequest + RetrievalResult + optional history
→ RetrievalHit to ContextSource adapter
→ selection / dedupe / section budget / compression
→ messages + ContextBuildReport
```

**现有正文保留**：候选池与最终 Prompt、Source 类型、分区预算、确定性压缩、Citation Candidate、included/dropped/compressed report，以及 `llm_core.context` 实验。

**需要补强**：

1. 增加真实 `RetrievalResult → ContextSource` 映射契约。
2. 保留 `chunk_id`、document locator、route ranks 和 retrieval score，不把检索分数当 Context 事实优先级。
3. 对比 Retriever 返回正确候选但 Context 因预算丢弃的失败。
4. 明确 RAG adapter 属于 `rag_core`，通用选择与预算仍属于 `llm_core.context`。

**主动失败**：正确候选未映射、source id 冲突、去重误删互补证据、压缩丢掉否定条件、history 挤掉 evidence。

**非目标**：不重新实现 Retriever，不在本篇做 Citation 支持性校验。

**掌握标准**：能比较 RetrievalReport 与 ContextBuildReport，判断事实丢在检索还是上下文阶段。

## 16. 可信生成、Sources、Citation Candidate 与证据不足

**篇型**：机制篇。

**核心问题**：模型怎样基于受控上下文生成结构化评审，同时让来源候选、材料外结论和证据不足保持可见？

**输入输出**：

```text
ReviewRequest + messages + ContextBuildReport
→ real structured LLM call
→ parsed ReviewReport
→ Sources + Citation Candidate check + generation diagnostics
```

**正文解释顺序**：

1. 区分 Source、retrieved candidate、Context citation candidate、模型声明的 citation 和 V1 validated citation。
2. 解释 Prompt 如何要求只依据 evidence，但 Prompt 不能证明模型遵守。
3. 复用 Structured Output，给风险项保留来源声明与不确定信息。
4. V0 只检查模型声明的 source id 是否属于本轮 Citation Candidate，不判断证据是否真正支持结论。
5. 区分“检索无结果”“上下文无证据”“模型未引用”“模型编造来源”。
6. 解释证据不足信号如何进入 V0 输出，但严格 Refusal、补充问题和支持性校验留给 V1。

**代码与实验**：扩展固定 RAG generation pipeline，真实调用结构化模型；同一问题比较直接 LLM、正确 evidence、噪声 evidence 和空 evidence。复用 `rag_retrieval_lab`，不新增独立 package 或平行 app。

**主动失败**：模型引用不存在 source、正确来源进入上下文但模型不用、材料不足却生成确定结论、Structured Output 解析失败、真实 Provider 鉴权/限流失败。

**非目标**：不宣称完成 Citation 支持性校验；不实现 V1 的严格 Refusal 与追问闭环。

**掌握标准**：能说明 V0 的 Citation Candidate 能证明什么、不能证明什么，并能把失败定位到 retrieval、context、generation 或 schema。

## 推荐实施顺序

1. 先深化第 7 步总认知地图，但不加入实现细节。
2. 第 8、9 步共同建立 `rag_core` 的文档与 Chunk 契约以及 ingestion lab。
3. 第 10 步建立真实 Embedding 调用；第 11、12 步分别形成 lexical 与 dense 单路基线。
4. 第 13、14 步统一融合和 Retriever 诊断契约。
5. 第 15 步在已有 Context Builder 上补 RAG adapter。
6. 第 16 步接入真实结构化生成并冻结 V0 / V1 的可信边界。

任何一步正式落地时，正文、通用代码、实验、测试和 README 一起完成；本评审稿本身不能作为“已学习”或“已实现”的证据。
