# pgvector、Dense Retrieval 与向量索引

> 机制篇：把第 9 步的可回查 Chunk 与第 10 步的真实 Embedding 连接起来，在 PostgreSQL 中完成可观察的向量检索。
>
> 课程位置：[标准学习路径](../learning-path.md) V0 第十二步。必要前置是 [Embedding 表示与向量相似度](embedding-and-similarity.md)；为了看清两条召回路线的差异，也应先完成 [Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索](lexical-retrieval.md)。本文交付 `Chunk → pgvector → DenseHit`，不实现 RRF、统一阈值、最终 Context 或 Citation 校验。

## 先看一个“程序没坏，但就是找不到”的问题

资料中有一句：

```text
仅已支付且已完成的订单可申请售后。
```

用户问：

```text
哪些订单可以发起逆向服务？
```

如果你刚学完第 11 步，可能会疑惑：资料明明写了相关规则，为什么 PostgreSQL FTS 可能返回 0 条？

先把两边真正进入词面检索的词列出来：

```text
资料词项：已支付 / 已完成 / 订单 / 申请 / 售后
查询词项：订单 / 发起 / 逆向 / 服务
```

它们可能只共享“订单”，也可能因为查询组合、分词和 Chunk 内容而没有足够的共同词项。“申请售后”和“发起逆向服务”表达接近的意思，但字面不同。词面检索只能使用实际出现的词，不能自己推断这两个说法相近。

怎样区分“查询成功但没有匹配”和“数据库执行失败”？先在同一次实验中再查一个资料里原样出现的精确字段：

```text
source_channel
```

如果 FTS 能正常返回包含 `source_channel` 的接口规则，同时连接、SQL 和 migration 都成功，那么数据库正在按词项条件正常工作。第一条查询没有找到，不是服务停止或 SQL 报错，而是当前匹配方法没有足够的共同词面。

现在才可以给这个现象命名：

> 这是 Lexical Retrieval 的能力范围。它擅长相同词语和精确标识，不会自动理解所有同义改写。

第 10 步已经观察过，“申请售后”和“发起逆向服务”的 Embedding 可能比较接近。问题是，当时只比较了提前选好的几个句子，并没有从整个 Chunk 集合中搜索。

本文要完成的变化是：

```text
第 10 步：几段已知文本 → 成对相似度

第 12 步：用户问题 + 全部可见 Chunk
         → 找出距离最近的 Chunk
         → DenseHit[]
```

读完后，你应该能够：

- 解释 Embedding Provider、Vector Store、Dense Retriever 和 Vector Index 各自负责什么。
- 将真实 Chunk 向量保存到 PostgreSQL，并保留 `chunk_id` 和 Embedding 空间身份。
- 使用 pgvector cosine distance 从可见 Chunk 中返回 `DenseHit`。
- 解释 distance 为什么越小越近，不能与 FTS rank 直接比较。
- 区分 exact search 与 HNSW 索引路线。
- 根据“0 条结果、维度不一致、空间不一致、索引未使用”等现象找到优先排查位置。

本文不会证明 Dense 一定优于 Lexical，也不会把距离近的 Chunk 直接当成正确证据。

## Dense Retrieval 到底多做了什么

“Dense”不是“数据很多”的意思。这里指每段文本被表示成一个大多数维度都有数值的稠密向量。

最小数据流是：

```text
知识侧：
Chunk.text
→ 真实 Embedding 服务
→ Chunk vector
→ 绑定 chunk_id 与 Embedding 空间
→ 保存到 Vector Store

查询侧：
query text
→ 同一个兼容 Embedding 空间
→ query vector
→ 与可见 Chunk vector 计算距离
→ 按距离排序
→ DenseHit[]
```

和第 10 步相比，新增了三个动作：

1. **持久化**：Chunk 向量不能每次查询都重新生成。
2. **候选范围**：只比较当前允许检索的 Chunk，而不是随意拿两段文本。
3. **排名**：计算 query 与每个候选的距离，再返回前 `candidate_k` 条。

