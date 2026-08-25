# rag_retrieval_lab

这是第一阶段固定 RAG 的机制实验入口。每个步骤只维护自己的运行命令、实验变量、输出观察和代码阅读路径；课程原理仍在 `course/`，产品安装和配置仍在 `review_assistant/README.md`。

## 学习顺序

```text
10 Embedding 表示
→ 11 Lexical Retrieval + PostgreSQL FTS
→ 12 pgvector Dense Retrieval
→ 13 RRF 融合
→ 14 Retriever 控制与诊断
→ 15 Context 装配
→ 16 结构化生成与 Citation Candidate
```

按步骤进入：

| 步骤 | 操作文档 | 课程机制 | 运行入口 |
| --- | --- | --- | --- |
| 10 | 本 README 的 Embedding 入口 | [Embedding 表示与向量相似度](../../../course/mechanisms/embedding-and-similarity.md) | [`inspect_embedding.py`](inspect_embedding.py) |
| 11 | [从空库到第一次按词检索](docs/11-lexical-retrieval.md) | [Lexical Retrieval、BM25 边界与 PostgreSQL FTS](../../../course/mechanisms/lexical-retrieval.md) | [`inspect_lexical_retrieval.py`](inspect_lexical_retrieval.py) |
| 12 | [pgvector Dense Retrieval](docs/12-pgvector-dense.md) | [pgvector、Dense Retrieval 与向量索引](../../../course/mechanisms/vector-store-and-pgvector.md) | [`inspect_dense_retrieval.py`](inspect_dense_retrieval.py) |
| 13 | [Lexical + Dense + RRF](docs/13-rrf.md) | [多路召回与 RRF 融合](../../../course/mechanisms/multi-retrieval-and-rrf.md) | [`inspect_rrf_retrieval.py`](inspect_rrf_retrieval.py) |
| 14 | [固定 Retriever 控制与诊断](docs/14-retriever-contract.md) | [Top-k、阈值、Metadata Filter 与 Retrieval 诊断](../../../course/mechanisms/retriever-contract.md) | [`inspect_retrieval_contract.py`](inspect_retrieval_contract.py) |
| 15 | [从 RetrievalResult 到 BuiltContext](docs/15-context.md) | [Context Engineering](../../../course/mechanisms/context-engineering.md) | [`inspect_rag_context.py`](inspect_rag_context.py) |
| 16 | [结构化生成与 Citation Candidate](docs/16-trusted-generation.md) | [可信生成](../../../course/mechanisms/trusted-generation.md) | [`inspect_trusted_generation.py`](inspect_trusted_generation.py) |

## 共享规则

- 主路径使用真实 PostgreSQL、真实 Embedding 和真实模型；缺少配置或外部服务失败时返回非零状态，不回退到 SQLite、Mock 或静态结果。
- 步骤 11 使用固定 `order_rules.md` fixture 写入 `rag_chunks`，不代表产品已有用户资料管理 API。
- 步骤 12 起需要 `0002` migration、真实 Embedding 配置和 pgvector；步骤 11 只执行 `0001`。
- 详细数据库 Role、Database、环境变量和 migration 由 [`review_assistant/README.md`](../../../review_assistant/README.md#postgresql-本地准备) 维护。
- SQL 展开观察见 [`sql/README.md`](sql/README.md)。

## 步骤 10：Embedding 成对相似度

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --verbose
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py --log-format json
```

需要显式配置真实 Embedding 凭证。该实验只观察句对表示距离，不匹配整库候选，也不证明最终证据质量。

## 测试

```bash
uv run pytest source/packages/rag_core/tests/test_lexical.py source/packages/rag_core/tests/test_postgres_fts.py -q -m "not integration"
uv run pytest source/packages/rag_core/tests/test_pgvector_dense.py -q -m "not integration"
uv run pytest source/packages/rag_core/tests/test_rrf.py -q
uv run pytest source/packages/rag_core/tests/test_hybrid_retriever.py -q
uv run pytest source/packages/rag_core/tests/test_rag_context.py source/packages/llm_core/tests/test_context.py -q
uv run pytest source/packages/rag_core/tests/test_trusted_generation.py source/packages/llm_core/tests/test_client_structured.py -q
```

真实 PostgreSQL 集成测试使用独立测试库：

```bash
TEST_DATABASE_URL="$DATABASE_URL" uv run pytest source/packages/rag_core/tests/test_postgres_fts.py -q -m integration
uv run pytest source/packages/rag_core/tests/test_pgvector_dense.py -q -m integration
```
