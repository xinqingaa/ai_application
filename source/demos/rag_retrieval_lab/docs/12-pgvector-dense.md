# 步骤 12：pgvector Dense Retrieval

> 这是第 12 步的操作文档。它回答“怎样准备 pgvector、运行 Dense Retrieval、阅读输出和做 exact/HNSW 对照”，不重复机制正文的完整原理。
>
> - 机制：[pgvector、Dense Retrieval 与向量索引](../../../../course/mechanisms/vector-store-and-pgvector.md)
> - 第 10 步概念：[Embedding 表示与向量相似度](../../../../course/mechanisms/embedding-and-similarity.md)
> - 第 11 步对照：[Lexical Retrieval、BM25 边界与 PostgreSQL FTS](../../../../course/mechanisms/lexical-retrieval.md)

第 11 步按词查找，第 12 步按向量距离查找。两步使用同一批 Chunk 和 Query，但检索维度不同：第 11 步比较词项，第 12 步比较 Embedding 空间中的位置。

## 1. 运行前准备

第 11 步已经准备好 PostgreSQL、`DATABASE_URL`、Role、Database 和 `0001` migration。本步骤在同一个数据库上继续执行 `0002`，并增加真实 Embedding 服务配置。

### 1.1 执行 pgvector migration

```bash
set -a && source .env && set +a
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f review_assistant/infra/migrations/0002_add_pgvector_embeddings.sql
```

`0002` 做两件事：启用 PostgreSQL 的 `vector` 扩展；创建 `review_assistant.rag_chunk_embeddings`，保存 Chunk 向量和 Embedding 空间身份。

确认扩展和表：

```bash
psql "$DATABASE_URL" -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
psql "$DATABASE_URL" -c "\dt review_assistant.rag_chunk_embeddings"
```

如果这里失败，先排查 PostgreSQL 安装是否包含 pgvector；不要把 migration 失败当成“Embedding 效果不好”。

### 1.2 配置真实 Embedding

`.env` 至少需要：

```dotenv
DATABASE_URL=postgresql://...
OPENAI_EMBEDDING_API_KEY=真实凭证
OPENAI_EMBEDDING_BASE_URL=支持 embeddings 的 endpoint
OPENAI_EMBEDDING_MODEL=支持 embeddings 的模型
```

Chat 的 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 不会自动代替 Embedding 配置。Embedding 服务必须真正支持 embeddings 端点；缺少 key、404、鉴权失败或限流会以错误结束，不会回退到假向量。

## 2. 按顺序运行三种模式

程序会读取固定 fixture，写入 Chunk，调用真实 Embedding 生成 Chunk 向量，再把 Query 转成向量并检索。

### 2.1 先跑 exact：正确性基线

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py \
  --search-mode exact --verbose
```

`exact` 会检查当前可见范围中的全部向量，按 cosine distance 从小到大排序。它最适合先确认“向量、空间、过滤和候选结果都能正常工作”。

### 2.2 再跑 HNSW：索引路线

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py \
  --search-mode hnsw --verbose
```

程序会为当前 Embedding 空间创建或复用 HNSW 索引，然后查询索引。HNSW 是近似最近邻路线，目标是减少大规模数据的查询成本，不保证每次都和 exact 返回完全相同的候选。

### 2.3 最后跑 compare：并排比较

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py \
  --search-mode compare --verbose
```

这是推荐的观察方式：同一次运行中分别执行 exact 和 HNSW，比较距离、Chunk 顺序和 `index_used`。小 fixture 很可能选择顺序扫描，因此 `index_used=no` 不代表 HNSW 创建失败。

JSON Lines 适合保存和逐字段比较：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py \
  --search-mode compare --log-format json
```

## 3. 先读懂一次完整调用

```text
load_retrieval_chunks
→ PostgresChunkStore.upsert_chunks
→ LLMClient.embed（Chunk）
→ PostgresVectorStore.upsert_embeddings
→ LLMClient.embed（Query）
→ PostgresDenseRetriever.search
→ DenseHit + DenseDiagnostics
```

这条链和第 11 步最大的不同是：查询不是拆成词交给 FTS，而是先调用同一 Embedding 空间生成 Query vector，再和数据库中的 Chunk vectors 计算 distance。

## 4. 终端输出怎么读

### 4.1 运行标题和入库信息

常见标题类似：

```text
dataset=v0-retrieval-exploration-1.0.0 · mode=compare · candidate_k=5
chunks=2 · vectors=2 · space=...
provider=... · model=... · dimensions=... · preprocessing=retrieval-text-v1
chunk_embedding=... ms · query_embedding=... ms
HNSW index=... · setup=... ms
```

| 字段 | 含义 |
| --- | --- |
| `dataset` | 固定资料和 Query 探针版本 |
| `mode` | `exact`、`hnsw` 或同时比较的 `compare` |
| `candidate_k` | 每个 Query 最多返回多少个 DenseHit |
| `chunks` | 写入或更新的 Chunk 数 |
| `vectors` | 写入的向量数；应与参与 Embedding 的 Chunk 对得上 |
| `space` | 当前 Embedding 空间的稳定身份 |
| `provider` / `model` | 真实 Embedding 服务和模型 |
| `dimensions` | 每个向量的维度；query 和 Chunk 必须兼容 |
| `preprocessing` | 生成向量前的文本处理版本 |
| `chunk_embedding` | 为资料生成向量的耗时 |
| `query_embedding` | 为 Query 生成向量的耗时 |
| `HNSW index` / `setup` | HNSW 索引名称和创建或确认耗时 |