Dense Retrieval 仍然没有完成：

- 理解否定和例外。
- 判断资料是否是当前有效版本。
- 判断候选能否支持最终结论。
- 把 lexical 和 dense 的结果融合。
- 决定哪些候选进入模型上下文。

所以本文输出叫 `DenseHit`，不叫 `Evidence` 或 `Answer`。

## 四个角色不要混在一起

先用生活化分工理解：

| 角色 | 可以暂时理解为 | 当前项目中的责任 |
| --- | --- | --- |
| Embedding Provider | 把文字翻译成数字坐标的服务 | `LLMClient.embed` 调用真实外部模型 |
| Vector Store | 保存坐标和原文身份的仓库 | `PostgresVectorStore` 保存 Chunk vector 与空间身份 |
| Dense Retriever | 拿查询坐标寻找附近资料的查询者 | `PostgresDenseRetriever.search` 过滤、计算距离和排名 |
| Vector Index | 帮查询者少走一些路的索引结构 | 当前空间对应的 pgvector HNSW index |

它们不能互相替代：

- pgvector 不会替你调用 Embedding 模型。
- Embedding API 不会替你保存 `chunk_id` 和资料版本。
- HNSW 不会让模型更懂“虚拟商品不进入售后”。
- Dense Retriever 不会验证最终回答引用是否正确。

如果把四个动作都写成一个 `vector_search()` 黑盒，运行成功时看起来很方便，失败时却不知道应该检查模型、存储、查询还是索引。

## pgvector 是 PostgreSQL 的扩展，不是另一个模型

当前项目已经在第 11 步使用 PostgreSQL 保存 Chunk。第 12 步继续使用同一个数据库，并通过 pgvector 增加：

- `vector` 数据类型。
- cosine、inner product、L2 等距离运算符。
- HNSW、IVFFlat 等近似向量索引。

启用扩展：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

这里的“扩展”表示给 PostgreSQL 安装额外的数据类型、函数、运算符和索引能力。它不是 Python package，也不是远程 Embedding 服务。

当前 migration 位于：

- [`0001_create_rag_chunks.sql`](../../review_assistant/infra/migrations/0001_create_rag_chunks.sql)：共享 Chunk、原文、Metadata 和 FTS 表示。
- [`0002_add_pgvector_embeddings.sql`](../../review_assistant/infra/migrations/0002_add_pgvector_embeddings.sql)：pgvector extension 和 Chunk embedding 表。

两个表的关系是：

```text
rag_chunks
└── chunk_id：Chunk 稳定身份、原文、来源、Metadata、词法表示

rag_chunk_embeddings
├── chunk_id：回到 rag_chunks
├── embedding_space_ref：属于哪个 Embedding 空间
├── provider / config / model / dimensions / preprocessing
└── embedding：真实向量
```

为什么不把向量直接当成一列随便加到 `rag_chunks`？因为同一个 Chunk 可能因模型或预处理变化而重新生成表示。分开保存后，`chunk_id + embedding_space_ref` 能明确表示“哪个 Chunk 在哪个空间中的向量”。

这不是要求产品长期保留无限多旧空间。知识治理、重建和删除策略会继续演进；当前先把身份表达正确，避免新旧向量悄悄混用。

## 先做 exact search：最慢但最容易判断对错

假设当前可见范围只有四个 Chunk。最直接的方法是：

```text
query vector
→ 分别计算与 Chunk A / B / C / D 的距离
→ 对四个距离排序
→ 返回前 k 条
```

这叫 exact nearest-neighbor search。它会检查当前范围中的全部向量，因此结果是当前距离函数下的精确近邻。

如果有一百万个 Chunk，每次检查一百万条会越来越慢。但在学习和建立小型 V0 基线时，exact 有一个非常重要的价值：

> 它是正确性基线。后面增加近似索引后，可以比较索引是否为了速度漏掉了 exact 本来能找到的候选。

