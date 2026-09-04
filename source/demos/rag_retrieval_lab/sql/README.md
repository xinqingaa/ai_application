# Lexical Retrieval 调试 SQL

这些文件**只用于本地观察** `review_assistant.rag_chunks`，方便对照词面检索实验。它们不是 migration，不会改表结构，也不写入产品代码路径。

在 GUI 里把很长的 `content`、`lexical_text`、`search_vector` 挤在一张宽表里，终端会折成一团。请用这里的脚本，不要把 `SELECT ...` 存成临时文件名。

## 怎么跑

在仓库根目录（已 `source .env`，且 `psql` 在 `PATH` 中）：

```bash
set -a && source .env && set +a

# 先看两行摘要（窄表，终端可读）
psql "$DATABASE_URL" -f source/demos/rag_retrieval_lab/sql/list_chunk_previews.sql

# 再看原文 / 拆词 / 词袋（每列单独一行）
psql "$DATABASE_URL" -f source/demos/rag_retrieval_lab/sql/inspect_rag_chunks.sql
```

Cursor 的 PostgreSQL 插件若仍用宽表预览，改在终端执行上面两条，或在插件查询里只用 `list_chunk_previews.sql` 的 `SELECT`。

## 文件

| 文件 | 用途 |
| --- | --- |
| `list_chunk_previews.sql` | 只列出 `chunk_id` 和单行原文摘要 |
| `inspect_rag_chunks.sql` | 展开显示 `content`、`lexical_text`、`search_vector` |

## 对照查询

下面的 SQL 只读数据库，不会重新执行 Loader、Chunker 或应用词法分析。它们适合把 Python 命令已经写入的资料，单独从 PostgreSQL 这一层拿出来观察。

### 词项分别命中哪些 Chunk

```sql
WITH q AS (
    SELECT websearch_to_tsquery('pg_catalog.simple', '售后') AS tsq
)
SELECT
    c.chunk_id,
    ts_rank(c.search_vector, q.tsq) AS rank,
    c.content
FROM review_assistant.rag_chunks AS c
CROSS JOIN q
WHERE c.search_vector @@ q.tsq
ORDER BY rank DESC, c.chunk_id;
```

预期 `售后` 可以命中包含售后规则的多个 Chunk。把查询词替换为 `techidsourcechannel` 后，预期只命中接口约束 Chunk。这里看到的是倒排索引和数据库匹配，不是语义相似度。

### OR 与 AND 的数据库层对照

```sql
WITH queries AS (
    SELECT
        'OR' AS mode,
        websearch_to_tsquery('pg_catalog.simple', '售后 OR 接口') AS tsq
    UNION ALL
    SELECT
        'AND',
        websearch_to_tsquery('pg_catalog.simple', '售后 接口')
)
SELECT
    q.mode,
    c.chunk_id,
    ts_rank(c.search_vector, q.tsq) AS rank,
    c.content
FROM queries AS q
JOIN review_assistant.rag_chunks AS c
  ON c.search_vector @@ q.tsq
ORDER BY q.mode, rank DESC, c.chunk_id;
```

预期 OR 的结果不少于 AND；AND 只保留同时包含“售后”和“接口”的 Chunk。SQL 中的结果只说明数据库匹配，不包含应用实际拆词、配置版本或结构化错误。

若要观察应用完整链路，请回到 `inspect_lexical_retrieval.py --verbose`；若要机器可读地比较匹配总数和返回数，请使用 `--log-format json`。

完整操作顺序见 [实验篇](../../../../course/lessons/011.lexical-retrieval.lab.md)；词面机制见 [课程正文](../../../../course/lessons/011.lexical-retrieval.mechanism.md)。
