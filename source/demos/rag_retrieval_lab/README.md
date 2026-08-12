# rag_retrieval_lab

> 课表位置：[标准学习路径](../../../course/learning-path.md) V0 步骤 10 起。步骤 10 先读 [Embedding 表示与向量相似度](../../../course/mechanisms/embedding-and-similarity.md)，步骤 11 阅读 [Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索](../../../course/mechanisms/lexical-retrieval.md)，步骤 12 阅读 [pgvector、Dense Retrieval 与向量索引](../../../course/mechanisms/vector-store-and-pgvector.md)，步骤 13 阅读 [多路召回与 RRF 融合](../../../course/mechanisms/multi-retrieval-and-rrf.md)，步骤 14 阅读 [Top-k、阈值、Metadata Filter 与 Retrieval 诊断](../../../course/mechanisms/retriever-contract.md)。

本实验负责运行方式、输出解读和代码阅读路径。机制原理在课程正文；真实 Embedding HTTP 调用位于 [`llm_core.LLMClient.embed`](../../packages/llm_core/client/service.py)，RAG 侧表示与成对相似度位于 [`rag_core.embedding`](../../packages/rag_core/embedding/)。

## 步骤 10：成对相似度

在仓库根目录运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py
```

主路径必须显式配置真实 Embedding 凭证 `OPENAI_EMBEDDING_API_KEY`，并按需要配置 `OPENAI_EMBEDDING_BASE_URL` / `OPENAI_EMBEDDING_MODEL`。Embedding 不自动复用 chat 的 key 或 base URL。

注意：`OPENAI_BASE_URL` 只服务 chat。若 chat 使用 DeepSeek 等不提供 `/embeddings` 的平台，必须为 Embedding 单独选择支持该端点的服务。缺少专用 key 时返回 `AUTH`；显式配置了不支持 `/embeddings` 的 endpoint 或不存在的模型时可能返回 `404` / `PROVIDER_ERROR`。实验不会静默改用 mock。

默认输出展示：

- 使用的 embedding Provider、模型、维度、预处理版本、latency 和 usage
- 探针文本及其分组
- 若干 focus pairs 的成对分数与预期说明

这些分数只描述表示空间距离，不代表已经完成知识库检索，也不代表证据充分或评审正确。

查看全部成对分数：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --verbose
```

切换度量：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --metric euclidean
```

JSON Lines：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --log-format json
```

探针材料位于 [`review_assistant/fixtures/v0/retrieval/embedding_probes.json`](../../../review_assistant/fixtures/v0/retrieval/embedding_probes.json)，继续使用“售后入口与订单状态”业务域。

## Demo 调用路径

```text
main
→ 读取 embedding_probes.json
→ LLMClient.embed（真实服务）
→ EmbeddingRecord[]
→ pairwise_similarity
→ focus pairs / compact / verbose / json 呈现
```

本步只观察探针句对的表示距离。匹配一整库候选、持久化向量、多路融合和检索诊断，由课表后续步骤再进入。

## 步骤 11：PostgreSQL FTS Lexical Retrieval

先按 [`review_assistant/README.md`](../../../review_assistant/README.md) 安装并初始化真实 PostgreSQL、配置 `DATABASE_URL`、执行 migration。实验不会自动安装服务、自动建表，也不会回退到 SQLite 或内存检索。

在仓库根目录运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py
```

默认实验会：

1. 用第 8 步 Loader 读取 `order_rules.md`。
2. 用第 9 步 structure-aware 策略生成真实 Chunk。
3. 使用同一 `LexicalAnalyzer` 处理 Chunk 与查询。
4. 幂等 upsert 到 `review_assistant.rag_chunks`。
5. 用 PostgreSQL `websearch_to_tsquery`、`@@` 和 `ts_rank` 返回候选。
6. 比较精确标识、词面一致、自然问句、同义改写、否定规则和正常噪声。

查看 `tsquery`、PostgreSQL lexeme、命中词和每个候选：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py --verbose
```

比较召回型 OR 与严格 AND：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py --query-operator and --verbose
```

JSON Lines：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py --log-format json
```

默认输出包含：