不要一开始就启用 ANN，然后看到结果不同却不知道是向量语义、过滤、索引参数还是近似召回造成的。

当前 exact 查询的核心形态可以简化为：

```sql
SELECT
    chunk.chunk_id,
    chunk.content,
    embedding.embedding <=> %(query_vector)s AS cosine_distance
FROM review_assistant.rag_chunk_embeddings AS embedding
JOIN review_assistant.rag_chunks AS chunk
  ON chunk.chunk_id = embedding.chunk_id
WHERE embedding.embedding_space_ref = %(embedding_space_ref)s
  AND chunk.business_metadata ->> 'knowledge_scope' = %(knowledge_scope)s
ORDER BY cosine_distance ASC
LIMIT %(candidate_k)s;
```

读这段 SQL 时先抓住四件事：

1. `JOIN` 通过 `chunk_id` 找回原文和来源。
2. `embedding_space_ref` 阻止不同 Embedding 空间混用。
3. `knowledge_scope` 先限制业务可见范围。
4. `<=>` 产生 cosine distance，`ASC` 表示从小到大排列。

数据库执行 SQL；哪些字段构成空间、哪些资料允许参与、返回什么诊断，仍由应用建立契约。

## cosine similarity 与 cosine distance 方向相反

第 10 步的成对实验使用 `cosine similarity`：

```text
越接近 1 → 方向越接近 → higher is closer
```

pgvector 的 `<=>` 返回 `cosine distance`：

```text
cosine distance = 1 - cosine similarity
```

所以：

```text
similarity = 0.90 → distance = 0.10
similarity = 0.35 → distance = 0.65
```

在 distance 中，`0.10` 比 `0.65` 更近。

当前结果刻意保留两个字段：

```text
cosine_distance   = 0.10  # lower is better
cosine_similarity = 0.90  # higher is better
```

它们只是同一个 cosine 关系的两种读法。SQL 排名使用原生 `cosine_distance`，诊断额外给出 similarity 帮助你承接第 10 步的直觉。

不能把这些数与第 11 步的 `fts_rank` 相加：

```text
PostgreSQL FTS rank：词项匹配路线自己的排序值
pgvector distance：向量空间路线自己的距离值
```

两个数字来源、方向和分布都不同。后续融合会使用排名，而不是假装它们处于同一个分数空间。

## 向量必须和 Chunk 身份绑定

下面这段调用来自真实公共入口：

```python
chunk_embeddings = embed_texts(
    [chunk.text for chunk in chunks],
    text_ids=[chunk.chunk_id for chunk in chunks],
    preprocessing_version="retrieval-text-v1",
)

vector_report = PostgresVectorStore().upsert_embeddings(
    chunks,
    chunk_embeddings.records,
)
```

[`PostgresVectorStore.upsert_embeddings`](../../source/packages/rag_core/vector_store/postgres.py) 不只检查“有几个向量”。它要求：

- Chunk 数量和 EmbeddingRecord 数量一致。
- 每条 `EmbeddingRecord.text_id` 等于对应 `chunk_id`。
- `EmbeddingRecord.text` 与 `Chunk.text` 一致。
- 一批记录属于同一个 Embedding 空间。
- 向量真实长度与声明维度一致。
- cosine 路线不接受零向量。

这些是不变量。任何一条不成立，都应该在入库前失败，而不是保存一批无法解释的浮点数。

尤其不能只依赖列表顺序：

```text
chunks  = [A, B]
vectors = [B 的向量, A 的向量]
```

数量完全一样，也能成功写入数据库，但以后 A 会召回 B 的语义。`text_id == chunk_id` 和原文一致性检查就是为了阻止这种“能运行但结果一直不对”的错误。

## Embedding 空间不是只有维度

两组向量都是 1536 维，不代表它们可以比较。

当前最小空间身份是：

```text
provider
+ config_ref
+ model
+ dimensions
+ preprocessing_version
→ embedding_space_ref
```

