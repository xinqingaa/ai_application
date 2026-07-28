# V0 第三段 7-16 课程设计评审稿

> 本文件是第 7–16 步实施前的临时设计输入，不是课程真源，不规定新的阅读顺序，也不记录实时进度。正式顺序以 `course/learning-path.md` 为准，V0 业务契约以项目篇为准；每一步完成后，结论进入对应正文、代码、测试和 README，不回写本草稿。第 16 步完成并确认有效决策已被正式真源吸收后，删除本文件。

## 结论

第三段不增加新步骤。第 8-16 步仍按当前学习路径排列，概念篇和机制篇的穿插发生在正文内部：机制篇先建立本篇必需的局部概念，再进入数据变化、真实实验和失败定位。

第 7 步仍需从“为什么使用 RAG、与相近方案有什么区别”深化为第三段总认知地图，但不负责讲完后续全部检索概念。表示、匹配、分数、排名、过滤以及 lexical / dense 的局部边界，放在第 10 步 Embedding 正文进入机制之前解释。

第 7 步需要补齐五组概念层内容：

1. **对象地图**：Target Requirement、Reference Knowledge、Historical Material、File、KnowledgeDocument、DocumentElement、Chunk、Embedding Record、Retrieval Hit、Context Source、Review Result 分别是什么。
2. **三条流**：知识生产流、在线检索流、证据进入生成流；每条流的输入、输出和责任边界。
3. **检索位置地图**：知道表示、匹配、排名、过滤、融合和最终选择属于不同环节，但把具体区别留给第 10 步正文的概念过渡。
4. **质量坐标**：可解析、可检索、相关、可进入上下文、能支撑结论不是同一个“准确率”。
5. **第三段导航**：8-9 生产知识，10-14 找到候选，第 15 步选择上下文，第 16 步约束生成。

补齐后，第 7 步仍是系统级概念篇：建立对象、关系、选型和失败地图，不展开 lexical / dense 的局部原理，也不讲解析库 API、相似度公式推导、SQL、索引参数或 RRF 实现。

## 第三段共同主线

全部机制使用 V0 项目篇定义的同一组“售后入口与订单状态”对象和同一批问题，避免每篇换案例。当前待评审 PRD 是 Target Requirement，作为评审主体直接输入；订单状态规则、接口文档和客户端规则是 Reference Knowledge；历史评审记录是 Historical Material，必须保留历史角色。