- 原始查询、应用词项、PostgreSQL query lexeme 和最终 `tsquery`
- `lexical_config_ref`、query operator 和 `candidate_k`
- 命中数、返回数、稳定 `chunk_id` 和路由排名
- 原生 `fts_rank`、方向和匹配词
- 真实数据库错误的 stage、code 和 message

探针位于共享的 [`retrieval_queries.json`](../../../review_assistant/fixtures/v0/retrieval/retrieval_queries.json)。它是探索性机制材料，不是冻结的 V0 acceptance 集，也不证明最终 RAG 质量。步骤 12 继续使用同一批问题，避免通过更换样例制造路线差异。

### 步骤 11 调用路径

```text
main
→ load_document
→ chunk_document
→ LexicalAnalyzer.analyze_document
→ PostgresFTSRetriever.upsert_chunks
→ PostgreSQL generated tsvector + GIN
→ LexicalAnalyzer.analyze_query
→ websearch_to_tsquery + @@ + ts_rank
→ LexicalSearchResult
```

### 步骤 11 读码顺序

1. [`inspect_lexical_retrieval.py`](inspect_lexical_retrieval.py)：看真实实验怎样组合已有 Loader、Chunker 和 Retriever。
2. [`lexical/analyzer.py`](../../packages/rag_core/lexical/analyzer.py)：看中文词项、技术标识和配置版本。
3. [`retrieval/postgres_fts.py`](../../packages/rag_core/retrieval/postgres_fts.py)：看参数化 SQL、事务、upsert、query 和错误转换。
4. [`0001_create_rag_chunks.sql`](../../../review_assistant/infra/migrations/0001_create_rag_chunks.sql)：看表、约束、生成列和索引。
5. [`test_lexical.py`](../../packages/rag_core/tests/test_lexical.py) 与 [`test_postgres_fts.py`](../../packages/rag_core/tests/test_postgres_fts.py)：看确定性契约和真实集成边界。

## 步骤 12：pgvector Dense Retrieval

先按 [`review_assistant/README.md`](../../../review_assistant/README.md) 执行 `0001` 与 `0002` migration，并配置真实 `DATABASE_URL`、`OPENAI_EMBEDDING_API_KEY` 和对应 Embedding endpoint/model。

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py
```

默认 `compare` 模式会：

1. 使用与步骤 11 完全相同的 Loader、Chunk 策略和共享查询集。
2. 调用真实 Embedding 服务分别生成 Chunk 向量和 query 向量。
3. 将向量连同 `chunk_id`、模型、维度和预处理版本写入 pgvector。
4. 运行 exact 正确性基线。
5. 为当前 Embedding 空间建立 HNSW partial index，再运行索引可用查询。
6. 记录 PostgreSQL 是否真的选择该索引；小数据集选择顺序扫描不等于索引损坏。

只运行 exact：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py --search-mode exact
```

查看每个候选、可见数量和查询计划：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py --verbose
```

JSON Lines：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py --log-format json
```

默认输出包含：

- Provider、模型、维度、预处理版本和 `embedding_space_ref`
- Chunk 与 query 的真实 Embedding latency
- exact / HNSW 的 `cosine_distance`、方向和 route rank
- 索引名称、`index_used` 与查询计划节点
- 当前空间已索引数量、Metadata Filter 后可见数量和实际返回数量

步骤 12 的真实调用路径：

```text
load_retrieval_chunks
→ PostgresChunkStore.upsert_chunks
→ LLMClient.embed（Chunk）
→ PostgresVectorStore.upsert_embeddings
→ LLMClient.embed（query）
→ PostgresDenseRetriever.search
→ DenseHit + DenseDiagnostics
```

读码顺序：

1. [`inspect_dense_retrieval.py`](inspect_dense_retrieval.py)
2. [`vector_store/models.py`](../../packages/rag_core/vector_store/models.py)
3. [`vector_store/postgres.py`](../../packages/rag_core/vector_store/postgres.py)
4. [`retrieval/postgres_dense.py`](../../packages/rag_core/retrieval/postgres_dense.py)
5. [`0002_add_pgvector_embeddings.sql`](../../../review_assistant/infra/migrations/0002_add_pgvector_embeddings.sql)
6. [`test_pgvector_dense.py`](../../packages/rag_core/tests/test_pgvector_dense.py)