[`EmbeddingSpace`](../../source/packages/rag_core/vector_store/models.py) 为这些字段生成稳定 fingerprint。例如，下面任一变化都会形成新空间：

- 从模型 A 换到模型 B。
- Provider 不变，但 endpoint 背后的模型实现变化。
- 向量维度变化。
- 从“只嵌入 Chunk 原文”改成“标题 + Chunk 原文”。
- 文本清洗或截断策略升级。

query 也必须使用兼容空间：

```text
旧模型生成的 Chunk vectors
+ 新模型生成的 query vector
→ 维度可能相同
→ 数字可以计算
→ 结果没有可解释意义
```

数据库只知道浮点数组。应用必须阻止这种混用。

当前实验使用同一个 `retrieval-text-v1` 处理 Chunk 与 query，是 V0 的明确取舍，不是所有检索系统的唯一做法。未来若 query 与 document 使用不同但经过模型明确支持的编码方式，也必须把这种关系建模成正式空间契约，不能靠调用者记忆。

## 过滤不是“搜完以后随便删几条”

需求评审助手中的 Chunk 有不同身份：

- 当前有效 Reference Knowledge。
- Historical Material。
- 不允许成为当前证据的资料。
- 不同 `knowledge_scope` 下的资料。

如果用户本轮只允许检索 `after_sale`，其他业务域不应因为向量接近就进入候选。

当前 Dense Retriever 支持最小可见范围：

```text
embedding_space_ref
+ knowledge_scope
+ source_role
+ evidence_eligibility
→ visible Chunk pool
→ distance ranking
```

这一步先回答“谁有资格参加本轮比较”，然后才谈谁更近。

当前诊断同时记录：

- `indexed_chunk_count`：当前 Embedding 空间一共存了多少 Chunk vector。
- `visible_chunk_count`：加上本轮业务过滤后，还剩多少 Chunk。
- `returned_chunk_count`：`candidate_k` 截取后实际返回多少条。

因此，0 条结果不再只有一种解释：

```text
indexed = 0
→ 当前空间尚未入库，或 query 使用了不同空间

indexed > 0, visible = 0
→ Metadata / source role / evidence eligibility 排除了全部 Chunk

visible > 0, returned = 0
→ 应继续检查距离条件或查询执行；当前第 12 步尚未增加 route threshold
```

完整 Metadata Filter、每路阈值、淘汰原因和统一无结果分类会在后续 Retriever 契约中深化。本文先让最小过滤发生在候选范围形成之前。

## 为什么有 exact 以后还需要向量索引

exact search 的成本会随可见向量数量增长。ANN 是 Approximate Nearest Neighbor，中文常译为“近似最近邻”。它尝试少检查一部分向量，更快找到“很可能接近”的候选。

代价是：

```text
更快
↔ 可能漏掉 exact 能找到的近邻
```

pgvector 当前常见两种 ANN 索引：

| 索引 | 直观特点 | 需要注意 |
| --- | --- | --- |
| HNSW | 建立近邻图，通常查询性能和 speed-recall 取舍较好 | 构建更慢、占用更多内存 |
| IVFFlat | 先把向量分组，查询只探测部分组 | 需要训练式分组和 `lists/probes` 调节，候选不足时召回下降 |

当前 V0 机制实验选择 HNSW，不是宣布 HNSW 永远优于 IVFFlat，而是因为小型增量数据上可以先建立一条较少参数的索引观察路线。

## 当前 HNSW 为什么按 Embedding 空间建立

如果一张表里同时有：

```text
模型 A 的 1536 维向量
模型 B 的 1536 维向量
```

只按“都是 1536 维”建一个索引会把两个不同坐标系混进同一近邻结构。即使查询最后过滤模型 B，索引内部候选搜索也可能先被不兼容向量干扰。

当前 [`ensure_hnsw_index`](../../source/packages/rag_core/vector_store/postgres.py) 创建：