```text
Reference Knowledge + Historical Material
→ TXT / Markdown / DOCX / PDF
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

**进入加载机制前的概念判断**：

先区分四个对象，避免从“选哪个解析库”开始理解知识生产：

```text
FileArtifact：收到的物理文件及其格式、名称、大小和内容哈希
KnowledgeDocument：具有稳定业务身份和版本的知识文档
DocumentElement：解析后仍保留结构与来源位置的段落、标题、表格或页面元素
Chunk：后续为检索生成的单元，本篇尚不产生
```

正文进入实现前需要先说明：

1. 文件上传成功只证明拿到了字节，不证明内容已经成为知识。
2. 同一业务文档可以有多个文件版本；`document_id` 与文件名、数据库自增 ID 不是同一概念。
3. Source Locator 负责回到原文位置，业务 Metadata 负责范围与过滤，两者不能混为一个无约束字典。
4. 清洗既可能是无损规范化，也可能是有损转换；删除换行、表头或页边信息都可能改变语义和定位。
5. TXT 行、Markdown 标题、DOCX 段落/表格和 PDF 页面具有不同定位能力，不应强制伪装成统一页码。
6. 文本型 PDF 与扫描 PDF 是两类输入。前者能直接提取文本，后者需要 OCR/VLM，不支持时必须显式失败。

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

**进入 Chunking 前的概念判断**：

Chunk 是应用为了检索建立的工程单元，不是文档中天然存在的“正确语义块”。同一段原文可能同时对应不同责任的单元：

```text
子 Chunk：用于精确匹配和排名
父 Chunk：用于取回更完整语境
Context Source：决定最终交给模型的内容
Source Locator：负责让用户回到原始文档位置
```

正文进入切分策略前需要先说明：

1. 检索单元、上下文单元和引用定位单元可以不同，不能默认一个 Chunk 同时最适合三种任务。
2. Chunk 越小不等于越精确：条件与例外可能被拆开；Chunk 越大也不等于信息越全：噪声和预算会增加。
3. overlap 用重复换取边界完整性，也会增加索引量、重复召回和去重压力。
4. 父子块不是“高级切分”的同义词。只有子块便于召回、父块确实补充必要语境时才有价值。
5. 来源 Metadata、业务过滤 Metadata、策略版本和运行诊断是不同信息，不允许把模型推测写成来源事实。
6. `chunk_id` 标识某个文档版本和切分策略下的片段；内容或策略改变后必须能区分新旧 Chunk。

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

**进入 Embedding 前的概念过渡**：

先用下面这条候选形成链建立检索视角，再进入向量机制：

```text
query + visible Chunk pool
→ 表示 query 与 Chunk
→ 按某种规则匹配
→ 产生各自分数和排名
→ 过滤不可见或不合格候选
→ 按需要融合多路排名
→ 返回候选证据
```

这一部分先解释：

1. 表示、匹配、原生分数、排名、过滤、融合和最终选择是不同操作。
2. lexical 依赖词面表示与匹配，dense 依赖 Embedding 表示空间；两者擅长的问题不同。
3. 相似、相关和能够支撑结论不是同一件事，Retriever 只生产候选证据。
4. 不同检索器的原生分数语义和方向不同，不能未经证明直接相加。
5. Recall、Precision、Ranking Quality 和最终生成质量需要分别观察。

概念过渡只帮助读者知道 Embedding 位于检索链的“表示”环节。BM25、PostgreSQL FTS、pgvector、RRF 和具体诊断仍由后续机制篇展开。

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

**进入 Lexical Retrieval 前的概念判断**：

先把“文本里出现过某个字符串”与“检索系统召回并排序候选”分开：

```text
字符串包含 / 正则：对当前文本做确定性匹配
关键词搜索：用查询词寻找候选的宽泛产品名称
Lexical Retrieval：经过分词、规范化、倒排匹配和排序的检索机制
```

正文进入 BM25 和 PostgreSQL 前需要先说明：

1. Token、term、document frequency、posting list 和 rank 分别处于不同环节。
2. 匹配决定哪些 Chunk 成为候选，排序决定候选先后；命中不等于排在前面。
3. 精确接口名、状态码和字段名适合词面检索，同义改写通常是它的弱项。
4. BM25 是利用词频、逆文档频率和长度归一化的排序方法，不是所有全文检索系统的统称。
5. PostgreSQL FTS 使用自己的词典、`tsvector`、`tsquery` 与 `ts_rank` / `ts_rank_cd`；本项目学习 BM25 原理，但不能把 PostgreSQL 原生 rank 改名为 BM25 分数。
6. 中文文本、英文标识符、下划线和大小写会影响 term 形成，分词与规范化配置属于检索语义，而不只是预处理细节。

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

**进入 pgvector 前的概念判断**：

先区分四个对象，避免把 pgvector 当作 Embedding 模型：

```text
Embedding Provider：把文本转换为向量
Vector Store：保存向量及其所属 Chunk、模型与版本
Vector Index：缩小需要比较的向量范围
Dense Retriever：组织 query embedding、过滤、搜索、排名和诊断
```

正文进入 SQL 和索引参数前需要先说明：

1. 向量已经生成不等于 Dense Retrieval 已经成立；还需要存储关系、查询契约、过滤、分数方向和诊断。
2. exact search 比较所有可见候选；ANN 用可能损失召回换取速度。HNSW / IVFFlat 是索引策略，不会让向量语义本身变好。
3. cosine distance、cosine similarity、inner product 和 L2 的数值方向不同，不能统一包装成含义模糊的 `score`。
4. query 与 document 必须使用兼容的 Embedding 模型、维度和预处理版本。
5. Metadata Filter 不只是性能优化，还表达知识范围和可见性；先全库召回再过滤可能已经改变 top-k 语义。
6. 模型或维度变化需要重建向量与索引，不能把新旧表示空间混在同一检索结果中。

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

**进入 RRF 前的概念判断**：

先区分四类经常被统称为“混合检索”的操作：

```text
多路召回：多个 Retriever 分别产生候选
Score Fusion：融合语义可比较、经过校准的原始分数
Rank Fusion：只依据各路排名合并候选
Reranker：重新读取候选内容并产生新的相关性排序
```

正文进入 RRF 公式前需要先说明：

1. lexical 与 dense 的价值来自弱项互补，不要求每条 Case 都由两路同时命中。
2. PostgreSQL rank 与向量距离的量纲、方向和分布不同，未经校准不能直接相加。
3. RRF 属于 Rank Fusion，只使用名次贡献，不会把两路原始分数变成可比较分数。
4. 融合需要稳定 `chunk_id` 判断“是否为同一候选”；文本相同不一定是同一来源，文本不同也可能属于同一父块。
5. 某一路失败与该路正常返回空列表是不同状态，不能为了完成融合而静默抹平错误。
6. RRF 改善的是候选覆盖与排名，不能自动证明证据正确，也不能替代后续 Reranker 或生成评估。

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

**进入 Retriever 契约前的概念判断**：

先把几个看似都是“筛结果”的控制拆开：

```text
Metadata Filter：限定允许参与检索的知识范围
candidate_k：控制每一路最多保留多少候选
route threshold：按该路原生分数淘汰不合格候选
RRF：融合通过各路控制的排名
final_top_k：限制融合后最终交给下游的数量
```

正文进入配置与诊断前需要先说明：

1. Filter 判断候选是否有资格参与，threshold 判断该路匹配是否达到要求，top-k 只做数量截断，三者不能互换。
2. `candidate_k` 与 `final_top_k` 服务不同阶段；都命名为 `top_k` 会让运行记录失去解释力。
3. 阈值属于具体检索器的原生分数空间，必须记录名称、方向和应用位置。
4. 控制顺序会改变候选集合，是 Retriever 语义的一部分，而不是实现细节。
5. “无结果”至少要区分知识中无答案、可见范围为空、匹配失败、阈值淘汰、某一路错误和最终截断。
6. Retrieval Report 是业务结果之外的诊断契约；普通用户不必看到全部字段，但实验、调试和回归必须保留。

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

**从 Retrieval 进入 Context 前的概念过渡**：

现有正文已经解释 Context、Source、Evidence、预算、压缩和 Citation Candidate。接入真实 RAG 时只补下面这条对象转换：

```text
RetrievalHit：Retriever 判断可能相关的 Chunk 及排名诊断
→ ContextSource：带来源身份、类型和可引用资格的候选材料
→ included / dropped / compressed source
→ BuiltContext：本轮模型真正看到的输入
```

这一部分需要明确：

1. Retrieval Hit 被召回不代表一定进入 Context，进入 Context 也不代表模型一定正确使用。
2. retrieval score 只表达该 Retriever 的匹配信号，不等于来源权威性、证据优先级或事实可信度。
3. `chunk_id`、document locator、route rank 和原生分数应随映射保留，不能只传一段裸文本。
4. Context 去重必须区分完全重复与互补证据，不能因为文本相似就删除来自不同规则或版本的材料。
5. Retrieval Report 与 Context Build Report 分别回答“找到了什么”和“模型看到了什么”，失败定位时需要并列比较。

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

**进入可信生成前的概念判断**：

先建立完整证据生命周期，避免把“模型输出了来源 ID”误认为 Citation 已可信：

```text
Source：系统中带身份的原始材料
→ Retrieved Candidate：Retriever 返回的候选 Chunk
→ Citation Candidate：本轮 Context 中允许模型引用的来源
→ Claimed Citation：模型在结果里声明使用的来源
→ Validated Citation：应用确认来源存在且能够支持结论的引用
```

正文进入 Prompt、Schema 和真实模型调用前需要先说明：

1. Source 是材料身份，Evidence 是能够支持当前结论的材料角色；并非所有 Source 在当前问题下都是 Evidence。
2. Citation Candidate 只证明某个来源允许被引用，不证明它真的支持风险结论。
3. Claimed Citation 由模型声明，可能不存在、引用错对象，或者来源存在但内容不支持结论。
4. Validated Citation 需要应用侧存在性、定位和支持性校验，属于 V1，不应由 V0 提前宣称完成。
5. “没有检索结果”“没有材料进入 Context”“模型没有引用”“模型编造来源”是四类不同失败。
6. V0 可以输出证据不足信号和无法确认项，但严格 Refusal、补充问题及证据充分性闭环进入 V1。
7. Prompt 可以要求依据证据，Schema 可以约束字段形状，两者都不能单独证明内容可信。

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
3. 第 10 步先建立表示、匹配、分数、排名和 lexical / dense 的概念判断，再进入真实 Embedding 调用。
4. 第 11、12 步分别形成 lexical 与 dense 单路基线。
5. 第 13、14 步统一融合和 Retriever 诊断契约。
6. 第 15 步在已有 Context Builder 上补 RAG adapter。
7. 第 16 步接入真实结构化生成并冻结 V0 / V1 的可信边界。

任何一步正式落地时，正文、通用代码、实验、测试和 README 一起完成；本评审稿本身不能作为“已学习”或“已实现”的证据，也不维护完成勾选。第 16 步完成后按文首退出条件删除，不长期保留为第四类课程文档。