## 步骤 13：Lexical + Dense + RRF

完成步骤 12 的真实依赖配置后运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py
```

默认使用同一批 Chunk、同一查询和 exact dense，仅增加 RRF 作为主要变化变量。查看每个融合候选的两路名次、倒数贡献和原生值：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --verbose
```

切换平滑常数或 dense 索引路线时，属于新的融合/检索配置：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --rrf-k 20
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --dense-mode hnsw
```

JSON Lines：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --log-format json
```

实验出现任一路真实失败时，会保留该路 `FAILED` 与已有候选，但进程返回非零状态，不把部分结果伪装成完整融合成功。

## 步骤 14：固定 Retriever 控制与诊断

步骤 14 继续使用同一批 Chunk、问题和真实服务，把前几步组合成固定控制顺序：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py
```

默认不设置 route threshold，先观察基线。展开每个原生阈值决策和 `final_top_k` 决策：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --verbose
```

一次只改变一个变量，例如：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --lexical-candidate-k 2 --verbose
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --dense-max-distance 0.35 --verbose
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --final-top-k 1 --verbose
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --knowledge-scope missing_scope
```

输出按 `pre_filter → route_candidate_k → route_threshold → rrf → final_top_k` 记录数量变化，并区分可见范围为空、两路无匹配、全部低于阈值和真实路由失败。阈值是当前实验输入，不是项目永久最佳值。

JSON Lines：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_retrieval_contract.py --log-format json
```

## 从 Demo 进入核心代码

1. [`inspect_embedding.py`](inspect_embedding.py)：看探针如何进入公共 API。
2. [`llm_core/client/service.py`](../../packages/llm_core/client/service.py)：看 `embed` 的 role 守卫与空文本拒绝。
3. [`llm_core/providers/openai_compat.py`](../../packages/llm_core/providers/openai_compat.py)：看真实 `embeddings.create` 与错误映射。
4. [`rag_core/embedding/models.py`](../../packages/rag_core/embedding/models.py)：看 `EmbeddingRecord`、度量方向和 Embedding 空间一致性校验。
5. [`tests/test_client_embed.py`](../../packages/llm_core/tests/test_client_embed.py) 与 [`tests/test_embedding.py`](../../packages/rag_core/tests/test_embedding.py)：看离线契约。

## 运行测试

```bash
uv run pytest source/packages/llm_core/tests/test_client_embed.py source/packages/rag_core/tests/test_embedding.py -q
```

步骤 11 的离线测试：

```bash
uv run pytest source/packages/rag_core/tests/test_lexical.py source/packages/rag_core/tests/test_postgres_fts.py -q -m "not integration"
```

步骤 12 的离线契约测试：

```bash
uv run pytest source/packages/rag_core/tests/test_pgvector_dense.py -q -m "not integration"
```

步骤 13 的确定性融合测试：

```bash
uv run pytest source/packages/rag_core/tests/test_rrf.py -q
```

步骤 14 的固定控制与诊断测试：

```bash
uv run pytest source/packages/rag_core/tests/test_hybrid_retriever.py -q
```

配置独立测试库后运行真实 PostgreSQL 集成测试：

```bash
TEST_DATABASE_URL="$DATABASE_URL" uv run pytest source/packages/rag_core/tests/test_postgres_fts.py -q -m integration
```

使用独立测试库运行真实 pgvector 集成测试：

```bash
uv run pytest source/packages/rag_core/tests/test_pgvector_dense.py -q -m integration
```

不要对包含重要数据的数据库直接复用这条学习命令；集成测试会删除自己写入的测试 Chunk，但不会替你隔离其他数据。

## 当前实验不观察什么

- 步骤 10 不对知识库候选做匹配与排名；步骤 11 已建立 PostgreSQL FTS
- 步骤 12 已持久化向量并建立按 Embedding 空间隔离的 pgvector HNSW 索引
- 不装配模型上下文，也不用最终评审回答判断 Embedding 质量
- 不允许主路径 mock embedding 结果冒充真实模型效果
- 步骤 13 已实现应用侧 RRF；步骤 14 已实现统一控制顺序、每路阈值、`final_top_k` 和完整淘汰原因
- 仍不装配最终 Context，也不把检索分数当作事实权威性