```text
embedding::vector(真实维度)
+ WHERE embedding_space_ref = 当前空间
→ 当前空间专属 HNSW partial index
```

这里同时解决两个问题：

1. migration 不必假定所有真实 Embedding 服务都是固定 1536 维。
2. 同维度但不同模型或预处理版本不会进入同一个 HNSW index。

pgvector 的 `vector` HNSW 索引有维度上限。当前实现超过上限时明确失败，要求重新选择存储类型或索引方案，不会偷偷截断向量。

## 索引创建成功，不等于本次查询使用了索引

学习数据库时很容易形成一个误解：

```text
CREATE INDEX 成功
→ 所有查询都会使用这个索引
```

PostgreSQL Planner 会比较不同执行计划的成本。当前 fixture 只有很少的 Chunk，顺序读完几行可能比进入 HNSW 更便宜。因此你可能看到：

```text
HNSW index 已存在
index_used = false
plan 包含 Seq Scan
```

这不等于索引坏了。

当前 HNSW 查询可以开启 `inspect_plan=True`，执行 `EXPLAIN (FORMAT JSON)` 并记录：

- index name。
- `index_used`。
- plan node types。

判断顺序应该是：

1. 索引对象是否存在，定义是否属于当前空间和 cosine operator class。
2. 查询表达式是否与索引表达式一致。
3. 当前空间与 Metadata Filter 是否匹配。
4. Planner 是否因为数据量太小而选择顺序扫描。
5. 若要证明性能收益，是否有足够代表性的数据量和独立性能实验。

不要为了让截图出现 `Index Scan` 就把小 fixture 复制几万遍，然后宣称检索质量提升。索引计划观察和业务检索质量是两种证据。

## ANN 与 Metadata Filter 还有一个自然边界

在 SQL 语义上，`WHERE knowledge_scope = ...` 明确限制了最终可见结果。但 ANN 索引内部可能先扫描有限的近邻，再应用普通 Metadata 条件。

假设 HNSW 初步检查 40 个近邻，而其中只有 10% 属于当前 `knowledge_scope`，最终可能只剩大约 4 条，即使 `candidate_k=10`。

pgvector 提供 iterative index scan 等机制继续扩大扫描，但这仍是速度、召回、过滤比例和参数之间的取舍。

第 12 步只需要建立两个判断：

- exact 是当前小数据的正确性基线。
- ANN + filter 可能少返回候选，不能看到少于 `candidate_k` 就直接认为知识中没有答案。

完整的过滤顺序、候选数量和无结果原因会在统一 Retriever 诊断中继续处理。

## 真实代码怎样推进一次 Dense Retrieval

### 公共入口

一次完整机制实验使用三个公共对象：

```python
chunk_store = PostgresChunkStore(dsn)
vector_store = PostgresVectorStore(dsn)
retriever = PostgresDenseRetriever(dsn)
```

它们的责任分别是：

- `PostgresChunkStore`：保存 lexical 与 dense 共用的 Chunk 原文、来源和 Metadata。
- `PostgresVectorStore`：保存 Chunk 对应的向量与 Embedding 空间。
- `PostgresDenseRetriever`：使用 query vector 过滤、计算距离和返回候选。

第 11 步的 `PostgresFTSRetriever.upsert_chunks` 仍可用，但内部委托给共享 `PostgresChunkStore`。这次拆分不是为了增加类，而是避免出现“Dense Retrieval 必须借用 FTS 类才能保存 Chunk”的错误责任关系。

### 核心调用链

真实实验入口是 [`inspect_dense_retrieval.py`](../../source/demos/rag_retrieval_lab/inspect_dense_retrieval.py)：