这些字段回答“向量从哪里来、是否属于同一空间、耗时在哪里”，不直接代表检索质量。

### 4.2 查询汇总表

表格标题会注明：`cosine distance 越小越近`。

| 字段 | 含义 |
| --- | --- |
| `Query` | 原始用户问题 |
| `Group` | 固定探针的观察分组 |
| `Hits` | 实际返回的候选数 |
| `Top distance` | 第一名的 cosine distance；越小越近 |
| `Top Chunk` | 第一名 Chunk 的原文摘要 |
| `HNSW used` | HNSW 查询是否实际使用了索引计划 |
| `Observe` | 当前探针要观察的现象，不是自动评分 |

不要把 `Top distance` 和第 11 步的 `fts_rank` 相加，也不要把距离越小误读成结果越正确。

### 4.3 `--verbose` 详细区

每个 Query 下会按路线显示类似：

```text
exact: indexed=2 · visible=2 · returned=2 · index_used=false · plan=not inspected
hnsw: indexed=2 · visible=2 · returned=2 · index_used=false · plan=Seq Scan → ...
```

| 字段 | 含义 |
| --- | --- |
| `exact` / `hnsw` | 当前是哪条检索路线 |
| `indexed` | 当前 Embedding 空间中已保存的向量数量 |
| `visible` | 经过 `knowledge_scope`、`source_role`、`evidence_eligibility` 过滤后可参与比较的数量 |
| `returned` | `candidate_k` 截断后实际返回的数量 |
| `index_used` | PostgreSQL 这次是否采用 HNSW 索引 |
| `plan` | 查询计划节点；只有 HNSW 检查计划时才有意义 |
| `Distance` | cosine distance，越小越近 |
| `Similarity` | 便于承接第 10 步直觉的 `1 - distance`，越大越近 |
| `Chunk` | 稳定 Chunk ID |
| `Content` | 命中 Chunk 原文摘要 |

重点按下面路径读：

```text
space
→ indexed
→ visible
→ distance
→ returned
→ index_used / plan
```

### 4.4 0 条结果或错误怎么判断

| 现象 | 优先解释 |
| --- | --- |
| `indexed=0` | 当前空间没有向量，或空间身份不一致 |
| `indexed>0`、`visible=0` | Metadata、来源角色或证据资格过滤掉全部 Chunk |
| `visible>0`、`returned=0` | 先检查查询执行、空间和候选参数；本步骤没有静默阈值 |
| `dimension mismatch` | Query 与 Chunk 向量维度不一致 |
| Embedding `AUTH` / `404` / `RATE_LIMIT` | 真实 Provider 配置或服务故障 |
| `index_used=no` | 小数据集上顺序扫描可能更便宜，不等于索引损坏 |

## 5. 做三组对照

### 对照一：exact 与 HNSW

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py \
  --search-mode compare --candidate-k 5 --verbose
```

预测：两条路线通常会返回相近候选，但 HNSW 可能因近似搜索或过滤出现差异；当前只有两个 Chunk 时，`index_used=no` 很正常。看每个 Query 下两行路线的 `Distance`、`Chunk` 顺序和 `index_used`，不要只看有没有结果。

### 对照二：改变 `candidate_k`

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py \
  --search-mode exact --candidate-k 1 --verbose

uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py \
  --search-mode exact --candidate-k 5 --verbose
```

只改变候选上限。`indexed` 和 `visible` 不应因为 `candidate_k` 改变，`returned` 和显示的候选数可以改变。

### 对照三：和第 11 步并排观察

对同一个 Query，先运行第 11 步的 lexical 命令，再运行本步骤的 exact 命令。记录：

```text
Lexical：共同词项、fts_rank、候选 Chunk
Dense：cosine_distance、cosine_similarity、候选 Chunk
```

`发起逆向服务` 可能词面漏召回而向量找回售后规则；`source_channel` 可能是词面路线更稳定；“虚拟商品不进入售后”即使距离很近，也不代表系统理解了否定关系。对照的目的不是证明某一路永远更好，而是观察两种表示如何互补、又各自在哪里失效。

## 6. SQL 与 Python 命令的区别

直接 SQL 可以观察数据库中的向量列、距离表达式和查询计划；Python 命令还负责读取 fixture、调用真实 Embedding、保存空间身份、应用可见范围并输出 DenseDiagnostics。

```text
SQL：数据库层的向量匹配
Python 命令：真实应用链路 + 数据库层 + Provider 诊断
```

因此 SQL 适合排查“表里是否有向量、距离怎么算、计划是什么”，Python 命令适合确认“应用生成了什么向量、使用了哪个空间、最终返回了哪些候选”。两者结果不一致时，先检查 Python 输出中的 `space`、`dimensions`、`visible` 和 `search_mode`。

## 7. 读码入口

1. [`inspect_dense_retrieval.py`](../inspect_dense_retrieval.py)
2. [`vector_store/postgres.py`](../../../packages/rag_core/vector_store/postgres.py)
3. [`retrieval/postgres_dense.py`](../../../packages/rag_core/retrieval/postgres_dense.py)
4. [`0002_add_pgvector_embeddings.sql`](../../../../review_assistant/infra/migrations/0002_add_pgvector_embeddings.sql)

完整原理、自然边界和修改题见[机制正文](../../../../course/mechanisms/vector-store-and-pgvector.md)。
