# 步骤 12：pgvector Dense Retrieval

先按 [`review_assistant/README.md`](../../../../review_assistant/README.md#postgresql-本地准备) 执行 `0001`、`0002` migration，并配置真实 `DATABASE_URL`、`OPENAI_EMBEDDING_API_KEY`、Embedding endpoint 和 model。

运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py --search-mode exact
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py --verbose
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py --log-format json
```

观察 Provider、模型、维度、`embedding_space_ref`、Chunk/query latency、exact/HNSW 距离方向、`index_used` 和查询计划。小数据集选择顺序扫描不等于索引损坏。

```text
load_retrieval_chunks
→ PostgresChunkStore.upsert_chunks
→ LLMClient.embed（Chunk）
→ PostgresVectorStore.upsert_embeddings
→ LLMClient.embed（query）
→ PostgresDenseRetriever.search
→ DenseHit + DenseDiagnostics
```

读码入口：[`inspect_dense_retrieval.py`](../inspect_dense_retrieval.py)、[`vector_store/postgres.py`](../../../packages/rag_core/vector_store/postgres.py)、[`retrieval/postgres_dense.py`](../../../packages/rag_core/retrieval/postgres_dense.py)、[`0002_add_pgvector_embeddings.sql`](../../../../review_assistant/infra/migrations/0002_add_pgvector_embeddings.sql)。