```text
load_retrieval_chunks
→ 第 8 步 Loader
→ 第 9 步 structure-aware Chunking
→ PostgresChunkStore.upsert_chunks

Chunk.text[]
→ 第 10 步 LLMClient.embed（真实服务）
→ EmbeddingRecord[]
→ PostgresVectorStore.upsert_embeddings
→ rag_chunk_embeddings

query text[]
→ 同一真实 Embedding 空间
→ query EmbeddingRecord[]
→ PostgresDenseRetriever.search
→ DenseHit[] + DenseDiagnostics
```

这里没有新增 Embedding Provider。`rag_core` 继续复用 `llm_core`，真实鉴权、HTTP、限流、超时和供应商错误仍由统一调用层处理。

### `DenseHit` 保存什么

```text
DenseHit
├── chunk_id / document_id / document_version
├── content
├── source_role / evidence_eligibility
├── business_metadata
├── cosine_distance
├── cosine_similarity
└── route_rank
```

它既保留距离，也保留回查来源需要的身份。后续不能只传一段 `content` 字符串，否则 RRF 去重、Context 来源标记和 Citation Candidate 都找不到稳定对象。

### 正常结果与诊断分开

`DenseSearchResult` 包含：

```text
hits         → 业务候选
diagnostics  → 本次检索怎样执行
```

诊断保存空间、范围、数量、方向、模式、索引和计划。用户最终看到的业务报告不需要展示全部字段，但学习实验和运行记录必须能回答“为什么是这些候选”。

## 使用同一批问题观察两条路线

共享问题位于 [`retrieval_queries.json`](../../review_assistant/fixtures/v0/retrieval/retrieval_queries.json)。第 11、12 步使用同一个文件和同一组 Chunk，不通过更换样例制造某条路线更强。

运行前先预测：

| 问题 | Lexical 预测 | Dense 预测 |
| --- | --- | --- |
| `source_channel` | 精确标识强项 | 可能命中，但排名未必比 lexical 稳定 |
| `申请售后` | 词面直接命中 | 语义也应接近 |
| `发起逆向服务` | 可能因缺少共同词面而漏掉 | 有机会补回“申请售后”规则 |
| `虚拟商品 售后` | 能命中包含这些词的例外 | 也可能很近，但距离不解释否定 |
| `售前活动入口` | 可能空或出现弱词面噪声 | “售前/售后”主题接近，可能出现语义噪声 |

真实实验命令由 [rag_retrieval_lab README](../../source/demos/rag_retrieval_lab/README.md) 维护。最小入口是：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py
```

主路径会调用真实 Embedding 和真实 PostgreSQL，不在缺少 key、migration 或 extension 时返回本地假结果。

观察时不要只看“有没有命中”，至少检查：

1. `embedding_space_ref` 是否与 Chunk 入库一致。
2. `indexed / visible / returned` 数量在哪里发生变化。
3. `cosine_distance` 的方向是否按越小越近阅读。
4. top Chunk 的原文是否真的与问题相关。
5. 精确字段、同义问题、否定问题和噪声问题分别表现怎样。
6. HNSW 是否真的被 Planner 选择。

## 三个结果很像，原因却完全不同

### 1. `发起逆向服务` 在 lexical 为 0，dense 找回售后规则

这说明：

```text
两边字面不同
→ lexical 没有足够共同词项
→ Embedding 空间仍认为意思接近
→ dense 补回候选
```

它能证明两路有互补可能，不能证明 Dense 已经足够上线。还要检查其他问题、噪声、成本和延迟。

### 2. `虚拟商品不进入售后` 距离很近

表现：例外 Chunk 可能排在前面。

这不一定是错误。用户确实在问虚拟商品和售后，它在主题上很相关。Dense Retriever 的任务是召回相关原文，不是独立完成否定推理。

后续 Context 与模型需要看到完整句子，可信生成和 Citation 校验还要继续约束结论。

### 3. 过滤后返回 0 条

先查看：

```text
indexed_chunk_count
visible_chunk_count
```

如果 indexed 有值而 visible 为 0，优先检查 `knowledge_scope`、来源角色和证据资格。不要先重建向量，也不要先更换模型。

## 真实故障怎样定位

| 表现 | 优先检查 | 说明 |
| --- | --- | --- |
| 缺少 `OPENAI_EMBEDDING_API_KEY` | Embedding 配置 | 请求未获得真实向量，不进入数据库检索 |
| Embedding endpoint 404 | 是否把仅聊天平台当作 Embedding 服务 | Provider 能力或模型配置问题 |
| `migration_required` | 是否按顺序执行 `0001`、`0002` | 表、extension 或运算符缺失 |
| `permission_denied` | 应用 Role 是否能建表、写入或创建 index | 不应改用超级用户长期运行 |
| Chunk 外键失败 | 是否先由 `PostgresChunkStore` 保存 Chunk | 向量不能成为无来源的悬空记录 |
| `text_id` 与 `chunk_id` 不同 | Embedding 结果与 Chunk 顺序/绑定 | 应用契约错误，不是模型质量问题 |
| vector 长度与 dimensions 不同 | Provider 响应或本地记录构造 | 在入库前拒绝 |
| query 空间没有已索引 Chunk | Provider、模型、维度、预处理是否变化 | 新空间需要重新生成 Chunk vectors |
| HNSW `index_used=false` | 查询计划和数据规模 | 索引可能正常但 Planner 没选择 |
| 语义接近但业务约束相反 | 查看完整原文 | Dense 的自然边界，不是数据库异常 |

错误定位顺序要沿数据流推进：

```text
query 是否成功生成真实向量
→ 空间身份是否一致
→ Chunk vector 是否已入库
→ Metadata 后是否还有可见 Chunk
→ distance 和排序方向是否正确
→ ANN index 是否存在且可能被使用
→ 候选原文是否暴露语义边界
```

不要一看到结果差就直接调 Prompt。此时 Prompt 还没有进入链路。

## 测试能证明什么，不能证明什么

[`test_pgvector_dense.py`](../../source/packages/rag_core/tests/test_pgvector_dense.py) 使用人工小向量验证确定性逻辑，例如：

- 空间 fingerprint 会随模型或预处理变化。
- 声明维度与真实长度不一致会被拒绝。
- Chunk 与 EmbeddingRecord 必须按稳定 ID 绑定。
- cosine distance 能正确映射为 similarity。
- Metadata 前后数量进入诊断。
- 配置独立数据库后，真实 pgvector 能完成 exact search。

这些测试可以使用人工向量，因为它们验证的是应用和数据库契约。

它们不能证明：

- 真实模型能理解“逆向服务”。
- Dense 比 lexical 更好。
- HNSW 对当前数据规模有性能收益。
- 候选能支持最终评审结论。

这些结论必须来自真实 Embedding 实验和后续固定评估，不能用单元测试通过替代。

## pgvector 和 Psycopg 封装了什么

pgvector 封装：

- PostgreSQL `vector` / `halfvec` 等类型。
- 距离运算符。
- HNSW、IVFFlat operator class 和索引访问方法。
- 向量相关函数。

`pgvector-python` 为 Psycopg 封装：

- Python vector 与 PostgreSQL vector 的参数适配。
- 连接上的 vector 类型注册。

它们没有替应用解决：

- 哪段文本属于哪个 `chunk_id`。
- 哪些字段构成 Embedding 空间。
- 模型变化后何时重建。
- 哪些 Metadata 控制可见范围。
- distance 的业务阈值应该是多少。
- ANN 参数是否达到质量和延迟目标。
- 候选是否真的支持最终结论。

框架和 extension 让向量查询可执行，应用契约让查询结果可解释。

## 修改题：给 Chunk 加标题再做 Embedding

需求变化：为了让短 Chunk 保留章节语义，准备把 Embedding 输入从：

```text
Chunk.text
```

改成：

```text
标题路径 + "\n" + Chunk.text
```

修改前先回答：

1. 原始 `Chunk.text` 是否应该一起改变？为什么？
2. `preprocessing_version` 是否必须升级？
3. 新向量能否继续写入旧 `embedding_space_ref`？
4. 哪些 Chunk 需要重新生成向量？
5. lexical index 是否也必须重建？
6. 共享问题集中的哪些 Case 可能改善，哪些可能因标题噪声退化？
7. 如何保留旧实验结果，避免看到新结果后才选择有利样例？

建议判断：

- 原始 Chunk 和来源定位不应为了 Embedding 前缀而被篡改。
- Embedding 输入预处理发生变化，必须升级版本并形成新空间。
- 当前资料需要重新生成向量。
- lexical 是否重建取决于 lexical_text 是否变化，不能因为 Dense 改动而机械重建全部索引。
- 是否更好必须使用相同问题集比较，不由单条同义问题决定。

这道修改题训练的是“需求变化后应该改哪一层”，不是只把字符串拼接进去让程序继续运行。

## 判断是否已经掌握

不看正文，尝试回答：

1. 为什么 `发起逆向服务` 查不到时，不能直接说 PostgreSQL 坏了？怎样用同一次实验验证？
2. 第 10 步的 pairwise similarity 与第 12 步 Dense Retrieval 有什么区别？
3. Embedding Provider、Vector Store、Dense Retriever 和 Vector Index 分别负责什么？
4. 为什么 `DenseHit` 不是 Evidence？
5. cosine similarity 与 pgvector cosine distance 的方向有什么不同？
6. 为什么 FTS rank 不能与 cosine distance 直接相加？
7. 哪些字段共同组成当前 Embedding 空间？
8. 为什么同维度向量仍可能不能比较？
9. `text_id == chunk_id` 守住了什么错误？
10. exact search 为什么应该保留为 ANN 的正确性基线？
11. HNSW 改善的是什么，不能改善什么？
12. 为什么索引存在但 `index_used=false` 不一定是故障？
13. indexed 大于 0、visible 等于 0 时先检查哪里？
14. ANN 与 Metadata Filter 一起使用时为什么可能少于 `candidate_k`？
15. 换模型或 Embedding 预处理后为什么需要重建 Chunk vectors？
16. 哪些结论能由离线测试证明，哪些必须运行真实 Embedding？

如果你能画出 `Chunk → Embedding → pgvector → DenseHit`，运行真实实验，解释距离方向、空间身份、exact/HNSW 差异，并完成预处理修改题，就达到本节需要的 Dense Retrieval 掌握程度。

## 本节交付与边界

本节已经交付：

- lexical 与 dense 共用的 PostgreSQL Chunk 存储入口。
- pgvector extension 与 Chunk embedding migration。
- Chunk、向量和 Embedding 空间的稳定绑定。
- exact cosine Dense Retrieval。
- 按真实空间和维度建立的 HNSW partial index。
- indexed / visible / returned、距离方向和查询计划诊断。
- 与第 11 步完全相同的 Chunk 和共享问题集。
- 真实 Embedding + PostgreSQL 实验入口。
- 离线契约测试与显式真实 pgvector 集成测试入口。

仍未交付：

- lexical 与 dense 的 RRF 融合。
- 每路阈值、完整 Metadata Filter 和统一淘汰原因。
- 最终 `RetrievalResult` 与 `RetrievalReport`。
- Context Construction 适配。
- 结构化评审生成与 Citation Candidate。
- Citation 支持性校验和证据充分性判断。
- 固定数据集上的完整检索评估。

完成后回到 [标准学习路径](../learning-path.md)，由唯一课表决定后续内容。

## 官方参考

- [pgvector：Getting Started、距离运算符、HNSW、IVFFlat 与过滤](https://github.com/pgvector/pgvector)
- [pgvector-python：Psycopg 3 类型注册与查询](https://github.com/pgvector/pgvector-python)
- [PostgreSQL：CREATE EXTENSION](https://www.postgresql.org/docs/current/sql-createextension.html)
- [PostgreSQL：CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html)
